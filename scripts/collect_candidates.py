"""Generate offline candidate traces using train questions and answers only."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datamate.evaluation.labels import label_match, pa_reward  # noqa: E402
from datamate.data.calendar import calendar_context  # noqa: E402
from datamate.generation.local_gguf import LocalSQLGenerator  # noqa: E402
from datamate.features import candidate_features  # noqa: E402
from datamate.execution.sql import execute_select  # noqa: E402
from datamate.data.catalog import BusinessCatalog  # noqa: E402


def read_jsonl(path: pathlib.Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-root", type=pathlib.Path, default=ROOT / "train")
    parser.add_argument("--model-path", type=pathlib.Path, default=None)
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "artifacts" / "train_candidates.jsonl")
    parser.add_argument("--limit", type=int, default=None, help="Deterministic small smoke run; default processes all train questions")
    parser.add_argument("--candidates", type=int, default=3, choices=(1, 2, 3))
    args = parser.parse_args()
    model_path = args.model_path or pathlib.Path(os.environ.get(
        "DATAMATE_MODEL_PATH", ROOT / "models" / "qwen2.5-coder-1.5b-q4" / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
    ))
    if not model_path.is_file():
        raise FileNotFoundError(f"Model not found: {model_path}. Run scripts/download_model.py first.")

    questions = read_jsonl(args.train_root / "questions.jsonl")
    references = {row["id"]: row for row in read_jsonl(args.train_root / "answers.jsonl")}
    if args.limit is not None:
        questions = questions[:max(0, args.limit)]
    generator = LocalSQLGenerator(model_path, seed=int(os.environ.get("DATAMATE_SEED", "2026")))
    rules = (args.train_root / "rulebook.md").read_text(encoding="utf-8-sig", errors="replace")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    catalog_cache: dict[str, BusinessCatalog] = {}
    try:
        with args.output.open("w", encoding="utf-8", newline="\n") as out:
            for position, question in enumerate(questions, start=1):
                question_started = time.monotonic()
                business_id = question["business_id"]
                if business_id not in catalog_cache:
                    catalog_cache[business_id] = BusinessCatalog(args.train_root / "data" / business_id)
                catalog = catalog_cache[business_id]
                business_readme_path = args.train_root / "data" / business_id / "README.md"
                business_readme = business_readme_path.read_text(encoding="utf-8-sig", errors="replace")[:4000] if business_readme_path.is_file() else ""
                schema = catalog.schema_text(str(question.get("question", "")))
                cal = calendar_context(args.train_root / "calendar.csv", question)
                candidates: list[dict] = []
                for candidate_index in range(args.candidates):
                    raw = generator.generate_one(question, schema, candidate_index, f"{rules}\n{business_readme}", cal)
                    sql = raw.get("sql", "").strip()
                    if raw.get("type") == "unanswerable":
                        candidate = {
                            **raw,
                            "answer": {"type": "unanswerable"},
                            "result": {"ok": True, "columns": [], "rows": [], "error": None, "elapsed_ms": 0},
                        }
                    elif not sql or any(sql.casefold() == item.get("sql", "").casefold() for item in candidates):
                        continue
                    else:
                        result = execute_select(catalog, sql)
                        from datamate.application.answers import answer_from_result
                        answer = answer_from_result(raw.get("type", ""), result.columns, result.rows) if result.ok else None
                        candidate = {
                            **raw,
                            "answer": answer,
                            "result": {
                                "ok": result.ok,
                                "columns": result.columns,
                                "rows": result.rows,
                                "error": result.error,
                                "elapsed_ms": result.elapsed_ms,
                            },
                        }
                    candidates.append(candidate)
                answers = [candidate.get("answer") for candidate in candidates]
                for candidate in candidates:
                    candidate["all_answers"] = answers
                    candidate["features"] = candidate_features(
                        question, candidate, schema, f"{rules}\n{business_readme}"
                    )
                reference = references.get(question["id"])
                row_labels = [
                    {
                        **candidate,
                        "label": int(label_match(candidate["answer"], reference)) if candidate.get("answer") and reference else 0,
                        "reward": pa_reward(candidate["answer"], reference) if candidate.get("answer") and reference else 0,
                    }
                    for candidate in candidates
                ]
                out.write(json.dumps({
                    "id": question["id"],
                    "business_id": business_id,
                    "question": question,
                    "reference": reference,
                    "candidates": row_labels,
                    "generation_elapsed_ms": int((time.monotonic() - question_started) * 1000),
                }, ensure_ascii=False, default=str) + "\n")
                out.flush()
                if position % 25 == 0:
                    print(f"Collected {position}/{len(questions)} questions", file=sys.stderr)
    finally:
        for catalog in catalog_cache.values():
            catalog.close()
    print(f"Wrote candidate traces to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
