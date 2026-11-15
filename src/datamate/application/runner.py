"""Local question runner with typed submissions and separate diagnostics."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import pathlib
import time
from collections.abc import Mapping
from typing import Any

from datamate.agent.guardrails import (
    BudgetLedger,
    CONTRACT_VERSION,
    GuardrailError,
    build_error,
    build_submission_record,
    build_typed_answer,
    map_outcome,
    validate_internal_result,
    validate_request,
    verify_evidence,
)
from datamate.application.candidates import CandidatePipeline
from datamate.data.catalog import BusinessCatalog


_ERROR_CODES = {
    "ambiguous_entity",
    "budget_exhausted",
    "catalog_unavailable",
    "forbidden_function",
    "forbidden_statement",
    "forbidden_table_reference",
    "internal_error",
    "invalid_model_output",
    "invalid_request",
    "invalid_tool_argument",
    "multiple_statements",
    "no_source_table",
    "reference_leakage",
    "row_limit_exceeded",
    "sql_parse_error",
    "timeout",
    "unknown_column",
    "unknown_table",
    "unsupported_sql",
    "unsupported_tool",
    "verification_failed",
}


def _questions_path(data_root: pathlib.Path) -> pathlib.Path:
    for candidate in (data_root / "questions.jsonl", data_root / "train" / "questions.jsonl"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"questions.jsonl not found under {data_root}")


def _load_questions(data_root: pathlib.Path) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    with _questions_path(data_root).open(encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid question JSON at line {line_number}: {error}") from error
            request = validate_request(value)
            if request["id"] in seen_ids:
                raise ValueError(f"duplicate question id: {request['id']}")
            seen_ids.add(request["id"])
            questions.append(request)
    return questions


def _error_for_candidate(candidate: Mapping[str, Any] | None) -> tuple[str, dict[str, Any] | None]:
    if not candidate:
        return "invalid_model_output", None
    raw = candidate.get("error")
    result = candidate.get("result")
    if isinstance(raw, Mapping):
        code = str(raw.get("code", "invalid_model_output"))
        error = {
            "code": code if code in _ERROR_CODES else "invalid_model_output",
            "message": str(raw.get("message", "candidate was rejected")),
            "stage": raw.get("stage", "validation"),
            "retryable": bool(raw.get("retryable", False)),
            "detail": raw.get("detail"),
        }
        if code in {"unknown_table", "unknown_column"}:
            return "schema_mismatch", error
        if code in {"invalid_model_output", "invalid_tool_argument"}:
            return "invalid_model_output", error
        if code == "timeout":
            return "timeout", error
        if code == "catalog_unavailable":
            return "blocked_on_catalog", error
        return "insufficient_evidence", error
    if result is not None and not result.ok:
        code = result.error_code or "execution_error"
        stored_code = code if code in _ERROR_CODES else "internal_error"
        reason = {
            "timeout": "timeout",
            "row_limit_exceeded": "budget_exhausted",
            "unknown_table": "schema_mismatch",
            "unknown_column": "schema_mismatch",
            "catalog_unavailable": "blocked_on_catalog",
        }.get(code, "execution_error")
        return reason, build_error(
            stored_code,
            result.error or "SQL execution failed",
            stage="execution",
            detail={"elapsed_ms": result.elapsed_ms},
        )
    return "insufficient_evidence", None


def _tool_call(
    candidate: Mapping[str, Any] | None,
    budget_error: GuardrailError | None = None,
) -> list[dict[str, Any]]:
    if not candidate:
        return []
    result = candidate.get("result")
    if result is None:
        error = candidate.get("error")
        if not isinstance(error, Mapping):
            return []
        code = str(error.get("code", "invalid_model_output"))
        return [
            {
                "call_id": "tc_1",
                "tool": "run_sql",
                "status": "rejected",
                "args": {},
                "elapsed_ms": 0,
                "row_count": None,
                "rows_returned": 0,
                "error": {
                    "code": code if code in _ERROR_CODES else "invalid_model_output",
                    "message": str(error.get("message", "candidate was rejected")),
                    "stage": str(error.get("stage", "validation")),
                    "retryable": bool(error.get("retryable", False)),
                    "detail": error.get("detail"),
                },
                "source_refs": [],
                "sql_validation": None,
            }
        ]
    plan = candidate.get("candidate_plan") or {}
    if budget_error is not None:
        status = "timeout" if budget_error.code == "timeout" else "error"
    elif result.ok:
        status = "ok"
    else:
        status = "timeout" if result.error_code == "timeout" else "error"
    raw_code = budget_error.code if budget_error else result.error_code or "internal_error"
    if budget_error is not None:
        error = build_error(
            raw_code if raw_code in _ERROR_CODES else "internal_error",
            budget_error.message,
            stage="execution",
            detail={"elapsed_ms": result.elapsed_ms},
        )
    elif result.ok:
        error = None
    else:
        error = build_error(
            raw_code if raw_code in _ERROR_CODES else "internal_error",
            result.error or "SQL execution failed",
            stage="execution",
            detail={"elapsed_ms": result.elapsed_ms},
        )
    return [
        {
            "call_id": "tc_1",
            "tool": "run_sql",
            "status": status,
            "args": {"sql": plan.get("sql", ""), "max_rows": 200},
            "elapsed_ms": result.elapsed_ms,
            "row_count": len(result.rows),
            "rows_returned": len(result.rows),
            "error": error,
            "source_refs": result.source_refs,
            "sql_validation": result.sql_validation or None,
        }
    ]


def _verification_for_abstain(reason_code: str) -> dict[str, Any]:
    return verify_evidence(
        plan=None,
        retrieved_sources=[],
        tool_results=[],
        answer={"type": "unanswerable", "answer": None},
        execution_status="abstain",
        reason_code=reason_code,
    )


def _make_result(
    request: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any] | None,
    generator_configured: bool,
    duration_ms: int,
    planner_note: str | None = None,
) -> dict[str, Any]:
    result = candidate.get("result") if candidate else None
    ledger = BudgetLedger()
    budget_error = None
    try:
        if result is not None:
            ledger.consume_retrieval_round()
            ledger.consume_tool_call("run_sql", rows=len(result.rows))
            ledger.tick(result.elapsed_ms, is_query=True)
        non_query_elapsed = max(0, duration_ms - (result.elapsed_ms if result else 0))
        if non_query_elapsed:
            ledger.tick(non_query_elapsed)
    except GuardrailError as error:
        budget_error = error

    answer = candidate.get("answer") if candidate else None
    verification = candidate.get("verification") if candidate else None
    is_unanswerable = bool(answer and answer.get("type") == "unanswerable")
    accepted = bool(
        budget_error is None
        and answer
        and isinstance(verification, Mapping)
        and verification.get("passed") is True
        and (is_unanswerable or (candidate.get("features") or {}).get("sql_valid") is True)
    )
    if accepted:
        if is_unanswerable:
            status, reason_code = "abstain", "insufficient_evidence"
            answer = build_typed_answer("unanswerable", None)
        else:
            status, reason_code = "answered", "ok"
            answer = build_typed_answer(answer["type"], answer["answer"])
    elif budget_error is not None:
        reason_code = "timeout" if budget_error.code == "timeout" else "budget_exhausted"
        status = map_outcome(reason_code)["execution_status"]
        answer = build_typed_answer("unanswerable", None)
        verification = _verification_for_abstain(reason_code)
    else:
        reason_code, error = _error_for_candidate(candidate) if generator_configured else (
            "invalid_model_output",
            build_error(
                "invalid_model_output",
                planner_note or "no local planner is configured; this baseline abstains safely",
                stage="planning",
            ),
        )
        status = map_outcome(reason_code)["execution_status"]
        answer = build_typed_answer("unanswerable", None)
        verification = (
            verification
            if isinstance(verification, Mapping)
            else _verification_for_abstain(reason_code)
        )

    tool_calls = _tool_call(candidate, budget_error)
    errors: list[dict[str, Any]] = []
    if budget_error is not None:
        errors = [
            build_error(
                budget_error.code if budget_error.code in _ERROR_CODES else "budget_exhausted",
                budget_error.message,
                stage="execution",
                detail=budget_error.detail,
            )
        ]
    elif not accepted:
        if not generator_configured:
            errors = [error]
        else:
            _, error = _error_for_candidate(candidate)
            errors = [error] if error else []

    plan = candidate.get("plan") if accepted and candidate else None
    evidence = []
    if accepted and plan:
        evidence = [
            {
                "source_ref": source["source_ref"],
                "kind": "catalog",
                "table": source.get("table"),
                "column": source.get("column"),
                "locator": source.get("locator"),
                "supports": "catalog source used by a logically planned read-only query",
            }
            for source in plan.get("sources", [])
        ]

    budget_usage = ledger.snapshot()
    budget_usage["elapsed_ms"] = duration_ms

    diagnostics = {
        "contract_version": CONTRACT_VERSION,
        "question_id": request["id"],
        "business_id": request["business_id"],
        "as_of_date": request["as_of_date"],
        "execution_status": status,
        "reason_code": reason_code,
        "answer_type": answer["type"],
        "duration_ms": duration_ms,
        "retrieval": {"rounds": budget_usage["retrieval_rounds"], "sources": result.source_refs if result else []},
        "tool_calls": tool_calls,
        "verification": verification,
        "errors": errors,
        "notes": [] if generator_configured else [
            planner_note or "Local model inference is not integrated in this baseline."
        ],
        "environment": {
            "contract_version": CONTRACT_VERSION,
            "datafusion_version": importlib.metadata.version("datafusion"),
            "runtime": "offline",
        },
    }
    internal = {
        "contract_version": CONTRACT_VERSION,
        "question_id": request["id"],
        "business_id": request["business_id"],
        "execution_status": status,
        "reason_code": reason_code,
        "answer": answer,
        "plan": plan,
        "evidence": evidence,
        "tool_calls": tool_calls,
        "verification": verification,
        "budgets": budget_usage,
        "errors": errors,
        "diagnostics": diagnostics,
    }
    validate_internal_result(internal)
    return internal


def run(
    data_root: pathlib.Path,
    result_root: pathlib.Path,
    *,
    generator: Any | None = None,
    model_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Run all input questions, writing submission JSONL and separate logs."""

    data_root = pathlib.Path(data_root)
    result_root = pathlib.Path(result_root)
    questions = _load_questions(data_root)
    if model_path is None and os.environ.get("DATAMATE_MODEL_PATH"):
        model_path = pathlib.Path(os.environ["DATAMATE_MODEL_PATH"])
    planner_init_error = None
    if generator is None and model_path is not None:
        model_file = pathlib.Path(model_path)
        if model_file.exists():
            try:
                from datamate.generation.vllm_adapter import VllmPlanner

                generator = VllmPlanner(model_file)
                if hasattr(generator, "warmup"):
                    generator.warmup()
            except Exception as exc:
                generator = None
                planner_init_error = f"vLLM adapter failed to load: {exc}"

    candidate_count = int(os.environ.get("DATAMATE_CANDIDATE_COUNT", "1"))
    pipeline = CandidatePipeline(data_root, generator, count=candidate_count) if generator is not None else None
    submissions: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []

    for request in questions:
        started = time.monotonic()
        candidates: list[dict[str, Any]] = []
        if pipeline is not None:
            try:
                business_dir = pipeline.business_dir(request["business_id"])
                with BusinessCatalog(business_dir) as catalog:
                    candidates = pipeline.generate(request, catalog)
            except (FileNotFoundError, OSError) as error:
                candidates = [
                    {
                        "error": {
                            "code": "catalog_unavailable",
                            "message": str(error),
                            "stage": "retrieval",
                            "retryable": False,
                            "detail": None,
                        },
                        "features": {"sql_valid": False},
                    }
                ]
            except Exception as error:
                candidates = [
                    {
                        "error": {
                            "code": "invalid_model_output",
                            "message": f"candidate generation failed: {error}",
                            "stage": "planning",
                            "retryable": False,
                            "detail": None,
                        },
                        "features": {"sql_valid": False},
                    }
                ]
        accepted = next(
            (
                item
                for item in candidates
                if item.get("answer")
                and (item.get("verification") or {}).get("passed") is True
                and (
                    item.get("answer", {}).get("type") == "unanswerable"
                    or (item.get("features") or {}).get("sql_valid") is True
                )
            ),
            candidates[0] if candidates else None,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        planner_note = None
        if generator is None:
            if planner_init_error:
                planner_note = planner_init_error
            elif model_path is None:
                planner_note = "no local planner adapter is configured; baseline abstains safely"
            elif not pathlib.Path(model_path).is_file():
                planner_note = f"model file does not exist: {model_path}; baseline abstains safely"
            else:
                planner_note = "model file exists but the local planner adapter could not be initialized"
        internal = _make_result(
            request,
            candidate=accepted,
            generator_configured=generator is not None,
            duration_ms=duration_ms,
            planner_note=planner_note,
        )
        submissions.append(
            build_submission_record(
                request["id"],
                internal["answer"],
                internal["execution_status"],
            )
        )
        logs.append(
            {
                "id": request["id"],
                "answer": internal["answer"],
                "elapsed_ms": duration_ms,
                "thinking": None,
                "code": internal["reason_code"],
                "output": internal,
            }
        )

    result_root.mkdir(parents=True, exist_ok=True)
    log_root = result_root / "logs"
    log_root.mkdir(parents=True, exist_ok=True)
    (result_root / "submission.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n" for record in submissions),
        encoding="utf-8",
    )
    (log_root / "questions.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n" for record in logs),
        encoding="utf-8",
    )
    return {"questions": len(submissions), "answered": sum(log["code"] == "ok" for log in logs)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local DataMate baseline.")
    parser.add_argument("--data-root", type=pathlib.Path, default=pathlib.Path("/data"))
    parser.add_argument("--result-root", type=pathlib.Path, default=pathlib.Path("/result"))
    env_model = os.environ.get("DATAMATE_MODEL_PATH")
    parser.add_argument(
        "--model-path",
        type=pathlib.Path,
        default=pathlib.Path(env_model) if env_model else None,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run(args.data_root, args.result_root, model_path=args.model_path)
    print(f"questions={summary['questions']} answered={summary['answered']}")
    return 0
