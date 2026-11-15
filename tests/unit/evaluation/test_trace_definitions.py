"""Checked-in trace records cover the representative questions and split."""

import json
import unittest
from pathlib import Path

from tests.support import REPO_ROOT


class TraceDefinitionTests(unittest.TestCase):
    def test_definition_groups_cover_questions_once_with_current_metadata(self):
        root = Path(REPO_ROOT)
        groups = json.loads((root / "scripts/trace_records.json").read_text(encoding="utf-8"))
        questions = json.loads(
            (root / "configs/representative_questions.json").read_text(encoding="utf-8")
        )["questions"]
        holdout_businesses = set(
            json.loads((root / "configs/splits/seed_2026.json").read_text(encoding="utf-8"))[
                "holdout_businesses"
            ]
        )

        self.assertEqual(set(groups), {"base8", "part1", "part2"})
        self.assertEqual([len(groups[name]) for name in ("base8", "part1", "part2")], [8, 26, 26])
        records = [record for name in ("base8", "part1", "part2") for record in groups[name]]
        self.assertEqual(len(records), 60)
        self.assertEqual(len({record["question_id"] for record in records}), 60)

        question_by_id = {question["id"]: question for question in questions}
        self.assertEqual(set(question_by_id), {record["question_id"] for record in records})
        for record in records:
            question = question_by_id[record["question_id"]]
            self.assertEqual(record["business_id"], question["business_id"])
            self.assertEqual(record["question"], question["question"])
            self.assertEqual(record["as_of_date"], question["as_of_date"])
            expected_split = (
                "holdout" if question["business_id"] in holdout_businesses else "development"
            )
            self.assertEqual(record["split_group"], expected_split)


if __name__ == "__main__":
    unittest.main()
