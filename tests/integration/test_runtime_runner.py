"""End-to-end baseline runner tests using only synthetic business data."""

from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

from jsonschema import Draft202012Validator

from datamate.application.runner import _make_result, run


class RuntimeRunnerTests(unittest.TestCase):
    def _inputs(self, root: pathlib.Path) -> pathlib.Path:
        data_root = root / "data"
        business = data_root / "data" / "biz_001"
        business.mkdir(parents=True)
        (business / "sales.csv").write_text("amount\n4\n3\n", encoding="utf-8")
        (data_root / "questions.jsonl").write_text(
            json.dumps(
                {
                    "id": "q_synthetic0001",
                    "business_id": "biz_001",
                    "question": "What is total amount?",
                    "as_of_date": "2026-01-01",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return data_root

    def test_injected_fake_planner_writes_typed_submission_and_separate_log(self):
        class FakeGenerator:
            def generate_one(self, question, schema, index, rules, calendar):
                return {"sql": "SELECT SUM(amount) AS total FROM sales", "type": "number"}

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            data_root = self._inputs(root)
            result_root = root / "result"
            summary = run(data_root, result_root, generator=FakeGenerator())
            submission = json.loads((result_root / "submission.jsonl").read_text(encoding="utf-8"))
            log = json.loads((result_root / "logs" / "questions.jsonl").read_text(encoding="utf-8"))

            self.assertEqual(summary, {"questions": 1, "answered": 1})
            self.assertEqual(
                submission,
                {"id": "q_synthetic0001", "type": "number", "answer": 7},
            )
            self.assertEqual(log["answer"], {"type": "number", "answer": 7})
            self.assertEqual(log["output"]["reason_code"], "ok")
            self.assertNotIn("verification", submission)

            contract = json.loads(
                pathlib.Path("configs/inference_contract.json").read_text(encoding="utf-8")
            )
            Draft202012Validator(contract).validate(log["output"])
            submission_schema = {
                "$schema": contract["$schema"],
                "$defs": contract["$defs"],
                "$ref": "#/$defs/submission",
            }
            Draft202012Validator(submission_schema).validate(submission)

    def test_missing_planner_fails_closed_with_contract_valid_abstention(self):
        request = {
            "id": "q_synthetic0001",
            "business_id": "biz_001",
            "question": "What is total amount?",
            "as_of_date": "2026-01-01",
        }
        result = _make_result(
            request,
            candidate=None,
            generator_configured=False,
            duration_ms=3,
        )
        contract = json.loads(
            pathlib.Path("configs/inference_contract.json").read_text(encoding="utf-8")
        )
        Draft202012Validator(contract).validate(result)
        self.assertEqual(result["execution_status"], "abstain")
        self.assertEqual(result["reason_code"], "invalid_model_output")


if __name__ == "__main__":
    unittest.main()
