"""Read-only inventory and structural checks for the local DataMate packages."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read_jsonl(path: pathlib.Path) -> tuple[list[dict], list[str]]:
    rows, errors = [], []
    with path.open(encoding="utf-8-sig") as stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("record must be a JSON object")
                rows.append(row)
            except (json.JSONDecodeError, ValueError) as error:
                errors.append(f"{path.name}:{line_no}: {error}")
    return rows, errors


def inspect(name: str, include_answers: bool) -> dict:
    root = ROOT / name
    result = {"name": name, "present": root.is_dir(), "questions": 0,
              "businesses": 0, "business_ids": [], "file_count": 0,
              "formats": {}, "errors": []}
    if not root.is_dir():
        result["errors"].append(f"Missing directory: {root}")
        return result
    question_file = root / "questions.jsonl"
    if not question_file.is_file():
        result["errors"].append("Missing questions.jsonl")
        return result
    questions, errors = read_jsonl(question_file)
    result["errors"].extend(errors)
    result["questions"] = len(questions)
    ids = [q.get("id") for q in questions]
    if None in ids:
        result["errors"].append("Some questions have no id")
    if len(ids) != len(set(ids)):
        result["errors"].append("Duplicate question IDs")
    business_ids = sorted({q.get("business_id") for q in questions if q.get("business_id")})
    result["business_ids"] = business_ids
    result["businesses"] = len(business_ids)
    if include_answers and (root / "answers.jsonl").is_file():
        answers, answer_errors = read_jsonl(root / "answers.jsonl")
        result["errors"].extend(answer_errors)
        answer_ids = [a.get("id") for a in answers]
        if len(answer_ids) != len(set(answer_ids)):
            result["errors"].append("Duplicate answer IDs")
        result["answers"] = len(answers)
        if set(ids) != set(answer_ids):
            result["errors"].append("Question and answer IDs do not match")
        result["answer_types"] = dict(collections.Counter(a.get("type", "missing") for a in answers))
    data_dir = root / "data"
    if not data_dir.is_dir():
        result["errors"].append("Missing data/ directory")
    else:
        actual = {p.name for p in data_dir.iterdir() if p.is_dir()}
        result["missing_business_dirs"] = sorted(set(business_ids) - actual)
        if result["missing_business_dirs"]:
            result["errors"].append("Some question businesses have no data directory")
        files = [p for p in data_dir.rglob("*") if p.is_file()]
        result["file_count"] = len(files)
        result["formats"] = dict(collections.Counter(p.suffix.lower() or "[no extension]" for p in files))
    result["calendar_present"] = (root / "calendar.csv").is_file()
    result["rulebook_present"] = (root / "rulebook.md").is_file()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("train", "public_test", "all"), default="all")
    parser.add_argument("--output", type=pathlib.Path, help="Optional JSON report path.")
    args = parser.parse_args()
    names = ("train", "public_test") if args.dataset == "all" else (args.dataset,)
    reports = [inspect(name, name == "train") for name in names]
    output = {"datasets": reports, "ok": all(not report["errors"] for report in reports)}
    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
