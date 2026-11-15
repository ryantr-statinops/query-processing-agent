"""JSON parsing helpers for locally generated candidate plans."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from datamate.agent.guardrails import GuardrailError


_FENCED_JSON = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)


def parse_candidate_json(text: str) -> dict[str, Any]:
    """Parse one candidate object from plain, fenced or prefaced model output."""

    if not isinstance(text, str) or not text.strip():
        raise GuardrailError("invalid_model_output", "model output is empty")
    candidates = [match.group(1) for match in _FENCED_JSON.finditer(text)]
    candidates.append(text.strip())
    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, Mapping):
            return dict(value)
        for index, character in enumerate(candidate):
            if character != "{":
                continue
            try:
                value, _ = decoder.raw_decode(candidate, index)
            except json.JSONDecodeError:
                continue
            if isinstance(value, Mapping):
                return dict(value)
    raise GuardrailError("invalid_model_output", "model output did not contain a JSON object")
