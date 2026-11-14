"""Entities helpers for the inference contract. Source data and labels are never loaded on import."""

from __future__ import annotations
import re
import unicodedata
from typing import Any, Mapping, Sequence
from ._shared import (
    GuardrailError,
    _is_finite_number,
)


def normalise_text(value: Any) -> str:
    """Casefold, strip Vietnamese diacritics and collapse punctuation."""

    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold().replace("đ", "d")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def resolve_entity(
    raw_text: str,
    candidates: Sequence[Mapping[str, Any]],
    *,
    min_score: float = 0.8,
    min_margin: float = 0.15,
    max_matches: int = 5,
) -> dict[str, Any]:
    """Resolve one entity mention against catalog candidates.

    Scores are caller-supplied lexical/similarity scores in ``[0, 1]``. When a
    candidate has no score, a normalised exact match scores 1.0 and anything
    else scores 0.0.
    """

    if not isinstance(raw_text, str) or not raw_text.strip():
        raise GuardrailError("invalid_tool_argument", "entity text must be non-empty")
    if not 0 <= min_score <= 1 or not 0 <= min_margin <= 1:
        raise GuardrailError("invalid_tool_argument", "score thresholds must be in [0, 1]")
    if max_matches < 1:
        raise GuardrailError("invalid_tool_argument", "max_matches must be positive")

    normalised_raw = normalise_text(raw_text)
    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        value = candidate.get("value")
        if value is None:
            continue
        explicit = candidate.get("score")
        if explicit is None:
            score = 1.0 if normalise_text(value) == normalised_raw else 0.0
        else:
            if not _is_finite_number(explicit):
                raise GuardrailError(
                    "invalid_tool_argument",
                    "candidate score must be a finite number in [0, 1]",
                    detail={"value": str(value)},
                )
            score = float(explicit)
            if not 0 <= score <= 1:
                raise GuardrailError(
                    "invalid_tool_argument",
                    "candidate score must be in [0, 1]",
                    detail={"value": str(value)},
                )
        scored.append(
            {
                "value": value,
                "score": score,
                "source_ref": candidate.get("source_ref"),
                "table": candidate.get("table"),
                "column": candidate.get("column"),
            }
        )

    scored.sort(key=lambda item: (-item["score"], normalise_text(item["value"])))
    matches = scored[:max_matches]
    if not matches or matches[0]["score"] < min_score:
        return {
            "status": "unmatched",
            "raw_text": raw_text,
            "normalised": normalised_raw,
            "matches": matches,
            "reason_code": "ambiguous_entity" if matches else "insufficient_evidence",
        }

    second = scored[1] if len(scored) > 1 else None
    if (
        second is not None
        and second["score"] >= min_score
        and matches[0]["score"] - second["score"] < min_margin
    ):
        return {
            "status": "ambiguous",
            "raw_text": raw_text,
            "normalised": normalised_raw,
            "matches": matches,
            "reason_code": "ambiguous_entity",
        }

    return {
        "status": "resolved",
        "raw_text": raw_text,
        "normalised": normalised_raw,
        "matches": matches,
        "reason_code": "ok",
    }
