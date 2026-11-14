import math
import unittest

from datamate.agent import guardrails as g


class RequestValidationTests(unittest.TestCase):
    def request(self, **overrides):
        payload = {
            "id": "q_synthetic0001",
            "business_id": "biz_105",
            "question": "tong doanh thu thang 5/2026",
            "as_of_date": "2026-06-24",
        }
        payload.update(overrides)
        return payload

    def test_accepts_canonical_request(self):
        result = g.validate_request(self.request())
        self.assertEqual(result["id"], "q_synthetic0001")

    def test_rejects_bad_question_id(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_request(self.request(id="not-a-question"))
        self.assertEqual(caught.exception.code, "invalid_request")

    def test_rejects_bad_business_id(self):
        with self.assertRaises(g.GuardrailError):
            g.validate_request(self.request(business_id="biz_1055"))

    def test_rejects_non_canonical_date(self):
        with self.assertRaises(g.GuardrailError):
            g.validate_request(self.request(as_of_date="24/06/2026"))
        with self.assertRaises(g.GuardrailError):
            g.validate_request(self.request(as_of_date="2026-02-30"))

    def test_rejects_unknown_fields(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_request(self.request(extra="x"))
        self.assertIn("unknown_fields", caught.exception.detail)

    def test_rejects_reference_fields(self):
        with self.assertRaises(g.GuardrailError):
            g.validate_request(self.request(gold_answer=123))

    def test_detects_nested_reference_leakage(self):
        payload = {"context": [{"table": "sales", "label": "hidden"}]}
        leaks = g.find_reference_leakage(payload)
        self.assertEqual(leaks, ["$.context[0].label"])

    def test_entity_match_score_is_not_a_label(self):
        payload = {"matches": [{"value": "Sting", "score": 0.9}]}
        self.assertEqual(g.find_reference_leakage(payload), [])


class SqlStaticValidationTests(unittest.TestCase):
    allowed_tables = ["sales", "price_history"]
    allowed_columns = ["Hàng", "Trị giá", "Ngày giao dịch", "ten_hang", "Giá mới"]

    def test_accepts_simple_select(self):
        result = g.validate_sql_static(
            'SELECT "Hàng", SUM("Trị giá") FROM "sales" GROUP BY "Hàng"',
            self.allowed_tables,
            self.allowed_columns,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["tables"], ["sales"])
        self.assertFalse(result["plan_checked"])

    def test_accepts_cte_and_join(self):
        sql = (
            'WITH x AS (SELECT "Hàng", "Trị giá" FROM "sales") '
            'SELECT x."Hàng", p."Giá mới" FROM x '
            'JOIN "price_history" AS p ON x."Hàng" = p.ten_hang'
        )
        result = g.validate_sql_static(sql, self.allowed_tables, self.allowed_columns)
        self.assertEqual(result["tables"], ["price_history"])
        self.assertEqual(result["ctes"], ["x"])

    def test_semicolon_inside_string_is_not_a_split(self):
        result = g.validate_sql_static(
            "SELECT 'a;b' AS note FROM \"sales\"",
            self.allowed_tables,
            None,
        )
        self.assertTrue(result["ok"])

    def test_trailing_semicolon_is_allowed(self):
        g.validate_sql_static('SELECT * FROM "sales";', self.allowed_tables)

    def test_comments_are_ignored(self):
        sql = (
            '-- a comment with DROP TABLE\n'
            "SELECT /* another UPDATE */ * FROM \"sales\""
        )
        g.validate_sql_static(sql, self.allowed_tables)

    def test_rejects_multiple_statements(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_sql_static(
                'SELECT * FROM "sales"; SELECT * FROM "sales"',
                self.allowed_tables,
            )
        self.assertEqual(caught.exception.code, "multiple_statements")

    def test_rejects_dml_and_ddl(self):
        for sql in (
            'DELETE FROM "sales"',
            'UPDATE "sales" SET "Trị giá" = 0',
            'DROP TABLE "sales"',
            'CREATE TABLE x (a INT)',
            'INSERT INTO "sales" VALUES (1)',
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(g.GuardrailError) as caught:
                    g.validate_sql_static(sql, self.allowed_tables)
                self.assertEqual(caught.exception.code, "forbidden_statement")

    def test_rejects_utility_statements(self):
        for sql in ("SHOW TABLES", "EXPLAIN SELECT * FROM \"sales\"", "PRAGMA foo"):
            with self.subTest(sql=sql):
                with self.assertRaises(g.GuardrailError):
                    g.validate_sql_static(sql, self.allowed_tables)

    def test_rejects_table_functions(self):
        for sql in (
            "SELECT * FROM read_csv('x.csv')",
            "SELECT * FROM generate_series(1, 3)",
            "SELECT * FROM unnest([1, 2])",
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(g.GuardrailError) as caught:
                    g.validate_sql_static(sql, self.allowed_tables)
                self.assertEqual(caught.exception.code, "forbidden_function")

    def test_rejects_qualified_table(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_sql_static(
                "SELECT * FROM information_schema.tables",
                self.allowed_tables,
            )
        self.assertEqual(caught.exception.code, "forbidden_table_reference")

    def test_rejects_unknown_table(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_sql_static("SELECT * FROM other", self.allowed_tables)
        self.assertEqual(caught.exception.code, "unknown_table")

    def test_extract_from_is_not_a_table_reference(self):
        result = g.validate_sql_static(
            'SELECT EXTRACT(YEAR FROM "Ngày giao dịch") FROM "sales"',
            self.allowed_tables,
            self.allowed_columns,
        )
        self.assertEqual(result["tables"], ["sales"])

    def test_rejects_unknown_quoted_column(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_sql_static(
                'SELECT "not_a_column" FROM "sales"',
                self.allowed_tables,
                self.allowed_columns,
            )
        self.assertEqual(caught.exception.code, "unknown_column")

    def test_allows_quoted_alias(self):
        result = g.validate_sql_static(
            'SELECT "Trị giá" AS "revenue" FROM "sales"',
            self.allowed_tables,
            self.allowed_columns,
        )
        self.assertTrue(result["ok"])

    def test_allows_quoted_alias_without_as(self):
        result = g.validate_sql_static(
            'SELECT "Trị giá" "revenue" FROM "sales"',
            self.allowed_tables,
            self.allowed_columns,
        )
        self.assertTrue(result["ok"])


def datafusion_available():
    try:
        return g.SqlPlanProbe({}).available
    except Exception:
        return False


@unittest.skipUnless(datafusion_available(), "DataFusion is not installed")
class SqlPlanProbeTests(unittest.TestCase):
    def setUp(self):
        self.probe = g.SqlPlanProbe(
            {
                "sales": {
                    "Hàng": "VARCHAR",
                    "so_luong": "DOUBLE",
                    "Trị giá": "DOUBLE",
                    "Ngày giao dịch": "DATE",
                },
                "price_history": {
                    "ten_hang": "VARCHAR",
                    "Ngày áp dụng": "DATE",
                    "Giá mới": "DOUBLE",
                },
            }
        )

    def test_accepts_join_and_reports_both_tables(self):
        result = self.probe.validate(
            'SELECT s."Hàng", p."Giá mới" FROM "sales" s '
            'JOIN "price_history" p ON s."Hàng" = p.ten_hang'
        )
        self.assertTrue(result["plan_checked"])
        self.assertEqual(result["tables"], ["sales", "price_history"])

    def test_accepts_cte(self):
        result = self.probe.validate(
            'WITH x AS (SELECT "Hàng" FROM "sales") SELECT * FROM x'
        )
        self.assertEqual(result["tables"], ["sales"])

    def test_rejects_unknown_column(self):
        with self.assertRaises(g.GuardrailError) as caught:
            self.probe.validate("SELECT missing_column FROM sales")
        self.assertEqual(caught.exception.code, "unknown_column")

    def test_rejects_unknown_table(self):
        with self.assertRaises(g.GuardrailError) as caught:
            self.probe.validate("SELECT * FROM missing")
        self.assertEqual(caught.exception.code, "unknown_table")

    def test_rejects_statement_without_source_table(self):
        with self.assertRaises(g.GuardrailError) as caught:
            self.probe.validate("SELECT 1")
        self.assertEqual(caught.exception.code, "no_source_table")

    def test_rejects_information_schema(self):
        with self.assertRaises(g.GuardrailError):
            self.probe.validate("SELECT * FROM information_schema.tables")

    def test_rejects_generate_series(self):
        with self.assertRaises(g.GuardrailError):
            self.probe.validate("SELECT * FROM generate_series(1, 3)")

    def test_rejects_show(self):
        with self.assertRaises(g.GuardrailError):
            self.probe.validate("SHOW TABLES")

    def test_rejects_multi_statement(self):
        with self.assertRaises(g.GuardrailError) as caught:
            self.probe.validate('SELECT * FROM "sales"; SELECT * FROM "sales"')
        self.assertEqual(caught.exception.code, "multiple_statements")


class BudgetTests(unittest.TestCase):
    def test_snapshot_matches_candidate_defaults(self):
        ledger = g.BudgetLedger()
        snapshot = ledger.snapshot()
        self.assertEqual(snapshot["limits"]["max_input_tokens"], 1500)
        self.assertEqual(snapshot["limits"]["max_tool_calls"], 6)
        self.assertEqual(snapshot["limits"]["max_sql_attempts"], 3)
        self.assertEqual(snapshot["limits"]["max_retrieval_rounds"], 2)
        self.assertEqual(snapshot["limits"]["max_result_rows"], 200)
        self.assertEqual(snapshot["limits"]["max_sample_rows"], 5)

    def test_sql_attempts_are_bounded(self):
        ledger = g.BudgetLedger()
        for _ in range(3):
            ledger.consume_tool_call("run_sql", rows=1)
        with self.assertRaises(g.GuardrailError) as caught:
            ledger.consume_tool_call("run_sql", rows=1)
        self.assertEqual(caught.exception.code, "budget_exhausted")

    def test_tool_calls_are_bounded(self):
        ledger = g.BudgetLedger()
        for _ in range(6):
            ledger.consume_tool_call("get_schema")
        with self.assertRaises(g.GuardrailError) as caught:
            ledger.consume_tool_call("get_schema")
        self.assertEqual(caught.exception.code, "budget_exhausted")

    def test_retrieval_rounds_are_bounded(self):
        ledger = g.BudgetLedger()
        ledger.consume_retrieval_round()
        ledger.consume_retrieval_round()
        with self.assertRaises(g.GuardrailError):
            ledger.consume_retrieval_round()

    def test_result_and_sample_row_limits(self):
        ledger = g.BudgetLedger()
        with self.assertRaises(g.GuardrailError) as caught:
            ledger.consume_tool_call("run_sql", rows=201)
        self.assertEqual(caught.exception.code, "row_limit_exceeded")
        with self.assertRaises(g.GuardrailError):
            ledger.consume_tool_call("sample_rows", rows=6)

    def test_question_deadline(self):
        ledger = g.BudgetLedger()
        ledger.tick(30000)
        with self.assertRaises(g.GuardrailError) as caught:
            ledger.tick(1)
        self.assertEqual(caught.exception.code, "timeout")

    def test_input_token_budget(self):
        ledger = g.BudgetLedger(max_input_tokens=10)
        ledger.set_input_tokens(10)
        with self.assertRaises(g.GuardrailError) as caught:
            ledger.set_input_tokens(11)
        self.assertEqual(caught.exception.code, "budget_exhausted")


class EntityResolutionTests(unittest.TestCase):
    def test_normalises_vietnamese_diacritics(self):
        self.assertEqual(g.normalise_text("Sting dâu 330ml"), "sting dau 330ml")

    def test_resolves_exact_normalised_match(self):
        result = g.resolve_entity(
            "Sting dâu 330ml",
            [{"value": "Sting dâu 330ml"}],
        )
        self.assertEqual(result["status"], "resolved")

    def test_does_not_treat_substring_as_exact(self):
        result = g.resolve_entity("sting dau", [{"value": "Sting dâu 330ml"}])
        self.assertEqual(result["status"], "unmatched")

    def test_resolves_with_supplied_score(self):
        result = g.resolve_entity(
            "sting",
            [{"value": "Sting dâu", "score": 0.95}, {"value": "Sting me", "score": 0.4}],
        )
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["matches"][0]["value"], "Sting dâu")

    def test_marks_close_candidates_ambiguous(self):
        result = g.resolve_entity(
            "sting",
            [{"value": "Sting dâu", "score": 0.95}, {"value": "Sting me", "score": 0.9}],
        )
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["reason_code"], "ambiguous_entity")

    def test_rejects_invalid_scores(self):
        with self.assertRaises(g.GuardrailError):
            g.resolve_entity("x", [{"value": "y", "score": 1.5}])

    def test_rejects_non_numeric_and_non_finite_scores(self):
        for score in (math.nan, math.inf, "0.9", True):
            with self.subTest(score=score):
                with self.assertRaises(g.GuardrailError):
                    g.resolve_entity("x", [{"value": "y", "score": score}])


class TypedAnswerTests(unittest.TestCase):
    def test_number(self):
        self.assertEqual(g.build_typed_answer("number", 0)["answer"], 0)
        self.assertEqual(g.build_typed_answer("number", 18.6)["answer"], 18.6)

    def test_number_rejects_bool_string_and_nan(self):
        for value in (True, "10", math.nan, math.inf):
            with self.subTest(value=value):
                with self.assertRaises(g.GuardrailError):
                    g.build_typed_answer("number", value)

    def test_percent_rounds_to_two_decimals(self):
        self.assertEqual(g.build_typed_answer("percent", 12.345)["answer"], 12.35)
        self.assertEqual(g.build_typed_answer("percent", -50)["answer"], -50.0)

    def test_date(self):
        self.assertEqual(g.build_typed_answer("date", "2026-05")["answer"], "2026-05")
        self.assertEqual(g.build_typed_answer("date", "2026-05-24")["answer"], "2026-05-24")
        for value in ("24/05/2026", "2026-13", "2026-02-30"):
            with self.subTest(value=value):
                with self.assertRaises(g.GuardrailError):
                    g.build_typed_answer("date", value)

    def test_boolean_string_list(self):
        self.assertTrue(g.build_typed_answer("boolean", True)["answer"])
        self.assertEqual(g.build_typed_answer("string", "Cà phê sữa")["answer"], "Cà phê sữa")
        self.assertEqual(g.build_typed_answer("list", [3, 10])["answer"], [3, 10])

    def test_list_preserves_order_and_rejects_empty(self):
        self.assertEqual(g.build_typed_answer("list", ["b", "a"])["answer"], ["b", "a"])
        with self.assertRaises(g.GuardrailError):
            g.build_typed_answer("list", [])

    def test_table(self):
        value = {
            "columns": ["khach_hang", "so_tien_no"],
            "rows": [["A", 100000], ["B", 50000]],
        }
        self.assertEqual(g.build_typed_answer("table", value)["answer"], value)

    def test_table_rejects_ragged_rows(self):
        with self.assertRaises(g.GuardrailError):
            g.build_typed_answer("table", {"columns": ["a", "b"], "rows": [["x"]]})

    def test_rejects_integers_too_large_for_float(self):
        huge = 10**400
        for answer_type, value in (
            ("number", huge),
            ("percent", huge),
            ("list", [huge]),
            ("table", {"columns": ["a"], "rows": [[huge]]}),
        ):
            with self.subTest(answer_type=answer_type):
                with self.assertRaises(g.GuardrailError):
                    g.build_typed_answer(answer_type, value)

    def test_unanswerable_requires_null(self):
        self.assertIsNone(g.build_typed_answer("unanswerable", None)["answer"])
        with self.assertRaises(g.GuardrailError):
            g.build_typed_answer("unanswerable", 0)


class OutcomeMappingTests(unittest.TestCase):
    def test_operational_failures_abstain(self):
        for reason in (
            "execution_error",
            "source_missing",
            "blocked_on_catalog",
            "budget_exhausted",
            "insufficient_evidence",
            "timeout",
            "ambiguous_entity",
            "schema_mismatch",
        ):
            with self.subTest(reason=reason):
                self.assertEqual(g.map_outcome(reason)["execution_status"], "abstain")

    def test_proven_absence_is_unanswerable(self):
        for reason in (
            "unsupported_source_role",
            "period_out_of_coverage",
            "subjective_information",
        ):
            with self.subTest(reason=reason):
                outcome = g.map_outcome(reason)
                self.assertEqual(outcome["execution_status"], "unanswerable")
                self.assertEqual(outcome["submission_type"], "unanswerable")
                self.assertFalse(outcome["abstained"])

    def test_answered_requires_concrete_type(self):
        outcome = g.map_outcome("ok", "number")
        self.assertEqual(outcome["submission_type"], "number")
        with self.assertRaises(g.GuardrailError):
            g.map_outcome("ok", "unanswerable")

    def test_reason_codes_are_not_conflated(self):
        self.assertEqual(g.map_outcome("execution_error")["reason_code"], "execution_error")
        self.assertNotEqual(
            g.map_outcome("execution_error")["note"],
            g.map_outcome("source_missing")["note"],
        )


class SubmissionAndResultTests(unittest.TestCase):
    def internal_result(self):
        return {
            "contract_version": g.CONTRACT_VERSION,
            "question_id": "q_synthetic0001",
            "business_id": "biz_105",
            "execution_status": "answered",
            "reason_code": "ok",
            "answer": {"type": "number", "answer": 123456},
            "plan": None,
            "evidence": [],
            "tool_calls": [],
            "verification": {"passed": True},
            "budgets": {},
            "errors": [],
            "diagnostics": {},
        }

    def test_abstain_submission_hides_abstain_status(self):
        record = g.build_submission_record(
            "q_synthetic0001",
            {"type": "unanswerable", "answer": None},
            "abstain",
        )
        self.assertEqual(record, {"id": "q_synthetic0001", "type": "unanswerable", "answer": None})

    def test_answered_submission_keeps_type_and_alias(self):
        record = g.build_submission_record(
            "q_synthetic0001",
            {"type": "string", "answer": "Sting dâu"},
            "answered",
            alias=["SP001"],
        )
        self.assertEqual(record["type"], "string")
        self.assertEqual(record["alias"], ["SP001"])

    def test_internal_result_accepts_consistent_answer(self):
        self.assertTrue(g.validate_internal_result(self.internal_result()))

    def test_internal_result_rejects_status_reason_mismatch(self):
        result = self.internal_result()
        result["reason_code"] = "execution_error"
        with self.assertRaises(g.GuardrailError):
            g.validate_internal_result(result)

    def test_internal_result_rejects_failed_verification(self):
        result = self.internal_result()
        result["verification"] = {"passed": False}
        with self.assertRaises(g.GuardrailError):
            g.validate_internal_result(result)

    def test_internal_result_requires_all_root_contract_fields(self):
        for field in ("plan", "evidence", "tool_calls"):
            with self.subTest(field=field):
                result = self.internal_result()
                del result[field]
                with self.assertRaises(g.GuardrailError):
                    g.validate_internal_result(result)

    def test_internal_result_rejects_malformed_ids(self):
        for field, value in (
            ("question_id", "q_valid\n"),
            ("business_id", "information_schema"),
        ):
            with self.subTest(field=field):
                result = self.internal_result()
                result[field] = value
                with self.assertRaises(g.GuardrailError):
                    g.validate_internal_result(result)

    def test_internal_result_requires_boolean_verification_status(self):
        result = self.internal_result()
        result["verification"] = {"passed": "false"}
        with self.assertRaises(g.GuardrailError):
            g.validate_internal_result(result)

    def test_internal_result_rejects_unknown_root_fields(self):
        result = self.internal_result()
        result["unexpected"] = True
        with self.assertRaises(g.GuardrailError):
            g.validate_internal_result(result)

    def test_diagnostic_record_keeps_reason(self):
        result = self.internal_result()
        result.update(
            {
                "execution_status": "abstain",
                "reason_code": "budget_exhausted",
                "answer": {"type": "unanswerable", "answer": None},
                "verification": {"passed": True},
            }
        )
        diagnostic = g.build_diagnostic_record(result)
        self.assertEqual(diagnostic["reason_code"], "budget_exhausted")
        self.assertEqual(diagnostic["execution_status"], "abstain")


class EvidenceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "intent": "revenue",
            "answer_type": "number",
            "sources": [{"source_ref": "catalog:sales", "kind": "catalog"}],
        }
        self.sql_result = {
            "tool": "run_sql",
            "status": "ok",
            "row_count": 1,
            "rows": [[0]],
            "sql_validation": {"plan_checked": True},
        }

    def verify(self, **overrides):
        arguments = {
            "plan": self.plan,
            "retrieved_sources": ["catalog:sales"],
            "tool_results": [self.sql_result],
            "answer": {"type": "number", "answer": 0},
            "execution_status": "answered",
            "reason_code": "ok",
        }
        arguments.update(overrides)
        return g.verify_evidence(**arguments)

    def test_accepts_zero_from_one_row(self):
        result = self.verify()
        self.assertTrue(result["passed"])
        self.assertEqual(result["reason_code"], "ok")

    def test_empty_result_is_not_zero(self):
        empty = dict(self.sql_result, row_count=0, rows=[])
        result = self.verify(tool_results=[empty])
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason_code"], "insufficient_evidence")

    def test_null_answer_fails(self):
        result = self.verify(answer={"type": "number", "answer": None})
        self.assertFalse(result["passed"])

    def test_ungrounded_citation_fails(self):
        plan = dict(self.plan, sources=[{"source_ref": "catalog:other", "kind": "catalog"}])
        result = self.verify(plan=plan)
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason_code"], "verification_failed")

    def test_answer_type_mismatch_fails(self):
        result = self.verify(answer={"type": "string", "answer": "x"})
        self.assertFalse(result["passed"])

    def test_requires_terminal_sql(self):
        result = self.verify(tool_results=[])
        self.assertFalse(result["passed"])

    def test_sql_execution_error_maps_to_execution_error(self):
        failed_sql = {
            "tool": "run_sql",
            "status": "error",
            "error": {"code": "internal_error"},
        }
        result = self.verify(
            tool_results=[{"tool": "get_schema", "status": "ok"}, failed_sql]
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason_code"], "execution_error")

    def test_sql_budget_rejection_maps_to_budget_exhausted(self):
        rejected_sql = {
            "tool": "run_sql",
            "status": "rejected",
            "error": {"code": "budget_exhausted"},
        }
        result = self.verify(
            tool_results=[{"tool": "get_schema", "status": "ok"}, rejected_sql]
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason_code"], "budget_exhausted")

    def test_requires_plan_checked_sql(self):
        unchecked = dict(
            self.sql_result,
            sql_validation={"plan_checked": False},
        )
        result = self.verify(tool_results=[unchecked])
        self.assertFalse(result["passed"])
        allowed = self.verify(tool_results=[unchecked], allow_static_plan=True)
        self.assertTrue(allowed["passed"])
        self.assertTrue(any("static" in risk for risk in allowed["residual_risks"]))

    def test_period_outside_coverage_is_unanswerable_reason(self):
        result = self.verify(date_coverage="none")
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason_code"], "period_out_of_coverage")

    def test_partial_coverage_warns(self):
        result = self.verify(date_coverage="partial")
        self.assertTrue(result["passed"])
        self.assertTrue(result["residual_risks"])

    def test_duplicate_risk_requires_dedup(self):
        failed = self.verify(duplicate_risk=True, dedup_applied=False)
        self.assertFalse(failed["passed"])
        passed = self.verify(duplicate_risk=True, dedup_applied=True)
        self.assertTrue(passed["passed"])

    def test_unit_conversion_requires_check(self):
        failed = self.verify(unit_conversion_required=True, unit_conversion_checked=False)
        self.assertFalse(failed["passed"])
        passed = self.verify(unit_conversion_required=True, unit_conversion_checked=True)
        self.assertTrue(passed["passed"])

    def test_abstain_consistency(self):
        result = self.verify(
            execution_status="abstain",
            reason_code="budget_exhausted",
            answer={"type": "unanswerable", "answer": None},
        )
        self.assertTrue(result["passed"])
        self.assertFalse(result["evidence_sufficient"])

    def test_abstain_cannot_claim_number(self):
        result = self.verify(
            execution_status="abstain",
            reason_code="budget_exhausted",
            answer={"type": "number", "answer": 5},
        )
        self.assertFalse(result["passed"])


class ToolCallPolicyTests(unittest.TestCase):
    def test_rejects_unknown_tool(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call("run_python", {})
        self.assertEqual(caught.exception.code, "unsupported_tool")

    def test_sample_rows_limit(self):
        with self.assertRaises(g.GuardrailError):
            g.validate_tool_call("sample_rows", {"table": "sales", "limit": 6})

    def test_search_entities_requires_query(self):
        with self.assertRaises(g.GuardrailError):
            g.validate_tool_call("search_entities", {"query": " "})

    def test_get_schema_requires_allowlisted_tables_and_known_arguments(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "get_schema",
                {"tables": ["information_schema.tables"]},
                allowed_tables=["orders"],
            )
        self.assertEqual(caught.exception.code, "unknown_table")

        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "get_schema",
                {"tables": ["orders"], "gold_answer": "leak"},
                allowed_tables=["orders"],
            )
        self.assertEqual(caught.exception.code, "invalid_tool_argument")

        result = g.validate_tool_call(
            "get_schema",
            {"tables": ["ORDERS"], "detail": "full"},
            allowed_tables=["orders"],
        )
        self.assertEqual(result["arguments"]["tables"], ["orders"])

    def test_search_entities_checks_requested_tables_and_columns(self):
        allowlist = {"orders": ["order_id", "amount"]}
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "search_entities",
                {"query": "shop", "tables": ["other"]},
                allowed_tables=["orders"],
                allowed_columns=allowlist,
            )
        self.assertEqual(caught.exception.code, "unknown_table")

        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "search_entities",
                {"query": "shop", "tables": ["orders"], "columns": ["secret"]},
                allowed_tables=["orders"],
                allowed_columns=allowlist,
            )
        self.assertEqual(caught.exception.code, "unknown_column")

        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "search_entities",
                {"query": "shop", "gold_answer": "leak"},
                allowed_tables=["orders"],
                allowed_columns=allowlist,
            )
        self.assertEqual(caught.exception.code, "invalid_tool_argument")

    def test_sample_rows_requires_allowlisted_table_and_columns(self):
        allowlist = {"orders": ["order_id", "amount"]}
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "sample_rows",
                {"table": "information_schema.tables"},
                allowed_tables=["orders"],
                allowed_columns=allowlist,
            )
        self.assertEqual(caught.exception.code, "unknown_table")

        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "sample_rows",
                {"table": "orders", "columns": ["secret"]},
                allowed_tables=["orders"],
                allowed_columns=allowlist,
            )
        self.assertEqual(caught.exception.code, "unknown_column")

        result = g.validate_tool_call(
            "sample_rows",
            {"table": "ORDERS", "columns": ["amount"], "limit": 5},
            allowed_tables=["orders"],
            allowed_columns=allowlist,
        )
        self.assertEqual(result["arguments"]["table"], "orders")

    def test_run_sql_rejects_unknown_arguments_and_bad_row_limit(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "run_sql",
                {"sql": "SELECT * FROM orders", "gold_answer": "leak"},
                allowed_tables=["orders"],
            )
        self.assertEqual(caught.exception.code, "invalid_tool_argument")

        with self.assertRaises(g.GuardrailError) as caught:
            g.validate_tool_call(
                "run_sql",
                {"sql": "SELECT * FROM orders", "max_rows": 201},
                allowed_tables=["orders"],
            )
        self.assertEqual(caught.exception.code, "invalid_tool_argument")

    def test_run_sql_without_probe_marks_static_only(self):
        result = g.validate_tool_call(
            "run_sql",
            {"sql": "SELECT * FROM sales"},
            allowed_tables=["sales"],
        )
        self.assertIn("plan_probe_not_configured", result["sql_validation"]["warnings"])


class ContextBudgetTests(unittest.TestCase):
    def test_context_budget_rejects_oversized_prompt(self):
        with self.assertRaises(g.GuardrailError) as caught:
            g.check_context_budget({"schema": "x" * 100}, max_tokens=10)
        self.assertEqual(caught.exception.code, "budget_exhausted")

    def test_context_budget_reports_sections(self):
        result = g.check_context_budget({"schema": "sales"}, max_tokens=100)
        self.assertEqual(result["tokens"], 2)


if __name__ == "__main__":
    unittest.main()
