# Query Processing Agent

Offline baseline and experiment harness for **Track 2 · DataMate** at Zalo AI Challenge 2026. It loads one business package, uses a local GGUF model to generate up to three read-only SQL candidates, and emits typed answers in the competition JSONL format.

## Stack

- `uv` manages the Python environment and checked-in `uv.lock`.
- Polars and Fastexcel use Rust-backed CSV/Excel processing.
- Apache DataFusion executes SQL through its Rust query engine.
- `mistralrs` runs the local GGUF model with its Rust inference engine.
- NumPy and scikit-learn provide small feature-based reranker and fitted-Q policy estimators.

## Setup

Install [uv](https://docs.astral.sh/uv/) and Python 3.10–3.13, then from the repository root:

```powershell
uv sync --locked
uv run python scripts/setup_data.py
uv run python scripts/download_model.py
```

The model and competition data remain local and are excluded from Git. To use a different model path:

```powershell
$env:DATAMATE_MODEL_PATH = "D:\path\to\qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
```

The loader uses one inference request at a time, disables prefix caching, tokenizes and trims each prompt to fit a 3,072-token request budget, and caps generation at 384 tokens. Set `DATAMATE_CONTEXT_SIZE` to change the budget after measuring memory and quality. The checked-in PyPI `mistralrs` dependency is the CPU runtime. The Dockerfile can replace it with a matching Linux CUDA wheel and cap the planned GPU memory to `3GiB`; set `DATAMATE_MEMORY_GOAL=none` for CPU-only inference.

## Experiment workflow

1. Create the fixed business-level split manifest:

   ```powershell
   uv run python scripts/make_splits.py
   ```

2. Generate and save candidate SQL, execution evidence, features, and train-only labels:

   ```powershell
   uv run python scripts/collect_candidates.py
   ```

   Use `--limit 20` for a quick smoke run. Remove that option for the full experiment; the 3,000-question collection makes up to 9,000 local model calls.

3. Run grouped OOF comparisons, fit the final development reranker and policy, and evaluate the reserved holdout once:

   ```powershell
   uv run python scripts/evaluate_experiment.py
   ```

   Results and fitted artifacts go under the Git-ignored `artifacts/` folder. The collector reads only `train/`; `public_test/` is only supplied to inference.

## Inference and Docker interface

`predict.sh` takes no arguments, reads `/data/questions.jsonl`, loads `/data/data/<business_id>/`, and writes `/result/submission.jsonl` plus per-question records under `/result/logs/`. Set `DATAMATE_MODEL_PATH`, `DATAMATE_RERANKER_PATH`, and `DATAMATE_POLICY_PATH` in the image environment if using the local model and trained artifacts. Without a model, the runner writes `abstain` answers, which is useful only for checking the output plumbing.

For the same CLI locally, run `uv run python -m datamate --help`. The package boundaries and shared candidate flow are described in the [package architecture](docs/05-package-architecture.md).

Each log has the required `id`, `answer`, `elapsed_ms`, and `thinking` fields, plus SQL in `code`, execution evidence in `output`, and candidate selection metadata.

Build the CPU image after downloading the model. Without evaluated artifacts it runs the candidate generator without a trained reranker or policy:

```powershell
docker build -t datamate:cpu .
```

For the evaluator GPU, pass the upstream `mistralrs` CUDA wheel URL that matches its driver and GPU, and reserve a 3 GiB memory goal:

```powershell
docker build -t datamate:gpu `
  --build-arg MISTRALRS_CUDA_WHEEL_URL="<matching upstream wheel URL>" `
  --build-arg DATAMATE_MEMORY_GOAL=3GiB .
```

The GPU wheel has to be chosen for the evaluator hardware; the local Quadro T1000 and Docker evaluator may need different runtime builds. The Docker image includes the model weights but expects `/data` mounted read-only and `/result` mounted writable.

## Documentation

- [Documentation index](docs/README.md)
- [Challenge scope, scoring, and rules](docs/01-competition.md)
- [Agent harness design](docs/02-harness.md)
- [Reranking, decision policies, and model training](docs/03-methods.md)
- [Implementation and evaluation plan](docs/04-workplan.md)
- [Package architecture](docs/05-package-architecture.md)
