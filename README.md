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

The version 0.1.0 inference contract and guardrails are implemented. A synthetic fake-planner path now exercises request validation, catalog loading, read-only SQL, evidence checks, typed answers and separate logs. The contract remains a proposal with open decisions, and the local GGUF generation adapter is still pending. Package boundaries are described in [the current package architecture](docs/architecture/package-structure.md).

## Data and rules

- Competition rules and answer format: [docs/01-competition.md](docs/01-competition.md).
- Data totals and per-business inventory: [docs/data-inventory.md](docs/data-inventory.md).
- Read-only schema catalog: [docs/data-schema-catalog.md](docs/data-schema-catalog.md). Catalog and tracing tools provide the documented source evidence; detailed generated artifacts remain local.
- Representative set: `configs/representative_questions.json` contains 60 train questions, two per business. Twelve are from the manifest holdout group and have already been exposed during exploration; they are not an independent holdout evaluation set.
- The source packages, rulebooks, labels, models and generated experiment artifacts are local and must not be committed.

## Preparation scripts

Run the available preparation steps from the repository root:

```powershell
uv run --locked --no-sync python scripts/run_pipeline.py
```

This verifies/extracts the datasets, checks their JSONL and business-directory structure, prepares the Qwen3.5-9B Q4_K_M weights (about 5.68 GB), and writes JSON reports under `artifacts/`. Use `--data-only` to skip model weights, `--skip-data-setup` to use extracted data, or `--skip-model-download` to skip model verification/download. Individual checks can also run with `scripts/inspect_data.py` and `scripts/check_environment.py`.

The pipeline prepares inputs only. The baseline runner is available, but without a configured planner it deliberately abstains; it is not a model benchmark. See the [script index](scripts/README.md) for the runtime, scorer, preparation, catalog and tracing commands, plus archived tools.

## Current status

`src/datamate` contains inference-contract guardrails, a generic CSV/Excel/SQLite catalog loader, bounded read-only DataFusion execution, a fake-planner candidate pipeline, a fail-closed `python -m datamate` runner, and a development scorer. Synthetic integration tests verify submission and diagnostic JSONL against the contract. The runner has no local GGUF inference adapter yet, so its normal CLI path emits a typed abstention until one is integrated. Semantic source mapping, ranking, Docker execution and measured model evaluation remain open.

Full unittest discovery currently reports two historical import errors in `tests/legacy/` (`datamate.data.sources` and the removed deterministic solver's `datamate.application.plans`); the runtime, contract and active package suites pass.

Do not run a full benchmark or treat historical reports as current solver performance. The team plan defines the gates for data validation, inference design, runtime and evaluation.

## Documentation

Start with the [documentation index](docs/README.md), then read the [proposed agentic RAG architecture](docs/architecture/agentic-rag.md) and the [team rebuild plan](docs/plan/rebuild.md).
