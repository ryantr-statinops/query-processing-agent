"""Group predictions by business or another supplied evaluation dimension."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from time import perf_counter, perf_counter_ns
from typing import Any

from .labels import label_match, pa_reward
from .metrics import score_predictions


def evaluate_grouped(
    agent: Any,
    questions: list[dict[str, Any]],
    references: Mapping[str, Mapping[str, Any]],
    group_key: str = "business_id",
    progress: Callable[[int, int, float], None] | None = None,
) -> dict[str, Any]:
    rows = []
    started_all = perf_counter()
    for question in questions:
        started = perf_counter_ns()
        result = agent.answer(question)
        answer, trace = result if isinstance(result, tuple) else (result, {})
        elapsed_ms = (perf_counter_ns() - started) / 1_000_000
        reference = references[question["id"]]
        rows.append(
            {
                "id": question["id"],
                group_key: question[group_key],
                "answer": answer,
                "correct": label_match(answer, reference),
                "pa_reward": pa_reward(answer, reference),
                "elapsed_ms": elapsed_ms,
                "trace": trace,
            }
        )
        if progress is not None and (len(rows) % 50 == 0 or len(rows) == len(questions)):
            progress(len(rows), len(questions), perf_counter() - started_all)

    group_rows: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group_rows[row[group_key]].append(row)
    predictions = {row["id"]: row["answer"] for row in rows}
    metrics = score_predictions(predictions, references)
    metrics["latency_ms"] = _latency(rows)
    return {
        "overall": metrics,
        "groups": {key: _row_metrics(group) for key, group in sorted(group_rows.items())},
        "rows": rows,
    }


def evaluate_predictions_grouped(
    questions: list[dict[str, Any]],
    predictions: Mapping[str, Mapping[str, Any]],
    references: Mapping[str, Mapping[str, Any]],
    *,
    group_key: str = "business_id",
    elapsed_ms: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    rows = []
    for question in questions:
        question_id = question["id"]
        answer = predictions.get(question_id)
        rows.append(
            {
                "id": question_id,
                group_key: question[group_key],
                "answer": answer,
                "correct": label_match(answer, references[question_id]),
                "pa_reward": pa_reward(answer, references[question_id]),
                "elapsed_ms": (elapsed_ms or {}).get(question_id),
            }
        )
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row[group_key]].append(row)
    all_predictions = {row["id"]: row["answer"] for row in rows}
    overall = score_predictions(all_predictions, references)
    overall["latency_ms"] = _latency(rows)
    return {
        "overall": overall,
        "groups": {key: _row_metrics(group) for key, group in sorted(groups.items())},
        "rows": rows,
    }


def _latency(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    values = sorted(row["elapsed_ms"] for row in rows if row.get("elapsed_ms") is not None)
    if not values:
        return {"p50": None, "p95": None}

    def percentile(fraction: float) -> float:
        index = round((len(values) - 1) * fraction)
        return float(values[index])

    return {"p50": percentile(0.50), "p95": percentile(0.95)}


def _row_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Evaluated rows carry a reward already; use it so references need not be
    # copied into the report rows.
    rewards = [row["pa_reward"] for row in rows]
    correct = sum(reward > 0 for reward in rewards)
    wrong = sum(reward < 0 for reward in rewards)
    abstain = sum(
        row["pa_reward"] == 0
        and isinstance(row["answer"], Mapping)
        and row["answer"].get("type") == "abstain"
        for row in rows
    )
    missing = sum(
        row["answer"] is None
        for row in rows
    )
    total = len(rows)
    answered = correct + wrong
    return {
        "questions": total,
        "correct": correct,
        "wrong": wrong,
        "abstain": abstain,
        "missing": missing,
        "coverage": answered / total if total else 0.0,
        "accuracy_answered": correct / answered if answered else 0.0,
        "pa": sum(rewards) / total if total else 0.0,
        "latency_ms": _latency(rows),
    }
