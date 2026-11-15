"""Reproducible challenge and candidate metrics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .labels import label_match, pa_reward


def score_predictions(
    predictions: Mapping[str, Mapping[str, Any]],
    references: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Score every reference ID, treating absent predictions as zero-reward misses."""

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
    answered = correct + wrong
    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "abstain": abstain,
        "missing": missing,
        "coverage": answered / total if total else 0.0,
        "accuracy_answered": correct / answered if answered else 0.0,
        "pa": (correct - wrong) / total if total else 0.0,
    }


def candidate_metrics(
    candidate_groups: Mapping[str, list[Mapping[str, Any]]],
    references: Mapping[str, Mapping[str, Any]],
) -> dict[str, float | int]:
    count = oracle = top1 = 0
    for question_id, candidates in candidate_groups.items():
        if question_id not in references or not candidates:
            continue
        count += 1
        oracle += int(any(label_match(item.get("answer", {}), references[question_id]) for item in candidates))
        top1 += int(label_match(candidates[0].get("answer", {}), references[question_id]))
    return {
        "questions": count,
        "oracle_at_n": oracle / count if count else 0.0,
        "top1_accuracy": top1 / count if count else 0.0,
    }
