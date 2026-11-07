"""Convert SQL results to DataMate typed answers."""

from __future__ import annotations

import datetime as dt
import decimal
from typing import Any


def answer_from_result(answer_type: str, columns: list[str], rows: list[list[Any]]) -> dict[str, Any] | None:
    kind = answer_type.lower()
    if kind == "unanswerable":
        return {"type": "unanswerable"}
    if kind not in {"number", "percent", "string", "date", "boolean", "list", "table"}:
        return None
    if kind == "table":
        return {"type": "table", "answer": {"columns": columns, "rows": rows}}
    if kind == "list":
        return {"type": "list", "answer": [row[0] if len(row) == 1 else row for row in rows]}
    if len(rows) != 1 or not rows[0]:
        return None
    value = rows[0][0]
    if kind in {"number", "percent"}:
        if value is None or isinstance(value, bool):
            return None
        try:
            number = decimal.Decimal(str(value))
        except decimal.InvalidOperation:
            return None
        if not number.is_finite():
            return None
        return {"type": kind, "answer": int(number) if number == number.to_integral_value() else float(number)}
    if kind == "date":
        if isinstance(value, (dt.date, dt.datetime)):
            value = value.isoformat()[:10]
        return {"type": kind, "answer": str(value)} if value is not None else None
    if kind == "boolean":
        if isinstance(value, str):
            value = value.strip().lower() in {"1", "true", "yes", "y", "có", "co"}
        else:
            value = bool(value)
        return {"type": kind, "answer": value}
    return {"type": kind, "answer": "" if value is None else str(value)}
