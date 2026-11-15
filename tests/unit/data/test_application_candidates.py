"""Synthetic end-to-end tests for candidate execution and typed answer output."""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from datamate.agent.guardrails import GuardrailError
from datamate.application.answers import answer_from_result
from datamate.application.candidates import CandidatePipeline
from datamate.data.catalog import BusinessCatalog
from datamate.generation.local_gguf import parse_candidate_json


class TypedAnswerTests(unittest.TestCase):
    def test_scalar_list_table_and_unanswerable_shapes(self):
        self.assertEqual(answer_from_result("number", ["n"], [[12]]), {"type": "number", "answer": 12})
        self.assertEqual(answer_from_result("list", ["name"], [["a"], ["b"]]),
                         {"type": "list", "answer": ["a", "b"]})
        self.assertEqual(answer_from_result("table", ["name"], [["a"]]),
                         {"type": "table", "answer": {"columns": ["name"], "rows": [["a"]]}})
        self.assertEqual(answer_from_result("unanswerable", [], []),
                         {"type": "unanswerable", "answer": None})

    def test_empty_result_is_not_coerced_to_zero(self):
        with self.assertRaises(GuardrailError) as caught:
            answer_from_result("number", ["n"], [])
        self.assertEqual(caught.exception.code, "insufficient_evidence")


class CandidatePipelineTests(unittest.TestCase):
    def test_candidate_attempts_are_limited_by_the_tool_budget(self):
        with self.assertRaises(ValueError):
            CandidatePipeline(pathlib.Path("."), object(), count=4)

    def test_valid_fake_plan_executes_and_verifies_with_source_refs(self):
        class FakeGenerator:
            def generate_one(self, question, schema, index, rules, calendar):
                self.assertions = (question["id"], "sales" in schema, index, rules, calendar)
                return {"sql": "SELECT SUM(amount) AS total FROM sales", "type": "number"}

        with tempfile.TemporaryDirectory() as folder:
            data_root = pathlib.Path(folder)
            business_dir = data_root / "data" / "biz_001"
            business_dir.mkdir(parents=True)
            (business_dir / "sales.csv").write_text("amount\n4\n", encoding="utf-8")
            catalog = BusinessCatalog(business_dir)
            try:
                candidate = CandidatePipeline(data_root, FakeGenerator(), count=1).generate(
                    {
                        "id": "q_synthetic0001",
                        "business_id": "biz_001",
                        "question": "What is total amount?",
                        "as_of_date": "2026-01-01",
                    },
                    catalog,
                )[0]
                self.assertEqual(candidate["answer"], {"type": "number", "answer": 4})
                self.assertTrue(candidate["result"].ok)
                self.assertTrue(candidate["features"]["sql_valid"])
                self.assertTrue(candidate["features"]["evidence_verified"])
                self.assertEqual(candidate["features"]["source_refs"], ["catalog:biz_001:sales.csv"])
            finally:
                catalog.close()

    def test_invalid_sql_is_rejected_before_execution(self):
        class UnsafeGenerator:
            def generate_one(self, question, schema, index, rules, calendar):
                return {"sql": "SELECT * FROM unrelated", "type": "number"}

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            business_dir = root / "data" / "biz_001"
            business_dir.mkdir(parents=True)
            (business_dir / "sales.csv").write_text("amount\n4\n", encoding="utf-8")
            catalog = BusinessCatalog(business_dir)
            try:
                candidate = CandidatePipeline(root, UnsafeGenerator(), count=1).generate(
                    {
                        "id": "q_synthetic0001",
                        "business_id": "biz_001",
                        "question": "amount?",
                        "as_of_date": "2026-01-01",
                    },
                    catalog,
                )[0]
                self.assertFalse(candidate["features"]["sql_valid"])
                self.assertEqual(candidate["error"]["code"], "unknown_table")
                self.assertIsNone(candidate["result"])
            finally:
                catalog.close()

    def test_null_aggregate_keeps_execution_trace_but_does_not_answer_zero(self):
        class EmptyGenerator:
            def generate_one(self, question, schema, index, rules, calendar):
                return {
                    "sql": "SELECT SUM(amount) AS total FROM sales WHERE amount < 0",
                    "type": "number",
                }

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            business_dir = root / "data" / "biz_001"
            business_dir.mkdir(parents=True)
            (business_dir / "sales.csv").write_text("amount\n4\n", encoding="utf-8")
            catalog = BusinessCatalog(business_dir)
            try:
                candidate = CandidatePipeline(root, EmptyGenerator(), count=1).generate(
                    {
                        "id": "q_synthetic0001",
                        "business_id": "biz_001",
                        "question": "What is total amount?",
                        "as_of_date": "2026-01-01",
                    },
                    catalog,
                )[0]
                self.assertTrue(candidate["result"].ok)
                self.assertEqual(candidate["result"].rows, [[None]])
                self.assertIsNone(candidate["answer"])
                self.assertEqual(candidate["error"]["code"], "insufficient_evidence")
                self.assertTrue(candidate["features"]["sql_valid"])
            finally:
                catalog.close()


class CandidateJsonTests(unittest.TestCase):
    def test_parses_fenced_and_embedded_candidate_json(self):
        plan = {"sql": "SELECT 1 FROM sales", "type": "number"}
        self.assertEqual(parse_candidate_json('```json\n{"sql":"SELECT 1 FROM sales","type":"number"}\n```'), plan)
        self.assertEqual(parse_candidate_json(f"Plan follows: {plan!r}".replace("'", '"')), plan)


if __name__ == "__main__":
    unittest.main()
