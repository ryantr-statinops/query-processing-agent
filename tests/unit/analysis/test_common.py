"""Regression tests for the shared analysis I/O helpers."""

import json
from pathlib import Path
import tempfile
import unittest

from openpyxl import Workbook

from analysis.common import (
    fold_vietnamese,
    iter_business_dirs,
    iter_source_rows,
    load_jsonl,
    write_json_artifact,
)


class AnalysisCommonTests(unittest.TestCase):
    def test_jsonl_reads_utf8_bom_and_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "questions.jsonl"
            path.write_text('\ufeff{"id":"q1"}\n\n{"id":"q2"}\n', encoding="utf-8")
            self.assertEqual(load_jsonl(path), [{"id": "q1"}, {"id": "q2"}])

    def test_vietnamese_folding_preserves_punctuation(self):
        self.assertEqual(fold_vietnamese("Hôm nay, ĐẸP!"), "hom nay, dep!")

    def test_business_directories_are_ordered_by_split_and_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("train/data/biz_102", "train/data/biz_101", "public_test/data/dev_001"):
                (root / relative).mkdir(parents=True)
            found = [(split, path.name) for split, path in iter_business_dirs(root)]
        self.assertEqual(
            found,
            [("train", "biz_101"), ("train", "biz_102"), ("public_test", "dev_001")],
        )

    def test_csv_reader_handles_bom_and_row_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_text('\ufeffname,value\nA,1\nB,2\n', encoding="utf-8")
            rows = list(iter_source_rows(path, rows_per_sheet=2))
        self.assertEqual(rows, [(None, 1, ["name", "value"]), (None, 2, ["A", "1"])])

    def test_xlsx_reader_limits_sheets_and_closes_workbook(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.xlsx"
            workbook = Workbook()
            workbook.active.title = "first"
            workbook.active.append(["name", "value"])
            workbook.active.append(["A", 1])
            second = workbook.create_sheet("second")
            second.append(["ignored", 2])
            workbook.save(path)
            rows = list(iter_source_rows(path, sheet_limit=1, rows_per_sheet=1))
            path.rename(Path(directory) / "renamed.xlsx")
        self.assertEqual(rows, [("first", 1, ("name", "value"))])

    def test_json_artifacts_go_under_artifacts_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = write_json_artifact("sample.json", {"ok": True}, root=root)
            self.assertEqual(output.relative_to(root).as_posix(), "artifacts/analysis/sample.json")
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"ok": True})


if __name__ == "__main__":
    unittest.main()
