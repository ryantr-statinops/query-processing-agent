# DataMate · Zalo AI Challenge 2026

**Planning draft · November 5, 2026 (GMT+7)**

The project aims to build a harness that turns raw business data and a Vietnamese question into a valid DataMate submission. The same harness will measure how retrieval, reranking, and policy learning affect performance on businesses held out from model development.

## Reading order

1. [Challenge scope, scoring, and rules](01-competition.md) covers inputs, outputs, deadlines, and Docker constraints.
2. [Agent harness design](02-harness.md) breaks the pipeline into testable components and walks through a question from raw data to answer.
3. [Reranking, decision policies, and model training](03-methods.md) defines each method, its objective, and when RL is worth testing.
4. [Implementation and evaluation plan](04-workplan.md) specifies the experiment sequence, metrics, milestones, and submission checklist.

## Design hypothesis

An end-to-end harness is feasible within the competition schedule if the offline baseline runs early and the team has compute for a Docker rehearsal. The baseline retrieves the relevant schema and rules, generates one SQL query, executes it with read-only access, and exports a typed answer for local scoring. Later work should follow the failure modes measured on that baseline. Expected score and runtime remain open until the team runs the official kit and profiles inference.

The quantitative research question is **how to make decisions under uncertainty and a compute budget**. Measure whether the generator produces a correct candidate, whether the verifier selects it when it is available, and whether the decision policy knows when to answer, gather more evidence, or abstain. When comparing verifiers, keep the candidate pool fixed so changes in generation do not affect the comparison.

## First working session

1. Get the official kit from the **Data** tab. Record the release or archive hash, open the rulebook and evaluator, and inspect a sample of each available file format.
2. Assign training businesses to development, calibration, and holdout groups before choosing examples or building prompts.
3. Pick one lookup and one single-table aggregate from the development group. Write the SQL by hand, record the execution trace, serialize the answers, and check both with the evaluator. Test a labeled `unanswerable` question and the `abstain` action separately.
4. Replace the handwritten queries with one generation from a local model and score the same cases again.

The interfaces, examples, and milestones in these documents describe the proposed implementation.
