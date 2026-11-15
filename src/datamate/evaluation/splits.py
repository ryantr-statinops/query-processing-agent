"""Business-grouped development/holdout manifest helpers."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


def _load_questions(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def load_split_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    validate_split_manifest(manifest)
    manifest["manifest_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest


def validate_split_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("split_unit") != "business_id":
        raise ValueError("split manifest must group by business_id")
    development = set(manifest.get("development_businesses", []))
    holdout = set(manifest.get("holdout_businesses", []))
    if not development or not holdout or development & holdout:
        raise ValueError("development and holdout businesses must be non-empty and disjoint")
    folds = manifest.get("folds", [])
    if not folds:
        raise ValueError("split manifest must contain development folds")
    assigned: set[str] = set()
    for fold in folds:
        current = set(fold)
        if not current or current & assigned or current & holdout:
            raise ValueError("development folds must be non-empty, disjoint and exclude holdout")
        assigned |= current
    if assigned != development:
        raise ValueError("development folds must cover all development businesses")


def build_split_manifest(train_root: Path, seed: int = 2026, holdout_fraction: float = 0.2) -> dict[str, Any]:
    questions = _load_questions(train_root / "questions.jsonl")
    counts = Counter(question["business_id"] for question in questions)
    businesses = sorted(counts)
    if len(businesses) < 2:
        raise ValueError("at least two businesses are required to build a split")
    if not 0 < holdout_fraction < 1:
        raise ValueError("holdout_fraction must be between zero and one")

    shuffled = businesses[:]
    random.Random(seed).shuffle(shuffled)
    holdout_count = max(1, round(len(businesses) * holdout_fraction))
    holdout = sorted(shuffled[:holdout_count])
    development = sorted(shuffled[holdout_count:])
    fold_count = min(5, len(development))
    fold_groups = [[] for _ in range(fold_count)]
    for index, business in enumerate(development):
        fold_groups[index % fold_count].append(business)
    return {
        "seed": seed,
        "split_unit": "business_id",
        "question_counts": dict(sorted(counts.items())),
        "holdout_businesses": holdout,
        "development_businesses": development,
        "folds": fold_groups,
        "holdout_question_count": sum(counts[business] for business in holdout),
        "development_question_count": sum(counts[business] for business in development),
    }
