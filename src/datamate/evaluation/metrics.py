"""Penalized-accuracy and candidate-pool metrics."""

from __future__ import annotations

from typing import Any

from .labels import label_match, pa_reward


def score_predictions(predictions: dict[str, dict[str, Any]], references: dict[str, dict[str, Any]]) -> dict[str, Any]:
    correct = wrong = abstain = missing = 0
    for question_id, reference in references.items():
        prediction = predictions.get(question_id)
        if prediction is None:
            missing += 1
            continue
        reward = pa_reward(prediction, reference)
        if reward > 0:
            correct += 1
        elif reward < 0:
            wrong += 1
        else:
            abstain += 1
    total = len(references)
    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "abstain": abstain,
        "missing": missing,
        "coverage": (total - abstain - missing) / total if total else 0.0,
        "accuracy_answered": correct / (correct + wrong) if correct + wrong else 0.0,
        "pa": (correct - wrong) / total if total else 0.0,
    }


def candidate_metrics(candidate_groups: dict[str, list[dict[str, Any]]], references: dict[str, dict[str, Any]]) -> dict[str, float]:
    count = oracle = top1 = 0
    for qid, candidates in candidate_groups.items():
        if qid not in references or not candidates:
            continue
        count += 1
        oracle += int(any(label_match(c.get("answer", {}), references[qid]) for c in candidates))
        top1 += int(label_match(candidates[0].get("answer", {}), references[qid]))
    return {"questions": count, "oracle_at_n": oracle / count if count else 0.0, "top1_accuracy": top1 / count if count else 0.0}
