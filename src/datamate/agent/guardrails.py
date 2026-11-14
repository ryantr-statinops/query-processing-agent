"""Read-only guardrails for the DataMate agentic RAG inference contract v0.

The module is deliberately dependency-light: import time uses only the Python
standard library. DataFusion logical-plan validation is optional and imported
lazily, so contract tests and schema tooling can run without the Rust stack.

Boundaries enforced here:

* request validation;
* SQL tokenisation and static validation (statement form, forbidden words,
  table functions, relation allow-list, quoted-column grounding);
* optional DataFusion logical-plan validation (unknown table/column detection);
* tool-call policy and bounded budgets;
* entity ambiguity resolution;
* evidence, grain, coverage and answer-shape verification;
* typed-answer serialisation and competition submission records;
* outcome mapping that keeps execution status separate from answer type.

This module never executes arbitrary Python, shell commands, network requests
or filesystem operations. SQL is only planned by DataFusion, never collected.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Mapping, Sequence

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

# A reason code is not an execution status. Proven absence of a source role is
# an answerable "unanswerable"; operational failure is an abstain.
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


# ---------------------------------------------------------------------------
# Request and leakage guards
# ---------------------------------------------------------------------------


def validate_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one question request and return its canonical form."""

    if not isinstance(payload, Mapping):
        raise GuardrailError("invalid_request", "request must be a JSON object", stage="request")

    unknown = set(payload) - {"id", "business_id", "question", "as_of_date"}
    if unknown:
        raise GuardrailError(
            "invalid_request",
            "request contains unknown fields",
            stage="request",
            detail={"unknown_fields": sorted(unknown)},
        )

    question_id = payload.get("id")
    business_id = payload.get("business_id")
    question = payload.get("question")
    as_of_date = payload.get("as_of_date")

    if not isinstance(question_id, str) or not _QUESTION_ID.match(question_id):
        raise GuardrailError(
            "invalid_request",
            "id must match q_<alphanumeric>",
            stage="request",
            detail={"field": "id"},
        )
    if not isinstance(business_id, str) or not _BUSINESS_ID.match(business_id):
        raise GuardrailError(
            "invalid_request",
            "business_id must match biz_<3 digits> or dev_<3 digits>",
            stage="request",
            detail={"field": "business_id"},
        )
    if not isinstance(question, str):
        raise GuardrailError("invalid_request", "question must be a string", stage="request")
    question = question.strip()
    if not question or len(question) > MAX_QUESTION_CHARS or "\x00" in question:
        raise GuardrailError(
            "invalid_request",
            "question is empty, too long, or contains a NUL byte",
            stage="request",
            detail={"field": "question", "max_chars": MAX_QUESTION_CHARS},
        )
    if not isinstance(as_of_date, str):
        raise GuardrailError(
            "invalid_request",
            "as_of_date must be an ISO date string",
            stage="request",
            detail={"field": "as_of_date"},
        )
    try:
        parsed = date.fromisoformat(as_of_date)
    except ValueError as exc:
        raise GuardrailError(
            "invalid_request",
            "as_of_date must be YYYY-MM-DD",
            stage="request",
            detail={"field": "as_of_date"},
        ) from exc
    if parsed.isoformat() != as_of_date:
        raise GuardrailError(
            "invalid_request",
            "as_of_date must be canonical YYYY-MM-DD",
            stage="request",
            detail={"field": "as_of_date"},
        )

    validate_no_reference_leakage(payload)
    return {
        "id": question_id,
        "business_id": business_id,
        "question": question,
        "as_of_date": as_of_date,
    }


def find_reference_leakage(payload: Any, path: str = "$") -> list[str]:
    """Return paths whose mapping keys look like gold/reference data."""

    found: list[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key).casefold().replace("-", "_")
            child = f"{path}.{key}"
            if key_text in FORBIDDEN_REFERENCE_KEYS:
                found.append(child)
            found.extend(find_reference_leakage(value, child))
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            found.extend(find_reference_leakage(value, f"{path}[{index}]"))
    return found


def validate_no_reference_leakage(payload: Any) -> None:
    """Raise when a prompt/evidence payload carries reference-answer fields."""

    leaks = find_reference_leakage(payload)
    if leaks:
        raise GuardrailError(
            "invalid_model_output",
            "reference-answer fields are not allowed in inference payloads",
            stage="request",
            detail={"paths": leaks},
        )


# ---------------------------------------------------------------------------
# SQL tokenisation and static validation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SqlToken:
    kind: str
    value: str
    position: int
    line: int


