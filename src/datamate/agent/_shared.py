"""Shared helpers for the inference contract. Source data and labels are never loaded on import."""

from __future__ import annotations
import math
import re
from typing import Any, Mapping


CONTRACT_VERSION = "0.1.0"


ANSWER_TYPES = (
    "number",
    "percent",
    "date",
    "boolean",
    "string",
    "list",
    "table",
    "unanswerable",
)


CONCRETE_ANSWER_TYPES = ANSWER_TYPES[:-1]


EXECUTION_STATUSES = ("answered", "unanswerable", "abstain")


TOOL_NAMES = ("get_schema", "search_entities", "sample_rows", "run_sql")


REASON_CODES = (
    "ok",
    "invalid_request",
    "invalid_model_output",
    "ambiguous_question",
    "ambiguous_entity",
    "blocked_on_catalog",
    "source_missing",
    "unsupported_source_role",
    "period_out_of_coverage",
    "subjective_information",
    "insufficient_evidence",
    "execution_error",
    "timeout",
    "budget_exhausted",
    "schema_mismatch",
    "verification_failed",
)


REASON_OUTCOMES: dict[str, tuple[str, str]] = {
    "ok": ("answered", "answer expected from verified evidence"),
    "unsupported_source_role": (
        "unanswerable",
        "proven absence of a required source role",
    ),
    "period_out_of_coverage": (
        "unanswerable",
        "requested period is entirely outside measured data coverage",
    ),
    "subjective_information": (
        "unanswerable",
        "question asks for information the data cannot record",
    ),
    "invalid_request": ("abstain", "request could not be validated"),
    "invalid_model_output": ("abstain", "model output could not be parsed or grounded"),
    "ambiguous_question": ("abstain", "question meaning is unresolved"),
    "ambiguous_entity": ("abstain", "entity match is unresolved"),
    "blocked_on_catalog": ("abstain", "verified catalog is unavailable or incomplete"),
    "source_missing": ("abstain", "expected runtime source is absent"),
    "insufficient_evidence": ("abstain", "evidence is empty, null or unverified"),
    "execution_error": ("abstain", "query execution failed"),
    "timeout": ("abstain", "question or query deadline exceeded"),
    "budget_exhausted": ("abstain", "tool, retry or token budget exhausted"),
    "schema_mismatch": ("abstain", "retrieved schema does not match runtime data"),
    "verification_failed": ("abstain", "evidence or answer verification failed"),
}


TOOL_ERROR_CODES = (
    "sql_parse_error",
    "multiple_statements",
    "forbidden_statement",
    "forbidden_function",
    "forbidden_table_reference",
    "unknown_table",
    "unknown_column",
    "no_source_table",
    "catalog_unavailable",
    "ambiguous_entity",
    "timeout",
    "row_limit_exceeded",
    "budget_exhausted",
    "invalid_tool_argument",
    "unsupported_tool",
    "internal_error",
)


FORBIDDEN_REFERENCE_KEYS = frozenset(
    {
        "gold",
        "gold_answer",
        "reference",
        "reference_answer",
        "reference_answers",
        "expected_answer",
        "expected_answers",
        "ground_truth",
        "answer_key",
        "label",
        "labels",
        "evaluation_score",
        "metric_score",
    }
)


MAX_QUESTION_CHARS = 2000


MAX_SQL_CHARS = 20000


MAX_RESULT_ROWS = 200


MAX_SAMPLE_ROWS = 5


_QUESTION_ID = re.compile(r"^q_[A-Za-z0-9_-]+$")


_BUSINESS_ID = re.compile(r"^(?:biz|dev)_[0-9]{3}$")


_MONTH = re.compile(r"^[0-9]{4}-(?:0[1-9]|1[0-2])$")


_FORBIDDEN_KEYWORDS = frozenset(
    {
        "insert",
        "update",
        "delete",
        "merge",
        "upsert",
        "drop",
        "create",
        "alter",
        "truncate",
        "rename",
        "grant",
        "revoke",
        "copy",
        "attach",
        "detach",
        "pragma",
        "vacuum",
        "analyze",
        "explain",
        "describe",
        "show",
        "set",
        "reset",
        "call",
        "execute",
        "prepare",
        "deallocate",
        "declare",
        "fetch",
        "load",
        "install",
        "unload",
        "export",
        "import",
        "cache",
        "uncache",
        "refresh",
        "optimize",
        "repair",
        "use",
        "kill",
        "shutdown",
        "begin",
        "commit",
        "rollback",
        "savepoint",
        "release",
        "into",
        "outfile",
        "dumpfile",
    }
)


_UNSAFE_TABLE_FUNCTIONS = frozenset(
    {
        "read_csv",
        "read_parquet",
        "read_json",
        "read_ndjson",
        "read_avro",
        "csv_scan",
        "parquet_scan",
        "json_scan",
        "avro_scan",
        "generate_series",
        "range",
        "unnest",
        "read_files",
        "read_table",
        "external_table",
        "load_file",
    }
)


_CLAUSE_BOUNDARIES = frozenset(
    {
        "where",
        "group",
        "having",
        "order",
        "limit",
        "offset",
        "union",
        "intersect",
        "except",
        "window",
        "qualify",
        "fetch",
    }
)


_FROM_TERMINATORS = _CLAUSE_BOUNDARIES | {"join", "left", "right", "full", "inner", "cross", "natural"}


_IDENT_START = re.compile(r"[^\W\d]", re.UNICODE)


_OPERATORS = ("::", ">=", "<=", "<>", "!=", "||", "->>", "->", "=>")


class GuardrailError(Exception):
    """Structured guardrail failure.

    ``code`` is a tool error code, not a final question reason code. Callers map
    it through :func:`map_outcome` or a stage-specific policy.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        stage: str = "validation",
        retryable: bool = False,
        detail: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.stage = stage
        self.retryable = retryable
        self.detail = dict(detail or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "stage": self.stage,
            "retryable": self.retryable,
            "detail": self.detail or None,
        }


def build_error(
    code: str,
    message: str,
    *,
    stage: str = "validation",
    retryable: bool = False,
    detail: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the contract's structured error object."""

    return {
        "code": code,
        "message": message,
        "stage": stage,
        "retryable": retryable,
        "detail": dict(detail or {}) or None,
    }


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    if not _is_number(value):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False
