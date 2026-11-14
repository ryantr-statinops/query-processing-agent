"""Tools helpers for the inference contract. Source data and labels are never loaded on import."""

from __future__ import annotations
from typing import Any, Iterable, Mapping
from .sql import (
    SqlPlanProbe,
    validate_sql_static,
)
from ._shared import (
    GuardrailError,
    MAX_RESULT_ROWS,
    MAX_SAMPLE_ROWS,
    TOOL_NAMES,
    _is_finite_number,
)


def _validate_tool_argument_keys(
    tool: str,
    arguments: Mapping[str, Any],
    *,
    allowed: set[str],
    required: set[str] = frozenset(),
) -> None:
    unknown = set(arguments) - allowed
    missing = required - set(arguments)
    if unknown or missing:
        raise GuardrailError(
            "invalid_tool_argument",
            f"invalid arguments for {tool}",
            detail={
                "tool": tool,
                "unknown_fields": sorted(str(key) for key in unknown),
                "missing_fields": sorted(missing),
            },
        )


def _allowlisted_names(
    values: Any,
    allowed: Iterable[str] | None,
    *,
    field: str,
    code: str,
) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise GuardrailError(
            "invalid_tool_argument",
            f"{field} must be a list of strings",
            detail={"field": field},
        )
    if allowed is None:
        raise GuardrailError(
            "catalog_unavailable",
            f"verified allow-list is required to validate {field}",
            detail={"field": field},
        )
    lookup = {str(name).casefold(): str(name) for name in allowed}
    resolved: list[str] = []
    for value in values:
        canonical = lookup.get(value.casefold())
        if canonical is None:
            raise GuardrailError(
                code,
                f"{field} is not in the verified allow-list: {value}",
                detail={field: value},
            )
        resolved.append(canonical)
    return resolved


def _allowed_columns_for(
    allowed_columns: Iterable[str] | Mapping[str, Iterable[str]] | None,
    tables: Iterable[str] | None = None,
) -> list[str] | None:
    if allowed_columns is None:
        return None
    if isinstance(allowed_columns, Mapping):
        selected = {table.casefold() for table in tables} if tables is not None else None
        values = [
            column
            for table, columns in allowed_columns.items()
            if selected is None or str(table).casefold() in selected
            for column in columns
        ]
        return list(dict.fromkeys(str(value) for value in values))
    return list(dict.fromkeys(str(value) for value in allowed_columns))


def validate_tool_call(
    tool: str,
    arguments: Mapping[str, Any],
    *,
    probe: SqlPlanProbe | None = None,
    allowed_tables: Iterable[str] | None = None,
    allowed_columns: Iterable[str] | Mapping[str, Iterable[str]] | None = None,
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
    if allowed_tables is not None:
        allowed_tables = tuple(allowed_tables)
    if isinstance(allowed_columns, Mapping):
        allowed_columns = {
            str(table): tuple(columns) for table, columns in allowed_columns.items()
        }
    elif allowed_columns is not None:
        allowed_columns = tuple(allowed_columns)

    if tool == "get_schema":
        _validate_tool_argument_keys(tool, arguments, allowed={"tables", "detail"})
        tables = None
        if "tables" in arguments:
            tables = _allowlisted_names(
                arguments["tables"], allowed_tables, field="tables", code="unknown_table"
            )
        elif allowed_tables is None:
            raise GuardrailError(
                "catalog_unavailable",
                "verified table allow-list is required for get_schema",
            )
        if tables is None:
            tables = _allowlisted_names(
                list(allowed_tables or []),
                allowed_tables,
                field="tables",
                code="unknown_table",
            )
        if len(tables) > 21:
            raise GuardrailError(
                "invalid_tool_argument",
                "get_schema.tables cannot exceed 21 tables",
                detail={"limit": 21, "count": len(tables)},
            )
        if "detail" in arguments and (
            not isinstance(arguments["detail"], str)
            or arguments["detail"] not in {"summary", "full"}
        ):
            raise GuardrailError(
                "invalid_tool_argument",
                "get_schema.detail must be summary or full",
            )
        normalized = dict(arguments)
        normalized["tables"] = tables
        return {"tool": tool, "arguments": normalized}

    if tool == "search_entities":
        _validate_tool_argument_keys(
            tool,
            arguments,
            allowed={"query", "tables", "columns", "limit", "min_score"},
            required={"query"},
        )
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
        if "min_score" in arguments:
            min_score = arguments["min_score"]
            if not _is_finite_number(min_score) or not 0 <= min_score <= 1:
                raise GuardrailError(
                    "invalid_tool_argument",
                    "search_entities.min_score must be a finite number between 0 and 1",
                )
        normalized = {**dict(arguments), "query": query.strip(), "limit": limit}
        if "tables" in arguments:
            normalized["tables"] = _allowlisted_names(
                arguments["tables"], allowed_tables, field="tables", code="unknown_table"
            )
        elif allowed_tables is None:
            raise GuardrailError(
                "catalog_unavailable",
                "verified table allow-list is required for search_entities",
            )
        if "columns" in arguments:
            table_scope = normalized.get("tables")
            allowed = _allowed_columns_for(allowed_columns, table_scope)
            normalized["columns"] = _allowlisted_names(
                arguments["columns"], allowed, field="columns", code="unknown_column"
            )
        return {"tool": tool, "arguments": normalized}

    if tool == "sample_rows":
        _validate_tool_argument_keys(
            tool,
            arguments,
            allowed={"table", "columns", "limit"},
            required={"table"},
        )
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
        resolved_tables = _allowlisted_names(
            [table], allowed_tables, field="table", code="unknown_table"
        )
        normalized = {**dict(arguments), "table": resolved_tables[0], "limit": limit}
        if "columns" in arguments:
            allowed = _allowed_columns_for(allowed_columns, [resolved_tables[0]])
            normalized["columns"] = _allowlisted_names(
                arguments["columns"], allowed, field="columns", code="unknown_column"
            )
        return {"tool": tool, "arguments": normalized}

    _validate_tool_argument_keys(
        tool,
        arguments,
        allowed={"sql", "max_rows", "purpose"},
        required={"sql"},
    )
    sql = arguments.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        raise GuardrailError("invalid_tool_argument", "run_sql.sql must be a non-empty string")
    max_rows = arguments.get("max_rows", MAX_RESULT_ROWS)
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or not 1 <= max_rows <= MAX_RESULT_ROWS:
        raise GuardrailError(
            "invalid_tool_argument",
            f"run_sql.max_rows must be between 1 and {MAX_RESULT_ROWS}",
        )
    if "purpose" in arguments and not isinstance(arguments["purpose"], str):
        raise GuardrailError("invalid_tool_argument", "run_sql.purpose must be a string")
    sql_columns = _allowed_columns_for(allowed_columns)
    if probe is None:
        static_allowed = list(allowed_tables or [])
        validation = validate_sql_static(sql, static_allowed, sql_columns)
        validation["warnings"].append("plan_probe_not_configured")
    else:
        validation = probe.validate(sql, allowed_tables, sql_columns)
    return {
        "tool": tool,
        "arguments": {**dict(arguments), "sql": sql},
        "sql_validation": validation,
    }