def tokenize_sql(sql: str) -> list[SqlToken]:
    """Tokenise SQL without executing or normalising it.

    Comments are dropped. Single-quoted strings and double-quoted/backticked
    identifiers are opaque tokens, so keyword checks cannot be fooled by text
    inside them.
    """

    if not isinstance(sql, str):
        raise GuardrailError("sql_parse_error", "SQL must be a string", stage="validation")
    if len(sql) > MAX_SQL_CHARS:
        raise GuardrailError(
            "sql_parse_error",
            "SQL exceeds the maximum length",
            stage="validation",
            detail={"max_chars": MAX_SQL_CHARS},
        )

    tokens: list[SqlToken] = []
    index = 0
    line = 1
    length = len(sql)

    while index < length:
        char = sql[index]

        if char in " \t\r":
            index += 1
            continue
        if char == "\n":
            line += 1
            index += 1
            continue

        if char == "-" and index + 1 < length and sql[index + 1] == "-":
            index += 2
            while index < length and sql[index] != "\n":
                index += 1
            continue

        if char == "/" and index + 1 < length and sql[index + 1] == "*":
            start_line = line
            index += 2
            closed = False
            while index + 1 < length:
                if sql[index] == "*" and sql[index + 1] == "/":
                    index += 2
                    closed = True
                    break
                if sql[index] == "\n":
                    line += 1
                index += 1
            if not closed:
                raise GuardrailError(
                    "sql_parse_error",
                    "unterminated block comment",
                    stage="validation",
                    detail={"line": start_line},
                )
            continue

        if char == "'":
            start = index
            start_line = line
            index += 1
            value: list[str] = []
            closed = False
            while index < length:
                if sql[index] == "'":
                    if index + 1 < length and sql[index + 1] == "'":
                        value.append("'")
                        index += 2
                        continue
                    index += 1
                    closed = True
                    break
                if sql[index] == "\n":
                    line += 1
                value.append(sql[index])
                index += 1
            if not closed:
                raise GuardrailError(
                    "sql_parse_error",
                    "unterminated string literal",
                    stage="validation",
                    detail={"line": start_line},
                )
            tokens.append(SqlToken("string", "".join(value), start, start_line))
            continue

        if char in {'"', "`"}:
            quote = char
            start = index
            start_line = line
            index += 1
            value = []
            closed = False
            while index < length:
                if sql[index] == quote:
                    if quote == '"' and index + 1 < length and sql[index + 1] == '"':
                        value.append('"')
                        index += 2
                        continue
                    index += 1
                    closed = True
                    break
                if sql[index] == "\n":
                    line += 1
                value.append(sql[index])
                index += 1
            if not closed:
                raise GuardrailError(
                    "sql_parse_error",
                    "unterminated quoted identifier",
                    stage="validation",
                    detail={"line": start_line},
                )
            tokens.append(SqlToken("quoted_ident", "".join(value), start, start_line))
            continue

        if char == "$":
            if index + 1 < length and sql[index + 1].isdigit():
                start = index
                index += 1
                while index < length and sql[index].isdigit():
                    index += 1
                tokens.append(SqlToken("param", sql[start:index], start, line))
                continue
            raise GuardrailError(
                "sql_parse_error",
                "dollar-quoted strings and $ parameters are not supported",
                stage="validation",
                detail={"line": line},
            )

        if char == "?":
            tokens.append(SqlToken("param", "?", index, line))
            index += 1
            continue

        if char.isdigit() or (char == "." and index + 1 < length and sql[index + 1].isdigit()):
            start = index
            if char == ".":
                index += 1
                while index < length and sql[index].isdigit():
                    index += 1
            else:
                while index < length and sql[index].isdigit():
                    index += 1
                if index < length and sql[index] == ".":
                    index += 1
                    while index < length and sql[index].isdigit():
                        index += 1
            if index < length and sql[index] in "eE":
                probe = index + 1
                if probe < length and sql[probe] in "+-":
                    probe += 1
                if probe < length and sql[probe].isdigit():
                    index = probe
                    while index < length and sql[index].isdigit():
                        index += 1
            tokens.append(SqlToken("number", sql[start:index], start, line))
            continue

        if _IDENT_START.match(char):
            start = index
            while index < length and (sql[index] == "_" or sql[index].isalnum()):
                index += 1
            tokens.append(SqlToken("word", sql[start:index], start, line))
            continue

        operator = next((op for op in _OPERATORS if sql.startswith(op, index)), None)
        if operator:
            tokens.append(SqlToken("operator", operator, index, line))
            index += len(operator)
            continue

        if char in "(),;.[]{}":
            tokens.append(SqlToken("punct", char, index, line))
            index += 1
            continue

        if char in "+-*/%=<>!~&|^@#:":
            tokens.append(SqlToken("operator", char, index, line))
            index += 1
            continue

        raise GuardrailError(
            "sql_parse_error",
            f"unsupported character in SQL: {char!r}",
            stage="validation",
            detail={"line": line, "position": index},
        )

    return tokens


def _split_statements(tokens: Sequence[SqlToken]) -> list[list[SqlToken]]:
    statements: list[list[SqlToken]] = []
    current: list[SqlToken] = []
    for token in tokens:
        if token.kind == "punct" and token.value == ";":
            if current:
                statements.append(current)
                current = []
            continue
        current.append(token)
    if current:
        statements.append(current)
    return statements


def _paren_depths(tokens: Sequence[SqlToken]) -> list[int]:
    depths: list[int] = []
    depth = 0
    for token in tokens:
        depths.append(depth)
        if token.kind == "punct" and token.value == "(":
            depth += 1
        elif token.kind == "punct" and token.value == ")":
            depth = max(0, depth - 1)
    return depths


def _next_is_open_paren(tokens: Sequence[SqlToken], index: int) -> bool:
    return index + 1 < len(tokens) and tokens[index + 1].kind == "punct" and tokens[index + 1].value == "("


def _skip_parens(tokens: Sequence[SqlToken], index: int) -> int:
    if index >= len(tokens) or tokens[index].value != "(":
        raise GuardrailError("sql_parse_error", "expected '('", stage="validation")
    depth = 0
    while index < len(tokens):
        token = tokens[index]
        if token.kind == "punct" and token.value == "(":
            depth += 1
        elif token.kind == "punct" and token.value == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    raise GuardrailError("sql_parse_error", "unbalanced parentheses", stage="validation")


def _collect_ctes(tokens: Sequence[SqlToken]) -> tuple[list[str], list[str]]:
    first_word = next(
        (index for index, token in enumerate(tokens) if token.kind == "word"),
        None,
    )
    if first_word is None or tokens[first_word].value.casefold() != "with":
        return [], []

    names: list[str] = []
    aliases: list[str] = []
    index = first_word + 1
    if index < len(tokens) and tokens[index].kind == "word" and tokens[index].value.casefold() == "recursive":
        index += 1

    while index < len(tokens):
        if tokens[index].kind not in ("word", "quoted_ident"):
            break
        name = tokens[index].value
        index += 1
        if index < len(tokens) and tokens[index].value == "(":
            close = _skip_parens(tokens, index)
            aliases.extend(
                token.value
                for token in tokens[index + 1 : close - 1]
                if token.kind in ("word", "quoted_ident")
            )
            index = close
        if index >= len(tokens) or tokens[index].value.casefold() != "as":
            raise GuardrailError(
                "sql_parse_error",
                "CTE is missing AS",
                stage="validation",
                detail={"cte": name},
            )
        index += 1
        while index < len(tokens) and tokens[index].kind == "word" and tokens[index].value.casefold() in {
            "materialized",
            "not",
        }:
            index += 1
        if index >= len(tokens) or tokens[index].value != "(":
            raise GuardrailError(
                "sql_parse_error",
                "CTE body must be parenthesised",
                stage="validation",
                detail={"cte": name},
            )
        index = _skip_parens(tokens, index)
        names.append(name.casefold())
        if index < len(tokens) and tokens[index].kind == "punct" and tokens[index].value == ",":
            index += 1
            continue
        break
    return names, aliases


def _collect_aliases(tokens: Sequence[SqlToken]) -> set[str]:
    aliases: set[str] = set()
    for index, token in enumerate(tokens[:-1]):
        if token.kind == "word" and token.value.casefold() == "as":
            following = tokens[index + 1]
            if following.kind in ("word", "quoted_ident"):
                aliases.add(following.value.casefold())
    return aliases


