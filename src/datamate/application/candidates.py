"""Small, injectable candidate pipeline for end-to-end baseline evaluation."""

from __future__ import annotations

import pathlib
from collections.abc import Mapping
from typing import Any

from datamate.agent.guardrails import (
    CONCRETE_ANSWER_TYPES,
    GuardrailError,
    validate_request,
    validate_tool_call,
    verify_evidence,
)
from datamate.data.catalog import BusinessCatalog
from datamate.execution.sql import MAX_QUERY_TIMEOUT_SECONDS, execute_select
from datamate.generation.local_gguf import parse_candidate_json

from .answers import answer_from_result


class CandidatePipeline:
    """Run generated SQL candidates through the same validation and execution gates."""

    def __init__(
        self,
        data_root: pathlib.Path,
        generator: Any,
        count: int = 3,
        *,
        timeout_seconds: float = MAX_QUERY_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 3:
            raise ValueError("candidate count must be between 1 and 3")
        self.data_root = pathlib.Path(data_root)
        self.generator = generator
        self.count = count
        self.timeout_seconds = timeout_seconds

    def business_dir(self, business_id: str) -> pathlib.Path:
        candidates = (self.data_root / "data" / business_id, self.data_root / business_id)
        for path in candidates:
            if path.is_dir():
                return path
        raise FileNotFoundError(f"Business package not found: {business_id}")

    def _context_file(self, name: str) -> str:
        path = self.data_root / name
        return path.read_text(encoding="utf-8-sig", errors="replace") if path.is_file() else ""

    @staticmethod
    def _contract_plan(
        request: Mapping[str, Any],
        candidate: Mapping[str, Any],
        source_refs: list[str],
        catalog: BusinessCatalog,
    ) -> dict[str, Any]:
        tables_by_ref = {table.source_ref: table for table in catalog.tables}
        shape = {
            "list": "list",
            "table": "table",
            "boolean": "boolean",
        }.get(candidate["type"], "scalar")
        return {
            "intent": "other",
            "metric": None,
            "time": {
                "raw_text": request["question"],
                "mode": "unknown",
                "as_of_date": request["as_of_date"],
                "coverage": "unknown",
            },
            "entities": [],
            "filters": [],
            "group_by": [],
            "order_by": [],
            "limit": None,
            "answer_type": candidate["type"],
            "expected_shape": shape,
            "sources": [
                {
                    "source_ref": source_ref,
                    "kind": "catalog",
                    "table": tables_by_ref[source_ref].name,
                    "column": None,
                    "locator": tables_by_ref[source_ref].source,
                    "retrieved_for": "read-only SQL execution",
                }
                for source_ref in source_refs
                if source_ref in tables_by_ref
            ],
            "steps": [
                {
                    "step_id": 1,
                    "tool": "run_sql",
                    "purpose": "execute the candidate query against verified business tables",
                    "args": {"sql": candidate["sql"], "max_rows": 200},
                    "sql": candidate["sql"],
                    "depends_on": [],
                }
            ],
            "assumptions": ["The query output columns match the requested typed answer."],
            "unknowns": ["Question intent, time interpretation and source grain need review."],
        }

    @staticmethod
    def _parse_plan(raw: Any) -> dict[str, Any]:
        plan = parse_candidate_json(raw) if isinstance(raw, str) else raw
        if not isinstance(plan, Mapping):
            raise GuardrailError("invalid_model_output", "candidate plan must be a JSON object")
        sql = plan.get("sql")
        answer_type = plan.get("type", plan.get("answer_type"))
        if isinstance(answer_type, str):
            answer_type = answer_type.strip().lower()
        if isinstance(sql, str):
            sql = sql.strip()
            if sql.startswith("```"):
                lines = sql.splitlines()
                if len(lines) >= 2 and lines[-1].startswith("```"):
                    sql = "\n".join(lines[1:-1]).strip()
            if sql.endswith(";"):
                sql = sql[:-1].strip()

        if answer_type == "unanswerable":
            return {**dict(plan), "sql": sql or "SELECT 1", "type": "unanswerable"}
        if not isinstance(sql, str) or not sql.strip():
            raise GuardrailError("invalid_model_output", "candidate plan has no SQL")
        if not isinstance(answer_type, str):
            raise GuardrailError("invalid_model_output", "candidate plan has no answer type")
        if answer_type not in CONCRETE_ANSWER_TYPES:
            raise GuardrailError("invalid_model_output", "candidate answer type must be concrete")
        return {**dict(plan), "sql": sql, "type": answer_type}

    def generate(
        self,
        question: Mapping[str, Any],
        catalog: BusinessCatalog | None = None,
    ) -> list[dict[str, Any]]:
        request = validate_request(question)
        owns_catalog = catalog is None
        if catalog is None:
            catalog = BusinessCatalog(self.business_dir(request["business_id"]))
        try:
            schema = catalog.schema_text(request["question"])
            rules = self._context_file("rulebook.md")
            calendar = self._context_file("calendar.csv")
            candidates: list[dict[str, Any]] = []
            for index in range(self.count):
                plan: dict[str, Any] | None = None
                result = None
                try:
                    raw_plan = self.generator.generate_one(
                        request,
                        schema,
                        index,
                        rules,
                        calendar,
                    )
                    plan = self._parse_plan(raw_plan)
                    if plan["type"] == "unanswerable":
                        answer = {"type": "unanswerable", "answer": None}
                        contract_plan = self._contract_plan(
                            request,
                            plan,
                            [],
                            catalog,
                        )
                        verification = verify_evidence(
                            plan=contract_plan,
                            retrieved_sources=[],
                            tool_results=[],
                            answer=answer,
                            execution_status="abstain",
                            reason_code="insufficient_evidence",
                        )
                        candidates.append(
                            {
                                "plan": contract_plan,
                                "answer": answer,
                                "verification": verification,
                                "features": {"sql_valid": True},
                                "result": None,
                            }
                        )
                        break
                    checked_call = validate_tool_call(
                        "run_sql",
                        {"sql": plan["sql"], "max_rows": 200, "purpose": "answer the question"},
                        allowed_tables=catalog.table_names,
                        allowed_columns=catalog.allowed_columns,
                    )
                    result = execute_select(
                        catalog,
                        checked_call["arguments"]["sql"],
                        timeout_seconds=self.timeout_seconds,
                        max_rows=checked_call["arguments"]["max_rows"],
                    )
                    contract_plan = self._contract_plan(
                        request,
                        plan,
                        result.source_refs,
                        catalog,
                    )
                    answer = answer_from_result(plan["type"], result.columns, result.rows) if result.ok else None
                    tool_result = {
                        "tool": "run_sql",
                        "status": "ok" if result.ok else ("timeout" if result.error_code == "timeout" else "error"),
                        "row_count": len(result.rows),
                        "rows": result.rows,
                        "sql_validation": result.sql_validation,
                        "error": None if result.ok else {"code": result.error_code, "message": result.error},
                    }
                    verification = verify_evidence(
                        plan=contract_plan,
                        retrieved_sources=result.source_refs,
                        tool_results=[tool_result],
                        answer=answer or {"type": "unanswerable", "answer": None},
                        execution_status="answered" if result.ok and answer is not None else "abstain",
                        reason_code=(
                            "ok"
                            if result.ok and answer is not None
                            else "timeout" if result.error_code == "timeout" else "insufficient_evidence"
                        ),
                        date_coverage="unknown",
                    )
                    candidates.append(
                        {
                            "index": index,
                            "plan": contract_plan,
                            "candidate_plan": plan,
                            "answer": answer,
                            "result": result,
                            "verification": verification,
                            "features": {
                                "sql_valid": bool(result.sql_validation.get("plan_checked")),
                                "evidence_verified": verification["passed"],
                                "source_refs": result.source_refs,
                            },
                        }
                    )
                except GuardrailError as error:
                    candidates.append(
                        {
                            "index": index,
                            "plan": None,
                            "candidate_plan": plan,
                            "answer": None,
                            "result": result,
                            "error": error.to_dict(),
                            "features": {
                                "sql_valid": bool(result and result.sql_validation.get("plan_checked")),
                                "evidence_verified": False,
                            },
                        }
                    )
            return candidates
        finally:
            if owns_catalog:
                catalog.close()
