# Package structure and dependency boundaries

The project is an installable `src/datamate` package managed by uv. The current
inference contract is version 0.1.0 and remains a proposal. A synthetic runtime
slice exercises the contract with an injected fake planner; local GGUF inference
and semantic source mapping are not implemented yet.

## Implemented packages

| Package | Responsibility | Status and boundary |
| --- | --- | --- |
| `agent` | Request validation, SQL policy, budgets, tool policy, entity helpers, typed answers and evidence checks. | Implemented contract helpers. DataFusion remains lazy in the SQL plan probe. |
| `application` | Candidate pipeline, typed result conversion, output validation and question runner. | Implemented synthetic path. The CLI abstains safely when no planner is configured. |
| `data` | Generic CSV, Excel and SQLite loading into an in-memory per-business catalog; catalog audit tooling. | Loader retains source references and original-header mapping. Business grain, aliases and source roles still need semantic review. |
| `execution` | Read-only DataFusion query execution. | SQL allow-list/statement checks, logical planning, row cap and worker-process hard deadline. It reloads the business catalog for each query. |
| `generation` | Structured output parsing for candidate plans. | JSON parsing is implemented; the offline local GGUF model adapter is pending. |
| `evaluation` | Typed answer comparison, PA/coverage metrics, business-grouped scoring, split validation, and tracing audits. | Development scoring is implemented. Holdout results remain exploratory because 12 sample labels were exposed. |

`python -m datamate --data-root <path> --result-root <path>` writes typed
`submission.jsonl` and separate per-question JSONL diagnostics. Without an injected
planner, it emits typed abstentions and does not represent model quality.

## Dependency direction

`application` composes `agent`, `data`, `execution` and `generation`. `agent`,
`data`, `execution`, `generation` and future `ranking` code must not import
reference-based evaluation or load gold answers. `evaluation` may consume
predictions and references after inference. Catalog audits and trace records remain
development tools and are not included in inference context.

Within `agent`, shared constants/errors are foundational. SQL validation, request
validation, budgets, entity matching and typed answers are independent helpers;
tool validation uses SQL guards, and evidence verification uses typed answers and
outcome policy. Runtime SQL planning uses the verified in-memory catalog, while SQL
execution runs in a killable worker because the DataFusion Python API does not expose
query cancellation.

## Pending runtime work

- Implement and test the offline local GGUF planner within the approved inference
  contract and hardware budget.
- Ground intent, time, grain, filters, source roles and units against reviewed
  catalog/tracing evidence. The synthetic baseline only verifies the technical
  request-to-query-to-output path.
- Add candidate ranking and measured retries after a real planner is available.
- Run performance and accuracy evaluation on development businesses. Do not use the
  exposed representative holdout rows as independent evidence.
- Add Docker/offline acceptance after local model inference and source mapping pass.

## Commands, tests and artifacts

Use `uv sync --locked` and the script commands listed in the project README. Run
`uv run python -m unittest discover -s tests -v` for all tests. Detailed output,
source packages and models remain local under their ignored locations. A package
build or synthetic contract pass does not establish model accuracy or semantic
correctness.

Historical solver architecture is preserved under `docs/archive/`; it does not
describe the current runtime implementation.
