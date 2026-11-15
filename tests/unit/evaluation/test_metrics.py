"""Regression tests for challenge scoring and grouped evaluation reports."""

import json
from pathlib import Path
import tempfile
import unittest

from datamate.evaluation.grouped import evaluate_grouped, evaluate_predictions_grouped
from datamate.evaluation.labels import answers_match, label_match, pa_reward
from datamate.evaluation.metrics import score_predictions
from datamate.evaluation.splits import build_split_manifest, validate_split_manifest


class AnswerMatchingTests(unittest.TestCase):
    def test_number_boolean_and_percent_types_are_strict(self):
        self.assertTrue(answers_match({"type": "number", "answer": 10}, {"type": "number", "answer": 10.0}))
        self.assertFalse(answers_match({"type": "number", "answer": True}, {"type": "number", "answer": 1}))
        self.assertFalse(answers_match({"type": "boolean", "answer": 0}, {"type": "boolean", "answer": False}))
        self.assertTrue(answers_match({"type": "percent", "answer": 12.345}, {"type": "percent", "answer": 12.35}))
        self.assertFalse(answers_match({"type": "percent", "answer": True}, {"type": "percent", "answer": 1.0}))

    def test_string_alias_list_order_and_unanswerable_rules(self):
        reference = {"type": "string", "answer": "Cà phê", "alias": ["coffee"]}
        self.assertTrue(label_match({"type": "string", "answer": "COFFEE"}, reference))
        self.assertFalse(answers_match({"type": "list", "answer": ["a", "b"]}, {"type": "list", "answer": ["b", "a"]}))
        self.assertTrue(answers_match({"type": "unanswerable", "answer": None}, {"type": "unanswerable", "answer": None}))
        self.assertEqual(pa_reward({"type": "unanswerable"}, {"type": "number", "answer": 0}), -1)
        self.assertEqual(pa_reward({"type": "abstain"}, {"type": "number", "answer": 0}), 0)

    def test_table_columns_align_by_name_and_rows_compare_as_a_set(self):
        predicted = {"type": "table", "answer": {"columns": ["revenue", "group"], "rows": [[200, "B"], [100, "A"]]}}
        reference = {"type": "table", "answer": {"columns": ["group", "revenue"], "rows": [["A", 100.0], ["B", 200.0]]}}
        self.assertTrue(answers_match(predicted, reference))
        positional = {"type": "table", "answer": {"columns": ["first", "second"], "rows": [["A", 100], ["B", 200]]}}
        self.assertTrue(answers_match(positional, reference))


class MetricsTests(unittest.TestCase):
    def test_penalized_accuracy_counts_missing_as_zero_reward(self):
        references = {
            "correct": {"type": "number", "answer": 5},
            "wrong": {"type": "number", "answer": 5},
            "abstain": {"type": "number", "answer": 5},
            "missing": {"type": "number", "answer": 5},
        }
        predictions = {
            "correct": {"type": "number", "answer": 5},
            "wrong": {"type": "number", "answer": 8},
            "abstain": {"type": "abstain"},
        }
        self.assertEqual(
            score_predictions(predictions, references),
            {
                "total": 4,
                "correct": 1,
                "wrong": 1,
                "abstain": 1,
                "missing": 1,
                "coverage": 0.5,
                "accuracy_answered": 0.5,
                "pa": 0.0,
            },
        )

    def test_grouped_evaluation_reports_per_business_and_abstention(self):
        questions = [{"id": "a", "business_id": "biz_101"}, {"id": "b", "business_id": "biz_101"}]
        references = {"a": {"type": "number", "answer": 1}, "b": {"type": "number", "answer": 0}}
        predictions = {"a": {"type": "number", "answer": 1}, "b": {"type": "abstain"}}
        report = evaluate_predictions_grouped(questions, predictions, references)
        self.assertEqual(report["overall"]["correct"], 1)
        self.assertEqual(report["overall"]["abstain"], 1)
        self.assertEqual(report["groups"]["biz_101"]["questions"], 2)

    def test_grouped_agent_interface_accepts_answer_and_trace_tuple(self):
        class Agent:
            def answer(self, question):
                return {"id": question["id"], "type": "number", "answer": 1}, {"stage": "execution"}

        questions = [{"id": "a", "business_id": "biz_101"}]
        report = evaluate_grouped(Agent(), questions, {"a": {"type": "number", "answer": 1}})
        self.assertEqual(report["overall"]["pa"], 1.0)
        self.assertEqual(report["rows"][0]["trace"], {"stage": "execution"})


class SplitManifestTests(unittest.TestCase):
    def test_split_is_deterministic_complete_and_business_disjoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = [{"id": f"q{index}", "business_id": f"biz_{index:03}"} for index in range(30)]
            (root / "questions.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
            )
            first = build_split_manifest(root)
            second = build_split_manifest(root)
        self.assertEqual(first, second)
        self.assertEqual(len(first["holdout_businesses"]), 6)
        validate_split_manifest(first)

    def test_checked_in_split_manifest_is_disjoint_and_covers_development(self):
        root = Path(__file__).resolve().parents[3]
        manifest = json.loads((root / "configs/splits/seed_2026.json").read_text(encoding="utf-8"))
        validate_split_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
