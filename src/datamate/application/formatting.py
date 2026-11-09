"""Stable typed result formatting shared by ranking and table handlers."""

from collections.abc import Mapping, Sequence

from datamate.application.evidence import UnsupportedQuestion


def ranked_table(rows: Sequence[Mapping], columns: Sequence[str], *, limit: int,
                 tie_breaker: str | None = None) -> dict:
    if limit < 1 or any(not set(columns) <= set(row) for row in rows):
        raise UnsupportedQuestion("invalid_result_table")
    materialized = list(rows)
    if tie_breaker and materialized:
        if tie_breaker not in columns:
            raise UnsupportedQuestion("invalid_result_tie_breaker")
        value_columns = [column for column in columns if column != tie_breaker]
        if value_columns:
            materialized.sort(key=lambda row: (row[value_columns[0]] is None,
                                               -(row[value_columns[0]] or 0), row[tie_breaker]))
        else:
            materialized.sort(key=lambda row: row[tie_breaker])
    selected = [{column: row[column] for column in columns} for row in materialized[:limit]]
    return table_answer(columns, selected)


def table_answer(columns: Sequence[str], rows: Sequence[Mapping | Sequence]) -> dict:
    """Serialize internal rows to the competition's typed table answer shape."""
    output = []
    for row in rows:
        values = [row[column] for column in columns] if isinstance(row, Mapping) else list(row)
        if len(values) != len(columns):
            raise UnsupportedQuestion("invalid_result_row_width")
        output.append(values)
    return {"type": "table", "answer": {"columns": list(columns), "rows": output}}
