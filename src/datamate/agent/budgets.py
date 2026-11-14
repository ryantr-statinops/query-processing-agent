"""Budgets helpers for the inference contract. Source data and labels are never loaded on import."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from ._shared import (
    GuardrailError,
    MAX_RESULT_ROWS,
    MAX_SAMPLE_ROWS,
    TOOL_NAMES,
)


@dataclass
class BudgetLedger:
    """Mutable per-question budget accounting.

    Defaults mirror the *candidate* limits in ``configs/inference_contract.json``;
    they are not approved production values.
    """

    max_input_tokens: int = 1500
    max_tool_calls: int = 6
    max_retrieval_rounds: int = 2
    max_sql_attempts: int = 3
    max_result_rows: int = MAX_RESULT_ROWS
    max_sample_rows: int = MAX_SAMPLE_ROWS
    query_timeout_ms: int = 15000
    question_timeout_ms: int = 30000

    input_tokens: int = 0
    tool_calls: int = 0
    retrieval_rounds: int = 0
    sql_attempts: int = 0
    result_rows: int = 0
    elapsed_ms: int = 0

    def __post_init__(self) -> None:
        for name in (
            "max_input_tokens",
            "max_tool_calls",
            "max_retrieval_rounds",
            "max_sql_attempts",
            "max_result_rows",
            "max_sample_rows",
            "query_timeout_ms",
            "question_timeout_ms",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise GuardrailError(
                    "invalid_tool_argument",
                    f"{name} must be a positive integer",
                    detail={"field": name},
                )
        if self.max_sample_rows > self.max_result_rows:
            raise GuardrailError(
                "invalid_tool_argument",
                "max_sample_rows cannot exceed max_result_rows",
            )

    def tick(self, elapsed_ms: int, *, is_query: bool = False) -> None:
        if not isinstance(elapsed_ms, int) or isinstance(elapsed_ms, bool) or elapsed_ms < 0:
            raise GuardrailError(
                "invalid_tool_argument",
                "elapsed_ms must be a non-negative integer",
            )
        if not isinstance(is_query, bool):
            raise GuardrailError("invalid_tool_argument", "is_query must be a boolean")
        self.elapsed_ms += elapsed_ms
        if is_query and elapsed_ms > self.query_timeout_ms:
            raise GuardrailError(
                "timeout",
                "query deadline exceeded",
                stage="execution",
                detail={
                    "elapsed_ms": elapsed_ms,
                    "limit_ms": self.query_timeout_ms,
                },
            )
        if self.elapsed_ms > self.question_timeout_ms:
            raise GuardrailError(
                "timeout",
                "question deadline exceeded",
                stage="execution",
                detail={
                    "elapsed_ms": self.elapsed_ms,
                    "limit_ms": self.question_timeout_ms,
                },
            )

    def set_input_tokens(self, tokens: int) -> None:
        if tokens < 0:
            raise GuardrailError("invalid_tool_argument", "token count cannot be negative")
        self.input_tokens = tokens
        if tokens > self.max_input_tokens:
            raise GuardrailError(
                "budget_exhausted",
                "input token budget exceeded",
                stage="retrieval",
                detail={"tokens": tokens, "limit": self.max_input_tokens},
            )

    def consume_retrieval_round(self) -> None:
        if self.retrieval_rounds >= self.max_retrieval_rounds:
            raise GuardrailError(
                "budget_exhausted",
                "retrieval round budget exhausted",
                stage="retrieval",
                detail={"rounds": self.retrieval_rounds, "limit": self.max_retrieval_rounds},
            )
        self.retrieval_rounds += 1

    def consume_tool_call(self, tool: str, *, rows: int = 0) -> None:
        if tool not in TOOL_NAMES:
            raise GuardrailError(
                "unsupported_tool",
                f"tool is not allowed: {tool}",
                stage="validation",
                detail={"tool": tool},
            )
        if self.tool_calls >= self.max_tool_calls:
            raise GuardrailError(
                "budget_exhausted",
                "tool-call budget exhausted",
                stage="planning",
                detail={"tool_calls": self.tool_calls, "limit": self.max_tool_calls},
            )
        if tool == "run_sql" and self.sql_attempts >= self.max_sql_attempts:
            raise GuardrailError(
                "budget_exhausted",
                "SQL attempt budget exhausted",
                stage="execution",
                detail={"sql_attempts": self.sql_attempts, "limit": self.max_sql_attempts},
            )
        if rows < 0:
            raise GuardrailError("invalid_tool_argument", "row count cannot be negative")
        if rows > self.max_result_rows:
            raise GuardrailError(
                "row_limit_exceeded",
                "result row limit exceeded",
                stage="execution",
                detail={"rows": rows, "limit": self.max_result_rows},
            )
        if tool == "sample_rows" and rows > self.max_sample_rows:
            raise GuardrailError(
                "row_limit_exceeded",
                "sample row limit exceeded",
                stage="execution",
                detail={"rows": rows, "limit": self.max_sample_rows},
            )

        self.tool_calls += 1
        if tool == "run_sql":
            self.sql_attempts += 1
        self.result_rows = max(self.result_rows, rows)

    def snapshot(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "tool_calls": self.tool_calls,
            "retrieval_rounds": self.retrieval_rounds,
            "sql_attempts": self.sql_attempts,
            "result_rows": self.result_rows,
            "elapsed_ms": self.elapsed_ms,
            "limits": {
                "max_input_tokens": self.max_input_tokens,
                "max_tool_calls": self.max_tool_calls,
                "max_retrieval_rounds": self.max_retrieval_rounds,
                "max_sql_attempts": self.max_sql_attempts,
                "max_result_rows": self.max_result_rows,
                "max_sample_rows": self.max_sample_rows,
                "query_timeout_ms": self.query_timeout_ms,
                "question_timeout_ms": self.question_timeout_ms,
            },
        }


def estimate_tokens(text: str) -> int:
    """Conservative token estimate for Vietnamese/English mixed prompts.

    Roughly three characters per token, rounded up. This is a safety estimate,
    not a model tokenizer measurement.
    """

    if not isinstance(text, str):
        raise GuardrailError("invalid_tool_argument", "token estimate requires text")
    return max(1, (len(text) + 2) // 3) if text else 0


def check_context_budget(
    sections: Mapping[str, str],
    *,
    max_tokens: int = 1500,
) -> dict[str, Any]:
    counts = {name: estimate_tokens(text) for name, text in sections.items()}
    total = sum(counts.values())
    if total > max_tokens:
        raise GuardrailError(
            "budget_exhausted",
            "retrieved context exceeds the input token budget",
            stage="retrieval",
            detail={"tokens": total, "limit": max_tokens, "sections": counts},
        )
    return {"tokens": total, "limit": max_tokens, "sections": counts}
