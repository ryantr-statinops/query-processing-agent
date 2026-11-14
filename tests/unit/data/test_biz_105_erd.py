import re
import unittest
from pathlib import Path

from tests.support import REPO_ROOT

ERD_PATH = REPO_ROOT / "docs" / "architecture" / "biz_105-erd.md"


class Biz105ErdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = ERD_PATH.read_text(encoding="utf-8")

    def test_document_exists_and_declares_evidence_status(self):
        self.assertIn("Evidence status", self.text)
        self.assertIn("artifacts/data_prep/data_catalog.json", self.text)
        self.assertIn("absent", self.text)
        self.assertIn("not run here", self.text)

    def test_physical_inventory_totals(self):
        self.assertIn("6 physical files", self.text)
        self.assertIn("21 tables", self.text)
        self.assertIn("140,245", self.text)
        self.assertIn("2,222", self.text)
        self.assertIn("2026-06-24", self.text)

    def test_all_seventeen_sales_sheets_are_listed(self):
        matches = re.findall(r"\| `SoBanHang_(?:1|2026)\.xlsx` \| `Thang [0-9]{2} 20[0-9]{2}` \|", self.text)
        self.assertEqual(len(matches), 17)

    def test_all_physical_columns_are_present(self):
        columns = [
            "Hàng",
            "so_luong",
            "Unit",
            "Trị giá",
            "Status",
            "Giá lẻ",
            "Giờ",
            "Mã hóa đơn",
            "Ngày giao dịch",
            "Khách",
            "Ngày áp dụng",
            "ten_hang",
            "Giá mới",
            "Giá cũ",
            "Tên món",
            "Đơn vị gốc",
            "ĐV nhập",
            "Hệ số",
            "Số phiếu",
            "Ngày nhập",
            "Ghi chu",
            "Thành tiền",
            "Nhà cung cấp",
            "Tên mặt hàng",
            "Giá nhập",
            "ĐVT",
            "SL nhập",
            "Hàng hóa",
            "Đơn vị tính",
            "Tồn cuối",
        ]
        for column in columns:
            with self.subTest(column=column):
                self.assertIn(f"`{column}`", self.text)

    def test_verified_and_candidate_are_separated(self):
        self.assertIn("**Verified**", self.text)
        self.assertIn("**Candidate**", self.text)
        self.assertIn("candidate key", self.text.lower())

    def test_relationship_register_is_complete(self):
        for index in range(1, 13):
            with self.subTest(relationship=index):
                self.assertRegex(self.text, rf"\| R{index} \|")

    def test_unmeasured_or_sparse_joins_allow_missing_matches(self):
        for relationship in (
            'SALES_LINE }o--o| UNIT_CONVERSION : "R2',
            'SALES_LINE }o--o| STOCK_SNAPSHOT : "R3',
            'PURCHASE_LINE }o--o| UNIT_CONVERSION : "R5',
            'PURCHASE_LINE }o--o| STOCK_SNAPSHOT : "R6',
            'SALES_LINE }o--o| SALES_ORDER : "R7',
            'PURCHASE_LINE }o--o| SUPPLIER : "R12',
        ):
            with self.subTest(relationship=relationship):
                self.assertIn(relationship, self.text)

    def test_join_contract_includes_name_and_temporal_columns(self):
        self.assertIn("normalised `Hàng` = normalised `ten_hang`", self.text)
        self.assertIn("`Ngày áp dụng <= Ngày giao dịch`", self.text)
        self.assertIn("`Mã hóa đơn`", self.text)
        self.assertIn("`Tồn cuối`", self.text)
        self.assertIn("as-of join", self.text)

    def test_cardinality_nullability_and_coverage_are_addressed(self):
        for phrase in (
            "Key uniqueness and null status",
            "Referential coverage and many-to-many risks",
            "Expected cardinality",
            "Coverage",
            "Fan-out",
            "unmeasured",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_temporal_and_fanout_warnings_are_explicit(self):
        self.assertIn("Price fan-out", self.text)
        self.assertIn("Stock is a snapshot", self.text)
        self.assertIn("cross-sheet id collisions", self.text)
        self.assertIn("rulebook §8", self.text)

    def test_missing_sources_are_not_claimed_as_verified(self):
        for source in ("SoGiaoHang", "SoHanNo", "feedback/survey"):
            with self.subTest(source=source):
                self.assertIn(source, self.text)
        self.assertIn("Not present", self.text)

    def test_unresolved_questions_are_listed(self):
        section = self.text.split("## 8. Unresolved questions", 1)
        self.assertEqual(len(section), 2)
        questions = [line for line in section[1].splitlines() if line.strip().startswith("- ")]
        self.assertGreaterEqual(len(questions), 10)

    def test_document_does_not_publish_answers(self):
        lowered = self.text.casefold()
        self.assertNotIn("gold answer is", lowered)
        self.assertNotIn("reference answer:", lowered)
        self.assertIn("no value in this document is a gold answer", lowered)

    def test_mermaid_erd_present(self):
        self.assertIn("```mermaid", self.text)
        self.assertIn("erDiagram", self.text)
        for entity in (
            "SALES_LINE",
            "PRICE_HISTORY",
            "UNIT_CONVERSION",
            "PURCHASE_LINE",
            "STOCK_SNAPSHOT",
            "SALES_ORDER",
            "CALENDAR",
        ):
            with self.subTest(entity=entity):
                self.assertIn(entity, self.text)


if __name__ == "__main__":
    unittest.main()
