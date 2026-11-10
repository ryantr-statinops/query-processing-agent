from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datamate.data.sources import AmbiguousSource, Source, bind_sources


class SourceTests(unittest.TestCase):
    def test_aliases_and_ambiguous_tables(self):
        first = Source(Path("receipts.xlsx"), "Sheet1", ("Thời gian", "Số tiền"))
        other = Source(Path("other.xlsx"), "Sheet1", first.columns)
        fields = {"day": ("thoi_gian",), "amount": ("so_tien",)}
        self.assertEqual(bind_sources([first, other], fields, ("receipts",))[0].fields["day"], "Thời gian")
        self.assertEqual(bind_sources([first], {"missing": ("x",)}, ()), [])
        with self.assertRaises(AmbiguousSource):
            bind_sources([first, other], fields, ())


    def test_csv_preserves_codes_and_raw_money(self):
        from datamate.data.sources import csv_source, load_csv

        with TemporaryDirectory() as folder:
            path = Path(folder) / "sales.csv"
            path.write_text('id,amount,other\n001,"12,300",x\n', encoding="utf-8")
            binding, = bind_sources([csv_source(path)], {"id": ("id",), "amount": ("amount",)}, ())
            self.assertEqual(load_csv(binding).row(0), ("001", "12,300"))


    def test_sheet_year(self):
        from datamate.data.sources import sheet_year

        self.assertEqual(sheet_year(Source(Path("sales.xlsx"), "09.2026", ("Ngày",))), 2026)
        self.assertIsNone(sheet_year(Source(Path("sales.xlsx"), "Sheet1", ("Ngày",))))


    def test_sqlite_preserves_source_and_quotes_names(self):
        import sqlite3
        from datamate.data.sources import sqlite_sources, load_sqlite

        with TemporaryDirectory() as folder:
            path = Path(folder) / "pos.sqlite"
            with sqlite3.connect(path) as database:
                database.execute('CREATE TABLE "receipt detail" ("item code" TEXT)')
                database.execute('INSERT INTO "receipt detail" VALUES (?)', ("001",))
            database.close()
            before = path.read_bytes()
            binding, = bind_sources(list(sqlite_sources(path)), {"id": ("item code",)}, ())
            self.assertEqual(load_sqlite(binding).row(0), ("001",))
            self.assertEqual(path.read_bytes(), before)


    def test_cache_is_bounded_and_scoped(self):
        from datamate.data.sources import SourceCatalog

        with TemporaryDirectory() as folder:
            for label in ("first", "second"):
                root = Path(folder) / label
                root.mkdir()
                for name in ("a", "b"):
                    (root / (name + ".csv")).write_text(f"id\n{label}-{name}\n", encoding="utf-8")
            first, second = (SourceCatalog(Path(folder) / label, capacity=1) for label in ("first", "second"))
            binding = lambda catalog, name: bind_sources(catalog.sources, {"id": ("id",)}, (name,))[0]
            before = first.load(binding(first, "a"))
            self.assertIs(first.load(binding(first, "a")), before)
            self.assertEqual(second.load(binding(second, "a")).item(), "second-a")
            first.load(binding(first, "b"))
            self.assertIsNot(first.load(binding(first, "a")), before)

    def test_sector_rules_follow_schema_evidence_not_business_id(self):
        from datamate.data.sectors import detect_sector

        schema = Source(Path("anywhere.csv"), None, ("Biển số", "Công việc", "Phiếu bảo hành", "Thợ xưởng"))
        evidence = detect_sector([schema])
        self.assertEqual(evidence.sector, "repair")
        self.assertIsNone(detect_sector([]))

    def test_header_row_score_prefers_semantic_headers_over_title_rows(self):
        from datamate.data.sources import _header_score

        self.assertGreater(_header_score(("Ngày", "Mã đơn hàng", "Thành tiền", "Trạng thái")),
                           _header_score(("SỔ CHI TIẾT BÁN HÀNG", "__UNNAMED__1")))


    def test_normalizes_values_without_mutating_codes(self):
        from datetime import date
        from decimal import Decimal
        import polars as pl
        from datamate.data.normalize import date_value, number_value, status_value

        original = pl.DataFrame({"code": ["0001", "0002", "0003"],
                                 "date": ["7/9", "2026-09-08 08:10", "2026-09-09"],
                                 "total": ["89,526,400", "2.301,50", "1,6256tr"],
                                 "note": ["Đã huỷ", "khách lấy", "Thành công"]})
        result = original.with_columns(date_value("date", 2026).alias("date"),
                                       number_value("total").alias("total"), status_value("note", note=True).alias("status"))
        self.assertEqual(result.row(0), ("0001", date(2026, 9, 7), Decimal("89526400"), "Đã huỷ", "cancelled"))
        self.assertEqual(result.row(1)[1:3], (date(2026, 9, 8), Decimal("2301.50")))
        self.assertEqual(result.row(2)[1:3], (date(2026, 9, 9), Decimal("1625600.000000")))
        self.assertEqual(result.row(2)[4], "completed")

    def test_normalizes_common_in_progress_and_ok_statuses(self):
        import polars as pl
        from datamate.data.normalize import status_value

        statuses = pl.DataFrame({"status": ["ok", "Đang vận chuyển", "Đang gửi", "Chờ giao", "Đang xử lý",
                                             "Hoàn trả", "Không giao được"]})
        result = statuses.with_columns(status_value("status").alias("normalized"))
        self.assertEqual(result.get_column("normalized").to_list(),
                         ["completed", "shipping", "shipping", "shipping", "shipping", "returned", "cancelled"])

    def test_retail_aliases_and_status_synonyms_bind_orders(self):
        from datetime import date
        from datamate.data.retail import load_orders
        from datamate.data.sources import SourceCatalog

        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "sales.csv").write_text(
                "Mã bill,Ngày giao dịch,Tình trạng đơn,Amount\n"
                "0007,2026-09-01,Đang giao dịch,1200\n"
                "0008,2026-09-02,Đã hoàn hàng,500\n"
                "0009,2026-09-03,đã lấy,700\n",
                encoding="utf-8",
            )
            orders = load_orders(SourceCatalog(root))

        self.assertEqual(orders.get_column("order_id").to_list(), ["0007", "0008", "0009"])
        self.assertEqual(orders.get_column("day").to_list(), [date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3)])
        self.assertEqual(orders.get_column("status").to_list(), ["shipping", "returned", "completed"])
        self.assertEqual(orders.get_column("amount").to_list(), [1200, 500, 700])

    def test_sales_loader_drops_daily_summary_rows(self):
        from datamate.data.retail import load_sales_lines
        from datamate.data.sources import SourceCatalog

        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "sales_lines.csv").write_text(
                "Mã đơn hàng,Thành tiền,Tên hàng hóa\n"
                "0001,100,Sản phẩm A\n"
                "0002,900,TỔNG NGÀY 01/04\n",
                encoding="utf-8",
            )
            lines = load_sales_lines(SourceCatalog(root))

        self.assertEqual(lines.get_column("order_id").to_list(), ["0001"])
        self.assertEqual(lines.get_column("amount").to_list(), [100])

    def test_retail_loaders_bind_transaction_id_and_total_aliases(self):
        from datamate.data.retail import load_orders, load_sales_lines
        from datamate.data.sources import SourceCatalog

        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "ban_hang.csv").write_text(
                "Mã GD,Ngày,trang_thai,Tổng,Sản phẩm\n"
                "001,01/09/2026,Hoàn thành,300,Sản phẩm A\n",
                encoding="utf-8",
            )
            catalog = SourceCatalog(root)
            orders = load_orders(catalog)
            lines = load_sales_lines(catalog)

        self.assertEqual(orders.get_column("order_id").to_list(), ["001"])
        self.assertEqual(lines.get_column("amount").to_list(), [300])


    def test_grouped_rows_do_not_fill_across_orders(self):
        import polars as pl
        from datamate.data.normalize import grouped_rows

        frame = pl.DataFrame({"id": ["1", None, None, "2"], "status": ["hủy", None, None, None],
                              "amount": [1, 2, 2, 2]})
        result = grouped_rows(frame, "id", ("status",))
        self.assertEqual(result.rows(), [("1", "hủy", 1), ("1", "hủy", 2), ("2", None, 2)])

    def test_grouped_rows_preserve_normalized_date_and_decimal_types(self):
        from datetime import date
        from decimal import Decimal
        import polars as pl
        from datamate.data.normalize import grouped_rows

        frame = pl.DataFrame({"id": ["a", None], "day": [date(2026, 9, 1), None],
                              "amount": [Decimal("10.00"), None]})
        result = grouped_rows(frame, "id", ("day", "amount"))
        self.assertEqual(result.schema["day"], pl.Date)
        self.assertEqual(result.schema["amount"], frame.schema["amount"])
        self.assertEqual(result["amount"].to_list(), [Decimal("10.00")])
