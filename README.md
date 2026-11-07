# Query Processing Agent

**Current stage · Planning**

Query Processing Agent is a proposed entry for **Track 2 · DataMate** at Zalo AI Challenge 2026. The agent will answer Vietnamese questions about business records in CSV, Excel, or SQLite. It will return a typed answer, predict `unanswerable` when the data cannot support an answer, or `abstain` when the evidence is too weak to commit. [DataMate challenge](https://challenge.zalo.ai/portal/datamate/)

## Planned approach

1. Build an offline baseline that loads the business data, generates one SQL query, executes it with read-only access, and writes JSONL for the official evaluator.
2. Test reranking at two stages. Retrieve relevant schema and business rules before generating SQL, then use execution evidence to rank the resulting answers.
3. Calibrate a decision policy that can answer, gather more evidence, or stop. Use results from held-out businesses to decide whether to fine-tune the SQL generator or try reinforcement learning for a policy that can take several steps.

## Project status

The repository contains the challenge brief, proposed architecture, and evaluation plan. The first implementation milestone is to take one question from its raw data package to a valid JSONL prediction and check the score with the official evaluator.

## Get the DataMate data

After cloning the repository, run:

```powershell
python scripts/setup_data.py
```

The script downloads the official training and public-test archives when they are not already present, verifies their pinned SHA-256 hashes and ZIP integrity, then extracts them into `train/` and `public_test/`. It uses only Python's standard library. The downloaded archives and extracted competition data are ignored by Git and are not committed to the repository.

To use a local archive, place it at the repository root as `train.zip` or `public_test.zip` before running the script. If the organizers publish updated archives, update the official URLs and SHA-256 values in the setup script after verifying the release.

## Documentation

- [Documentation index](docs/README.md)
- [Challenge scope, scoring, and rules](docs/01-competition.md)
- [Agent harness design](docs/02-harness.md)
- [Reranking, decision policies, and model training](docs/03-methods.md)
- [Implementation and evaluation plan](docs/04-workplan.md)
