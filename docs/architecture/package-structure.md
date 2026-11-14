# Package structure and dependency boundaries

The project is an installable `src/datamate` package managed by uv. The current
inference deliverable is the version 0.1.0 contract and its guardrails; a complete
inference runtime is still pending. `python -m datamate` is the required future
inference entrypoint, but `__main__.py` is not implemented yet.

## Implemented code and refactor destinations

| Package | Responsibility |
| --- | --- |
| `agent` | Request validation, SQL planning guards, budgets, tool policy, entity resolution, typed answers and evidence verification. Public imports remain available through `datamate.agent.guardrails`. |
| `data.catalog_audit` | Read-only catalog scanning, source review and artifact validation in `build`, `review` and `validate`. Root script paths remain CLI wrappers. |
| `evaluation.tracing` | Development answer comparison and SQL audit helpers. Trace definitions and dataset records remain under `scripts/`. |

The refactor retains existing CLI paths and `datamate.agent.guardrails` imports.

## Runtime work still to implement

| Package | Future responsibility |
| --- | --- |
| `application` | Coordinate requests, build answers, write submissions and diagnostics. |
| `data` | Runtime loaders, calendar context and business catalog. |
| `execution` | Read-only DataFusion execution, cancellation and resource limits. |
| `generation` | Offline local model adapter, one request at a time. |
| `ranking` | Inference-only candidate features and selection policy. |
| `evaluation` | Development scorer, metrics and grouped comparisons. |

Do not create empty implementations to satisfy historical imports. The four legacy
test modules need runtime work and remain discoverable failures until that work exists.

## Dependency direction

`application` will compose inference components. `agent`, `data`, `execution`,
`generation` and `ranking` must not import reference-based evaluation or load gold
answers. `evaluation` may consume inference results after prediction. The development
catalog audit can check that a label file exists or count its lines for inventory;
it does not parse labels into inference context or compute answers from them.

Within `agent`, shared constants/errors are foundational. SQL validation, request
validation, budgets, entity matching and typed answers are independent helpers;
tool validation uses SQL guards, and evidence verification uses typed answers and
outcome policy. DataFusion stays lazily imported by the SQL planner.

## Commands, tests and artifacts

Use `uv sync --locked` and the script commands listed in the project README.
Run `uv run python -m unittest discover -s tests -v` for all tests. Detailed output,
source packages and models remain local under their ignored locations. A package
build or guardrail test pass does not establish a runnable inference system.

Historical solver architecture is preserved under `docs/archive/`; it does not
describe the current implementation.
