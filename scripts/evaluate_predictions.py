"""Score a prediction JSONL against development references and grouped splits."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
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


def _classify_intent(question_text: str) -> str:
    """Heuristic classification of question intent for exploratory failure analysis."""
    q = question_text.lower()
    # Priority 1: Cancellation & refund
    if any(k in q for k in ["hủy", "huỷ", "hoàn", "trả hàng"]):
        return "cancellation"
    # Priority 2: Comparisons, trends and percentages
    if any(k in q for k in ["tăng", "giảm", "tỷ trọng", "tăng trưởng", "so với", "chênh lệch", "%", "phần trăm"]):
        return "comparison"
    # Priority 3: Ranking and extremum
    if any(k in q for k in ["bán chạy", "top", "cao nhất", "thấp nhất", "nhiều nhất", "ít nhất", "xếp hạng", "thứ hạng"]):
        return "ranking"
    # Priority 4: Lookups & specific entities
    if any(k in q for k in ["ngày nào", "tháng nào", "hôm nào", "ai", "ở đâu", "mã nào", "tên gì"]):
        return "lookup"
    # Priority 5: Aggregations & business metrics
    if any(k in q for k in ["doanh thu", "dthu", "revenue", "tổng", "trung bình", "aov", "số đơn", "mấy đơn", "bao nhiêu", "đếm", "nợ", "công nợ", "tồn kho"]):
        return "aggregation"
    return "general"


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
    logs_path: Path | None = None,
    pilot_48: bool = False,
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
    if pilot_48:
        rep_path = root / "configs/representative_questions.json"
        if not rep_path.is_file():
            raise FileNotFoundError(f"Representative questions config not found at {rep_path}")
        rep_data = json.loads(rep_path.read_text(encoding="utf-8"))
        rep_ids = {q["id"] for q in rep_data.get("questions", [])}
        selected_questions = [q for q in selected_questions if q["id"] in rep_ids]
        if len(selected_questions) != 48:
            raise ValueError(
                f"Expected exactly 48 representative questions for development, got {len(selected_questions)}"
            )

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

    by_intent: dict[str, dict[str, Any]] = {}
    for q in selected_questions:
        q["_intent"] = _classify_intent(q.get("question", ""))
    for intent in sorted({q["_intent"] for q in selected_questions}):
        intent_questions = [q for q in selected_questions if q["_intent"] == intent]
        intent_ids = {q["id"] for q in intent_questions}
        by_intent[intent] = evaluate_predictions_grouped(
            intent_questions,
            {qid: a for qid, a in selected_predictions.items() if qid in intent_ids},
            {qid: a for qid, a in selected_references.items() if qid in intent_ids},
        )["overall"]

    vllm_version = None
    try:
        import importlib.metadata
        vllm_version = importlib.metadata.version("vllm")
    except Exception:
        pass

    prompt_config_hash = None
    try:
        from datamate.generation.vllm_adapter import VllmPlanner

        model_env = os.environ.get("DATAMATE_MODEL_PATH", "models/qwen3.5-9b-q4/Qwen3.5-9B-Q4_K_M.gguf")
        prompt_config_hash = VllmPlanner(model_env).get_config_hash()
    except Exception:
        prompt_config_hash = hashlib.sha256(b"datamate-vllm-planner-v2").hexdigest()[:16]

    latency_summary = None
    if logs_path is not None and logs_path.is_file():
        latencies: list[int] = []
        try:
            with logs_path.open(encoding="utf-8") as stream:
                for line in stream:
                    line = line.strip()
                    if line:
                        item = json.loads(line)
                        if item.get("id") in selected_ids and "elapsed_ms" in item:
                            val = item["elapsed_ms"]
                            if isinstance(val, (int, float)):
                                latencies.append(int(val))
            if latencies:
                latencies.sort()
                latency_summary = {
                    "count": len(latencies),
                    "min_ms": latencies[0],
                    "max_ms": latencies[-1],
                    "avg_ms": round(sum(latencies) / len(latencies), 1),
                    "p50_ms": latencies[len(latencies) // 2],
                    "p90_ms": latencies[int(len(latencies) * 0.90)],
                    "p95_ms": latencies[int(len(latencies) * 0.95)],
                }
        except Exception as log_err:
            print(f"Warning: Failed to process logs from {logs_path}: {log_err}", file=sys.stderr)

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    report["by_answer_type"] = by_answer_type
    report["by_intent"] = by_intent
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
        "vllm_version": vllm_version,
        "prompt_config_hash": prompt_config_hash,
        "model_path": os.environ.get("DATAMATE_MODEL_PATH"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "latency_summary": latency_summary,
        "pilot_48": pilot_48,
        "commit": commit,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="submission-style prediction JSONL")
    parser.add_argument("--logs", type=Path, default=None, help="optional path to questions.jsonl logs")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/evaluation/score.json")
    parser.add_argument("--split", choices=("development", "holdout"), default="development")
    parser.add_argument(
        "--pilot-48",
        action="store_true",
        help="evaluate on the 48 development representative exploration questions only",
    )
    parser.add_argument(
        "--exploratory-holdout",
        action="store_true",
        help="required to score exposed holdout labels; report is marked exploratory",
    )
    args = parser.parse_args(argv)
    predictions_path = args.predictions.resolve()
    output_path = args.output.resolve()
    logs_path = args.logs.resolve() if args.logs else None
    try:
        report = evaluate_files(
            predictions_path,
            output_path=output_path,
            split=args.split,
            exploratory_holdout=args.exploratory_holdout,
            logs_path=logs_path,
            pilot_48=args.pilot_48,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({"output": str(output_path), "split": args.split, **report["overall"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
