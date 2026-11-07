"""Inference-available candidate and prefix-state features."""

from __future__ import annotations

import re
from typing import Any


FEATURE_NAMES = (
    "sql_valid", "result_nonempty", "result_type_shape", "result_rows", "result_columns", "log_result_rows", "sql_chars",
    "joins", "group_by", "order_by", "aggregate", "where_clause", "date_evidence",
    "date_filter_present", "unit_evidence", "rulebook_token_coverage", "business_object_coverage",
    "question_token_coverage", "schema_token_coverage", "duplicate_answer_ratio",
    "candidate_count", "candidate_agreement", "ranking_margin",
)


def candidate_features(
    question: dict[str, Any], candidate: dict[str, Any], schema: str, rule_text: str = ""
) -> dict[str, float]:
    sql = str(candidate.get("sql", ""))
    result = candidate.get("result") or {}
    rows = result.get("rows") or []
    cols = result.get("columns") or []
    q_tokens = {x.casefold() for x in re.findall(r"[\w]+", question.get("question", "")) if len(x) > 2}
    source = f"{schema} {sql}".casefold()
    rules_source = rule_text.casefold()
    schema_tokens = {x.casefold() for x in re.findall(r"[\w]+", schema) if len(x) > 2}
    rule_tokens = {x.casefold() for x in re.findall(r"[\w]+", rules_source) if len(x) > 2}
    covered = len(q_tokens & set(re.findall(r"[\w]+", source))) / max(1, len(q_tokens))
    schema_covered = len(q_tokens & schema_tokens) / max(1, len(q_tokens))
    rule_covered = len(q_tokens & rule_tokens) / max(1, len(q_tokens))
    answer_type = str(candidate.get("type", "")).lower()
    expected_shape = (
        answer_type == "table" and bool(cols)
        or answer_type == "list" and (not rows or bool(rows[0]))
        or answer_type in {"number", "percent", "string", "date", "boolean"} and len(rows) == 1 and bool(rows[0])
        or answer_type == "unanswerable"
    )
    unit_terms = {"đồng", "vnd", "vnđ", "%", "kg", "gram", "ly", "cái", "hộp", "lít", "lần", "người"}
    question_units = {term for term in unit_terms if term in question.get("question", "").casefold()}
    unit_covered = bool(question_units & set(re.findall(r"[\w%]+", f"{schema} {sql}".casefold())))
    business_tokens = {x.casefold() for x in re.findall(r"[\w]+", f"{schema} {rows}" ) if len(x) > 2}
    entity_coverage = len(q_tokens & business_tokens) / max(1, len(q_tokens))
    answer = candidate.get("answer")
    all_answers = candidate.get("all_answers") or []
    duplicates = sum(1 for other in all_answers if other == answer)
    return {
        "sql_valid": float(bool(result.get("ok"))),
        "result_nonempty": float(bool(rows)),
        "result_type_shape": float(bool(expected_shape)),
        "result_rows": float(len(rows)),
        "result_columns": float(len(cols)),
        "log_result_rows": float(min(20, len(rows))),
        "sql_chars": float(min(5000, len(sql))),
        "joins": float(len(re.findall(r"\bjoin\b", sql, re.I))),
        "group_by": float(bool(re.search(r"\bgroup\s+by\b", sql, re.I))),
        "order_by": float(bool(re.search(r"\border\s+by\b", sql, re.I))),
        "aggregate": float(bool(re.search(r"\b(sum|count|avg|min|max)\s*\(", sql, re.I))),
        "where_clause": float(bool(re.search(r"\bwhere\b", sql, re.I))),
        "date_evidence": float(str(question.get("as_of_date", "")) in sql),
        "date_filter_present": float(bool(re.search(r"\b(date|ngay|thang|year|month)\b|\b20\d{2}[-/]\d{1,2}", sql, re.I))),
        "unit_evidence": float(unit_covered),
        "rulebook_token_coverage": rule_covered,
        "business_object_coverage": entity_coverage,
        "question_token_coverage": covered,
        "schema_token_coverage": schema_covered,
        "duplicate_answer_ratio": duplicates / max(1, len(all_answers)),
        "candidate_count": float(len(all_answers)),
        "candidate_agreement": duplicates / max(1, len(all_answers)),
        "ranking_margin": float(candidate.get("ranking_margin", 0.0)),
    }


def vector(features: dict[str, float]) -> list[float]:
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]


def prefix_features(candidates: list[dict[str, Any]], index: int) -> list[float]:
    seen = candidates[: index + 1]
    scored = sorted(seen, key=lambda c: float(c.get("rerank_score", c.get("heuristic_score", 0))), reverse=True)
    best = scored[0]
    values = vector(best.get("features", {}))
    second = float(scored[1].get("rerank_score", scored[1].get("heuristic_score", 0))) if len(scored) > 1 else 0.0
    first = float(best.get("rerank_score", best.get("heuristic_score", 0)))
    values[FEATURE_NAMES.index("candidate_count")] = float(len(seen))
    values[FEATURE_NAMES.index("ranking_margin")] = first - second
    answer_counts: dict[str, int] = {}
    for candidate in seen:
        key = repr(candidate.get("answer"))
        answer_counts[key] = answer_counts.get(key, 0) + 1
    strongest_agreement = max(answer_counts.values(), default=0) / len(seen)
    values[FEATURE_NAMES.index("candidate_agreement")] = strongest_agreement
    values[FEATURE_NAMES.index("duplicate_answer_ratio")] = (max(answer_counts.values(), default=0) - 1) / len(seen)
    return values
