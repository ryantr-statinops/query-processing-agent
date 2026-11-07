"""Shared candidate generation and execution for training and inference."""

from __future__ import annotations

import pathlib
from collections.abc import Callable
from typing import Any

from datamate.application.answers import answer_from_result
from datamate.data.calendar import calendar_context
from datamate.data.catalog import BusinessCatalog
from datamate.execution.sql import execute_select
from datamate.ranking.features import candidate_features


def load_context_text(path: pathlib.Path, limit: int = 12000) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")[:limit]


class CandidatePipeline:
    """Build and execute up to three SQL candidates for one question."""

    def __init__(self, data_root: pathlib.Path, generator: Any, count: int = 3):
        self.data_root = data_root
        self.generator = generator
        self.count = max(1, min(3, count))

    def generate(
        self,
        question: dict[str, Any],
        catalog: BusinessCatalog,
        stop_after_candidate: Callable[[list[dict[str, Any]]], bool] | None = None,
    ) -> list[dict[str, Any]]:
        if self.generator is None:
            return []

        business_id = str(question.get("business_id", ""))
        business_dir = self.data_root / "data" / business_id
        rules = load_context_text(self.data_root / "rulebook.md")
        business_readme = load_context_text(business_dir / "README.md", limit=4000)
        if business_readme:
            rules = f"{rules}\n\nBUSINESS README:\n{business_readme}"
        calendar = calendar_context(self.data_root / "calendar.csv", question)
        schema = catalog.schema_text(str(question.get("question", "")))

        candidates: list[dict[str, Any]] = []
        attempts = 0
        while len(candidates) < self.count and attempts < self.count:
            raw = self.generator.generate_one(question, schema, attempts, rules, calendar)
            attempts += 1
            sql = raw.get("sql", "").strip()
            if not sql and raw.get("type") != "unanswerable":
                continue
            if any(sql and sql.casefold() == str(item.get("sql", "")).casefold() for item in candidates):
                continue
            if raw.get("type") == "unanswerable":
                answer = {"type": "unanswerable"}
                result = {"ok": True, "columns": [], "rows": [], "error": None, "elapsed_ms": 0}
            else:
                execution = execute_select(catalog, sql)
                result = {
                    "ok": execution.ok,
                    "columns": execution.columns,
                    "rows": execution.rows,
                    "error": execution.error,
                    "elapsed_ms": execution.elapsed_ms,
                }
                answer = (
                    answer_from_result(raw.get("type", ""), execution.columns, execution.rows)
                    if execution.ok
                    else None
                )

            candidates.append({
                **raw,
                "answer": answer,
                "result": result,
                "heuristic_score": float(bool(result["ok"])),
            })
            all_answers = [candidate.get("answer") for candidate in candidates]
            for candidate in candidates:
                candidate["all_answers"] = all_answers
                candidate["features"] = candidate_features(question, candidate, schema, rules)
            if stop_after_candidate and stop_after_candidate(candidates):
                break
        return candidates
