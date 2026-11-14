"""Answers helpers for the inference contract. Source data and labels are never loaded on import."""

from __future__ import annotations
from datetime import date
from typing import Any, Mapping, Sequence
from .requests import (
    validate_no_reference_leakage,
)
from ._shared import (
    ANSWER_TYPES,
    CONCRETE_ANSWER_TYPES,
    CONTRACT_VERSION,
    EXECUTION_STATUSES,
    GuardrailError,
    REASON_OUTCOMES,
    _BUSINESS_ID,
    _MONTH,
    _QUESTION_ID,
    _is_finite_number,
)


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

    if not isinstance(result, Mapping):
        raise GuardrailError("invalid_model_output", "internal result must be an object")

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
    allowed = required | {"plan", "evidence", "tool_calls"}
    missing = required - set(result)
    missing |= {"plan", "evidence", "tool_calls"} - set(result)
    if missing:
        raise GuardrailError(
            "invalid_model_output",
            "internal result is missing fields",
            detail={"missing": sorted(missing)},
        )
    unknown = set(result) - allowed
    if unknown:
        raise GuardrailError(
            "invalid_model_output",
            "internal result contains unknown fields",
            detail={"unknown_fields": sorted(str(key) for key in unknown)},
        )

    if not isinstance(result["question_id"], str) or not _QUESTION_ID.fullmatch(result["question_id"]):
        raise GuardrailError("invalid_model_output", "question_id does not match the contract")
    if not isinstance(result["business_id"], str) or not _BUSINESS_ID.fullmatch(result["business_id"]):
        raise GuardrailError("invalid_model_output", "business_id does not match the contract")
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
    if not isinstance(answer, Mapping) or set(answer) != {"type", "answer"}:
        raise GuardrailError(
            "invalid_model_output",
            "answer must contain exactly type and answer",
        )
    validate_typed_answer(answer)
    if result["plan"] is not None and not isinstance(result["plan"], Mapping):
        raise GuardrailError("invalid_model_output", "plan must be an object or null")
    if not isinstance(result["evidence"], list):
        raise GuardrailError("invalid_model_output", "evidence must be an array")
    if not isinstance(result["tool_calls"], list):
        raise GuardrailError("invalid_model_output", "tool_calls must be an array")
    verification = result["verification"]
    if not isinstance(verification, Mapping) or not isinstance(verification.get("passed"), bool):
        raise GuardrailError(
            "invalid_model_output",
            "verification must be an object with a boolean passed field",
        )

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
        if (
            verification["passed"] is not True
        ):
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
