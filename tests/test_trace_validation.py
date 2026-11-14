import unittest

from scripts.trace_validation import answers_match, validate_records


class TraceValidationTests(unittest.TestCase):
    def test_wrong_computed_answer_is_unresolved(self):
        question = {"id": "q1", "business_id": "biz_1", "question": "total", "as_of_date": "2026-01-01", "reference": {"type": "number", "answer": 12}}
        trace = {"question_id": "q1", "business_id": "biz_1", "question": "total", "as_of_date": "2026-01-01", "split_group": "development", "answer_type": "number", "computed_answer": -999, "gold_comparison": {"match": True}, "status": "verified"}
        result = validate_records([question], [trace], set())[0]
        self.assertFalse(result["gold_comparison"]["match"])
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["gold_comparison"]["reference_answer"], 12)

    def test_typed_answer_comparison(self):
        self.assertFalse(answers_match("boolean", 1, True))
        self.assertFalse(answers_match("number", True, 1))
        self.assertFalse(answers_match("list", ["a", "b"], ["b", "a"]))
        self.assertFalse(answers_match("table", {"columns": ["a"], "rows": [[1], [2]]}, {"columns": ["a"], "rows": [[2], [3]]}))
        self.assertTrue(answers_match("table", {"columns": ["a"], "rows": [[1], [2]]}, {"columns": ["a"], "rows": [[2], [1]]}))

    def test_duplicate_ids_and_wrong_split_fail(self):
        question = {"id": "q1", "business_id": "biz_1", "question": "total", "as_of_date": "2026-01-01", "reference": {"type": "number", "answer": 12}}
        trace = {"question_id": "q1", "business_id": "biz_1", "question": "total", "as_of_date": "2026-01-01", "split_group": "holdout", "answer_type": "number", "computed_answer": 12}
        with self.assertRaises(ValueError):
            validate_records([question, question], [trace], set())
        with self.assertRaises(ValueError):
            validate_records([question], [trace], set())


if __name__ == "__main__":
    unittest.main()
