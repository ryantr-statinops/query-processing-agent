"""Typed answer and trace validation shared by the generator and audit tests."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation


def answers_match(answer_type: str, actual, expected) -> bool:
    if answer_type in {"number", "percent"}:
        if isinstance(actual, bool) or isinstance(expected, bool):
            return False
        try:
            return Decimal(str(actual)) == Decimal(str(expected))
        except (InvalidOperation, ValueError):
            return False
    if answer_type == "boolean":
        return type(actual) is bool and type(expected) is bool and actual is expected
    if answer_type in {"date", "string"}:
        return isinstance(actual, str) and isinstance(expected, str) and actual == expected
    if answer_type == "list":
        return isinstance(actual, list) and isinstance(expected, list) and actual == expected
    if answer_type == "table":
        return (isinstance(actual, dict) and isinstance(expected, dict)
                and actual.get("columns") == expected.get("columns")
                and isinstance(actual.get("rows"), list) and isinstance(expected.get("rows"), list)
                and sorted(map(repr, actual["rows"])) == sorted(map(repr, expected["rows"])))
    if answer_type == "unanswerable":
        return actual is None and expected is None
    return False


def validate_records(questions, traces, holdout_businesses):
    expected = {q["id"]: q for q in questions}
    if len(expected) != len(questions):
        raise ValueError("Duplicate question IDs in source questions")
    if len(traces) != len(expected) or {t.get("question_id") for t in traces} != set(expected):
        raise ValueError("Trace question IDs must exactly match the representative set")
    results = []
    for original in traces:
        record = dict(original)
        question = expected[record["question_id"]]
        for key in ("business_id", "question", "as_of_date"):
            if record.get(key) != question.get(key):
                raise ValueError(f"{record['question_id']}: {key} does not match source question")
        answer_type = question["reference"]["type"]
        if record.get("answer_type") != answer_type:
            raise ValueError(f"{record['question_id']}: answer type does not match source label")
        actual, reference = record.get("computed_answer"), question["reference"]["answer"]
        matches = answers_match(answer_type, actual, reference)
        record["gold_comparison"] = {"reference_type": answer_type, "reference_answer": reference, "match": matches}
        if not matches:
            record["status"] = "unresolved"
            record["uncertainty"] = list(record.get("uncertainty") or [])
            record["uncertainty"].append("Computed answer does not match the labeled reference; review calculation and source evidence.")
            record["decision_owner"] = "Lead / Người 5"
        elif answer_type == "unanswerable":
            record["status"] = "insufficient_evidence"
        else:
            record["status"] = "verified"
        expected_split = "holdout" if question["business_id"] in holdout_businesses else "development"
        if record.get("split_group") != expected_split:
            raise ValueError(f"{record['question_id']}: split group does not match seed manifest")
        results.append(record)
    return results
