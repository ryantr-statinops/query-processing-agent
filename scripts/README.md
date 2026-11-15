# Script index

Run commands from the repository root with the locked uv environment. The commands
listed here are the supported preparation, runtime-baseline, evaluation, catalog, and
tracing interfaces. The runner uses a fail-closed abstention until a local planner is
integrated; synthetic fake planners are exercised by tests. Detailed catalog flags and
source-evidence limitations are documented in the catalog handoff.

## Supported workflows

| Area | Command | Purpose |
| --- | --- | --- |
| Preparation | `uv run python scripts/run_pipeline.py --help` | Validate/extract local data and prepare optional model weights. Use `--data-only` to avoid model setup. |
| Preparation checks | `uv run python scripts/inspect_data.py` and `uv run python scripts/check_environment.py` | Inspect local data and environment readiness. |
| Runtime baseline | `uv run --locked --no-sync python -m datamate --help` | Show the offline runner arguments. Without an injected planner, the runner writes typed abstentions and per-question logs. |
| Runtime entrypoint | `sh predict.sh` | Evaluator-compatible argument-free wrapper; currently fail-closed until the local GGUF planner is integrated. |
| Catalog | `uv run python scripts/build_data_catalog.py --help` | Scan source files and produce the initial catalog artifacts. |
| Catalog | `uv run python scripts/review_data_catalog.py --help` | Add read-only semantic and relationship evidence. |
| Catalog | `uv run python scripts/validate_data_catalog.py --help` | Validate artifact structure, source fingerprints, and review provenance. |
| Tracing | `uv run python scripts/trace_full_dataset.py` | Rebuild the development trace from the checked-in definitions and representative questions. |
| Tracing | `uv run python scripts/verify_phase_criteria.py` | Run the independent tracing criteria audit against local data. It reads local source records, may take several minutes, and exits non-zero when discrepancies remain. |
| Evaluation | `uv run python scripts/evaluate_predictions.py --predictions <submission.jsonl>` | Score predictions on development businesses and write reproducibility metadata to `artifacts/evaluation/score.json`. Exposed holdout scoring requires `--split holdout --exploratory-holdout`. |
| Analysis | `uv run python -m analysis.questions --help` and `uv run python -m analysis.sources --help` | Run local, exploratory question and source-file inspections. |

The scanner, reviewer, and validator are implemented in
`src/datamate/data/catalog_audit/`. Runtime catalog loading and read-only SQL live in
`src/datamate/data/catalog.py` and `src/datamate/execution/sql.py`. Trace comparison
and SQL audit helpers live in `src/datamate/evaluation/tracing/`; the split-aware
scorer lives in `src/datamate/evaluation/`. `trace_records.json` is a development
input, not inference package data.

## Archived solver tools

These implementations are retained for historical reference. Their runtime imports
are not present in the current package, so they are not supported workflows yet.
The former root-level compatibility wrappers have been removed. These archived
implementations remain under `scripts/legacy/` and still require the runtime packages
listed in the status column.

| Former entry point | Implementation path | Status |
| --- | --- | --- |
| `scripts/benchmark_purchase_intent.py` | `scripts/legacy/benchmark_purchase_intent.py` | Requires removed application, data, evaluation, and ranking packages. |
| `scripts/collect_candidates.py` | `scripts/legacy/collect_candidates.py` | Requires the removed candidate pipeline and local model runtime. |
| `scripts/evaluate_deterministic_dev.py` | `scripts/legacy/evaluate_deterministic_dev.py` | Requires removed application and grouped-evaluation modules. |
| `scripts/evaluate_experiment.py` | `scripts/legacy/evaluate_experiment.py` | Requires removed evaluation and ranking modules. |
| `scripts/make_splits.py` | `scripts/legacy/make_splits.py` | Requires the not-yet-implemented runtime split package. |