def _check_statement_form(tokens: Sequence[SqlToken]) -> None:
    index = 0
    while index < len(tokens) and tokens[index].kind == "punct" and tokens[index].value == "(":
        index += 1
    if index >= len(tokens):
        raise GuardrailError("sql_parse_error", "empty SQL statement", stage="validation")
    token = tokens[index]
    if token.kind != "word":
        raise GuardrailError(
            "sql_parse_error",
            "SQL must start with SELECT or WITH",
            stage="validation",
            detail={"token": token.value},
        )
    keyword = token.value.casefold()
    if keyword in {"select", "with"}:
        return
    if keyword in _FORBIDDEN_KEYWORDS:
        raise GuardrailError(
            "forbidden_statement",
            f"statement type is not allowed: {token.value}",
            stage="validation",
            detail={"keyword": token.value},
        )
    raise GuardrailError(
        "sql_parse_error",
        "SQL must start with SELECT or WITH",
        stage="validation",
        detail={"token": token.value},
    )


def _parse_table_ref(
    tokens: Sequence[SqlToken],
    index: int,
    ctes: set[str],
) -> tuple[str | None, int]:
    """Return a physical table name (or None for a CTE/subquery) and next index."""

    if index >= len(tokens):
        raise GuardrailError("sql_parse_error", "FROM/JOIN is missing a relation", stage="validation")

    token = tokens[index]
    if token.kind == "punct" and token.value == "(":
        return None, index

    if token.kind == "word" and token.value.casefold() == "lateral":
        raise GuardrailError(
            "forbidden_table_reference",
            "LATERAL table references are not allowed",
            stage="validation",
        )

    if token.kind not in ("word", "quoted_ident"):
        raise GuardrailError(
            "sql_parse_error",
            "expected a table name after FROM/JOIN",
            stage="validation",
            detail={"token": token.value},
        )

    name = token.value
    if _next_is_open_paren(tokens, index):
        raise GuardrailError(
            "forbidden_function",
            f"table-valued functions are not allowed: {name}",
            stage="validation",
            detail={"function": name},
        )

    if index + 1 < len(tokens) and tokens[index + 1].kind == "punct" and tokens[index + 1].value == ".":
        raise GuardrailError(
            "forbidden_table_reference",
            "schema-qualified table references are not allowed",
            stage="validation",
            detail={"table": name},
        )

    if name.casefold() in ctes:
        return None, index
    return name, index


def _scan_table_references(
    tokens: Sequence[SqlToken],
    depths: Sequence[int],
    ctes: set[str],
) -> list[str]:
    tables: list[str] = []
    in_from = False

    for index, token in enumerate(tokens):
        if token.kind == "word":
            keyword = token.value.casefold()
            if keyword == "from" and depths[index] == 0:
                table, _ = _parse_table_ref(tokens, index + 1, ctes)
                if table is not None:
                    tables.append(table)
                in_from = True
                continue
            if keyword == "join":
                table, _ = _parse_table_ref(tokens, index + 1, ctes)
                if table is not None:
                    tables.append(table)
                in_from = False
                continue
            if keyword in _FROM_TERMINATORS and depths[index] == 0:
                in_from = False
                continue
        elif token.kind == "punct" and token.value == "," and depths[index] == 0 and in_from:
            table, _ = _parse_table_ref(tokens, index + 1, ctes)
            if table is not None:
                tables.append(table)

    return tables


def _check_quoted_columns(
    tokens: Sequence[SqlToken],
    tables: Sequence[str],
    ctes: Sequence[str],
    aliases: set[str],
    allowed_columns: Iterable[str],
) -> None:
    allowed = {str(column).casefold() for column in allowed_columns}
    table_names = {table.casefold() for table in tables} | set(ctes)
    column_context_keywords = {
        "select",
        "where",
        "and",
        "or",
        "on",
        "by",
        "having",
        "group",
        "order",
        "distinct",
        "case",
        "when",
        "then",
        "else",
        "returning",
    }

    for index, token in enumerate(tokens):
        if token.kind != "quoted_ident":
            continue
        name = token.value.casefold()
        if name in table_names or name in aliases:
            continue
        previous = tokens[index - 1] if index else None
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if previous is not None and previous.kind == "word" and previous.value.casefold() == "as":
            continue
        if (
            previous is not None
            and previous.kind == "word"
            and previous.value.casefold() in {"from", "join"}
        ):
            continue
        if following is not None and following.kind == "punct" and following.value == ".":
            continue
        in_column_position = (
            previous is not None
            and (
                previous.kind == "operator"
                or (previous.kind == "punct" and previous.value in {"(", ",", "."})
                or (
                    previous.kind == "word"
                    and previous.value.casefold() in column_context_keywords
                )
            )
        )
        if not in_column_position:
            continue
        if name not in allowed:
            raise GuardrailError(
                "unknown_column",
                f"unknown column: {token.value}",
                stage="validation",
                detail={"column": token.value},
            )


