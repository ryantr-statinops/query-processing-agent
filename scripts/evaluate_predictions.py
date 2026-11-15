"""Score a prediction JSONL against development references and grouped splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from datamate.evaluation.grouped import evaluate_predictions_grouped
from datamate.evaluation.splits import load_split_manifest


ROOT = Path(__file__).resolve().parents[1]


def _load_unique_jsonl(path: Path, id_field: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON in {path}:{line_number}: {error}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected a JSON object in {path}:{line_number}")
            record_id = record.get(id_field)
            if not isinstance(record_id, str) or not record_id:
                raise ValueError(f"Missing string {id_field} in {path}:{line_number}")
            if record_id in records:
                raise ValueError(f"Duplicate {id_field} {record_id!r} in {path}:{line_number}")
            records[record_id] = record
    return records


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_files(
    predictions_path: Path,
    *,
    output_path: Path,
    split: str = "development",
    exploratory_holdout: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    if split not in {"development", "holdout"}:
        raise ValueError("split must be development or holdout")
    if split == "holdout" and not exploratory_holdout:
        raise ValueError(
            "holdout labels have already been exposed; pass --exploratory-holdout to score them"
        )

    questions = _load_unique_jsonl(root / "train/questions.jsonl", "id")
    references = _load_unique_jsonl(root / "train/answers.jsonl", "id")
    predictions = _load_unique_jsonl(predictions_path, "id")
    manifest_path = root / "configs/splits/seed_2026.json"
    manifest = load_split_manifest(manifest_path)

    if set(questions) != set(references):
        raise ValueError("Question and reference IDs must match exactly")
    unknown_predictions = set(predictions) - set(questions)
    if unknown_predictions:
        raise ValueError(f"Prediction IDs are unknown to train questions: {sorted(unknown_predictions)[:5]}")

    selected_businesses = set(manifest[f"{split}_businesses"])
    selected_questions = [
        question
        for question in questions.values()
        if question.get("business_id") in selected_businesses
    ]
    selected_ids = {question["id"] for question in selected_questions}
    selected_references = {question_id: references[question_id] for question_id in selected_ids}
    selected_predictions = {question_id: predictions[question_id] for question_id in selected_ids if question_id in predictions}

    report = evaluate_predictions_grouped(
        selected_questions,
        selected_predictions,
        selected_references,
        group_key="business_id",
    )
    by_answer_type: dict[str, dict[str, Any]] = {}
    for answer_type in sorted({reference["type"] for reference in selected_references.values()}):
        type_questions = [
            question
            for question in selected_questions
            if selected_references[question["id"]]["type"] == answer_type
        ]
        type_ids = {question["id"] for question in type_questions}
        by_answer_type[answer_type] = evaluate_predictions_grouped(
            type_questions,
            {question_id: answer for question_id, answer in selected_predictions.items() if question_id in type_ids},
            {question_id: answer for question_id, answer in selected_references.items() if question_id in type_ids},
        )["overall"]

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    report["by_answer_type"] = by_answer_type
    report["metadata"] = {
        "split": split,
        "exploratory_only": split == "holdout",
        "holdout_notice": (
            "The 12 representative holdout labels have already been exposed; this score is exploratory."
            if split == "holdout"
            else None
        ),
        "questions": len(selected_questions),
        "predictions_present": len(selected_predictions),
        "missing_predictions": len(selected_ids - set(selected_predictions)),
        "manifest_sha256": manifest["manifest_sha256"],
        "predictions_sha256": _sha256(predictions_path),
        "questions_sha256": _sha256(root / "train/questions.jsonl"),
        "references_sha256": _sha256(root / "train/answers.jsonl"),
        "commit": commit,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="submission-style prediction JSONL")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/evaluation/score.json")
    parser.add_argument("--split", choices=("development", "holdout"), default="development")
    parser.add_argument(
        "--exploratory-holdout",
        action="store_true",
        help="required to score exposed holdout labels; report is marked exploratory",
    )
    args = parser.parse_args(argv)
    predictions_path = args.predictions.resolve()
    output_path = args.output.resolve()
    try:
        report = evaluate_files(
            predictions_path,
            output_path=output_path,
            split=args.split,
            exploratory_holdout=args.exploratory_holdout,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({"output": str(output_path), "split": args.split, **report["overall"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
