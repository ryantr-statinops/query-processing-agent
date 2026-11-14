"""Evidence helpers for the inference contract. Source data and labels are never loaded on import."""

from __future__ import annotations
from typing import Any, Iterable, Mapping, Sequence
from .answers import (
    map_outcome,
    validate_typed_answer,
)
from ._shared import (
    EXECUTION_STATUSES,
    GuardrailError,
)


def _source_ref(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        ref = value.get("source_ref") or value.get("id") or value.get("ref")
        return str(ref) if ref is not None else None
    return None


def _tool_row_count(result: Mapping[str, Any]) -> int:
    count = result.get("row_count")
    if isinstance(count, int) and not isinstance(count, bool):
        return count
    rows = result.get("rows")
    return len(rows) if isinstance(rows, list) else 0


def _tool_status(result: Mapping[str, Any]) -> str:
    return str(result.get("status") or "ok").casefold()


def _sql_validation(result: Mapping[str, Any]) -> Mapping[str, Any]:
    validation = result.get("sql_validation", result.get("validation", {}))
    return validation if isinstance(validation, Mapping) else {}


def verify_evidence(
    *,
    plan: Mapping[str, Any] | None,
    retrieved_sources: Iterable[Any],
    tool_results: Sequence[Mapping[str, Any]],
    answer: Mapping[str, Any],
    execution_status: str = "answered",
    reason_code: str = "ok",
    date_coverage: str = "full",
    duplicate_risk: bool = False,
    dedup_applied: bool | None = None,
    unit_conversion_required: bool = False,
    unit_conversion_checked: bool | None = None,
    allow_static_plan: bool = False,
) -> dict[str, Any]:
    """Check evidence, grounding, grain and answer shape before writing.

    Returns a verification object. ``passed`` means policy-compliant, not that
    the prediction is correct; labels are never consulted here.
    """

    if execution_status not in EXECUTION_STATUSES:
        raise GuardrailError("invalid_model_output", f"unknown execution status: {execution_status}")
    if date_coverage not in {"full", "partial", "none", "unknown", "not_applicable"}:
        raise GuardrailError("invalid_model_output", f"unknown date coverage: {date_coverage}")

    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    def add(name: str, status: str, detail: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    try:
        validate_typed_answer(answer)
        add("answer_shape", "pass", answer.get("type", ""))
    except GuardrailError as exc:
        add("answer_shape", "fail", exc.message)
        return {
            "passed": False,
            "checks": checks,
            "evidence_sufficient": False,
            "answer_type_matches": False,
            "date_coverage": date_coverage,
            "grain_checked": False,
            "dedup_applied": bool(dedup_applied),
            "unit_conversion_checked": bool(unit_conversion_checked),
            "plan_checked": False,
            "residual_risks": warnings,
            "reason_code": "invalid_model_output",
        }

    if execution_status != "answered":
        add("outcome_consistency", "pass" if answer["type"] == "unanswerable" else "fail")
        if reason_code == "ok":
            reason_code = "insufficient_evidence"
            add("reason_present", "warn", "abstain defaulted to insufficient_evidence")
        try:
            mapped = map_outcome(reason_code)
            consistent = mapped["execution_status"] == execution_status
        except GuardrailError:
            consistent = False
        add("reason_mapping", "pass" if consistent else "fail", reason_code)
        passed = answer["type"] == "unanswerable" and consistent
        return {
            "passed": passed,
            "checks": checks,
            "evidence_sufficient": False,
            "answer_type_matches": True,
            "date_coverage": date_coverage,
            "grain_checked": False,
            "dedup_applied": bool(dedup_applied),
            "unit_conversion_checked": bool(unit_conversion_checked),
            "plan_checked": False,
            "residual_risks": warnings,
            "reason_code": reason_code if not passed else reason_code,
        }

    failures: list[tuple[str, str]] = []

    def fail(check: str, code: str, detail: str = "") -> None:
        add(check, "fail", detail)
        failures.append((code, check))

    retrieved = {ref for ref in (_source_ref(item) for item in retrieved_sources) if ref}

    if not isinstance(plan, Mapping):
        fail("plan_present", "verification_failed", "missing structured plan")
        plan_sources: list[str] = []
        plan_answer_type = None
    else:
        plan_sources = [
            ref for ref in (_source_ref(item) for item in plan.get("sources", [])) if ref
        ]
        plan_answer_type = plan.get("answer_type")
        add("plan_present", "pass", str(plan.get("intent", "")))

    if plan_sources:
        ungrounded = [ref for ref in plan_sources if ref not in retrieved]
        if ungrounded:
            fail("citations_grounded", "verification_failed", ", ".join(ungrounded[:3]))
        else:
            add("citations_grounded", "pass", f"{len(plan_sources)} sources")
    else:
        fail("citations_grounded", "insufficient_evidence", "plan has no source references")

    if plan_answer_type is not None and plan_answer_type != answer["type"]:
        fail(
            "answer_type_matches",
            "invalid_model_output",
            f"plan={plan_answer_type} answer={answer['type']}",
        )
    else:
        add("answer_type_matches", "pass", str(answer["type"]))

    ok_results = [result for result in tool_results if _tool_status(result) == "ok"]
    failed_results = [result for result in tool_results if _tool_status(result) != "ok"]
    if not ok_results:
        if any(_tool_status(result) == "timeout" for result in failed_results):
            code = "timeout"
        elif any(_tool_status(result) == "error" for result in failed_results):
            code = "execution_error"
        else:
            code = "insufficient_evidence"
        fail("tool_evidence", code, "no successful tool result")
    else:
        add("tool_evidence", "pass", f"{len(ok_results)} successful tool calls")
    if failed_results and ok_results:
        warnings.append(f"{len(failed_results)} tool call(s) failed before a successful retry")
        add("tool_retries", "warn", f"{len(failed_results)} failed call(s)")

    sql_results = [result for result in ok_results if result.get("tool") == "run_sql"]
    sql_attempts = [result for result in tool_results if result.get("tool") == "run_sql"]
    if not sql_results:
        if sql_attempts:
            attempt_statuses = {_tool_status(result) for result in sql_attempts}
            attempt_codes = {
                (result.get("error") or {}).get("code")
                for result in sql_attempts
                if isinstance(result.get("error"), Mapping)
            }
            if "budget_exhausted" in attempt_codes:
                terminal_code = "budget_exhausted"
            elif "timeout" in attempt_statuses:
                terminal_code = "timeout"
            elif "error" in attempt_statuses:
                terminal_code = "execution_error"
            else:
                terminal_code = "verification_failed"
            fail("terminal_sql", terminal_code, "no successful read-only SQL result")
        else:
            fail("terminal_sql", "verification_failed", "v0 requires one read-only SQL step")
    else:
        plan_checked = all(bool(_sql_validation(result).get("plan_checked")) for result in sql_results)
        if not plan_checked and not allow_static_plan:
            fail(
                "sql_plan_checked",
                "verification_failed",
                "logical-plan validation is required by default",
            )
        elif not plan_checked:
            warnings.append("SQL accepted with static validation only")
            add("sql_plan_checked", "warn", "static-only")
        else:
            add("sql_plan_checked", "pass")

    row_total = sum(_tool_row_count(result) for result in sql_results)
    if row_total <= 0:
        fail("result_rows", "insufficient_evidence", "empty result is not a zero answer")
    else:
        add("result_rows", "pass", str(row_total))

    if answer["answer"] is None:
        fail("null_answer", "insufficient_evidence", "null is not a numeric zero")
    else:
        add("null_answer", "pass")

    if date_coverage == "none":
        fail("date_coverage", "period_out_of_coverage", "period outside data coverage")
    elif date_coverage in {"partial", "unknown"}:
        warnings.append(f"date coverage is {date_coverage}")
        add("date_coverage", "warn", date_coverage)
    else:
        add("date_coverage", "pass", date_coverage)

    if duplicate_risk and not dedup_applied:
        fail("grain_dedup", "verification_failed", "duplicate risk not resolved")
    elif duplicate_risk:
        add("grain_dedup", "pass", "dedup or rulebook handling declared")
    else:
        add("grain_dedup", "pass", "not flagged")

    if unit_conversion_required and not unit_conversion_checked:
        fail("unit_conversion", "verification_failed", "unit conversion not verified")
    elif unit_conversion_required:
        add("unit_conversion", "pass")
    else:
        add("unit_conversion", "skip")

    precedence = (
        "timeout",
        "budget_exhausted",
        "period_out_of_coverage",
        "execution_error",
        "invalid_model_output",
        "insufficient_evidence",
        "verification_failed",
    )
    reason = "ok"
    failed_codes = {code for code, _ in failures}
    for candidate in precedence:
        if candidate in failed_codes:
            reason = candidate
            break

    return {
        "passed": not failures,
        "checks": checks,
        "evidence_sufficient": not failures,
        "answer_type_matches": "answer_type_matches" not in {check for _, check in failures},
        "date_coverage": date_coverage,
        "grain_checked": bool(dedup_applied) if duplicate_risk else True,
        "dedup_applied": bool(dedup_applied),
        "unit_conversion_checked": bool(unit_conversion_checked),
        "plan_checked": bool(sql_results)
        and all(bool(_sql_validation(result).get("plan_checked")) for result in sql_results),
        "residual_risks": warnings,
        "reason_code": reason,
    }
