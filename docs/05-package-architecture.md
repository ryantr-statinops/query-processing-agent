# Package architecture

`src/datamate` is an installable Python package managed by `uv`. The `datamate` import name is configured explicitly because the distribution name is `query-processing-agent`. Run the inference CLI with `uv run python -m datamate`; `predict.sh` uses the same module entrypoint without evaluator-supplied arguments.

## Package map

| Package | Responsibility |
| --- | --- |
| `application` | Coordinate a question, build candidates, construct the typed answer, and write submissions and logs. |
| `data` | Load business tables, prepare calendar context, and define deterministic business splits. |
| `execution` | Run read-only SQL against the in-memory business catalog. |
| `generation` | Adapt the local GGUF model runtime to the SQL-candidate interface. |
| `ranking` | Extract inference-time candidate features, rerank candidates, and choose whether to submit, abstain, or generate more. |
| `evaluation` | Compare typed answers with training references and calculate development metrics. |

## Dependency direction

`application` composes the other packages. `data`, `execution`, `generation`, and `ranking` provide inference components and do not depend on `application`. `evaluation` is used by development scripts to score candidate traces; inference code does not import it or load reference answers.

## Question flow

1. `application.runner` reads question JSONL and initializes the agent and optional trained artifacts.
2. `application.agent` selects the business catalog and asks `application.candidates` to generate and execute candidates.
3. The candidate pipeline combines `data` context, local `generation`, read-only `execution`, and inference-only `ranking.features`.
4. The agent applies the optional reranker and policy, constructs the typed answer, then returns a trace to the runner.
5. The runner writes the unchanged submission contract to `/result/submission.jsonl` and diagnostics to `/result/logs/`.

The train candidate collector calls the same candidate pipeline and then uses `evaluation.labels` to attach training rewards. This keeps reference-based scoring outside inference while avoiding two separate implementations of SQL generation and execution.

## Development checks

Use `uv sync --locked` to install the package and dependencies. Run `uv run python -m datamate --help` to inspect the inference CLI, and `uv run python -m unittest discover -s tests -v` for unit and smoke tests. The grouped manifest is stored at `configs/splits/seed_2026.json`.
