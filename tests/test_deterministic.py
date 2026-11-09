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

    def test_purchase_loader_combines_matching_split_sources(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from datamate.application.purchases import answer_purchase_total
        from datamate.data.sources import SourceCatalog

        with TemporaryDirectory() as folder:
            root = Path(folder)
            header = "Mã nhập hàng,Thời gian,Cần trả NCC,Trạng thái\n"
            (root / "DanhSachNhapHang_2025.csv").write_text(header + "001,01/01/2025,100,Hoàn thành\n", encoding="utf-8")
            (root / "DanhSachNhapHang_2026.csv").write_text(header + "002,01/01/2026,200,Hoàn thành\n", encoding="utf-8")
            answer = answer_purchase_total(SourceCatalog(root), "Tháng 1/2025 tổng giá trị phiếu nhập", date(2026, 1, 1))
            self.assertEqual(answer, {"type": "number", "answer": 100})

    def test_purchase_loader_binds_sqlite_domain_schema_aliases(self):
        import sqlite3
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from datamate.application.purchases import answer_purchase_total
        from datamate.data.sources import SourceCatalog

        with TemporaryDirectory() as folder:
            root = Path(folder)
            with sqlite3.connect(root / "retail.db") as db:
                db.execute("CREATE TABLE phieu_nhap (NgayNhapKho TEXT, TongGiaTriNhap TEXT, TinhTrang TEXT)")
                db.execute("INSERT INTO phieu_nhap VALUES ('2026-09-01', '123000', 'Hoàn thành')")
            db.close()
            answer = answer_purchase_total(SourceCatalog(root), "Tháng 9/2026 tổng tiền nhập hàng",
                                           date(2026, 9, 7))
            self.assertEqual(answer, {"type": "number", "answer": 123000})


class SalesTests(unittest.TestCase):
    def test_order_count_deduplicates_and_excludes_cancelled_or_returned(self):
        import polars as pl
        from datamate.application.sales import count_orders

        orders = pl.DataFrame({"order_id": ["a", "a", "b", "c", "d"],
                               "day": [date(2026, 9, 1)] * 5,
                               "status": ["completed", "completed", "shipping", "cancelled", "returned"]})
        self.assertEqual(count_orders(orders, Period(date(2026, 9, 1), date(2026, 9, 1))),
                         {"type": "number", "answer": 2})

    def test_revenue_sums_lines_but_not_order_discount_or_shipping(self):
        import polars as pl
        from datamate.application.sales import revenue_total

        orders = pl.DataFrame({"order_id": ["a", "b", "c"],
                               "day": [date(2026, 9, 1)] * 3,
                               "status": ["completed", "returned", "shipping"],
                               "order_discount": [100, 0, 0], "shipping_fee": [50, 0, 0]})
        lines = pl.DataFrame({"order_id": ["a", "a", "b", "c"], "amount": [300, 200, 999, 100]})
        self.assertEqual(revenue_total(orders, lines, Period(date(2026, 9, 1), date(2026, 9, 1))),
                         {"type": "number", "answer": 600})

    def test_revenue_group_share_keeps_unassigned_revenue_in_denominator(self):
        import polars as pl
        from datamate.application.sales import revenue_by_group

        orders = pl.DataFrame({"order_id": ["a", "b"], "day": [date(2026, 9, 1)] * 2,
                               "status": ["completed", "completed"], "customer_group": ["VIP", None]})
        lines = pl.DataFrame({"order_id": ["a", "b"], "amount": [25, 75]})
        result = revenue_by_group(orders, lines, Period(date(2026, 9, 1), date(2026, 9, 1)), "customer_group")
        self.assertEqual(result["rows"], [{"group": "VIP", "revenue": 25, "share_percent": 25.0}])


class DeterministicAgentTests(unittest.TestCase):
    def test_agent_executes_purchase_question_and_abstains_outside_scope(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from datamate.application.deterministic import DeterministicAgent

        with TemporaryDirectory() as folder:
            business = Path(folder) / "data" / "biz_test"
            business.mkdir(parents=True)
            (business / "DanhSachNhapHang.csv").write_text(
                "Mã nhập hàng,Thời gian,Cần trả NCC,Trạng thái\n"
                "001,07/09/2026,100,Hoàn thành\n002,07/09/2026,900,Đã hủy\n", encoding="utf-8")
            agent = DeterministicAgent(Path(folder))
            answer, _ = agent.answer({"id": "q1", "business_id": "biz_test",
                                      "question": "tháng này tổng giá trị các phiếu nhập hàng là bao nhiu",
                                      "as_of_date": "2026-09-07"})
            self.assertEqual(answer, {"id": "q1", "type": "number", "answer": 100})
            unsupported, _ = agent.answer({"id": "q2", "business_id": "biz_test",
                                           "question": "xếp hạng nhà cung cấp nhập nhiều nhất",
                                           "as_of_date": "2026-09-07"})
            self.assertEqual(unsupported, {"id": "q2", "type": "abstain"})
            unavailable, _ = agent.answer({"id": "q3", "business_id": "biz_test",
                                           "question": "tháng 1/2025 tổng tiền phiếu nhập hàng",
                                           "as_of_date": "2026-09-07"})
            self.assertEqual(unavailable["type"], "unanswerable")
            ranking, _ = agent.answer({"id": "q4", "business_id": "biz_test",
                                       "question": "nhà cung cấp nào nhập nhiều nhất tháng này",
                                       "as_of_date": "2026-09-07"})
            self.assertEqual(ranking, {"id": "q4", "type": "abstain"})

    def test_agent_routes_order_count_and_sales_revenue_through_polars(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from datamate.application.deterministic import DeterministicAgent

        with TemporaryDirectory() as folder:
            business = Path(folder) / "data" / "biz_test"
            business.mkdir(parents=True)
            (business / "DanhSachHoaDon.csv").write_text(
                "Mã hóa đơn,Thời gian,Trạng thái\n1,01/09/2026,Hoàn thành\n"
                "2,01/09/2026,Đã hủy\n3,02/09/2026,Đang giao\n", encoding="utf-8")
            (business / "DanhSachHoaDonChiTiet.csv").write_text(
                "Mã hóa đơn,Mã hàng,Thành tiền\n1,a,100\n2,b,200\n3,c,300\n", encoding="utf-8")
            agent = DeterministicAgent(Path(folder))
            question = {"business_id": "biz_test", "as_of_date": "2026-09-02"}
            count, _ = agent.answer({**question, "id": "c", "question": "tháng này có bao nhiêu đơn"})
            revenue, _ = agent.answer({**question, "id": "r", "question": "doanh thu tháng này bao nhiêu"})
            self.assertEqual(count, {"id": "c", "type": "number", "answer": 2})
            self.assertEqual(revenue, {"id": "r", "type": "number", "answer": 400})


class CashTests(unittest.TestCase):
    def test_cash_uses_collection_time_and_excludes_shift_end(self):
        import polars as pl
        from datamate.application.cash import cash_collected

        payments = pl.DataFrame({"day": [date(2026, 9, 1)] * 3,
                                 "hour": [6, 13, 14], "amount": [10, 100, 900],
                                 "kind": ["sale", "debt", "sale"]})
        self.assertEqual(cash_collected(payments, Period(date(2026, 9, 1), date(2026, 9, 1)), "ca sáng"),
                         {"type": "number", "answer": 110})


class MetricTests(unittest.TestCase):
    def test_rates_changes_and_average_define_edges_and_round_half_up(self):
        from datamate.application.evidence import InsufficientEvidence
        from datamate.application.metrics import average, period_change, rate

        with self.assertRaises(InsufficientEvidence):
            rate(1, 0)
        self.assertEqual(period_change(50, 100)["rows"][0], {"difference": -50, "growth_percent": -50.0})
        self.assertIsNone(period_change(2, 0)["rows"][0]["growth_percent"])
        self.assertEqual(average(2, 3)["answer"], 1)


class ProductReportTests(unittest.TestCase):
    def test_rank_uses_base_quantity_and_excludes_service_fee(self):
        import polars as pl
        from datamate.application.product_reports import rank_products

        orders = pl.DataFrame({"order_id": ["o1", "o2"], "day": [date(2026, 9, 1)] * 2,
                               "status": ["completed", "completed"]})
        lines = pl.DataFrame({"order_id": ["o1", "o1", "o2"], "product_id": ["a", "fee", "a"],
                              "product_name": ["Milk", "Phí phục vụ", "Milk"], "quantity_base": [24, 100, 12]})
        result = rank_products(orders, lines, Period(date(2026, 9, 1), date(2026, 9, 1)), limit=2)
        self.assertEqual(result["rows"][0], {"product_id": "a", "value": 36, "product_name": "Milk"})

    def test_staff_and_busiest_windows_use_valid_orders(self):
        import polars as pl
        from datamate.application.staff_reports import busiest_windows, rank_staff

        orders = pl.DataFrame({"staff_id": ["s1", "s1", "s2"], "order_id": ["o1", "o2", "o3"],
                               "day": [date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 1)],
                               "hour": [8, 9, 8], "status": ["completed", "completed", "cancelled"],
                               "amount": [10, 20, 999]})
        self.assertEqual(rank_staff(orders, Period(date(2026, 9, 1), date(2026, 9, 2)), "revenue")["rows"][0]["staff_id"], "s1")
        self.assertEqual(busiest_windows(orders, Period(date(2026, 9, 1), date(2026, 9, 2)), by="hour")["rows"][0],
                         {"hour": 8, "orders": 1})


class CustomerIdentityTests(unittest.TestCase):
    def test_customer_codes_win_and_name_fallback_groups_only_normalized_names(self):
        import polars as pl
        from datamate.application.customers import with_customer_key

        coded = with_customer_key(pl.DataFrame({"customer_id": ["001", "002", None],
                                                 "customer_name": ["Same", "Same", "Khách lẻ"]}))
        self.assertEqual(coded["customer_key"].to_list(), ["001", "002", None])
        named = with_customer_key(pl.DataFrame({"customer_name": ["  An   Bình ", "an bình", "Khách lẻ"]}))
        self.assertEqual(named["customer_key"].to_list(), ["an bình", "an bình", None])

    def test_customer_rank_requires_three_valid_orders_and_keeps_cancel_count(self):
        import polars as pl
        from datamate.application.customers import rank_customers

        orders = pl.DataFrame({"customer_key": ["a", "a", "a", "a", "b", "b", "b"],
                               "order_id": ["1", "2", "3", "4", "5", "6", "7"],
                               "day": [date(2026, 9, 1)] * 7,
                               "status": ["completed"] * 3 + ["cancelled"] + ["completed"] * 3,
                               "amount": [10, 20, 30, 0, 1, 1, 1]})
        result = rank_customers(orders, Period(date(2026, 9, 1), date(2026, 9, 1)), "cancelled_orders")
        self.assertEqual(result["rows"][0]["customer_key"], "a")
        self.assertEqual(result["rows"][0]["cancelled_orders"], 1)


class FormattingTests(unittest.TestCase):
    def test_ranked_table_orders_ties_and_limits_short_lists(self):
        from datamate.application.formatting import ranked_table

        result = ranked_table([{"id": "b", "amount": 8}, {"id": "c", "amount": 8},
                               {"id": "a", "amount": 2}], ["id", "amount"], limit=2, tie_breaker="id")
        self.assertEqual(result, {"type": "table", "answer": {"columns": ["id", "amount"],
                                  "rows": [["b", 8], ["c", 8]]}})
        self.assertEqual(ranked_table([{"id": "a", "amount": 1}], ["id", "amount"], limit=5)["answer"]["rows"],
                         [["a", 1]])


class DebtTests(unittest.TestCase):
    def test_receivables_and_collection_period_include_prior_invoice(self):
        import polars as pl
        from datamate.application.debt import outstanding_as_of

        invoices = pl.DataFrame({"order_id": ["old", "new"], "day": [date(2026, 8, 1), date(2026, 9, 2)],
                                 "amount": [100, 80]})
        payments = pl.DataFrame({"order_id": ["old", "new"], "day": [date(2026, 9, 3), date(2026, 9, 4)],
                                 "amount": [60, 10], "excluded": [False, True]})
        self.assertEqual(outstanding_as_of(invoices, payments, date(2026, 9, 5))["rows"][0]["outstanding"], 120)

    def test_debt_activity_uses_payment_date_for_prior_order_collection(self):
        import polars as pl
        from datamate.application.debt import debt_activity

        invoices = pl.DataFrame({"day": [date(2026, 8, 1), date(2026, 9, 2)], "amount": [100, 80]})
        payments = pl.DataFrame({"day": [date(2026, 9, 3)], "amount": [60]})
        result = debt_activity(invoices, payments, Period(date(2026, 9, 1), date(2026, 9, 30)))
        self.assertEqual(result["rows"][0], {"new_debt": 80, "collections": 60})


class SupplierReportTests(unittest.TestCase):
    def test_supplier_spend_and_receipt_count_are_distinct_metrics(self):
        import polars as pl
        from datamate.application.purchase_reports import rank_suppliers

        receipts = pl.DataFrame({"receipt_id": ["1", "2", "3", "4"],
                                 "supplier_id": ["a", "a", "b", "c"],
                                 "day": [date(2026, 9, 1)] * 4,
                                 "status": ["completed", "completed", "completed", "cancelled"],
                                 "amount": [100, 100, 150, 999]})
        period = Period(date(2026, 9, 1), date(2026, 9, 1))
        self.assertEqual(rank_suppliers(receipts, period, "spend")["rows"][0]["supplier_id"], "a")
        self.assertEqual(rank_suppliers(receipts, period, "receipts")["rows"][0]["supplier_id"], "a")

    def test_purchase_price_is_weighted_and_net_quantity_uses_base_units(self):
        import polars as pl
        from datamate.application.purchase_reports import net_purchased_quantity, weighted_purchase_price

        period = Period(date(2026, 9, 1), date(2026, 9, 30))
        purchases = pl.DataFrame({"day": [date(2026, 9, 1)], "amount": [240], "quantity_base": [24],
                                  "product_id": ["p"], "unit_base": ["piece"], "source_unit": ["case"]})
        sales = pl.DataFrame({"day": [date(2026, 9, 2)], "quantity_base": [5], "product_id": ["p"],
                              "unit_base": ["piece"], "source_unit": ["piece"]})
        self.assertEqual(weighted_purchase_price(purchases, period)["answer"], 10)
        self.assertEqual(net_purchased_quantity(purchases, sales, period, period)["rows"][0]["net_quantity"], 19)


class InventoryTests(unittest.TestCase):
    def test_end_of_day_stock_includes_replenishment_on_as_of_day(self):
        import polars as pl
        from datamate.application.inventory import stock_as_of

        moves = pl.DataFrame({"product_id": ["p", "p"], "day": [date(2026, 9, 1), date(2026, 9, 2)],
                             "quantity_delta": [-3, 5], "value_delta": [-30, 50]})
        self.assertEqual(stock_as_of(moves, date(2026, 9, 2))["rows"],
                         [{"product_id": "p", "quantity": 2, "stock_value": 20}])

    def test_unsold_requires_a_pre_period_sale_and_no_sale_inside_period(self):
        import polars as pl
        from datamate.application.inventory import unsold_products

        orders = pl.DataFrame({"order_id": ["old", "current"], "day": [date(2026, 8, 1), date(2026, 9, 2)],
                              "status": ["completed", "completed"]})
        lines = pl.DataFrame({"order_id": ["old", "current"], "product_id": ["a", "b"]})
        products = pl.DataFrame({"product_id": ["a", "b", "new"], "name": ["A", "B", "New"]})
        result = unsold_products(orders, lines, products, Period(date(2026, 9, 1), date(2026, 9, 30)))
        self.assertEqual(result["rows"], [{"product_id": "a", "name": "A"}])


class PricingTests(unittest.TestCase):
    def test_price_uses_recorded_pre_discount_unit_price(self):
        import polars as pl
        from datamate.application.pricing import average_list_price, price_increase_effect

        period = Period(date(2026, 9, 1), date(2026, 9, 30))
        current = pl.DataFrame({"day": [date(2026, 9, 1)], "unit_price": [12], "quantity_base": [10],
                                "line_total_after_discount": [100]})
        previous = pl.DataFrame({"unit_price": [10], "quantity_base": [10]})
        self.assertEqual(average_list_price(current, period)["answer"], 12)
        self.assertEqual(price_increase_effect(previous, current)["answer"], 20)


class ProfitTests(unittest.TestCase):
    def test_gross_profit_uses_line_recorded_cost(self):
        import polars as pl
        from datamate.application.profit import gross_profit

        period = Period(date(2026, 9, 1), date(2026, 9, 30))
        lines = pl.DataFrame({"day": [date(2026, 9, 2)], "amount": [100], "quantity": [2],
                              "cost_per_unit": [30], "product_id": ["p"]})
        gross = gross_profit(lines, period)["total"]
        self.assertEqual(gross, 40)

    def test_net_profit_deducts_all_period_expenses(self):
        import polars as pl
        from datamate.application.profit import net_profit

        period = Period(date(2026, 9, 1), date(2026, 9, 30))
        expenses = pl.DataFrame({"day": [date(2026, 9, 3)], "amount": [20], "note": ["repair"]})
        self.assertEqual(net_profit(40, expenses, period)["answer"], 20)


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
        self.assertEqual(resolve_period("Tháng này", today), Period(date(2026, 9, 1), today))


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


class CafeTests(unittest.TestCase):
    def test_modifiers_are_classified_without_duplicate_value_or_quantity(self):
        import polars as pl
        from datamate.application.cafe import annotate_cafe_lines

        result = annotate_cafe_lines(pl.DataFrame({"product_name": ["Trà sữa size L, topping: trân châu"],
                                                   "quantity": [2], "amount": [100]}))
        self.assertEqual(result.select("base_item", "size", "toppings", "quantity", "amount").row(0),
                         ("Trà sữa", "L", ["trân châu"], 2, 100))


class PharmacyTests(unittest.TestCase):
    def test_prescription_revenue_and_combination_ingredient_key(self):
        import polars as pl
        from datamate.application.pharmacy import sales_by_ingredient, sales_by_prescription

        lines = pl.DataFrame({"product_id": ["a", "b"], "amount": [100, 200]})
        products = pl.DataFrame({"product_id": ["a", "b"], "prescription": [True, False],
                                 "ingredient": ["X", "X + Y"]})
        self.assertEqual(sales_by_prescription(lines, products)["rows"],
                         [{"prescription": False, "revenue": 200}, {"prescription": True, "revenue": 100}])
        self.assertEqual(len(sales_by_ingredient(lines, products)["rows"]), 2)

    def test_lot_expiry_uses_positive_remaining_quantity_and_remaining_cost(self):
        import polars as pl
        from datamate.application.pharmacy import expiring_lots

        lots = pl.DataFrame({"product_id": ["a", "b", "c"], "lot_id": ["1", "2", "3"],
                             "expiry": [date(2026, 9, 10), date(2026, 9, 9), date(2026, 9, 12)],
                             "remaining_quantity": [4, 3, 0], "unit_cost": [10, 20, 1]})
        result = expiring_lots(lots, date(2026, 9, 9), 2)
        self.assertEqual([row["remaining_cost"] for row in result["rows"]], [60, 40])


class ConstructionTests(unittest.TestCase):
    def test_deliveries_count_by_arrival_date_not_order_date(self):
        import polars as pl
        from datamate.application.construction import count_deliveries

        deliveries = pl.DataFrame({"delivery_id": ["d1", "d2", "d3"],
                                   "delivery_day": [date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3)],
                                   "status": ["delivered", "delivered", "pending"]})
        self.assertEqual(count_deliveries(deliveries, date(2026, 9, 2))["answer"], 2)


class BabyShopTests(unittest.TestCase):
    def test_invoice_total_applies_discounts_and_shipping_only_to_valid_orders(self):
        import polars as pl
        from datamate.application.baby_shop import invoice_totals

        orders = pl.DataFrame({"order_id": ["a", "b"], "status": ["completed", "cancelled"],
                               "gross": [100, 200], "order_discount": [10, 0], "voucher": [5, 0],
                               "points": [5, 0], "shipping": [8, 0]})
        self.assertEqual(invoice_totals(orders)["customer_payable"].to_list(), [88])

    def test_member_report_uses_signup_date_and_keeps_never_buyers(self):
        import polars as pl
        from datamate.application.baby_shop import member_summary, product_sizes

        members = pl.DataFrame({"customer_id": ["a", "b", "c"], "product_id": ["p1", "p2", "p3"],
                                "registered_day": [date(2026, 9, 1), date(2026, 9, 2), date(2026, 8, 1)],
                                "size_number": ["2", None, "4"], "size_label": [None, "M", None]})
        orders = pl.DataFrame({"customer_id": ["a"], "status": ["completed"]})
        period = Period(date(2026, 9, 1), date(2026, 9, 30))
        self.assertEqual(member_summary(members, orders, period)["rows"][0],
                         {"registered_members": 2, "new_members_with_sales": 1, "never_bought": 2})
        self.assertEqual(product_sizes(members)["size"].to_list(), ["2", "M", "4"])


class RepairTests(unittest.TestCase):
    def test_warranty_visits_are_not_charged_service_counts(self):
        import polars as pl
        from datamate.application.repair import count_repair_visits, service_visit_counts

        visits = pl.DataFrame({"visit_id": ["v1", "v2", "v3"], "work": ["nhot may", "nhớt láp", "nhot may"],
                              "amount": [100, 80, 0]})
        self.assertEqual(count_repair_visits(visits)["answer"], 3)
        self.assertEqual(service_visit_counts(visits)["rows"], [{"work": "nhớt láp", "visits": 1},
                                                                 {"work": "nhớt máy", "visits": 1}])

    def test_warranty_rate_uses_paid_denominator_and_repeat_uses_plate(self):
        import polars as pl
        from datamate.application.repair import repeat_vehicles, warranty_rate

        visits = pl.DataFrame({"visit_id": ["1", "2", "3"], "plate": ["A", "A", "B"],
                               "amount": [100, 0, 50], "is_warranty": [False, True, False]})
        self.assertEqual(warranty_rate(visits)["answer"], 50.0)
        self.assertEqual(repeat_vehicles(visits)["rows"], [{"plate": "A", "visits": 2}])


class PhoneTests(unittest.TestCase):
    def test_trade_in_is_separate_from_revenue_and_payable(self):
        import polars as pl
        from datamate.application.phones import phone_sale_totals

        orders = pl.DataFrame({"order_id": ["a", "b"], "status": ["completed", "cancelled"],
                               "revenue": [100, 900], "customer_payable": [80, 900],
                               "trade_in_value": [20, 0]})
        self.assertEqual(phone_sale_totals(orders)["rows"][0],
                         {"revenue": 100, "customer_payable": 80, "trade_in_value": 20})

    def test_installment_due_today_is_not_overdue_and_prepayment_reduces_balance(self):
        import polars as pl
        from datamate.application.phones import installment_balances

        schedule = pl.DataFrame({"installment_id": ["today", "old"],
                                 "due_day": [date(2026, 9, 7), date(2026, 9, 1)], "amount": [100, 100]})
        payments = pl.DataFrame({"installment_id": ["today"], "paid_day": [date(2026, 9, 6)], "amount": [40]})
        result = installment_balances(schedule, payments, date(2026, 9, 7))["rows"][0]
        self.assertEqual(result, {"outstanding": 160, "overdue": 100, "overdue_installments": 1})

    def test_model_capacity_and_quarter_warranty_use_imei(self):
        import polars as pl
        from datamate.application.phones import phone_model, warranty_rate_by_quarter

        self.assertEqual(phone_model("Phone X 4G 128GB"), ("phone x", "128GB"))
        period = Period(date(2026, 7, 1), date(2026, 9, 30))
        sales = pl.DataFrame({"imei": ["1", "2"], "sale_day": [date(2026, 8, 1)] * 2})
        claims = pl.DataFrame({"imei": ["1"], "claim_day": [date(2026, 9, 1)]})
        self.assertEqual(warranty_rate_by_quarter(sales, claims, period)["answer"], 50.0)
