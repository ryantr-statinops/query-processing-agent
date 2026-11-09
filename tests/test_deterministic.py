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


class PurchaseTests(unittest.TestCase):
    def test_purchase_total_uses_inclusive_period_and_excludes_cancelled(self):
        from decimal import Decimal
        import polars as pl
        from datamate.application.purchases import purchase_total

        frame = pl.DataFrame({"day": [date(2026, 9, 1), date(2026, 9, 7), date(2026, 9, 8)],
                              "amount": [Decimal("89526400"), Decimal("400"), Decimal("999")],
                              "status": ["completed", "cancelled", "completed"]})
        self.assertEqual(purchase_total(frame, Period(date(2026, 9, 1), date(2026, 9, 7))),
                         {"type": "number", "answer": 89526400})


class SalesTests(unittest.TestCase):
    def test_order_count_deduplicates_and_excludes_cancelled_or_returned(self):
        import polars as pl
        from datamate.application.sales import count_orders

        orders = pl.DataFrame({"order_id": ["a", "a", "b", "c", "d"],
                               "day": [date(2026, 9, 1)] * 5,
                               "status": ["completed", "completed", "shipping", "cancelled", "returned"]})
        self.assertEqual(count_orders(orders, Period(date(2026, 9, 1), date(2026, 9, 1))),
                         {"type": "number", "answer": 2})


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


    def test_aligns_partial_month_comparisons(self):
        from datamate.application.periods import comparison_periods

        today = date(2026, 3, 31)
        current, previous = comparison_periods("doanh thu tháng này so với tháng trước", today)
        self.assertEqual(current, Period(date(2026, 3, 1), today))
        self.assertEqual(previous, Period(date(2026, 2, 1), date(2026, 2, 28)))


    def test_tet_uses_both_lunar_years(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from datamate.application.periods import before_tet, tet_period

        with TemporaryDirectory() as folder:
            calendar = Path(folder) / "calendar.csv"
            calendar.write_text("date,lunar_year,lunar_month,lunar_day,lunar_leap\n"
                                "2026-02-10,2025,12,23,false\n2026-02-26,2026,1,10,false\n")
            period = tet_period("dịp tết năm 2026", date(2026, 3, 1), calendar)
            self.assertEqual(period, Period(date(2026, 2, 10), date(2026, 2, 26)))
            self.assertEqual(before_tet(period).end, date(2026, 2, 9))


    def test_shift_ranges_and_weekday_counts(self):
        from datamate.application.periods import count_weekdays, shift_hours

        self.assertEqual(shift_hours("ca sáng"), (6, 14))
        self.assertEqual(shift_hours("ca chiều"), (14, 22))
        self.assertEqual(count_weekdays(Period(date(2026, 9, 1), date(2026, 9, 30)), 0), 4)
        self.assertEqual(count_weekdays(Period(date(2026, 9, 1), date(2026, 9, 30)), 1), 5)


    def test_evidence_coverage_and_half_up_money(self):
        import polars as pl
        from datamate.application.evidence import InsufficientEvidence, in_period, numeric_answer

        table = pl.DataFrame({"day": [date(2026, 1, 1), date(2026, 1, 3)]})
        self.assertEqual(in_period(table, Period(date(2026, 1, 2), date(2026, 1, 2))).height, 0)
        self.assertEqual(in_period(table, Period(date(2025, 12, 31), date(2026, 1, 1))).height, 1)
        with self.assertRaises(InsufficientEvidence):
            in_period(table, Period(date(2025, 1, 1), date(2025, 1, 2)))
        self.assertEqual(numeric_answer(12.5, money=True), {"type": "number", "answer": 13})
