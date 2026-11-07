from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datamate.answers import answer_from_result, answers_match, pa_reward  # noqa: E402
from datamate.generation.local_gguf import parse_candidate_json  # noqa: E402
from datamate.execution.sql import execute_select  # noqa: E402
from datamate.data.splits import build_split_manifest  # noqa: E402
from datamate.data.catalog import BusinessCatalog  # noqa: E402


class AnswerTests(unittest.TestCase):
    def test_number_and_abstention_scoring(self):
        prediction = answer_from_result("number", ["value"], [[12]])
        self.assertEqual(prediction, {"type": "number", "answer": 12})
        self.assertTrue(answers_match(prediction, {"type": "number", "answer": 12}))
        self.assertEqual(pa_reward({"type": "abstain"}, {"type": "number", "answer": 12}), 0)

    def test_unanswerable_is_typed(self):
        self.assertEqual(answer_from_result("unanswerable", [], []), {"type": "unanswerable"})


class CatalogTests(unittest.TestCase):
    def test_polars_datafusion_select_and_reject_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            business = pathlib.Path(temp)
            (business / "records.csv").write_text("item,total\napples,4\npears,7\n", encoding="utf-8")
            catalog = BusinessCatalog(business)
            try:
                result = execute_select(catalog, "SELECT SUM(total) AS value FROM records")
                self.assertTrue(result.ok, result.error)
                self.assertEqual(result.rows, [[11]])
                self.assertFalse(execute_select(catalog, "UPDATE records SET total=0").ok)
                self.assertFalse(execute_select(catalog, "SELECT * FROM read_csv('/etc/passwd')").ok)
            finally:
                catalog.close()


class SplitTests(unittest.TestCase):
    def test_business_split_is_disjoint_deterministic_and_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            train_root = pathlib.Path(temp)
            records = [{"id": f"q{i}", "business_id": f"biz_{i:02}"} for i in range(30)]
            (train_root / "questions.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in records), encoding="utf-8"
            )
            first = build_split_manifest(train_root)
            second = build_split_manifest(train_root)
            self.assertEqual(first, second)
            holdout = set(first["holdout_businesses"])
            folds = [set(fold) for fold in first["folds"]]
            self.assertEqual(len(holdout), 6)
            self.assertTrue(all(not holdout.intersection(fold) for fold in folds))
            self.assertEqual(set.union(*folds) | holdout, {row["business_id"] for row in records})


class GeneratorParsingTests(unittest.TestCase):
    def test_extracts_json_from_markdown_fence(self):
        self.assertEqual(parse_candidate_json('```json\n{"sql":"SELECT 1","type":"number"}\n```'),
                         {"sql": "SELECT 1", "type": "number"})


class RunnerSmokeTests(unittest.TestCase):
    def test_runner_writes_submission_and_required_log_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            data_root = root / "data"
            business = data_root / "data" / "biz_1"
            business.mkdir(parents=True)
            (business / "records.csv").write_text("item,total\napples,4\n", encoding="utf-8")
            (data_root / "questions.jsonl").write_text(
                json.dumps({"id": "q1", "business_id": "biz_1", "question": "total?", "as_of_date": "2026-01-01"}) + "\n",
                encoding="utf-8",
            )
            (data_root / "calendar.csv").write_text("date,weekday\n2026-01-01,4\n", encoding="utf-8")
            (data_root / "rulebook.md").write_text("", encoding="utf-8")
            result_root = root / "result"
            subprocess.run(
                [sys.executable, str(ROOT / "src" / "runner.py"), "--data-root", str(data_root),
                 "--result-root", str(result_root), "--model-path", str(root / "missing.gguf")],
                check=True,
                capture_output=True,
                text=True,
            )
            submission = json.loads((result_root / "submission.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(submission, {"id": "q1", "type": "abstain"})
            log = json.loads((result_root / "logs" / "questions.jsonl").read_text(encoding="utf-8"))
            self.assertTrue({"id", "answer", "elapsed_ms", "thinking", "code", "output"}.issubset(log))


if __name__ == "__main__":
    unittest.main()
