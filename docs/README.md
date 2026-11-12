# DataMate documentation

This repository is in a rebuild phase. Documents under **Current project** describe challenge requirements, local data and the proposed agent architecture. Archived pages preserve design drafts or measurements for the removed solver; they are not instructions for the new runtime.

## Current project

1. [Challenge rules and answer contract](01-competition.md)
2. [Data inventory](data-inventory.md)
3. [Initial schema catalog](data-schema-catalog.md)
4. [Agentic RAG architecture proposal](architecture/agentic-rag.md)
5. [Harness responsibilities and evidence flow](02-harness.md)
6. [Team rebuild plan](plan/rebuild.md)

The team-specific execution briefs are in `docs/plan/01-data-catalog.md` through `docs/plan/05-evaluation-integration.md`.

## Archived material

See [archive index](archive/README.md) for superseded methods, workplan, package layout and runtime notes, plus the historical rulebook coverage audit. Do not use archived package paths or scores as current implementation status.

## Documentation policy

- Mark proposed architecture separately from implemented behavior.
- Keep source data, gold answers, model weights and generated experiment outputs out of Git.
- Update implementation and run instructions only after the relevant runtime command has been verified.
