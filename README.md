# DataMate — ZAIC 2026

This repository is being rebuilt as an offline agentic RAG system for the DataMate challenge. The previous solver implementation has been removed. The current work is focused on understanding the business data, tracing representative training questions, and agreeing on an inference contract before implementing a new runtime.

## Proposed answer flow

```text
question + business_id + as_of_date
  → retrieve business schema, README, rulebook and entity evidence
  → model proposes a structured plan
  → validate and execute a read-only data tool
  → verify evidence and serialize a typed answer
```

This is a target design, not a runnable implementation yet. Model choice, retrieval method, plan format and package layout remain open until the data tracing phase is complete.

## Data and rules

- Competition rules and answer format: [docs/01-competition.md](docs/01-competition.md).
- Data totals and per-business inventory: [docs/data-inventory.md](docs/data-inventory.md).
- Initial read-only schema scan: [docs/data-schema-catalog.md](docs/data-schema-catalog.md). Workbook headers and dimensions still need verification.
- Representative set: `configs/representative_questions.json` contains 60 train questions, two per business. Twelve are from the manifest holdout group and have already been exposed during exploration; they are not an independent holdout evaluation set.
- The source packages, rulebooks, labels, models and generated experiment artifacts are local and must not be committed.

## Preparation scripts

Run the available preparation steps from the repository root:

```powershell
uv run --locked --no-sync python scripts/run_pipeline.py
```

This verifies/extracts the datasets, checks their JSONL and business-directory structure, prepares the Qwen3.5-9B Q4_K_M weights (about 5.68 GB), and writes JSON reports under `artifacts/`. Use `--data-only` to skip model weights, `--skip-data-setup` to use extracted data, or `--skip-model-download` to skip model verification/download. Individual checks can also run with `scripts/inspect_data.py` and `scripts/check_environment.py`.

The pipeline prepares inputs only. Inference and model benchmarking become available after the `src/datamate` runtime is rebuilt.

## Current status

`src/` contains only a rebuild marker; there is no supported inference entrypoint or baseline command today. The data setup script remains at `scripts/setup_data.py`. The old source tree was removed, so the checked-in tests and experiment scripts that import `datamate` require a new package scaffold or replacement before they can serve as passing project checks.

Do not run a full benchmark or treat historical reports as current solver performance. The team plan defines the gates for data validation, inference design, runtime and evaluation.

## Documentation

Start with the [documentation index](docs/README.md), then read the [proposed agentic RAG architecture](docs/architecture/agentic-rag.md) and the [team rebuild plan](docs/plan/rebuild.md).
