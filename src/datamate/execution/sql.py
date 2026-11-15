"""Bounded, read-only SQL execution against one business catalog."""

from __future__ import annotations

import math
import multiprocessing
import pathlib
import time
from dataclasses import dataclass, field
from typing import Any

from datamate.agent.guardrails import GuardrailError, MAX_RESULT_ROWS, validate_sql_static

from ..data.catalog import BusinessCatalog

MAX_QUERY_TIMEOUT_SECONDS = 15.0


@dataclass
class QueryResult:
    ok: bool
    columns: list[str]
    rows: list[list[Any]]
    error: str | None
    elapsed_ms: int
    error_code: str | None = None
    source_refs: list[str] = field(default_factory=list)
    sql_validation: dict[str, Any] = field(default_factory=dict)


def _validate(catalog: BusinessCatalog, sql: str) -> dict[str, Any]:
    return validate_sql_static(
        sql,
        catalog.table_names,
        [column for columns in catalog.allowed_columns.values() for column in columns],
    )


def _query_worker(
    connection: Any,
    business_dir: str,
    sql: str,
    max_rows: int,
) -> None:
    """Rebuild the read-only catalog in a killable worker for hard deadlines."""

    catalog: BusinessCatalog | None = None
    try:
        from datafusion import SQLOptions

        catalog = BusinessCatalog(pathlib.Path(business_dir))
        validation = _validate(catalog, sql)
        options = (
            SQLOptions()
            .with_allow_ddl(False)
            .with_allow_dml(False)
            .with_allow_statements(False)
        )
        frame = catalog.context.sql_with_options(sql, options)
        # Force logical planning before collection, so invalid relations and
        # columns cannot be mistaken for empty query results.
        frame.logical_plan()
        validation["plan_checked"] = True
        batches = frame.limit(max_rows + 1).collect()
        columns = list(frame.schema().names)
        rows: list[list[Any]] = []
        for batch in batches:
            rows.extend(
                [batch.column(index)[row_index].as_py() for index in range(batch.num_columns)]
                for row_index in range(batch.num_rows)
            )
            if len(rows) > max_rows:
                connection.send(
                    {
                        "ok": False,
                        "columns": columns,
                        "rows": rows[:max_rows],
                        "error": f"result exceeds {max_rows} rows",
                        "error_code": "row_limit_exceeded",
                        "sql_validation": validation,
                        "tables": validation["tables"],
                    }
                )
                return
        connection.send(
            {
                "ok": True,
                "columns": columns,
                "rows": rows,
                "error": None,
                "error_code": None,
                "sql_validation": validation,
                "tables": validation["tables"],
            }
        )
    except GuardrailError as error:
        connection.send(
            {
                "ok": False,
                "columns": [],
                "rows": [],
                "error": error.message,
                "error_code": error.code,
                "sql_validation": {},
                "tables": [],
            }
        )
    except Exception as error:  # DataFusion reports engine failures as Rust exceptions.
        connection.send(
            {
                "ok": False,
                "columns": [],
                "rows": [],
                "error": str(error)[:500],
                "error_code": "execution_error",
                "sql_validation": {},
                "tables": [],
            }
        )
    finally:
        if catalog is not None:
            catalog.close()
        connection.close()


def execute_select(
    catalog: BusinessCatalog,
    sql: str,
    timeout_seconds: float = MAX_QUERY_TIMEOUT_SECONDS,
    max_rows: int = MAX_RESULT_ROWS,
) -> QueryResult:
    """Execute one validated SELECT in a process that can be terminated on timeout.

    DataFusion's Python API does not expose query cancellation. The isolated
    worker lets this boundary enforce a hard deadline instead of returning a
    timeout while a background query continues to consume resources.
    """

    started = time.monotonic()
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        return QueryResult(False, [], [], "timeout_seconds must be positive", 0, "invalid_tool_argument")
    if not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= MAX_QUERY_TIMEOUT_SECONDS:
        return QueryResult(
            False,
            [],
            [],
            f"timeout_seconds must be between 0 and {MAX_QUERY_TIMEOUT_SECONDS:g}",
            0,
            "invalid_tool_argument",
        )
    if (
        not isinstance(max_rows, int)
        or isinstance(max_rows, bool)
        or not 1 <= max_rows <= MAX_RESULT_ROWS
    ):
        return QueryResult(
            False,
            [],
            [],
            f"max_rows must be between 1 and {MAX_RESULT_ROWS}",
            0,
            "invalid_tool_argument",
        )
    if not isinstance(sql, str) or not sql.strip():
        return QueryResult(False, [], [], "SQL must be a non-empty string", 0, "invalid_tool_argument")

    try:
        # Run cheap structural/allow-list checks in the parent so rejected SQL
        # never starts a DataFusion worker.
        parent_validation = _validate(catalog, sql)
    except GuardrailError as error:
        return QueryResult(
            False,
            [],
            [],
            error.message,
            int((time.monotonic() - started) * 1000),
            error.code,
            [],
            {},
        )

    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=_query_worker,
        args=(sender, str(catalog.business_dir), sql, max_rows),
        daemon=True,
    )
    try:
        process.start()
    except (OSError, RuntimeError) as error:
        receiver.close()
        sender.close()
        return QueryResult(
            False,
            [],
            [],
            f"could not start query worker: {error}",
            int((time.monotonic() - started) * 1000),
            "execution_error",
            catalog.source_refs_for(parent_validation["tables"]),
            {**parent_validation, "plan_checked": False},
        )
    sender.close()
    try:
        if not receiver.poll(timeout_seconds):
            process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                process.kill()
                process.join(timeout=1)
            return QueryResult(
                False,
                [],
                [],
                f"query exceeded {timeout_seconds:g} seconds",
                int((time.monotonic() - started) * 1000),
                "timeout",
                catalog.source_refs_for(parent_validation["tables"]),
                {**parent_validation, "plan_checked": False},
            )

        payload = receiver.recv()
        process.join(timeout=1)
        validation = payload.get("sql_validation") or parent_validation
        tables = payload.get("tables") or parent_validation["tables"]
        return QueryResult(
            bool(payload["ok"]),
            list(payload["columns"]),
            list(payload["rows"]),
            payload.get("error"),
            int((time.monotonic() - started) * 1000),
            payload.get("error_code"),
            catalog.source_refs_for(tables),
            validation,
        )
    except (EOFError, OSError) as error:
        process.join(timeout=1)
        return QueryResult(
            False,
            [],
            [],
            f"query worker exited unexpectedly: {error}",
            int((time.monotonic() - started) * 1000),
            "execution_error",
            catalog.source_refs_for(parent_validation["tables"]),
            {**parent_validation, "plan_checked": False},
        )
    finally:
        receiver.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)
