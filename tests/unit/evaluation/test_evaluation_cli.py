"""The evaluation CLI defaults to development and records reproducibility metadata."""

import json
from pathlib import Path
import tempfile
import unittest

from scripts.evaluate_predictions import evaluate_files


class EvaluationCliTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        (root / "train").mkdir()
        (root / "configs/splits").mkdir(parents=True)
        questions = [
            {"id": "q_dev1", "business_id": "biz_101", "question": "q1", "as_of_date": "2026-01-01"},
            {"id": "q_dev2", "business_id": "biz_102", "question": "q2", "as_of_date": "2026-01-01"},
            {"id": "q_holdout", "business_id": "biz_103", "question": "q3", "as_of_date": "2026-01-01"},
        ]
        answers = [
            {"id": "q_dev1", "type": "number", "answer": 10},
            {"id": "q_dev2", "type": "number", "answer": 20},
            {"id": "q_holdout", "type": "number", "answer": 30},
        ]
        for filename, records in (("questions.jsonl", questions), ("answers.jsonl", answers)):
            (root / "train" / filename).write_text(
                "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
            )
        manifest = {
            "seed": 2026,
            "split_unit": "business_id",
            "development_businesses": ["biz_101", "biz_102"],
            "holdout_businesses": ["biz_103"],
            "folds": [["biz_101"], ["biz_102"]],
        }
        (root / "configs/splits/seed_2026.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        predictions = root / "predictions.jsonl"
        predictions.write_text(
            '{"id":"q_dev1","type":"number","answer":10}\n'
            '{"id":"q_holdout","type":"number","answer":-999}\n',
            encoding="utf-8",
        )
        return predictions

    def test_default_score_uses_development_and_records_missing_predictions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            predictions = self._fixture(root)
            output = root / "artifacts/score.json"
            report = evaluate_files(predictions, output_path=output, root=root)
            saved = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["overall"]["total"], 2)
        self.assertEqual(report["overall"]["correct"], 1)
        self.assertEqual(report["overall"]["missing"], 1)
        self.assertEqual(report["metadata"]["missing_predictions"], 1)
        self.assertEqual(report["metadata"]["split"], "development")
        self.assertFalse(report["metadata"]["exploratory_only"])
        self.assertEqual(saved, report)

    def test_exposed_holdout_requires_explicit_exploratory_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            predictions = self._fixture(root)
            with self.assertRaisesRegex(ValueError, "already been exposed"):
                evaluate_files(predictions, output_path=root / "report.json", split="holdout", root=root)
            report = evaluate_files(
                predictions,
                output_path=root / "holdout.json",
                split="holdout",
                exploratory_holdout=True,
                root=root,
            )
        self.assertTrue(report["metadata"]["exploratory_only"])
        self.assertEqual(report["overall"]["wrong"], 1)

    def test_evaluation_records_reproducible_metadata_and_intent_grouping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            predictions = self._fixture(root)
            logs = root / "logs.jsonl"
            logs.write_text('{"id":"q_dev1","elapsed_ms":150}\n{"id":"q_dev2","elapsed_ms":250}\n', encoding="utf-8")
            output = root / "artifacts/score_with_logs.json"
            report = evaluate_files(predictions, output_path=output, logs_path=logs, root=root)
            self.assertIn("by_intent", report)
            self.assertIn("prompt_config_hash", report["metadata"])
            self.assertIsNotNone(report["metadata"]["latency_summary"])
            self.assertEqual(report["metadata"]["latency_summary"]["count"], 2)
            self.assertEqual(report["metadata"]["latency_summary"]["avg_ms"], 200.0)


if __name__ == "__main__":
    unittest.main()
