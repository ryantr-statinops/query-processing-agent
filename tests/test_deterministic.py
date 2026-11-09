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


    def test_requires_supported_operation_and_parameters(self):
        from datamate.application.routing import select_plan
        from datamate.ranking.intents import IntentIndex

        index = IntentIndex((("purchase", "tổng tiền nhập hàng trong tháng"),))
        parse = {"purchase": lambda text: QuestionPlan("purchase", "number")
                 if "tổng tiền" in text and "tháng này" in text else None}
        self.assertIsInstance(select_plan("nhà cung cấp nhập hàng nào nhiều nhất", index, parse)[0], Unresolved)
        self.assertIsInstance(select_plan("tổng tiền nhập hàng", index, parse)[0], Unresolved)
        self.assertEqual(select_plan("tổng tiền nhập hàng tháng này", index, parse)[0].intent, "purchase")


class PeriodTests(unittest.TestCase):
    def test_explicit_periods(self):
        from datamate.application.periods import explicit_period

        today = date(2026, 2, 15)
        self.assertEqual(explicit_period("từ 01/02/2026 đến 03/02/2026", today),
                         Period(date(2026, 2, 1), date(2026, 2, 3)))
        self.assertEqual(explicit_period("tháng 9", today).start, date(2025, 9, 1))
        self.assertEqual(explicit_period("quý 4/2025", today).end, date(2025, 12, 31))
        self.assertIsNone(explicit_period("ngày 31/02/2026", today))


    def test_relative_periods(self):
        from datamate.application.periods import resolve_period

        today = date(2026, 9, 7)
        self.assertEqual(resolve_period("tháng này", today), Period(date(2026, 9, 1), today))
        self.assertEqual(resolve_period("tuần này", today), Period(today, today))
        self.assertEqual(resolve_period("tuần rồi", today), Period(date(2026, 8, 31), date(2026, 9, 6)))
        self.assertEqual(resolve_period("3 ngày gần nhất", today), Period(date(2026, 9, 5), today))
