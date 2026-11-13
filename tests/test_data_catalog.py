"""Synthetic checks for the standalone read-only catalog scanner."""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location("catalog_scan", Path(__file__).resolve().parents[1] / "scripts/build_data_catalog.py")
scan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scan)


class CatalogTests(unittest.TestCase):
    def test_title_repeated_header_blank_and_bad_date(self):
        rows = enumerate([["Report"], ["ID", "Ngày"], ["001", "31/01/2026"],
                          ["ID", "Ngày"], [], ["001", "bad"], ["001", "bad"]], 1)
        table, keys = scan.profile(Path("biz_demo/sales.csv"), None, rows, None,
                                   {"ID": "mã đơn", "Ngày": "ngày bán"})
        self.assertEqual(table["header_row_1based"], 2)
        self.assertEqual(table["data_rows"], 3)
        self.assertEqual(table["repeated_header_rows"], 1)
        self.assertEqual(table["blank_rows_after_header"], 1)
        self.assertEqual(table["exact_duplicate_excess_rows"], 1)
        self.assertEqual(table["columns"][1]["date_profile"]["invalid"], 2)
        self.assertEqual(keys["order"][("001",)], 3)

    def test_missing_year_requires_sheet_year(self):
        self.assertEqual(scan.parse_day("1 thg 6 2025"), "2025-06-01")
        self.assertIsNone(scan.parse_day("45658"))  # no unverified serial epoch assumption
        self.assertIsNone(scan.parse_day("29/02"))
        self.assertIsNone(scan.parse_day("29/02", 2025))
        self.assertEqual(scan.parse_day("29/02", 2024), "2024-02-29")

    def test_generated_catalog_retains_header_hints(self):
        document = "### biz_999\n- **sales.xlsx** / `Sheet1` — measured\n  - Columns: `ID` · `Date`\n"
        self.assertEqual(scan.prior_headers(document)[("biz_999", "sales.xlsx", "Sheet1")], ["ID", "Date"])

    def test_serial_requires_independent_same_row_date(self):
        columns = ["NgayLap", "ThoiGianLap"]
        table, _ = scan.profile(Path("biz_demo/pos.sqlite"), "don_hang",
                                enumerate([("45658", "2025-01-01 12:00:00"),
                                           ("45659", "2025-01-01 12:00:00")], 1), columns, {})
        dp = table["columns"][0]["date_profile"]
        self.assertEqual(dp["serial_corroborated"], 1)
        self.assertEqual(dp["invalid"], 1)

    def test_conversion_uses_product_and_unit(self):
        columns = ["Tên sản phẩm", "Đơn vị quy đổi"]
        rows = enumerate([columns, ["A", "box"], ["A", "case"]], 1)
        table, keys = scan.profile(Path("biz_demo/DanhSachQuyDoi.xlsx"), "Sheet1", rows, None,
                                   {columns[0]: "tên hàng", columns[1]: "đơn vị lớn"})
        self.assertEqual(table["keys"]["product_unit"]["distinct"], 2)
        self.assertEqual(keys["product_unit"][("A", "box")], 1)

    def test_debt_duration_is_not_calendar_date(self):
        table, _ = scan.profile(Path("biz_demo/debt.csv"), None,
                                enumerate([["Hạn nợ (ngày)"], [30]], 1), None,
                                {"Hạn nợ (ngày)": "số ngày được nợ"})
        self.assertNotIn("date_profile", table["columns"][0])

    def test_join_counts_nulls_and_fanout(self):
        desc = {"ID": "mã đơn"}
        a, ak = scan.profile(Path("biz_demo/a.csv"), None, enumerate([["ID"], ["a"], ["b"]], 1), None, desc)
        b, bk = scan.profile(Path("biz_demo/b.csv"), None, enumerate([["ID"], ["a"], ["a"], ["c"]], 1), None, desc)
        edge = scan.join_profile(a, b, "order", ak, bk)
        self.assertEqual(edge["inner_join_rows"], 2)
        self.assertEqual(edge["left_join_rows"], 3)
        self.assertEqual(edge["fanout_on_matched_left"], 2)
        self.assertEqual(edge["right_unmatched_non_null_rows"], 1)

    def test_sqlite_read_does_not_change_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE t (id TEXT)")
                connection.execute("INSERT INTO t VALUES ('001')")
            connection.close()
            before = scan.digest(path)
            for name, rows, columns in scan.source_tables(path):
                self.assertEqual(name, "t")
                self.assertEqual(columns, ["id"])
                self.assertEqual(list(rows), [(1, ("001",))])
            self.assertEqual(before, scan.digest(path))

    def test_xlsx_sparse_inline_and_date_style(self):
        ns = scan.NS["s"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.xlsx"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("xl/workbook.xml", f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="T01_2026" sheetId="1" r:id="rId1"/></sheets></workbook>')
                z.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
                z.writestr("xl/styles.xml", f'<styleSheet xmlns="{ns}"><cellXfs><xf numFmtId="0"/><xf numFmtId="14"/></cellXfs></styleSheet>')
                z.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{ns}"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>ID</t></is></c><c r="C1" t="inlineStr"><is><t>Ngày</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>001</t></is></c><c r="C2" s="1"><v>46023</v></c></row></sheetData></worksheet>')
            for sheet, rows in scan.xlsx_tables(path):
                records = list(rows)
                self.assertEqual(sheet, "T01_2026")
                self.assertEqual(records[0][1], ["ID", "", "Ngày"])
                self.assertEqual(records[1][1], ["001", "", "2026-01-01 00:00:00"])
                table, _ = scan.profile(path, sheet,
                                        iter(records + [(3, ["002", "", 46024])]), None,
                                        {"Ngày": "ngày bán"})
                dp = table["columns"][2]["date_profile"]
                self.assertEqual(dp["max"], "2026-01-02")
                self.assertEqual(dp["serial_workbook_epoch"], 1)


if __name__ == "__main__":
    unittest.main()
