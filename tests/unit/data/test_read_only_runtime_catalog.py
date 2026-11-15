"""Read-only source loading and SQL execution smoke tests."""

from __future__ import annotations

import pathlib
import sqlite3
import tempfile
import unittest

from openpyxl import Workbook

from datamate.data.catalog import BusinessCatalog
from datamate.execution.sql import execute_select


class RuntimeCatalogTests(unittest.TestCase):
    def test_csv_query_preserves_original_column_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            business_dir = pathlib.Path(folder) / "biz_001"
            business_dir.mkdir()
            (business_dir / "sales.csv").write_text(
                "Mã hàng,Trị giá\n001,4\n002,7\n", encoding="utf-8"
            )
            catalog = BusinessCatalog(business_dir)
            try:
                table = catalog.tables[0]
                self.assertEqual(table.source_ref, "catalog:biz_001:sales.csv")
                self.assertEqual(table.original_columns, {"ma_hang": "Mã hàng", "tri_gia": "Trị giá"})
                result = execute_select(catalog, "SELECT SUM(tri_gia) AS revenue FROM sales")
                self.assertTrue(result.ok, result.error)
                self.assertEqual(result.columns, ["revenue"])
                self.assertEqual(result.rows, [[11]])
                self.assertEqual(result.source_refs, ["catalog:biz_001:sales.csv"])
                self.assertTrue(result.sql_validation["plan_checked"])
            finally:
                catalog.close()

    def test_sql_guardrails_reject_writes_external_sources_and_unknown_tables(self):
        with tempfile.TemporaryDirectory() as folder:
            business_dir = pathlib.Path(folder) / "biz_001"
            business_dir.mkdir()
            (business_dir / "sales.csv").write_text("amount\n4\n", encoding="utf-8")
            catalog = BusinessCatalog(business_dir)
            try:
                for sql in (
                    "UPDATE sales SET amount = 0",
                    "SELECT * FROM read_csv('external.csv')",
                    "SELECT * FROM unknown_table",
                ):
                    with self.subTest(sql=sql):
                        result = execute_select(catalog, sql)
                        self.assertFalse(result.ok)
                        self.assertIsNotNone(result.error_code)
            finally:
                catalog.close()

    def test_row_limit_is_an_explicit_execution_error(self):
        with tempfile.TemporaryDirectory() as folder:
            business_dir = pathlib.Path(folder) / "biz_001"
            business_dir.mkdir()
            (business_dir / "sales.csv").write_text("amount\n1\n2\n3\n", encoding="utf-8")
            catalog = BusinessCatalog(business_dir)
            try:
                result = execute_select(catalog, "SELECT amount FROM sales", max_rows=2)
                self.assertFalse(result.ok)
                self.assertEqual(result.error_code, "row_limit_exceeded")
                self.assertEqual(result.rows, [[1], [2]])
            finally:
                catalog.close()

    def test_deadline_terminates_the_query_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            business_dir = pathlib.Path(folder) / "biz_001"
            business_dir.mkdir()
            (business_dir / "sales.csv").write_text("amount\n1\n", encoding="utf-8")
            catalog = BusinessCatalog(business_dir)
            try:
                result = execute_select(
                    catalog,
                    "SELECT SUM(s.amount) FROM sales AS s CROSS JOIN sales AS other",
                    timeout_seconds=0.001,
                )
                self.assertFalse(result.ok)
                self.assertEqual(result.error_code, "timeout")
                self.assertFalse(result.sql_validation["plan_checked"])
            finally:
                catalog.close()

    def test_sqlite_sources_are_loaded_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            business_dir = pathlib.Path(folder) / "biz_001"
            business_dir.mkdir()
            path = business_dir / "inventory.sqlite"
            connection = sqlite3.connect(path)
            try:
                connection.execute('CREATE TABLE "stock item" ("item code" TEXT, quantity INTEGER)')
                connection.execute('INSERT INTO "stock item" VALUES (?, ?)', ("001", 3))
                connection.commit()
            finally:
                connection.close()
            before = path.read_bytes()
            catalog = BusinessCatalog(business_dir)
            try:
                result = execute_select(catalog, "SELECT quantity FROM inventory_stock_item")
                self.assertTrue(result.ok, result.error)
                self.assertEqual(result.rows, [[3]], result)
                self.assertEqual(path.read_bytes(), before)
            finally:
                catalog.close()

    def test_excel_sheet_is_registered_with_source_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            business_dir = pathlib.Path(folder) / "biz_001"
            business_dir.mkdir()
            path = business_dir / "sales.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "April"
            sheet.append(["Item name", "Net amount"])
            sheet.append(["apples", 6])
            workbook.save(path)
            catalog = BusinessCatalog(business_dir)
            try:
                self.assertEqual(catalog.tables[0].source_ref, "catalog:biz_001:sales.xlsx:April")
                result = execute_select(catalog, "SELECT SUM(net_amount) AS total FROM sales_april")
                self.assertTrue(result.ok, result.error)
                self.assertEqual(result.rows, [[6]])
                self.assertEqual(result.source_refs, ["catalog:biz_001:sales.xlsx:April"])
            finally:
                catalog.close()


if __name__ == "__main__":
    unittest.main()
