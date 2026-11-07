"""Deterministic business-level train/holdout and cross-validation splits."""

from __future__ import annotations

import hashlib
import json
import pathlib
import random
from collections import Counter
from typing import Any


def build_split_manifest(train_root: pathlib.Path, seed: int = 2026) -> dict[str, Any]:
    questions_path = train_root / "questions.jsonl"
    counts: Counter[str] = Counter()
    with questions_path.open("r", encoding="utf-8-sig") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            business_id = record.get("business_id")
            if not isinstance(business_id, str) or not business_id:
                raise ValueError(f"Missing business_id on {questions_path}:{line_no}")
            counts[business_id] += 1

    businesses = sorted(counts)
    if len(businesses) < 10:
        raise ValueError("Need at least 10 businesses for 20% holdout and four folds")
    shuffled = businesses[:]
    random.Random(seed).shuffle(shuffled)
    holdout_count = round(len(businesses) * 0.2)
    holdout = sorted(shuffled[:holdout_count])
    development = shuffled[holdout_count:]
    folds = [[] for _ in range(4)]
    # Balance folds by question count while retaining seeded tie ordering.
    for business_id in sorted(development, key=lambda b: (-counts[b], development.index(b))):
        folds[min(range(4), key=lambda i: (sum(counts[b] for b in folds[i]), i))].append(business_id)

    return {
        "seed": seed,
        "split_unit": "business_id",
        "question_counts": dict(sorted(counts.items())),
        "holdout_businesses": holdout,
        "development_businesses": sorted(development),
        "folds": [sorted(fold) for fold in folds],
        "holdout_question_count": sum(counts[b] for b in holdout),
        "development_question_count": sum(counts[b] for b in development),
        "manifest_sha256": hashlib.sha256(
            json.dumps(
                {"seed": seed, "counts": dict(sorted(counts.items())), "holdout": holdout, "folds": folds},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    }


def write_split_manifest(train_root: pathlib.Path, output: pathlib.Path, seed: int = 2026) -> dict[str, Any]:
    manifest = build_split_manifest(train_root, seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest
