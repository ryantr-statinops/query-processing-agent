"""Compare typed predictions with development references using challenge rules."""

from __future__ import annotations

import decimal
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any


def _normalise_string(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(character for character in text if character.isalnum())


def _normalise_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, (int, float, decimal.Decimal)):
        try:
            number = decimal.Decimal(str(value))
            return ("number", number.normalize()) if number.is_finite() else ("invalid_number", repr(value))
        except decimal.InvalidOperation:
            return ("invalid_number", repr(value))
    if isinstance(value, str):
        return ("string", _normalise_string(value))
    if value is None:
        return ("null", None)
    return (type(value).__name__, value)


def _percent(value: Any) -> decimal.Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        number = decimal.Decimal(str(value))
        if not number.is_finite():
            return None
        return number.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
    except (decimal.InvalidOperation, TypeError, ValueError):
        return None


def _rows(answer: Any) -> list[list[Any]] | None:
    if not isinstance(answer, Mapping):
        return None
    rows = answer.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, (list, tuple)) for row in rows):
        return None
    return [list(row) for row in rows]


def _table_match(predicted: Any, reference: Any) -> bool:
    if not isinstance(predicted, Mapping) or not isinstance(reference, Mapping):
        return False
    predicted_columns = predicted.get("columns")
    reference_columns = reference.get("columns")
    if not isinstance(predicted_columns, list) or not isinstance(reference_columns, list):
        return False
    if len(predicted_columns) != len(reference_columns):
        return False
    predicted_rows = _rows(predicted)
    reference_rows = _rows(reference)
    if predicted_rows is None or reference_rows is None:
        return False
    if any(len(row) != len(predicted_columns) for row in predicted_rows):
        return False
    if any(len(row) != len(reference_columns) for row in reference_rows):
        return False

    predicted_names = [_normalise_string(column) for column in predicted_columns]
    reference_names = [_normalise_string(column) for column in reference_columns]
    if len(set(predicted_names)) == len(predicted_names) and set(predicted_names) == set(reference_names):
        order = [predicted_names.index(name) for name in reference_names]
    else:
        # The official evaluator falls back to positional alignment when names
        # cannot establish a one-to-one mapping.
        order = list(range(len(reference_columns)))

    predicted_set = {
        tuple(_normalise_scalar(row[index]) for index in order)
        for row in predicted_rows
    }
    reference_set = {
        tuple(_normalise_scalar(value) for value in row)
        for row in reference_rows
    }
    return predicted_set == reference_set


def answers_match(prediction: Mapping[str, Any], reference: Mapping[str, Any]) -> bool:
    """Match typed answers; abstention is handled as zero reward separately."""

    if not isinstance(prediction, Mapping) or not isinstance(reference, Mapping):
        return False
    answer_type = prediction.get("type")
    if answer_type != reference.get("type"):
        return False
    if answer_type == "unanswerable":
        return True
    if answer_type == "abstain":
        return False
    predicted = prediction.get("answer")
    expected = reference.get("answer")
    if answer_type == "percent":
        predicted_percent = _percent(predicted)
        return predicted_percent is not None and predicted_percent == _percent(expected)
    if answer_type in {"number", "date", "boolean"}:
        if answer_type == "number":
            if isinstance(predicted, bool) or isinstance(expected, bool):
                return False
            return _normalise_scalar(predicted) == _normalise_scalar(expected)
        if answer_type == "boolean":
            return type(predicted) is bool and type(expected) is bool and predicted is expected
        return isinstance(predicted, str) and isinstance(expected, str) and predicted == expected
    if answer_type == "string":
        return _normalise_string(predicted) == _normalise_string(expected)
    if answer_type == "list":
        return (
            isinstance(predicted, list)
            and isinstance(expected, list)
            and [_normalise_scalar(value) for value in predicted]
            == [_normalise_scalar(value) for value in expected]
        )
    if answer_type == "table":
        return _table_match(predicted, expected)
    return False


def label_match(prediction: Mapping[str, Any] | None, reference: Mapping[str, Any]) -> bool:
    """Match a string answer against its canonical value and accepted aliases."""

    if answers_match(prediction, reference):
        return True
    if not isinstance(prediction, Mapping) or prediction.get("type") != "string" or reference.get("type") != "string":
        return False
    aliases = reference.get("alias", [])
    if not isinstance(aliases, Sequence) or isinstance(aliases, (str, bytes)):
        return False
    predicted = _normalise_string(prediction.get("answer", ""))
    forms = [reference.get("answer", ""), *aliases]
    return predicted in {_normalise_string(form) for form in forms}


def pa_reward(prediction: Mapping[str, Any] | None, reference: Mapping[str, Any]) -> int:
    """Return the challenge Penalized Accuracy reward for one question."""

    if prediction is None:
        return 0
    if isinstance(prediction, Mapping) and prediction.get("type") == "abstain":
        return 0
    return 1 if label_match(prediction, reference) else -1
