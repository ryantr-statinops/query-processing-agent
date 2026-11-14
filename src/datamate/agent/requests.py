"""Requests helpers for the inference contract. Source data and labels are never loaded on import."""

from __future__ import annotations
from datetime import date
from typing import Any, Mapping
from ._shared import (
    FORBIDDEN_REFERENCE_KEYS,
    GuardrailError,
    MAX_QUESTION_CHARS,
    _BUSINESS_ID,
    _QUESTION_ID,
)


def validate_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one question request and return its canonical form."""

    if not isinstance(payload, Mapping):
        raise GuardrailError("invalid_request", "request must be a JSON object", stage="request")

    unknown = set(payload) - {"id", "business_id", "question", "as_of_date"}
    if unknown:
        raise GuardrailError(
            "invalid_request",
            "request contains unknown fields",
            stage="request",
            detail={"unknown_fields": sorted(unknown)},
        )

    question_id = payload.get("id")
    business_id = payload.get("business_id")
    question = payload.get("question")
    as_of_date = payload.get("as_of_date")

    if not isinstance(question_id, str) or not _QUESTION_ID.match(question_id):
        raise GuardrailError(
            "invalid_request",
            "id must match q_<alphanumeric>",
            stage="request",
            detail={"field": "id"},
        )
    if not isinstance(business_id, str) or not _BUSINESS_ID.match(business_id):
        raise GuardrailError(
            "invalid_request",
            "business_id must match biz_<3 digits> or dev_<3 digits>",
            stage="request",
            detail={"field": "business_id"},
        )
    if not isinstance(question, str):
        raise GuardrailError("invalid_request", "question must be a string", stage="request")
    question = question.strip()
    if not question or len(question) > MAX_QUESTION_CHARS or "\x00" in question:
        raise GuardrailError(
            "invalid_request",
            "question is empty, too long, or contains a NUL byte",
            stage="request",
            detail={"field": "question", "max_chars": MAX_QUESTION_CHARS},
        )
    if not isinstance(as_of_date, str):
        raise GuardrailError(
            "invalid_request",
            "as_of_date must be an ISO date string",
            stage="request",
            detail={"field": "as_of_date"},
        )
    try:
        parsed = date.fromisoformat(as_of_date)
    except ValueError as exc:
        raise GuardrailError(
            "invalid_request",
            "as_of_date must be YYYY-MM-DD",
            stage="request",
            detail={"field": "as_of_date"},
        ) from exc
    if parsed.isoformat() != as_of_date:
        raise GuardrailError(
            "invalid_request",
            "as_of_date must be canonical YYYY-MM-DD",
            stage="request",
            detail={"field": "as_of_date"},
        )

    validate_no_reference_leakage(payload)
    return {
        "id": question_id,
        "business_id": business_id,
        "question": question,
        "as_of_date": as_of_date,
    }


def find_reference_leakage(payload: Any, path: str = "$") -> list[str]:
    """Return paths whose mapping keys look like gold/reference data."""

    found: list[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key).casefold().replace("-", "_")
            child = f"{path}.{key}"
            if key_text in FORBIDDEN_REFERENCE_KEYS:
                found.append(child)
            found.extend(find_reference_leakage(value, child))
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            found.extend(find_reference_leakage(value, f"{path}[{index}]"))
    return found


def validate_no_reference_leakage(payload: Any) -> None:
    """Raise when a prompt/evidence payload carries reference-answer fields."""

    leaks = find_reference_leakage(payload)
    if leaks:
        raise GuardrailError(
            "invalid_model_output",
            "reference-answer fields are not allowed in inference payloads",
            stage="request",
            detail={"paths": leaks},
        )
