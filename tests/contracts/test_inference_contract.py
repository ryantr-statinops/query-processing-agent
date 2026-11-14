import json
import unittest
from pathlib import Path

from datamate.agent import guardrails as g
from jsonschema import Draft202012Validator

from tests.support import REPO_ROOT

CONTRACT_PATH = REPO_ROOT / "configs" / "inference_contract.json"


class ContractDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_version_matches_guardrails(self):
        self.assertEqual(self.contract["x-contract-version"], g.CONTRACT_VERSION)
        self.assertEqual(self.contract["properties"]["contract_version"]["const"], g.CONTRACT_VERSION)

    def test_required_sections_exist(self):
        for key in (
            "x-schemas",
            "x-budgets",
            "x-tool-contracts",
            "x-outcome-mapping",
            "x-retrieval-policy",
            "x-open-decisions",
            "x-examples",
        ):
            self.assertIn(key, self.contract)
        for name in (
            "request",
            "business_context",
            "retrieval_context",
            "plan",
            "answer",
            "tool_call",
            "verification",
            "submission",
            "diagnostics",
            "error",
        ):
            self.assertIn(name, self.contract["x-schemas"])

    def test_answer_types_match_guardrails(self):
        self.assertEqual(
            tuple(self.contract["$defs"]["answer_type"]["enum"]),
            g.ANSWER_TYPES,
        )

    def test_reason_codes_match_guardrails(self):
        self.assertEqual(
            tuple(self.contract["$defs"]["reason_code"]["enum"]),
            g.REASON_CODES,
        )

    def test_tool_contracts_match_guardrails(self):
        names = [tool["name"] for tool in self.contract["x-tool-contracts"]]
        self.assertEqual(tuple(names), g.TOOL_NAMES)
        for tool in self.contract["x-tool-contracts"]:
            self.assertIn("input_schema", tool)
            self.assertIn("output_schema", tool)
            self.assertTrue(tool["errors"])

    def test_budgets_are_candidates_and_match_ledger(self):
        budgets = self.contract["x-budgets"]
        self.assertEqual(budgets["status"], "candidate")
        ledger = g.BudgetLedger()
        for key, spec in budgets["values"].items():
            self.assertEqual(spec["status"], "candidate", key)
            self.assertEqual(spec["value"], getattr(ledger, key), key)

    def test_outcome_mapping_covers_every_reason(self):
        mapping = self.contract["x-outcome-mapping"]
        self.assertEqual(set(mapping), set(g.REASON_CODES))
        for reason, spec in mapping.items():
            self.assertIn(spec["execution_status"], g.EXECUTION_STATUSES)
            if reason == "ok":
                self.assertEqual(spec["submission_type"], "answer_type")
                self.assertEqual(g.map_outcome(reason, "number")["execution_status"], "answered")
            else:
                self.assertEqual(
                    spec["execution_status"],
                    g.map_outcome(reason)["execution_status"],
                    reason,
                )
                self.assertEqual(spec["submission_type"], "unanswerable", reason)

    def test_operational_and_proven_absence_outcomes_are_distinct(self):
        mapping = self.contract["x-outcome-mapping"]
        self.assertEqual(mapping["execution_error"]["execution_status"], "abstain")
        self.assertEqual(mapping["source_missing"]["execution_status"], "abstain")
        self.assertEqual(mapping["blocked_on_catalog"]["execution_status"], "abstain")
        self.assertEqual(mapping["budget_exhausted"]["execution_status"], "abstain")
        self.assertEqual(mapping["insufficient_evidence"]["execution_status"], "abstain")
        self.assertEqual(
            mapping["unsupported_source_role"]["execution_status"], "unanswerable"
        )

    def test_retrieval_policy_has_no_dense_index_and_blocks_labels(self):
        policy = self.contract["x-retrieval-policy"]
        self.assertFalse(policy["dense_index"])
        self.assertEqual(policy["max_rounds"], 2)
        self.assertIn("gold answers", policy["exclusions"])
        self.assertIn("public-test labels", policy["exclusions"])

    def test_open_decisions_are_not_silently_closed(self):
        decisions = self.contract["x-open-decisions"]
        self.assertGreaterEqual(len(decisions), 6)
        for decision in decisions:
            self.assertEqual(decision["status"], "open", decision["id"])
            self.assertTrue(decision["owner"])
            self.assertTrue(decision["question"])

    def test_contract_is_a_valid_json_schema(self):
        Draft202012Validator.check_schema(self.contract)

    def test_examples_cover_every_answer_type_and_failure_mode(self):
        examples = self.contract["x-examples"]
        answer_types = {
            example["instance"]["type"]
            for example in examples
            if example["target"] == "answer" and example["expect"] == "valid"
        }
        self.assertEqual(answer_types, set(g.ANSWER_TYPES))
        names = {example["name"] for example in examples}
        for required in (
            "result_abstain_parse_failure",
            "result_abstain_unknown_column",
            "result_abstain_ambiguous_entity",
            "result_abstain_no_evidence",
            "result_abstain_execution_error",
            "result_abstain_budget_exhausted",
            "result_abstain_blocked_catalog",
            "result_unanswerable_source_role",
        ):
            self.assertIn(required, names)

    def test_examples_use_synthetic_ids_and_no_reference_labels(self):
        for example in self.contract["x-examples"]:
            self.assertNotIn("gold", json.dumps(example).casefold())
            instance = example["instance"]
            if isinstance(instance, dict) and "question_id" in instance:
                self.assertTrue(instance["question_id"].startswith("q_synthetic"))

    def _target_schema(self, target):
        if target == "result":
            return self.contract
        return {"$defs": self.contract["$defs"], "$ref": f"#/$defs/{target}"}

    def test_examples_match_schema_or_contract(self):
        for example in self.contract["x-examples"]:
            with self.subTest(example=example["name"]):
                if example["validator"] == "schema":
                    validator = Draft202012Validator(self._target_schema(example["target"]))
                    errors = list(validator.iter_errors(example["instance"]))
                    if example["expect"] == "valid":
                        self.assertEqual(errors, [], [error.message for error in errors])
                    else:
                        self.assertTrue(errors, "expected schema failure")
                else:
                    if example["expect"] == "valid":
                        self.assertTrue(g.validate_internal_result(example["instance"]))
                    else:
                        with self.assertRaises(g.GuardrailError):
                            g.validate_internal_result(example["instance"])

    def test_valid_result_examples_pass_contract_validation(self):
        for example in self.contract["x-examples"]:
            if example["target"] == "result" and example["expect"] == "valid":
                with self.subTest(example=example["name"]):
                    self.assertTrue(g.validate_internal_result(example["instance"]))

    def test_request_examples_pass_request_validation(self):
        for example in self.contract["x-examples"]:
            if example["target"] == "request" and example["expect"] == "valid":
                with self.subTest(example=example["name"]):
                    g.validate_request(example["instance"])

    def test_submission_examples_are_typed(self):
        examples = [
            example["instance"]
            for example in self.contract["x-examples"]
            if example["target"] == "submission"
        ]
        self.assertTrue(examples)
        for submission in examples:
            self.assertIn(submission["type"], g.ANSWER_TYPES)
            self.assertIn("answer", submission)

    def test_no_raw_reference_keys_in_examples(self):
        self.assertEqual(g.find_reference_leakage(self.contract["x-examples"]), [])


class ContractFileTests(unittest.TestCase):
    def test_file_is_utf8_json(self):
        raw = CONTRACT_PATH.read_bytes()
        raw.decode("utf-8")
        parsed = json.loads(raw.decode("utf-8"))
        self.assertIsInstance(parsed, dict)

    def test_contract_is_marked_proposal(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["x-status"], "proposal")
        notes = " ".join(contract["x-normative-notes"])
        self.assertIn("candidate", notes)
        self.assertIn("Gold answers", notes)


if __name__ == "__main__":
    unittest.main()
