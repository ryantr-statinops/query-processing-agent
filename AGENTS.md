# Repository guidance

## Environment and dependencies

- Use `uv` for Python environment and dependency management. Keep `pyproject.toml` and `uv.lock` in sync.
- Prefer the existing Rust-backed stack: Polars/Fastexcel for tabular ingestion, DataFusion for SQL execution, and `mistralrs` for local GGUF inference.
- Keep model inference offline and bounded. The runner uses one request at a time; the documented GPU memory goal is 3 GiB.

## Data and evaluation

- Treat `train/`, `public_test/`, `models/`, and generated artifacts as local data. Never commit their contents.
- Use `train/answers.jsonl` for development labels. Do not use public-test labels or scores to fit models, choose settings, or tune thresholds.
- Keep all records for a business in the same split. Use the checked-in seed-2026 manifest for grouped OOF and holdout comparisons.
- Do not change source competition data while loading or normalizing it; create in-memory representations instead.

## Inference contract

- Keep `predict.sh` argument-free for the evaluator.
- Read input and business data from `/data` and write the submission to `/result/submission.jsonl`.
- Keep per-question diagnostic logs under `/result/logs/`; do not write diagnostics into the submission JSONL.
- Execute generated SQL through the read-only DataFusion path and preserve the typed DataMate answer format.

## Project checks

- Install the locked environment with `uv sync --locked`.
- Run the existing unit and smoke tests with `uv run python -m unittest discover -s tests -v` when validating implementation changes.
- Use `git diff --check` before committing. Keep downloaded model weights, competition data, and generated experiment outputs out of commits.
