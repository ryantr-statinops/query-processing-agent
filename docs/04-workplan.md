# Implementation and evaluation plan

## Evaluation protocol

Split the official training data **by business**. Use the `fit` group to develop prompts, build the few-shot index, train rerankers and decision models, and fine-tune the generator. Use the `calibration` group to calibrate probabilities, choose the threshold, and select among candidate configurations. Reserve the `holdout` group for a prespecified comparison and the final check. With few businesses, use grouped cross-validation within development to obtain out-of-fold predictions for the verifier or decision model while keeping a separate holdout. Keep every table and question variant from the same business in one group. Record business counts, question counts, answer types, and major error categories per split. During evaluation, the agent still receives the current question's business package and shared rules.

| Metric | What it tells us |
| --- | --- |
| PA and correct, wrong, and abstain counts | How a configuration performs under competition scoring. Report correct `unanswerable` predictions, false `unanswerable` predictions, and abstentions separately. |
| Coverage and accuracy at that coverage | Coverage is the fraction of questions receiving a prediction other than `abstain`, including `unanswerable`. For positive coverage, `PA = coverage × (2 × accuracy among answered questions − 1)`. Plot PA and error rate across coverage levels as the threshold varies. |
| Evidence recall@k and prompt tokens | Whether the prompt contains the required fields and rules. Measure recall on questions with annotated evidence. |
| Oracle@N and top-1 correctness | Oracle@N is the fraction of questions with a candidate that matches the reference before the gate. Compare top-1 correctness on the same candidate pool and report results separately for answerable questions. |
| Parse, execution, and semantic errors | Track parse failures, SQL errors, timeouts, serialization errors, and queries that run but produce the wrong answer. |
| Calibration | Measure Brier score, reliability by confidence range, and observed accuracy around the decision threshold. Break down by question type or source format where sample sizes allow. |
| Resource use | Measure p50 and p95 latency, generation and query counts, token usage, peak VRAM, data and model loading, throughput, and total wall-clock time. Include a cold Docker run. |

On 100 questions, 60 correct, 20 wrong, and 20 abstentions yield PA of 0.40. If a new policy abstains on 10 of those wrong answers and three of the correct answers, the counts become 57 correct, 10 wrong, and 33 abstentions, for PA of 0.47. Report the counts alongside PA. Compare configurations on the same questions. When the sample contains enough businesses, bootstrap at the business level so the uncertainty estimate accounts for correlated errors within a data package. Report slices by CSV, Excel, or SQLite source, answer type, business operation, and failure mode.

## Experiment sequence

Use the same split and evaluator for each comparison. Keep the seed, checkpoint, prompt, resource limits, and candidate pool fixed where the experiment allows. Save each configuration and its per-question changes.

| Run | Change | Evidence needed to proceed |
| --- | --- | --- |
| B0 | Run handwritten SQL on synthetic fixtures and selected fit questions. Compare the output with the official evaluator. | Data loads correctly, JSONL matches the contract, and scoring handles correct, wrong, `unanswerable`, and `abstain` cases. |
| B1 | Use a local model, a compact schema, one SQL generation, and read-only execution. | End-to-end local scores by business and traces that identify the failing stage. |
| E1 | Add lexical retrieval that keeps the keys needed for joins. Try context reranking if evidence coverage warrants it. | Check that evidence recall improves or holds steady, then compare prompt size, latency, and PA on retrieval-dependent questions. |
| E2 | Compare `N=1` with `N=2–3`, estimate oracle@N, then compare heuristic and learned verifiers on the same pool. | Higher oracle coverage at an acceptable cost and a verifier that turns some of that gain into higher PA. |
| E3 | Compare a rule-based gate with calibrated logistic regression. | Compare PA, wrong-answer count, coverage, and stability across businesses, including `unanswerable` predictions. |
| E4 | Compare conditional retries with a fixed schedule at the same compute budget. | A repeatable PA gain with enough time left under the Docker limit. |
| E5 | Try one filtered SFT run or one preference method if the fit split and schedule allow. | Better oracle@N, top-1 correctness, or PA under the same inference budget. Recalibrate the gate if the generator changes. |

For each run, log the run ID, commit, dataset and split hashes, prompt, model and configuration revisions, seed, candidate count and compute limits, PA and answer counts, p95 and total elapsed time, largest error category, and the decision to retain or drop the change. For the RL hypothesis, replay `stop`, `expand`, and `retry` branches on the same fit questions and measure the extra reward and compute. If existing logs contain only the action taken by a fixed policy, record which alternate actions lack evidence.

## Proposed schedule

All dates are in November 2026, GMT+7. See the competition deadlines and the release-time discrepancy in the [challenge brief](01-competition.md).

| Dates | Work | Milestone |
| --- | --- | --- |
| November 5–6 | Read the kit, rulebook, and Docker Guide. Inventory training data, freeze the splits, and run B0. | The evaluator runs locally. Key fixtures pass, and the initial question and error categories are documented. |
| November 7–9 | Implement loaders, catalog, one local model call, read-only execution, normalization, and JSONL writing. | B1 runs end to end. A Docker smoke test reads the mounted inputs and writes predictions. |
| November 10–12 | Fix the largest errors. Test retrieval, a small best-of-N pool, and a verifier. | Report changes in PA, oracle gap, and cost. Select a candidate configuration for calibration. |
| November 13–14 | Calibrate the gate and profile runtime. Try retry or SFT only if the earlier milestones are complete and time permits. | Record holdout PA and coverage for the selected configuration. Check cold-start runtime and repeatability across two runs. |
| November 15–16 | Freeze the configuration, rebuild Docker, and verify weights, logs, and checksum. | The offline image and required artifacts are ready before the submission deadline. |
| November 20–23 | Run the private test using the submitted image, validate the output, and upload JSONL. | The submission comes from the frozen solution, with logs available for comparison. |

If the schedule slips, prioritize the single-query baseline, reproducibility, and output validation. Defer the cross-encoder, larger candidate pools, fine-tuning, or sequential policy work based on measured costs. Once the workload size is known, estimate total time from model loading, ingestion, inference, and serialization on representative batches. Leave capacity for slow queries, larger packages, and recoverable failures. Add concurrency after checking resource limits and deterministic result writing.

## Before freezing the solution

- [ ] Check the latest rules and Docker Guide for the command, mount paths, log format, and required artifacts. [DataMate portal](https://challenge.zalo.ai/portal/datamate/)
- [ ] Record each model's name, weight revision, release date, license, parameter count, and quantization. Verify the combined inference parameter count.
- [ ] Build the image from scratch and run it with networking disabled and inputs mounted read-only. Confirm the package schema, rulebook, calendar, JSONL output, and logs.
- [ ] Check for duplicate or missing IDs, invalid types, malformed JSON, and encoding problems. Run the local evaluator. Simulate a timeout and verify that completed predictions remain readable.
- [ ] Repeat the run, measure cold-start cost, and estimate the full wall-clock budget. Save the image checksum, commit, dataset version, and configuration.
- [ ] Verify the required package contents and download link permissions. Submit the frozen solution by 23:59 on November 16 (GMT+7).
