"""Evidence gates: serial dates, grain, and semantic join validation."""
import importlib.util
from collections import Counter
from pathlib import Path
import tempfile
import subprocess
import sys
import os
import json
import unittest

SPEC = importlib.util.spec_from_file_location("catalog_review", Path(__file__).resolve().parents[1] / "scripts/review_data_catalog.py")
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class CatalogReviewTests(unittest.TestCase):
    def test_serial_requires_brackets_and_independent_date(self):
        values = ["01/01/2025", "45658", "1 thg 1 2025"]
        report, resolved = review.csv_serial_evidence(values, ["a", "b", "c"], {"b": {"2025-01-01"}}, "2025-12-31")
        self.assertEqual(report["confirmed_epoch"], "excel_1900")
        self.assertEqual(resolved, {1: "2025-01-01"})
        self.assertEqual(report["epoch_comparison"]["excel_1904"]["bracket_or_coverage_conflicts"], 1)

    def test_serial_without_independent_source_stays_unresolved(self):
        report, resolved = review.csv_serial_evidence(["01/01/2025", "45658", "01/01/2025"], ["a", "b", "c"], {}, "2025-12-31")
        self.assertIsNone(report["confirmed_epoch"])
        self.assertEqual(resolved, {})
        self.assertEqual(report["unresolved"], 1)

    def test_serial_conflicting_chronology_is_rejected(self):
        report, _ = review.csv_serial_evidence(["01/01/2025", "45660", "01/01/2025"], ["a", "b", "c"], {"b": {"2025-01-03"}}, "2025-12-31")
        self.assertIsNone(report["confirmed_epoch"])

    def test_duplicate_keys_rejected_but_case_sensitive_keys_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "test.json"
            p.write_text('{"outer":{"x":1,"x":2}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                review.load_json(p)
            p.write_text('{"Hủy":1,"hủy":2}', encoding="utf-8")
            self.assertEqual(len(review.load_json(p)), 2)

    def test_shared_key_does_not_approve_unrelated_sources(self):
        self.assertNotIn(("customers", "products"), review.RELATIONS)
        self.assertNotIn(("sales_lines", "price_history"), review.RELATIONS)
        self.assertEqual(review.RELATIONS[("lot_allocations", "sales_lines")], ("order_line",))

    def test_role_classification_keeps_lot_allocation_separate(self):
        def table(file, sheet=None):
            return {"file": file, "sheet_or_table": sheet}
        self.assertEqual(review.kind_for(table("pos.sqlite", "chi_tiet_don_lo")), "lot_allocations")
        self.assertEqual(review.kind_for(table("DuLieuXuat.xlsx", "DonNhapHang_ChiTiet")), "purchase_lines")
        self.assertEqual(review.kind_for(table("DanhSachHoaDonChiTiet_2.xlsx", "Sheet1")), "sales_lines")

    def test_payment_id_is_not_order_id(self):
        t = {"file": "SoQuy.xlsx", "sheet_or_table": "Sheet1",
             "columns": [{"name": "Mã phiếu"}, {"name": "Mã hóa đơn"}]}
        _, keys = review.review_keys(t)
        self.assertEqual(keys["order"], [1])
        self.assertEqual(keys["payment"], [0])

    def test_union_months_before_measuring_unmatched_rows(self):
        tables = [{"source_ref": "lines", "logical_role": "sales_lines", "data_rows": 2, "reviewed_keys": {"order": {"columns": ["ID"]}}},
                  {"source_ref": "jan", "logical_role": "orders", "data_rows": 1, "reviewed_keys": {"order": {"columns": ["ID"]}}},
                  {"source_ref": "feb", "logical_role": "orders", "data_rows": 1, "reviewed_keys": {"order": {"columns": ["ID"]}}}]
        records = {}
        for ref, values in (("lines", [("a",), ("b",)]), ("jan", [("a",)]), ("feb", [("b",)])):
            records[ref] = {"raw": {"order": Counter(values)}, "dedup": {"order": Counter(values)}, "nulls": Counter()}
        edges = [{"left": "lines", "right": r, "key_role": "order", "readme_ref": "README", "double_counting_policy": "aggregate first", "unmatched_interpretation": "check missing"} for r in ("jan", "feb")]
        result = review.union_edges(edges, tables, records, "biz_demo")[0]
        self.assertEqual(result["left_unmatched_non_null_rows"], 0)
        self.assertEqual(result["inner_join_rows"], 2)
        self.assertEqual(result["status"], "verified")

    def test_order_lot_grain_does_not_invent_a_line_key(self):
        table = {"logical_role": "lot_allocations", "reviewed_keys": {"order_lot": {"columns": ["Order", "Lot"], "null_rows": 0, "raw_duplicate_excess": 0}},
                 "columns": [{"name": "Qty", "readme_description": "số lượng bán lấy từ lô"}], "grain": "unknown", "grain_status": "needs_review", "header_status": "verified", "overflow_rows": 0}
        review.review_grain(table, "README", "Một dòng bán có thể lấy từ nhiều lô")
        self.assertEqual(table["grain_status"], "verified")
        self.assertIn("không có khóa dòng hàng", table["grain"])
        self.assertNotIn("order_line", table["reviewed_keys"])

    def test_summary_labels_are_not_item_names(self):
        self.assertTrue(review.summary_label("TỔNG NGÀY 01/02"))
        self.assertTrue(review.summary_label("Tổng tháng 9/2025"))
        self.assertFalse(review.summary_label("Cà phê sữa (M)"))
        self.assertNotEqual(review.name_key("Thuốc 10mg"), review.name_key("Thuốc 100mg"))

    def test_normalized_lookup_rejects_colliding_catalog_names(self):
        tables = [{"source_ref": "lines", "logical_role": "sales_lines", "data_rows": 1, "reviewed_keys": {"product_name": {"columns": ["Name"]}}},
                  {"source_ref": "products", "logical_role": "products", "data_rows": 2, "reviewed_keys": {"product_name": {"columns": ["Name"]}}}]
        records = {"lines": {"raw": {"product_name": Counter({("á",): 1})}, "dedup": {"product_name": Counter({("á",): 1})}, "nulls": Counter()},
                   "products": {"raw": {"product_name": Counter({("Á",): 1, ("A",): 1})}, "dedup": {"product_name": Counter({("Á",): 1, ("A",): 1})}, "nulls": Counter()}}
        edge = {"left": "lines", "right": "products", "key_role": "product_name", "readme_ref": "README", "double_counting_policy": "lookup", "unmatched_interpretation": "review aliases"}
        audit = review.union_edges([edge], tables, records, "biz_demo")[0]["name_normalization_review"]
        self.assertEqual(audit["status"], "needs_review")
        self.assertEqual(audit["additional_matches"], 0)

    def test_scanner_cli_handles_unicode_sources_on_cp1252_console(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            train, output = root / "train", root / "artifacts"
            train.mkdir()
            (train / "calendar.csv").write_text("date,weekday\n2025-01-01,3\n", encoding="utf-8")
            for name in ("questions.jsonl", "answers.jsonl", "rulebook.md"):
                (train / name).write_text("", encoding="utf-8")
            for i in range(101, 131):
                business = train / "data" / f"biz_{i}"
                business.mkdir(parents=True)
                (business / "README.md").write_text("## File\n- `Danh sách.csv` (csv)\n## Cột trong `Danh sách.csv`\n- **Mã đơn**: mã đơn\n- **Tên hàng**: tên hàng\n", encoding="utf-8")
                (business / "Danh sách.csv").write_text("Mã đơn,Tên hàng\n001,Hàng A\n", encoding="utf-8")
            env = dict(os.environ, PYTHONIOENCODING="cp1252")
            run = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/build_data_catalog.py"),
                                  "--train-root", str(train), "--output", str(output)], capture_output=True, env=env)
            self.assertEqual(run.returncode, 0, run.stderr.decode("cp1252", errors="replace"))
            self.assertIn("\\u00e1", run.stdout.decode("ascii"))
            catalog = json.loads((output / "data_catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["errors"], [])
            self.assertEqual(catalog["source_fingerprints"], review.base.snapshot(train))


if __name__ == "__main__":
    unittest.main()
