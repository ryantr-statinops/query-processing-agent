"""Small offline fitted-Q policy for stop, abstain, or request one more candidate."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from .features import prefix_features


class CandidateBandit:
    """Fitted-Q controller trained from fully replayed training candidate traces."""

    def __init__(self, seed: int = 2026, discount: float = 1.0):
        self.seed = seed
        self.discount = discount
        self.q_submit: RandomForestRegressor | None = None
        self.q_more: RandomForestRegressor | None = None

    def fit(self, traces: list[dict[str, Any]]) -> "CandidateBandit":
        submit_x: list[list[float]] = []
        submit_y: list[float] = []
        more_x: list[list[float]] = []
        more_y: list[float] = []
        for trace in traces:
            candidates = trace.get("candidates", [])
            rewards = trace.get("rewards", [])
            if not candidates or len(candidates) != len(rewards):
                continue
            values = [0.0] * (len(candidates) + 1)
            next_value = 0.0
            for i in range(len(candidates) - 1, -1, -1):
                state = prefix_features(candidates, i)
                submit_value = float(rewards[i])
                more_value = self.discount * next_value if i < len(candidates) - 1 else 0.0
                state.append(float(len(candidates) - i - 1))
                submit_x.append(state)
                submit_y.append(submit_value)
                if i < len(candidates) - 1:
                    more_x.append(state)
                    more_y.append(more_value)
                next_value = max(submit_value, 0.0, more_value)
                values[i] = next_value
        if not submit_x:
            raise ValueError("No labeled candidate traces available to train the RL policy")
        self.q_submit = self._regressor().fit(np.asarray(submit_x), np.asarray(submit_y))
        self.q_more = self._regressor().fit(np.asarray(more_x), np.asarray(more_y)) if more_x else None
        return self

    def _regressor(self) -> RandomForestRegressor:
        return RandomForestRegressor(
            n_estimators=120, max_depth=6, min_samples_leaf=5, random_state=self.seed, n_jobs=1
        )

    def choose(self, seen_candidates: list[dict[str, Any]], can_generate_more: bool) -> str:
        if not seen_candidates:
            return "generate_more" if can_generate_more else "abstain"
        if self.q_submit is None:
            raise RuntimeError("CandidateBandit must be trained before inference")
        best = sorted(
            seen_candidates,
            key=lambda c: float(c.get("rerank_score", c.get("heuristic_score", 0))),
            reverse=True,
        )[0]
        state = prefix_features(seen_candidates, len(seen_candidates) - 1)
        remaining = max(0, 3 - len(seen_candidates))
        state.append(float(remaining))
        vector = np.asarray([state])
        submit_value = float(self.q_submit.predict(vector)[0])
        more_value = float(self.q_more.predict(vector)[0]) if can_generate_more and self.q_more else float("-inf")
        # Deterministic tie preference: stop, then abstain, then spend more inference.
        if submit_value > 0 and submit_value >= more_value:
            return "submit"
        if can_generate_more and more_value > 0:
            return "generate_more"
        return "abstain"
