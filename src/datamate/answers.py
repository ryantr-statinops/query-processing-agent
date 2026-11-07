"""DataMate typed-answer construction and training-label comparison."""

from __future__ import annotations

import datetime as dt
import decimal
import re
import unicodedata
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


def _norm_string(value: Any) -> str:
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(ch for ch in value if ch.isalnum())


def _norm_scalar(value: Any) -> Any:
    if isinstance(value, (int, float, decimal.Decimal)) and not isinstance(value, bool):
        try:
            return decimal.Decimal(str(value)).normalize()
        except decimal.InvalidOperation:
            return value
    if isinstance(value, str):
        return _norm_string(value)
    return value


def answers_match(prediction: dict[str, Any], reference: dict[str, Any]) -> bool:
    if prediction.get("type") != reference.get("type"):
        return False
    kind = prediction.get("type")
    if kind == "abstain":
        return False
    if kind == "unanswerable":
        return True
    if kind == "percent":
        try:
            p = decimal.Decimal(str(prediction["answer"])).quantize(decimal.Decimal("0.01"))
            r = decimal.Decimal(str(reference["answer"])).quantize(decimal.Decimal("0.01"))
            return p == r
        except (KeyError, decimal.InvalidOperation):
            return False
    if kind in {"number", "string", "date", "boolean"}:
        return _norm_scalar(prediction.get("answer")) == _norm_scalar(reference.get("answer"))
    if kind == "list":
        left, right = prediction.get("answer"), reference.get("answer")
        return isinstance(left, list) and isinstance(right, list) and [_norm_scalar(x) for x in left] == [_norm_scalar(x) for x in right]
    if kind == "table":
        left, right = prediction.get("answer"), reference.get("answer")
        if not isinstance(left, dict) or not isinstance(right, dict):
            return False
        if [_norm_string(x) for x in left.get("columns", [])] != [_norm_string(x) for x in right.get("columns", [])]:
            return False
        return {tuple(_norm_scalar(x) for x in row) for row in left.get("rows", [])} == {
            tuple(_norm_scalar(x) for x in row) for row in right.get("rows", [])
        }
    return False


def label_match(prediction: dict[str, Any], reference: dict[str, Any]) -> bool:
    if answers_match(prediction, reference):
        return True
    if prediction.get("type") != "string" or reference.get("type") != "string":
        return False
    predicted = _norm_string(prediction.get("answer", ""))
    forms = [reference.get("answer", ""), *reference.get("alias", [])]
    return predicted in {_norm_string(form) for form in forms}


def pa_reward(prediction: dict[str, Any], reference: dict[str, Any]) -> int:
    if prediction.get("type") == "abstain":
        return 0
    return 1 if label_match(prediction, reference) else -1
