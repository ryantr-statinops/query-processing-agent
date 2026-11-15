"""Grouped source-analysis commands are import-safe and retain key heuristics."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from analysis.sources import (
    best_header,
    classify_cell,
    header_rows,
    headers,
    inventory,
    product_names,
    statuses,
)
from tests.support import REPO_ROOT


class SourceAnalysisTests(unittest.TestCase):
    def test_import_does_not_scan_sources_or_print(self):
        result = subprocess.run(
            [sys.executable, "-c", "import analysis.sources"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_best_header_uses_first_row_with_maximum_nonempty_cells(self):
        rows = [["title", None, None], ["a", "b", "c"], ["d", "e", "f"]]
        self.assertEqual(best_header(rows), 1)
        self.assertEqual(best_header([["a", "b"], [None, None, None]]), 0)

    def test_cell_classifier_preserves_legacy_categories(self):
        self.assertEqual(classify_cell(None), "empty")
        self.assertEqual(classify_cell(12), "int")
        self.assertEqual(classify_cell(1.5), "float")
        self.assertEqual(classify_cell("1.250đ"), "num_text")
        self.assertEqual(classify_cell("15/02/2026"), "date_text")

    def test_product_scan_uses_detected_header_and_first_product_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "products.csv"
            path.write_text(
                "Báo cáo,,,\nTên sản phẩm,Mã hàng,Giá\nCà phê,A1,20\nTrà,B2,15\n",
                encoding="utf-8",
            )
            self.assertEqual(product_names(path), ["Cà phê", "Trà"])

    def test_inventory_command_writes_artifact_without_mutating_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            business_dir = root / "train/data/biz_101"
            business_dir.mkdir(parents=True)
            (business_dir / "README.md").write_text(
                "Dữ liệu có đến hết 31/01/2026", encoding="utf-8"
            )
            (business_dir / "sales.csv").write_text("date,total\n", encoding="utf-8")
            (root / "train/questions.jsonl").write_text(
                '{"business_id":"biz_101","as_of_date":"2026-01-15"}\n',
                encoding="utf-8",
            )
            (root / "public_test").mkdir()
            (root / "public_test/questions.jsonl").write_text("", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(inventory(root), 0)
            artifact = json.loads(
                (root / "artifacts/analysis/inventory.json").read_text(encoding="utf-8")
            )
        self.assertEqual(artifact[0]["biz"], "biz_101")
        self.assertEqual(artifact[0]["nq"], 1)
        self.assertIn("2026-01-15..2026-01-15", output.getvalue())

    def test_header_commands_process_csv_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            business_dir = root / "train/data/biz_101"
            business_dir.mkdir(parents=True)
            path = business_dir / "sales.csv"
            path.write_text(
                "Report,,,\nDate,Product,Status\n2026-01-01,Tea,Done\n",
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(headers(root), 0)
                self.assertEqual(header_rows(root), 0)
            header_artifact = json.loads(
                (root / "artifacts/analysis/headers_detected.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual(header_artifact["biz_101"]["sales.csv"]["header_row"], 1)
        self.assertEqual(header_artifact["biz_101"]["sales.csv"]["header"], ["Date", "Product", "Status"])

    def test_statuses_extract_values_from_status_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            business_dir = root / "train/data/biz_101"
            business_dir.mkdir(parents=True)
            (business_dir / "sales.csv").write_text(
                "Date,Product,Trạng thái\n2026-01-01,Tea,Hoàn thành\n",
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(statuses(root), 0)
        self.assertIn("Hoàn thành", output.getvalue())


if __name__ == "__main__":
    unittest.main()
