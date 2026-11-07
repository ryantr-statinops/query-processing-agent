"""Learn a lightweight candidate verifier from training-only correctness labels."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import vector


class FeatureReranker:
    def __init__(self, seed: int = 2026):
        self.seed = seed
        self.model: Any | None = None
        self.fallback = False

    def fit(self, candidate_rows: list[dict[str, Any]]) -> "FeatureReranker":
        examples = [row for row in candidate_rows if row.get("label") in (0, 1)]
        labels = [int(row["label"]) for row in examples]
        if len(set(labels)) < 2:
            self.fallback = True
            return self
        x = np.asarray([vector(row["features"]) for row in examples], dtype=float)
        self.model = make_pipeline(
            StandardScaler(),
            LogisticRegression(C=0.5, class_weight="balanced", max_iter=500, random_state=self.seed),
        )
        self.model.fit(x, labels)
        return self

    def score(self, candidate: dict[str, Any]) -> float:
        if self.model is None:
            return float(candidate.get("heuristic_score", 0.0))
        probabilities = self.model.predict_proba(np.asarray([vector(candidate["features"])], dtype=float))[0]
        classes = list(self.model[-1].classes_)
        return float(probabilities[classes.index(1)])

    def rerank(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for candidate in candidates:
            candidate["rerank_score"] = self.score(candidate)
        return sorted(candidates, key=lambda c: (c["rerank_score"], c.get("result", {}).get("ok", False)), reverse=True)
