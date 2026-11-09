"""Evaluate the current deterministic runner on seed-2026 development only."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from datamate.application.deterministic import DeterministicAgent
from datamate.evaluation.grouped import evaluate_grouped

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    train = ROOT / "train"
    manifest = json.loads((ROOT / "configs" / "splits" / "seed_2026.json").read_text(encoding="utf-8"))
    allowed = set(manifest["development_businesses"])
    questions = [row for row in read_jsonl(train / "questions.jsonl") if row["business_id"] in allowed]
    expected = sum(manifest["question_counts"][business] for business in allowed)
    if len(questions) != expected or any(row["business_id"] not in allowed for row in questions):
        raise ValueError("Development rows do not match the seed-2026 business manifest")
    ids = {row["id"] for row in questions}
    references = {row["id"]: row for row in read_jsonl(train / "answers.jsonl") if row["id"] in ids}
    if set(references) != ids:
        raise ValueError("Development label set is incomplete")
    output = args.output or ROOT / "artifacts" / f"deterministic_dev_{datetime.now():%Y%m%d_%H%M%S}"
    output.mkdir(parents=True, exist_ok=False)
    agent = DeterministicAgent(train)
    try:
        result = evaluate_grouped(agent, questions, references)
    finally:
        for catalog in agent.catalogs.values():
            catalog.tables.clear()
    rows = result.pop("rows")
    summary = {"split": "seed_2026 development businesses only", "manifest_questions": expected,
               "evaluated_questions": len(rows), "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               **result}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "questions.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
