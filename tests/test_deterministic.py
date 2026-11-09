from datetime import date
import unittest

from datamate.application.plans import Period, QuestionPlan, Unresolved


class PlanTests(unittest.TestCase):
    def test_period_is_inclusive_and_rejects_inverted_bounds(self):
        day = date(2026, 1, 1)
        self.assertEqual(QuestionPlan("orders", "number", Period(day, day)).period.end, day)
        with self.assertRaises(ValueError):
            Period(day, date(2025, 12, 31))
        self.assertEqual(Unresolved("ambiguous_period").reason, "ambiguous_period")


class IntentTests(unittest.TestCase):
    def test_near_match_and_stable_tie(self):
        from datamate.ranking.intents import IntentIndex

        index = IntentIndex((("orders", "đếm số đơn hàng"), ("receipts", "tổng tiền phiếu nhập hàng")))
        self.assertEqual(index.rank("tông tiền phiếu nhập hàng bnhiu")[0].intent, "receipts")
        tied = IntentIndex((("first", "cùng chữ"), ("second", "cùng chữ")))
        self.assertEqual([match.intent for match in tied.rank("cùng chữ")], ["first", "second"])
