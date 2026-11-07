"""SELECT-only SQL execution using the Rust-based Apache DataFusion engine."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from datafusion import SQLOptions

from ..data.catalog import BusinessCatalog


@dataclass
class QueryResult:
    ok: bool
    columns: list[str]
    rows: list[list[Any]]
    error: str | None
    elapsed_ms: int


_FORBIDDEN_TABLE_FUNCTIONS = re.compile(
    r"\b(read_csv|read_parquet|read_json|read_avro|read_ndjson|read_ipc|read_table|"
    r"glob|listing|range|unnest)\s*\(",
    re.IGNORECASE,
)


def execute_select(
    catalog: BusinessCatalog,
    sql: str,
    timeout_seconds: float = 5.0,
    max_rows: int = 1000,
) -> QueryResult:
    del timeout_seconds  # DataFusion is bounded by the post-plan row limit for this baseline.
    started = time.monotonic()
    statement = sql.strip().rstrip(";").strip()
    if not re.match(r"(?is)^(select|with)\b", statement):
        return QueryResult(False, [], [], "Only SELECT/CTE queries are allowed", 0)
    if ";" in statement:
        return QueryResult(False, [], [], "Multiple SQL statements are not allowed", 0)
    if _FORBIDDEN_TABLE_FUNCTIONS.search(statement):
        return QueryResult(False, [], [], "External and table functions are not allowed", 0)

    options = (
        SQLOptions()
        .with_allow_ddl(False)
        .with_allow_dml(False)
        .with_allow_statements(False)
    )
    try:
        frame = catalog.context.sql(statement, options=options).limit(max_rows + 1)
        batches = frame.collect()
        columns = list(frame.schema().names)
        rows: list[list[Any]] = []
        for batch in batches:
            py_batch = batch
            rows.extend(
                [py_batch.column(col_index)[row_index].as_py() for col_index in range(py_batch.num_columns)]
                for row_index in range(py_batch.num_rows)
            )
            if len(rows) > max_rows:
                return QueryResult(
                    False,
                    columns,
                    rows[:max_rows],
                    f"Result exceeds {max_rows} rows",
                    int((time.monotonic() - started) * 1000),
                )
        return QueryResult(True, columns, rows, None, int((time.monotonic() - started) * 1000))
    except Exception as error:  # DataFusion raises typed engine errors outside sqlite3.Error.
        return QueryResult(False, [], [], str(error)[:500], int((time.monotonic() - started) * 1000))
