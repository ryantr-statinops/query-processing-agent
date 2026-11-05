# Reranking, decision policies, and model training

The reranker orders existing candidates. The decision policy chooses the next action from the available evidence. Training the language model changes which plans, queries, or sequences of actions it generates. All three components can share traces and labels while being evaluated separately.

| Method | What it changes | Learning or evaluation signal | Main cost |
| --- | --- | --- | --- |
| Inference-time reranking | Which context enters the prompt and which generated candidate ranks first | Evidence relevance, execution checks, and evaluator labels on training questions | Scoring context pairs, generating candidates, and executing queries |
| Harness decision policy | Whether to answer, predict `unanswerable`, abstain, or gather more evidence | Calibrated correctness, change in PA after an action, and action cost | Collecting representative traces and handling distribution shift |
| Language model training | The probability of generating useful plans, queries, or actions | Supervised examples, preference pairs, or rewards from rollouts | GPU time for rollouts and training, plus label verification |

## 1. Reranking at two stages

**Context.** Start with lexical retrieval over table and field names, README sections, rules, aliases, and representative values. Normalize text for search and preserve source values for the answer. Retrieve related fields together with the keys needed to join their tables. Annotate a small set of training questions with the required evidence. Measure per-item recall@k and the fraction of questions whose prompt contains all required evidence. If lexical retrieval misses paraphrases, try dense retrieval. Once the candidate pool has adequate recall, test a cross-encoder such as `bge-reranker-v2-m3` for ordering candidates. Measure its effect on Vietnamese questions and count it toward the inference parameter limit. [BAAI BGE models](https://bge.baai.ac.cn/)

**Output.** Compare a single greedy generation with a small best-of-N pool. Generate distinct plausible interpretations, such as summing item quantities versus counting distinct orders, then parse and execute each query in the harness. Reject invalid output types and queries that violate execution constraints. Rank valid candidates using evidence about dates, entities, units, row granularity, business rules, and agreement across distinct plans. An empty result can be correct, and several queries can agree because they share the same mistake. On labeled data, compare oracle@N, the fraction of questions with at least one correct candidate, with top-1 correctness on the same pool. The gap shows how much a better selector could recover from those candidates. This is an application of execution feedback to DataMate. [Execution-guided text-to-SQL](https://arxiv.org/abs/1807.03100)

## 2. Decide using expected competition score

Let $s$ contain the question, retrieved evidence, candidates, checks, previous actions, and remaining budget. For each normalized answer $a$, let $p_a(s)$ be the probability that the evaluator accepts **both its type and its value**. Let $p_U(s)$ be the probability that the reference is `unanswerable`. Under DataMate scoring, the best immediate expected score is the maximum over the available predictions and abstention.

$$
V_{\text{stop}}(s) = \max\left(\{0,\ 2p_U(s)-1\}\ \cup\ \{2p_a(s)-1 \mid a \in \mathcal A(s)\}\right).
$$

Here $0$ is the expected score of `abstain`, and $\mathcal A(s)$ contains the available ordinary answers. With reward $R$ for a correct prediction and penalty $C$ for a wrong one, submitting a candidate beats abstaining when $pR-(1-p)C>0$, or $p>C/(R+C)$. DataMate has $R=C=1$, so the theoretical break-even probability is **0.5**. Compare all available terminal actions and use `abstain` as a tie-break at zero. An ordinary answer with $p_a=0.62$ has expected score $+0.24$. An `unanswerable` prediction with $p_U=0.70$ has expected score $+0.40$. [DataMate evaluation](https://challenge.zalo.ai/portal/datamate/)

Start with a rule-based gate and compare it with logistic regression. Use features available at inference, such as required evidence coverage, schema checks, the ranking margin, join fan-out, result size, agreement across distinct plans, and token log probabilities when available. Label answers by evaluator correctness on training questions. Calibrate on separate businesses and check reliability and Brier score after top-1 selection, since selection can change the distribution of confidence. Compare thresholds on the calibration group and lock the policy before evaluating the holdout. Probability estimates near 0.5 deserve special attention because small calibration errors can change the action. [Calibration](https://proceedings.mlr.press/v70/guo17a.html), [Selective classification](https://papers.nips.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf)

Actions such as `expand_schema`, `generate_one_more`, and `retry_with_rule` can change the evidence and the options available. For a one-step lookahead, compare the score from stopping with $\mathbb E[V_{\text{stop}}(S')\mid s,a]-\lambda\,\mathbb E[\Delta t\mid s,a]$. The internal cost coefficient $\lambda$ trades expected points against time. PA itself scores answers, and the competition imposes a separate runtime limit. Estimate the value of an extra step by running alternate branches on the same training questions. A one-shot routing choice can be modeled as a contextual bandit. A controller that updates evidence and can act again can be modeled as a finite-horizon Markov decision process. Try offline RL only after the traces cover the relevant actions and the replay shows that additional steps can improve the result. Logs from a single fixed policy can leave alternate actions unobserved.

## 3. Train the generator when the candidate pool is the bottleneck

| Approach | Application to DataMate |
| --- | --- |
| **Supervised fine-tuning (SFT) after rejection sampling** | Generate several trajectories on the fit split. Execute them, retain correct trajectories with valid evidence, then train on the retained examples. One pass is supervised learning on filtered data. Repeating generation, filtering, and training is a form of self-training. |
| **DPO, SimPO, or ORPO** | Learn from chosen and rejected outputs for the same prompt. DPO uses a reference policy. SimPO compares length-normalized log probabilities with a margin. ORPO combines the supervised loss with an odds-ratio preference loss. These methods optimize preferences from a fixed batch of pairs. |
| **PPO or another rollout-based RL method** | Sample actions from a policy, execute them in the harness, and update the policy using rewards. For a language model, actions can be tokens or tool calls. For a controller, actions can be discrete choices such as fetching more schema or retrying, while the generator stays fixed. Account for sparse rewards, credit assignment, and rollout cost. |

[ReST](https://arxiv.org/abs/2308.08998), [DPO](https://arxiv.org/abs/2305.18290), [SimPO](https://arxiv.org/abs/2405.14734), [ORPO](https://arxiv.org/abs/2403.07691), [PPO](https://arxiv.org/abs/1707.06347)

Construct preference pairs around meaningful errors such as an incorrect date range, a count in place of a sum, a join that duplicates rows, or the wrong unit. A trajectory can match the reference by coincidence. Inspect the plan and run it on modified fixtures when the expected answer can be derived independently. Track the fraction of questions with a valid retained trajectory by error category so filtering does not leave only easy examples. If ranking by official score, the order is correct prediction, abstention, then wrong prediction. A correct `unanswerable` prediction belongs in the first group.

If oracle@N is low, check which evidence retrieval missed and which plans the generator omitted. If oracle@N is high and top-1 correctness is low, compare verifiers on the existing candidate pool first. Consider one filtered SFT run if the errors recur, the fit split yields enough valid trajectories, and the baseline Docker image already runs. Compare model changes on the same splits under the same inference budget, and recalibrate the gate if the generator changes.

## What to track besides the objective and optimizer

- **Data and state.** Track coverage across businesses, schemas, and question types. Check label quality, inference-time feature availability, action coverage, and replay fidelity.
- **Rewards and proxies.** Use PA to compare solutions. Check whether successful execution, candidate agreement, or a lower training loss actually predicts evaluator correctness. Monitor accidental matches and opportunities to exploit proxy rewards.
- **Risk and uncertainty.** Measure coverage, calibration, wrong answers, and PA by subgroup. A policy calibrated on familiar schemas can drift when business data changes.
- **Runtime and reproducibility.** Track model parameters, tokens, latency, peak memory, query counts, and repeatability inside the frozen Docker image.
