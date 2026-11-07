"""Training-label comparison and points-accuracy reward."""

from __future__ import annotations

import decimal
import unicodedata
from typing import Any


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