def validate_sql_static(
    sql: str,
    allowed_tables: Iterable[str],
    allowed_columns: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate SQL structure without a database planner.

    This is a strong first gate, not a replacement for logical-plan validation:
    nested subquery relations and unquoted columns are resolved by
    :class:`SqlPlanProbe`.
    """

    tokens = tokenize_sql(sql)
    statements = _split_statements(tokens)
    if len(statements) != 1:
        raise GuardrailError(
            "multiple_statements",
            "exactly one SQL statement is allowed",
            stage="validation",
            detail={"statement_count": len(statements)},
        )
    tokens = statements[0]

    _check_statement_form(tokens)
    depths = _paren_depths(tokens)

    for index, token in enumerate(tokens):
        if token.kind == "param":
            raise GuardrailError(
                "forbidden_statement",
                "SQL parameters are not allowed",
                stage="validation",
            )
        if token.kind == "word":
            keyword = token.value.casefold()
            if keyword in _FORBIDDEN_KEYWORDS:
                raise GuardrailError(
                    "forbidden_statement",
                    f"keyword is not allowed in read-only SQL: {token.value}",
                    stage="validation",
                    detail={"keyword": token.value},
                )
            if keyword in _UNSAFE_TABLE_FUNCTIONS and _next_is_open_paren(tokens, index):
                raise GuardrailError(
                    "forbidden_function",
                    f"table-valued functions are not allowed: {token.value}",
                    stage="validation",
                    detail={"function": token.value},
                )

    ctes, cte_aliases = _collect_ctes(tokens)
    tables = _scan_table_references(tokens, depths, set(ctes))

    allowed = {str(table).casefold() for table in allowed_tables}
    for table in tables:
        if table.casefold() not in allowed:
            raise GuardrailError(
                "unknown_table",
                f"table is not in the verified allow-list: {table}",
                stage="validation",
                detail={"table": table},
            )

    aliases = _collect_aliases(tokens) | {alias.casefold() for alias in cte_aliases}
    if allowed_columns is not None:
        _check_quoted_columns(tokens, tables, ctes, aliases, allowed_columns)

    return {
        "ok": True,
        "statement_type": "select",
        "tables": list(dict.fromkeys(tables)),
        "ctes": list(dict.fromkeys(ctes)),
        "plan_checked": False,
        "columns_checked": allowed_columns is not None,
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Optional DataFusion logical-plan validation
# ---------------------------------------------------------------------------


def _normalise_sql_type(type_name: Any) -> str:
    text = str(type_name or "VARCHAR").upper()
    if "TIMESTAMP" in text or "DATETIME" in text:
        return "TIMESTAMP"
    if "DATE" in text:
        return "DATE"
    if "BOOL" in text:
        return "BOOLEAN"
    if "INT" in text:
        return "BIGINT"
    if any(part in text for part in ("DOUBLE", "FLOAT", "REAL", "DECIMAL", "NUMERIC")):
        return "DOUBLE"
    return "VARCHAR"


def _normalise_schema(schema: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    normalised: dict[str, dict[str, str]] = {}
    for table, spec in schema.items():
        raw_columns: Any = spec.get("columns", spec) if isinstance(spec, Mapping) else spec
        columns: dict[str, str] = {}
        if isinstance(raw_columns, Mapping):
            for column, meta in raw_columns.items():
                if isinstance(meta, Mapping):
                    type_name = meta.get("type") or meta.get("data_type") or "VARCHAR"
                else:
                    type_name = meta
                columns[str(column)] = _normalise_sql_type(type_name)
        elif isinstance(raw_columns, Sequence) and not isinstance(raw_columns, (str, bytes)):
            for column in raw_columns:
                columns[str(column)] = "VARCHAR"
        else:
            raise GuardrailError(
                "catalog_unavailable",
                "schema columns must be a mapping or a sequence",
                detail={"table": str(table)},
            )
        normalised[str(table)] = columns
    return normalised


def _quote_ident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _collect_table_scans(plan: Any) -> list[str]:
    scans: list[str] = []

    def visit(node: Any, depth: int = 0) -> None:
        if depth > 100:  # defensive bound; logical plans are acyclic trees
            return
        try:
            text = node.display()
        except Exception:
            text = ""
        first_line = text.splitlines()[0] if text else ""
        if first_line.lstrip().startswith("TableScan:"):
            name = first_line.split("TableScan:", 1)[1].strip()
            for marker in (" projection=", " filters=", " fetch=", " order_by=", " limit="):
                name = name.split(marker, 1)[0].strip()
            name = name.strip('"`')
            scans.append(name)
        try:
            children = node.inputs()
        except Exception:
            children = []
        for child in children:
            visit(child, depth + 1)

    visit(plan)
    return scans


def _classify_datafusion_error(exc: Exception) -> GuardrailError:
    text = str(exc)
    lowered = text.casefold()

    if "single sql statement" in lowered:
        code = "multiple_statements"
    elif "dml not supported" in lowered or "ddl not supported" in lowered:
        code = "forbidden_statement"
    elif "table function" in lowered and "not found" in lowered:
        code = "forbidden_function"
    elif "table '" in lowered and "not found" in lowered:
        code = "unknown_table"
    elif "no field named" in lowered or ("column" in lowered and "not found" in lowered):
        code = "unknown_column"
    elif "parsererror" in lowered or "sql error" in lowered:
        code = "sql_parse_error"
    elif "not implemented" in lowered:
        code = "forbidden_statement"
    else:
        code = "sql_parse_error"

    detail: dict[str, Any] = {"planner_message": text[:500]}
    table_match = re.search(r"table '([^']+)' not found", text)
    if table_match:
        detail["table"] = table_match.group(1)
    field_match = re.search(r"No field named ([^.\s]+)", text)
    if field_match:
        detail["column"] = field_match.group(1).strip('"')

    return GuardrailError(code, text.splitlines()[0][:300], stage="validation", detail=detail)


class SqlPlanProbe:
    """Validate SQL through DataFusion's logical planner without collecting rows.

    Tables are registered as empty typed relations built from the verified
    catalog. Planning therefore resolves table and column names exactly as the
    read-only executor will, while no business data is read.
    """

    def __init__(self, schema: Mapping[str, Any]) -> None:
        self.schema = _normalise_schema(schema)
        self._datafusion: Any = None
        self._module_loaded = False
        self._context: Any = None
        self._signature: tuple[Any, ...] | None = None

    @property
    def available(self) -> bool:
        return self._load_datafusion() is not None

    def _load_datafusion(self) -> Any:
        if not self._module_loaded:
            self._module_loaded = True
            try:  # pragma: no cover - exercised when DataFusion is installed
                import datafusion

                self._datafusion = datafusion
            except Exception:
                self._datafusion = None
        return self._datafusion

    def _build_context(self) -> Any:
        module = self._load_datafusion()
        if module is None:
            raise GuardrailError(
                "catalog_unavailable",
                "DataFusion is not installed; logical-plan validation is unavailable",
                stage="validation",
            )
        signature = tuple(
            (table, tuple(sorted(columns.items()))) for table, columns in sorted(self.schema.items())
        )
        if self._context is not None and signature == self._signature:
            return self._context

        context = module.SessionContext()
        for table, columns in self.schema.items():
            if not columns:
                raise GuardrailError(
                    "catalog_unavailable",
                    "table has no columns in the verified schema",
                    detail={"table": table},
                )
            definitions = ", ".join(
                f"{_quote_ident(column)} {type_name}" for column, type_name in columns.items()
            )
            context.sql(f"CREATE TABLE IF NOT EXISTS {_quote_ident(table)} ({definitions})")
        self._context = context
        self._signature = signature
        return context

    def _options(self) -> Any:
        module = self._load_datafusion()
        options = module.SQLOptions()
        return (
            options.with_allow_ddl(False)
            .with_allow_dml(False)
            .with_allow_statements(False)
        )

    def validate(
        self,
        sql: str,
        allowed_tables: Iterable[str] | None = None,
        allowed_columns: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        allowed = list(allowed_tables) if allowed_tables is not None else list(self.schema)
        static = validate_sql_static(sql, allowed, allowed_columns)

        if not self.available:
            static["warnings"].append("datafusion_unavailable")
            return static

        context = self._build_context()
        try:
            frame = context.sql_with_options(sql, self._options())
        except Exception as exc:
            raise _classify_datafusion_error(exc) from exc

        try:
            plan = frame.logical_plan()
            scans = _collect_table_scans(plan)
        except Exception as exc:  # pragma: no cover - defensive planner boundary
            raise GuardrailError(
                "internal_error",
                f"could not inspect logical plan: {exc}",
                stage="validation",
            ) from exc

        if not scans:
            raise GuardrailError(
                "no_source_table",
                "query must read from a verified business table",
                stage="validation",
            )

        allowed_lookup = {str(table).casefold() for table in allowed}
        for scan in scans:
            if "(" in scan:
                raise GuardrailError(
                    "forbidden_function",
                    f"table-valued functions are not allowed: {scan}",
                    stage="validation",
                    detail={"function": scan},
                )
            if "." in scan:
                raise GuardrailError(
                    "forbidden_table_reference",
                    "schema-qualified table references are not allowed",
                    stage="validation",
                    detail={"table": scan},
                )
            if scan.casefold() not in allowed_lookup:
                raise GuardrailError(
                    "unknown_table",
                    f"table is not in the verified allow-list: {scan}",
                    stage="validation",
                    detail={"table": scan},
                )

        static.update(
            {
                "tables": list(dict.fromkeys(scans)),
                "plan_checked": True,
                "columns_checked": True,
            }
        )
        return static


# ---------------------------------------------------------------------------
# Tool policy and budgets
# ---------------------------------------------------------------------------


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
            if not isinstance(value, int) or value <= 0:
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

    def tick(self, elapsed_ms: int) -> None:
        if elapsed_ms < 0:
            raise GuardrailError("invalid_tool_argument", "elapsed_ms cannot be negative")
        self.elapsed_ms += elapsed_ms
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


def validate_tool_call(
    tool: str,
    arguments: Mapping[str, Any],
    *,
    probe: SqlPlanProbe | None = None,
    allowed_tables: Iterable[str] | None = None,
    allowed_columns: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate one tool request before it reaches the executor."""

    if tool not in TOOL_NAMES:
        raise GuardrailError(
            "unsupported_tool",
            f"tool is not allowed: {tool}",
            stage="validation",
            detail={"tool": tool},
        )
    if not isinstance(arguments, Mapping):
        raise GuardrailError(
            "invalid_tool_argument",
            "tool arguments must be an object",
            detail={"tool": tool},
        )

    if tool == "get_schema":
        tables = arguments.get("tables")
        if tables is not None and not (
            isinstance(tables, list) and all(isinstance(item, str) for item in tables)
        ):
            raise GuardrailError(
                "invalid_tool_argument",
                "get_schema.tables must be a list of table names",
            )
        return {"tool": tool, "arguments": dict(arguments)}

    if tool == "search_entities":
        query = arguments.get("query")
        limit = arguments.get("limit", 10)
        if not isinstance(query, str) or not query.strip():
            raise GuardrailError(
                "invalid_tool_argument",
                "search_entities.query must be a non-empty string",
            )
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise GuardrailError(
                "invalid_tool_argument",
                "search_entities.limit must be between 1 and 50",
            )
        return {"tool": tool, "arguments": {**dict(arguments), "query": query.strip(), "limit": limit}}

    if tool == "sample_rows":
        table = arguments.get("table")
        limit = arguments.get("limit", MAX_SAMPLE_ROWS)
        if not isinstance(table, str) or not table.strip():
            raise GuardrailError(
                "invalid_tool_argument",
                "sample_rows.table must be a non-empty string",
            )
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_SAMPLE_ROWS:
            raise GuardrailError(
                "invalid_tool_argument",
                f"sample_rows.limit must be between 1 and {MAX_SAMPLE_ROWS}",
            )
        return {"tool": tool, "arguments": {**dict(arguments), "table": table, "limit": limit}}

    sql = arguments.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        raise GuardrailError("invalid_tool_argument", "run_sql.sql must be a non-empty string")
    if probe is None:
        static_allowed = list(allowed_tables or [])
        validation = validate_sql_static(sql, static_allowed, allowed_columns)
        validation["warnings"].append("plan_probe_not_configured")
    else:
        validation = probe.validate(sql, allowed_tables, allowed_columns)
    return {
        "tool": tool,
        "arguments": {**dict(arguments), "sql": sql},
        "sql_validation": validation,
    }


# ---------------------------------------------------------------------------
# Entity resolution
# ---------------------------------------------------------------------------


def normalise_text(value: Any) -> str:
    """Casefold, strip Vietnamese diacritics and collapse punctuation."""

    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold().replace("đ", "d")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def resolve_entity(
    raw_text: str,
    candidates: Sequence[Mapping[str, Any]],
    *,
    min_score: float = 0.8,
    min_margin: float = 0.15,
    max_matches: int = 5,
) -> dict[str, Any]:
    """Resolve one entity mention against catalog candidates.

    Scores are caller-supplied lexical/similarity scores in ``[0, 1]``. When a
    candidate has no score, a normalised exact match scores 1.0 and anything
    else scores 0.0.
    """

    if not isinstance(raw_text, str) or not raw_text.strip():
        raise GuardrailError("invalid_tool_argument", "entity text must be non-empty")
    if not 0 <= min_score <= 1 or not 0 <= min_margin <= 1:
        raise GuardrailError("invalid_tool_argument", "score thresholds must be in [0, 1]")
    if max_matches < 1:
        raise GuardrailError("invalid_tool_argument", "max_matches must be positive")

    normalised_raw = normalise_text(raw_text)
    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        value = candidate.get("value")
        if value is None:
            continue
        explicit = candidate.get("score")
        if explicit is None:
            score = 1.0 if normalise_text(value) == normalised_raw else 0.0
        else:
            if not _is_finite_number(explicit):
                raise GuardrailError(
                    "invalid_tool_argument",
                    "candidate score must be a finite number in [0, 1]",
                    detail={"value": str(value)},
                )
            score = float(explicit)
            if not 0 <= score <= 1:
                raise GuardrailError(
                    "invalid_tool_argument",
                    "candidate score must be in [0, 1]",
                    detail={"value": str(value)},
                )
        scored.append(
            {
                "value": value,
                "score": score,
                "source_ref": candidate.get("source_ref"),
                "table": candidate.get("table"),
                "column": candidate.get("column"),
            }
        )

    scored.sort(key=lambda item: (-item["score"], normalise_text(item["value"])))
    matches = scored[:max_matches]
    if not matches or matches[0]["score"] < min_score:
        return {
            "status": "unmatched",
            "raw_text": raw_text,
            "normalised": normalised_raw,
            "matches": matches,
            "reason_code": "ambiguous_entity" if matches else "insufficient_evidence",
        }

    second = scored[1] if len(scored) > 1 else None
    if (
        second is not None
        and second["score"] >= min_score
        and matches[0]["score"] - second["score"] < min_margin
    ):
        return {
            "status": "ambiguous",
            "raw_text": raw_text,
            "normalised": normalised_raw,
            "matches": matches,
            "reason_code": "ambiguous_entity",
        }

    return {
        "status": "resolved",
        "raw_text": raw_text,
        "normalised": normalised_raw,
        "matches": matches,
        "reason_code": "ok",
    }


# ---------------------------------------------------------------------------
# Typed answers
# ---------------------------------------------------------------------------


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    if not _is_number(value):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _normalise_answer_value(answer_type: str, value: Any) -> Any:
    if answer_type not in ANSWER_TYPES:
        raise GuardrailError(
            "invalid_model_output",
            f"unknown answer type: {answer_type}",
            detail={"answer_type": str(answer_type)},
        )

    if answer_type == "unanswerable":
        if value is not None:
            raise GuardrailError(
                "invalid_model_output",
                "unanswerable answer must carry null",
            )
        return None

    if answer_type == "number":
        if not _is_finite_number(value):
            raise GuardrailError(
                "invalid_model_output",
                "number answer must be a finite JSON number",
            )
        return value

    if answer_type == "percent":
        if not _is_finite_number(value):
            raise GuardrailError(
                "invalid_model_output",
                "percent answer must be a finite JSON number without a % sign",
            )
        return round(float(value), 2)

    if answer_type == "date":
        if not isinstance(value, str):
            raise GuardrailError("invalid_model_output", "date answer must be a string")
        if _MONTH.match(value):
            return value
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise GuardrailError(
                "invalid_model_output",
                "date answer must be YYYY-MM-DD or YYYY-MM",
            ) from exc
        if parsed.isoformat() != value:
            raise GuardrailError("invalid_model_output", "date answer must be canonical ISO")
        return value

    if answer_type == "boolean":
        if not isinstance(value, bool):
            raise GuardrailError("invalid_model_output", "boolean answer must be true/false")
        return value

    if answer_type == "string":
        if not isinstance(value, str) or not value.strip():
            raise GuardrailError("invalid_model_output", "string answer must be non-empty")
        return value

    if answer_type == "list":
        if not isinstance(value, list) or not value:
            raise GuardrailError("invalid_model_output", "list answer must be a non-empty array")
        for item in value:
            if isinstance(item, bool):
                continue
            if isinstance(item, str) and item.strip():
                continue
            if _is_finite_number(item):
                continue
            raise GuardrailError(
                "invalid_model_output",
                "list items must be strings, finite numbers or booleans",
            )
        return value

    if answer_type == "table":
        if not isinstance(value, Mapping):
            raise GuardrailError("invalid_model_output", "table answer must be an object")
        columns = value.get("columns")
        rows = value.get("rows")
        if set(value) != {"columns", "rows"}:
            raise GuardrailError(
                "invalid_model_output",
                "table answer must contain exactly columns and rows",
            )
        if (
            not isinstance(columns, list)
            or not columns
            or not all(isinstance(column, str) and column.strip() for column in columns)
            or len(set(columns)) != len(columns)
        ):
            raise GuardrailError(
                "invalid_model_output",
                "table columns must be unique non-empty strings",
            )
        if not isinstance(rows, list) or not rows:
            raise GuardrailError("invalid_model_output", "table rows must be a non-empty array")
        for row in rows:
            if not isinstance(row, list) or len(row) != len(columns):
                raise GuardrailError(
                    "invalid_model_output",
                    "each table row must match the column count",
                )
            for cell in row:
                if isinstance(cell, bool) or isinstance(cell, str):
                    continue
                if _is_finite_number(cell):
                    continue
                raise GuardrailError(
                    "invalid_model_output",
                    "table cells must be strings, finite numbers or booleans",
                )
        return value

    raise GuardrailError("invalid_model_output", f"unsupported answer type: {answer_type}")


def build_typed_answer(answer_type: str, value: Any) -> dict[str, Any]:
    """Validate and serialise one competition typed answer."""

    return {"type": answer_type, "answer": _normalise_answer_value(answer_type, value)}


def validate_typed_answer(answer: Mapping[str, Any]) -> bool:
    if not isinstance(answer, Mapping):
        raise GuardrailError("invalid_model_output", "answer must be an object")
    if "type" not in answer or "answer" not in answer:
        raise GuardrailError(
            "invalid_model_output",
            "answer must contain type and answer",
        )
    _normalise_answer_value(answer["type"], answer["answer"])
    return True


# ---------------------------------------------------------------------------
# Outcome mapping and submission/diagnostic records
# ---------------------------------------------------------------------------


def map_outcome(reason_code: str, answer_type: str | None = None) -> dict[str, Any]:
    """Map a reason code to execution status and competition submission type."""

    if reason_code not in REASON_OUTCOMES:
        raise GuardrailError(
            "invalid_model_output",
            f"unknown reason code: {reason_code}",
            detail={"reason_code": str(reason_code)},
        )
    status, note = REASON_OUTCOMES[reason_code]

    if status == "answered":
        if answer_type not in CONCRETE_ANSWER_TYPES:
            raise GuardrailError(
                "invalid_model_output",
                "answered outcome requires a concrete answer type",
                detail={"answer_type": answer_type},
            )
        submission_type = answer_type
    else:
        submission_type = "unanswerable"

    return {
        "reason_code": reason_code,
        "execution_status": status,
        "submission_type": submission_type,
        "abstained": status == "abstain",
        "note": note,
    }


def build_submission_record(
    question_id: str,
    answer: Mapping[str, Any],
    execution_status: str,
    *,
    alias: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Build the evaluator-facing record without leaking abstain metadata."""

    if not isinstance(question_id, str) or not _QUESTION_ID.match(question_id):
        raise GuardrailError("invalid_request", "invalid question id")
    if execution_status not in EXECUTION_STATUSES:
        raise GuardrailError(
            "invalid_model_output",
            f"unknown execution status: {execution_status}",
        )
    validate_typed_answer(answer)

    if execution_status == "answered":
        if answer["type"] not in CONCRETE_ANSWER_TYPES:
            raise GuardrailError(
                "invalid_model_output",
                "answered record needs a concrete answer type",
            )
        record: dict[str, Any] = {
            "id": question_id,
            "type": answer["type"],
            "answer": answer["answer"],
        }
    else:
        if answer["type"] != "unanswerable" or answer["answer"] is not None:
            raise GuardrailError(
                "invalid_model_output",
                "unanswerable/abstain record must use type unanswerable and null answer",
            )
        record = {"id": question_id, "type": "unanswerable", "answer": None}

    if alias is not None:
        if not isinstance(alias, Sequence) or isinstance(alias, (str, bytes)):
            raise GuardrailError("invalid_model_output", "alias must be a sequence")
        record["alias"] = list(alias)
    validate_no_reference_leakage(record)
    return record


def validate_internal_result(result: Mapping[str, Any]) -> bool:
    """Validate the contract-level per-question record without JSON Schema."""

    required = {
        "contract_version",
        "question_id",
        "business_id",
        "execution_status",
        "reason_code",
        "answer",
        "verification",
        "budgets",
        "errors",
        "diagnostics",
    }
    missing = required - set(result)
    if missing:
        raise GuardrailError(
            "invalid_model_output",
            "internal result is missing fields",
            detail={"missing": sorted(missing)},
        )
    if result["contract_version"] != CONTRACT_VERSION:
        raise GuardrailError(
            "invalid_model_output",
            "internal result contract version does not match this module",
            detail={"expected": CONTRACT_VERSION, "actual": result["contract_version"]},
        )

    status = result["execution_status"]
    reason = result["reason_code"]
    if status not in EXECUTION_STATUSES:
        raise GuardrailError("invalid_model_output", f"unknown execution status: {status}")
    if reason not in REASON_OUTCOMES:
        raise GuardrailError("invalid_model_output", f"unknown reason code: {reason}")

    answer = result["answer"]
    validate_typed_answer(answer)

    if status == "answered":
        if reason != "ok":
            raise GuardrailError(
                "invalid_model_output",
                "answered result must use reason_code ok",
            )
        if answer["type"] not in CONCRETE_ANSWER_TYPES:
            raise GuardrailError(
                "invalid_model_output",
                "answered result cannot use unanswerable answer type",
            )
        if not isinstance(result.get("verification"), Mapping) or not result["verification"].get("passed"):
            raise GuardrailError(
                "verification_failed",
                "answered result requires passed verification",
            )
    else:
        if reason == "ok":
            raise GuardrailError(
                "invalid_model_output",
                "unanswerable/abstain result requires a non-ok reason",
            )
        if answer["type"] != "unanswerable" or answer["answer"] is not None:
            raise GuardrailError(
                "invalid_model_output",
                "unanswerable/abstain result must use type unanswerable and null answer",
            )
        mapped = map_outcome(reason)
        if mapped["execution_status"] != status:
            raise GuardrailError(
                "invalid_model_output",
                "reason code and execution status disagree",
                detail={"reason_code": reason, "execution_status": status},
            )

    if not isinstance(result["errors"], list):
        raise GuardrailError("invalid_model_output", "errors must be an array")
    if not isinstance(result["budgets"], Mapping):
        raise GuardrailError("invalid_model_output", "budgets must be an object")
    if not isinstance(result["diagnostics"], Mapping):
        raise GuardrailError("invalid_model_output", "diagnostics must be an object")
    return True


def build_diagnostic_record(result: Mapping[str, Any]) -> dict[str, Any]:
    """Return a log-safe record; abstain reasons never enter the submission."""

    record = {
        "contract_version": result.get("contract_version", CONTRACT_VERSION),
        "question_id": result["question_id"],
        "business_id": result["business_id"],
        "execution_status": result["execution_status"],
        "reason_code": result["reason_code"],
        "answer_type": result["answer"]["type"],
        "answer": result["answer"]["answer"],
        "verification": result.get("verification"),
        "tool_calls": result.get("tool_calls", []),
        "budgets": result.get("budgets", {}),
        "errors": result.get("errors", []),
    }
    validate_no_reference_leakage(record)
    return record


# ---------------------------------------------------------------------------
# Context budget and evidence verification
# ---------------------------------------------------------------------------


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


def _source_ref(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        ref = value.get("source_ref") or value.get("id") or value.get("ref")
        return str(ref) if ref is not None else None
    return None


def _tool_row_count(result: Mapping[str, Any]) -> int:
    count = result.get("row_count")
    if isinstance(count, int) and not isinstance(count, bool):
        return count
    rows = result.get("rows")
    return len(rows) if isinstance(rows, list) else 0


def _tool_status(result: Mapping[str, Any]) -> str:
    return str(result.get("status") or "ok").casefold()


def _sql_validation(result: Mapping[str, Any]) -> Mapping[str, Any]:
    validation = result.get("sql_validation", result.get("validation", {}))
    return validation if isinstance(validation, Mapping) else {}


def verify_evidence(
    *,
    plan: Mapping[str, Any] | None,
    retrieved_sources: Iterable[Any],
    tool_results: Sequence[Mapping[str, Any]],
    answer: Mapping[str, Any],
    execution_status: str = "answered",
    reason_code: str = "ok",
    date_coverage: str = "full",
    duplicate_risk: bool = False,
    dedup_applied: bool | None = None,
    unit_conversion_required: bool = False,
    unit_conversion_checked: bool | None = None,
    allow_static_plan: bool = False,
) -> dict[str, Any]:
    """Check evidence, grounding, grain and answer shape before writing.

    Returns a verification object. ``passed`` means policy-compliant, not that
    the prediction is correct; labels are never consulted here.
    """

    if execution_status not in EXECUTION_STATUSES:
        raise GuardrailError("invalid_model_output", f"unknown execution status: {execution_status}")
    if date_coverage not in {"full", "partial", "none", "unknown", "not_applicable"}:
        raise GuardrailError("invalid_model_output", f"unknown date coverage: {date_coverage}")

    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    def add(name: str, status: str, detail: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    try:
        validate_typed_answer(answer)
        add("answer_shape", "pass", answer.get("type", ""))
    except GuardrailError as exc:
        add("answer_shape", "fail", exc.message)
        return {
            "passed": False,
            "checks": checks,
            "evidence_sufficient": False,
            "answer_type_matches": False,
            "date_coverage": date_coverage,
            "grain_checked": False,
            "dedup_applied": bool(dedup_applied),
            "unit_conversion_checked": bool(unit_conversion_checked),
            "plan_checked": False,
            "residual_risks": warnings,
            "reason_code": "invalid_model_output",
        }

    if execution_status != "answered":
        add("outcome_consistency", "pass" if answer["type"] == "unanswerable" else "fail")
        if reason_code == "ok":
            reason_code = "insufficient_evidence"
            add("reason_present", "warn", "abstain defaulted to insufficient_evidence")
        try:
            mapped = map_outcome(reason_code)
            consistent = mapped["execution_status"] == execution_status
        except GuardrailError:
            consistent = False
        add("reason_mapping", "pass" if consistent else "fail", reason_code)
        passed = answer["type"] == "unanswerable" and consistent
        return {
            "passed": passed,
            "checks": checks,
            "evidence_sufficient": False,
            "answer_type_matches": True,
            "date_coverage": date_coverage,
            "grain_checked": False,
            "dedup_applied": bool(dedup_applied),
            "unit_conversion_checked": bool(unit_conversion_checked),
            "plan_checked": False,
            "residual_risks": warnings,
            "reason_code": reason_code if not passed else reason_code,
        }

    failures: list[tuple[str, str]] = []

    def fail(check: str, code: str, detail: str = "") -> None:
        add(check, "fail", detail)
        failures.append((code, check))

    retrieved = {ref for ref in (_source_ref(item) for item in retrieved_sources) if ref}

    if not isinstance(plan, Mapping):
        fail("plan_present", "verification_failed", "missing structured plan")
        plan_sources: list[str] = []
        plan_answer_type = None
    else:
        plan_sources = [
            ref for ref in (_source_ref(item) for item in plan.get("sources", [])) if ref
        ]
        plan_answer_type = plan.get("answer_type")
        add("plan_present", "pass", str(plan.get("intent", "")))

    if plan_sources:
        ungrounded = [ref for ref in plan_sources if ref not in retrieved]
        if ungrounded:
            fail("citations_grounded", "verification_failed", ", ".join(ungrounded[:3]))
        else:
            add("citations_grounded", "pass", f"{len(plan_sources)} sources")
    else:
        fail("citations_grounded", "insufficient_evidence", "plan has no source references")

    if plan_answer_type is not None and plan_answer_type != answer["type"]:
        fail(
            "answer_type_matches",
            "invalid_model_output",
            f"plan={plan_answer_type} answer={answer['type']}",
        )
    else:
        add("answer_type_matches", "pass", str(answer["type"]))

    ok_results = [result for result in tool_results if _tool_status(result) == "ok"]
    failed_results = [result for result in tool_results if _tool_status(result) != "ok"]
    if not ok_results:
        if any(_tool_status(result) == "timeout" for result in failed_results):
            code = "timeout"
        elif any(_tool_status(result) == "error" for result in failed_results):
            code = "execution_error"
        else:
            code = "insufficient_evidence"
        fail("tool_evidence", code, "no successful tool result")
    else:
        add("tool_evidence", "pass", f"{len(ok_results)} successful tool calls")
    if failed_results and ok_results:
        warnings.append(f"{len(failed_results)} tool call(s) failed before a successful retry")
        add("tool_retries", "warn", f"{len(failed_results)} failed call(s)")

    sql_results = [result for result in ok_results if result.get("tool") == "run_sql"]
    sql_attempts = [result for result in tool_results if result.get("tool") == "run_sql"]
    if not sql_results:
        if sql_attempts:
            attempt_statuses = {_tool_status(result) for result in sql_attempts}
            attempt_codes = {
                (result.get("error") or {}).get("code")
                for result in sql_attempts
                if isinstance(result.get("error"), Mapping)
            }
            if "budget_exhausted" in attempt_codes:
                terminal_code = "budget_exhausted"
            elif "timeout" in attempt_statuses:
                terminal_code = "timeout"
            elif "error" in attempt_statuses:
                terminal_code = "execution_error"
            else:
                terminal_code = "verification_failed"
            fail("terminal_sql", terminal_code, "no successful read-only SQL result")
        else:
            fail("terminal_sql", "verification_failed", "v0 requires one read-only SQL step")
    else:
        plan_checked = all(bool(_sql_validation(result).get("plan_checked")) for result in sql_results)
        if not plan_checked and not allow_static_plan:
            fail(
                "sql_plan_checked",
                "verification_failed",
                "logical-plan validation is required by default",
            )
        elif not plan_checked:
            warnings.append("SQL accepted with static validation only")
            add("sql_plan_checked", "warn", "static-only")
        else:
            add("sql_plan_checked", "pass")

    row_total = sum(_tool_row_count(result) for result in sql_results)
    if row_total <= 0:
        fail("result_rows", "insufficient_evidence", "empty result is not a zero answer")
    else:
        add("result_rows", "pass", str(row_total))

    if answer["answer"] is None:
        fail("null_answer", "insufficient_evidence", "null is not a numeric zero")
    else:
        add("null_answer", "pass")

    if date_coverage == "none":
        fail("date_coverage", "period_out_of_coverage", "period outside data coverage")
    elif date_coverage in {"partial", "unknown"}:
        warnings.append(f"date coverage is {date_coverage}")
        add("date_coverage", "warn", date_coverage)
    else:
        add("date_coverage", "pass", date_coverage)

    if duplicate_risk and not dedup_applied:
        fail("grain_dedup", "verification_failed", "duplicate risk not resolved")
    elif duplicate_risk:
        add("grain_dedup", "pass", "dedup or rulebook handling declared")
    else:
        add("grain_dedup", "pass", "not flagged")

    if unit_conversion_required and not unit_conversion_checked:
        fail("unit_conversion", "verification_failed", "unit conversion not verified")
    elif unit_conversion_required:
        add("unit_conversion", "pass")
    else:
        add("unit_conversion", "skip")

    precedence = (
        "timeout",
        "budget_exhausted",
        "period_out_of_coverage",
        "execution_error",
        "invalid_model_output",
        "insufficient_evidence",
        "verification_failed",
    )
    reason = "ok"
    failed_codes = {code for code, _ in failures}
    for candidate in precedence:
        if candidate in failed_codes:
            reason = candidate
            break

    return {
        "passed": not failures,
        "checks": checks,
        "evidence_sufficient": not failures,
        "answer_type_matches": "answer_type_matches" not in {check for _, check in failures},
        "date_coverage": date_coverage,
        "grain_checked": bool(dedup_applied) if duplicate_risk else True,
        "dedup_applied": bool(dedup_applied),
        "unit_conversion_checked": bool(unit_conversion_checked),
        "plan_checked": bool(sql_results)
        and all(bool(_sql_validation(result).get("plan_checked")) for result in sql_results),
        "residual_risks": warnings,
        "reason_code": reason,
    }
