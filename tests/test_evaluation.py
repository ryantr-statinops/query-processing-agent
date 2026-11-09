import unittest

from datamate.evaluation.grouped import evaluate_grouped


class GroupedEvaluationTests(unittest.TestCase):
    def test_metrics_group_by_development_business_and_report_abstention(self):
        class Agent:
            def answer(self, question):
                kind = "number" if question["id"] == "a" else "abstain"
                answer = {"id": question["id"], "type": kind}
                if kind == "number":
                    answer["answer"] = 1
                return answer, {}

        questions = [{"id": "a", "business_id": "biz_dev"}, {"id": "b", "business_id": "biz_dev"}]
        labels = {"a": {"id": "a", "type": "number", "answer": 1},
                  "b": {"id": "b", "type": "number", "answer": 0}}
        report = evaluate_grouped(Agent(), questions, labels)
        self.assertEqual(report["overall"]["correct"], 1)
        self.assertEqual(report["overall"]["abstain"], 1)
        self.assertEqual(report["groups"]["biz_dev"]["questions"], 2)
