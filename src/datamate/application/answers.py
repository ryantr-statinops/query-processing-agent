"""Convert DataFusion rows to the DataMate typed-answer contract."""

from __future__ import annotations

import datetime as dt
import decimal
import math
from typing import Any

from datamate.agent.guardrails import GuardrailError, build_typed_answer


def _json_value(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        if not value.is_finite():
            raise GuardrailError("invalid_model_output", "query returned a non-finite number")
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "item"):
        return _json_value(value.item())
    return value


def answer_from_result(
    answer_type: str,
    columns: list[str],
    rows: list[list[Any]],
) -> dict[str, Any]:
    """Build a validated typed answer; empty/null results are never changed to zero."""

    if answer_type == "unanswerable":
        return build_typed_answer(answer_type, None)
    if not rows:
        raise GuardrailError("insufficient_evidence", "query returned no rows")
    json_rows = [[_json_value(cell) for cell in row] for row in rows]

    if answer_type in {"number", "percent", "date", "boolean", "string"}:
        if len(json_rows) != 1 or len(columns) != 1 or len(json_rows[0]) != 1:
            raise GuardrailError(
                "invalid_model_output",
                "scalar answer types require exactly one row and one column",
            )
        value = json_rows[0][0]
        if value is None:
            raise GuardrailError("insufficient_evidence", "query returned a null scalar")
        if answer_type == "number" and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise GuardrailError("invalid_model_output", "query result is not a finite number")
        return build_typed_answer(answer_type, value)

    if answer_type == "list":
        if len(columns) != 1 or any(len(row) != 1 for row in json_rows):
            raise GuardrailError("invalid_model_output", "list answers require one result column")
        values = [row[0] for row in json_rows]
        if any(value is None for value in values):
            raise GuardrailError("invalid_model_output", "list results cannot contain null values")
        return build_typed_answer(answer_type, values)

    if answer_type == "table":
        if any(len(row) != len(columns) for row in json_rows):
            raise GuardrailError("invalid_model_output", "result rows do not match the result schema")
        if any(cell is None for row in json_rows for cell in row):
            raise GuardrailError("invalid_model_output", "table results cannot contain null cells")
        return build_typed_answer(answer_type, {"columns": columns, "rows": json_rows})

    raise GuardrailError("invalid_model_output", f"unsupported answer type: {answer_type}")
