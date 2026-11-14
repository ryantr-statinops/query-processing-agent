import sqlite3
import unittest

from scripts.tracing_sql import INVENTORY_LOT_BALANCE_SQL, OUTSTANDING_DEBT_SQL, dedupe_exact_order_lines


class AuditSqlTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def test_lot_balance_filters_cancelled_future_sales_and_future_receipts(self):
        self.db.executescript("""
            CREATE TABLE phieu_nhap (IDCuaHang TEXT, MaPhieuNhap TEXT, NgayNhapKho TEXT, TinhTrang TEXT);
            CREATE TABLE lo_hang (IDCuaHang TEXT, MaLo TEXT, MaPhieuNhap TEXT, HanSuDung TEXT, SLNhapQuyDoi INTEGER);
            CREATE TABLE don_hang (IDCuaHang TEXT, MaHoaDon TEXT, ThoiGianLap TEXT, TinhTrang TEXT);
            CREATE TABLE chi_tiet_don_lo (IDCuaHang TEXT, MaHoaDon TEXT, MaLo TEXT, SLQuyDoi INTEGER, SLTraQuyDoi INTEGER);
            INSERT INTO phieu_nhap VALUES ('s1','p1','2025-01-01','Hoàn thành'), ('s1','p2','2026-02-01','Hoàn thành');
            INSERT INTO lo_hang VALUES ('s1','lot1','p1','2027-01-01',100), ('s1','lot2','p2','2028-01-01',500);
            INSERT INTO don_hang VALUES ('s1','valid','2025-01-02','Hoàn thành'), ('s1','cancel','2025-01-03','Đã hủy'), ('s1','future','2026-01-02','Hoàn thành');
            INSERT INTO chi_tiet_don_lo VALUES ('s1','valid','lot1',60,5), ('s1','cancel','lot1',20,0), ('s1','future','lot1',15,0);
        """)
        rows = self.db.execute(INVENTORY_LOT_BALANCE_SQL, {"cutoff": "2025-12-31 23:59:59"}).fetchall()
        self.assertEqual(rows, [("s1", "lot1", "2027-01-01", 45)])

    def test_debt_aggregates_payments_excludes_cod_marketplace_and_counts_other_unpaid_methods(self):
        self.db.executescript("""
            CREATE TABLE don_hang (IDCuaHang TEXT, MaHoaDon TEXT, ThoiGianLap TEXT, TinhTrang TEXT, MaKhachHang TEXT, TongThanhToan INTEGER, PhuongThucTT TEXT, KenhBanHang TEXT);
            CREATE TABLE thanh_toan (IDCuaHang TEXT, MaHoaDon TEXT, NgayGioThu TEXT, SoTienThu INTEGER);
            CREATE TABLE khach_hang (IDCuaHang TEXT, MaKhachHang TEXT, TenGoi TEXT);
            INSERT INTO khach_hang VALUES ('s1','c1','Debt customer'), ('s1','c2','Other customer');
            INSERT INTO don_hang VALUES
                ('s1','debt','2025-01-01','Hoàn thành','c1',1000,'debt','Cửa hàng'),
                ('s1','cash','2025-01-01','Hoàn thành','c1',9000,'cash','Cửa hàng'),
                ('s1','transfer','2025-01-01','Hoàn thành','c1',8000,'transfer','Cửa hàng'),
                ('s1','cod','2025-01-01','Hoàn thành','c1',7000,'COD','Cửa hàng'),
                ('s1','market','2025-01-01','Hoàn thành','c2',6000,'debt','Marketplace'),
                ('s1','cancel','2025-01-01','Đã hủy','c2',5000,'debt','Cửa hàng');
            INSERT INTO thanh_toan VALUES
                ('s1','debt','2025-01-02',200), ('s1','debt','2025-01-03',300), ('s1','debt','2026-01-01',400);
        """)
        rows = self.db.execute(OUTSTANDING_DEBT_SQL, {"cutoff": "2025-12-31 23:59:59"}).fetchall()
        self.assertEqual(rows, [("s1", "c1", "Debt customer", 17500)])

    def test_exact_duplicate_lines_are_removed_only_within_same_order(self):
        lines = [("order1", "Tea", 2, 100), ("order1", "Tea", 2, 100), ("order2", "Tea", 2, 100)]
        self.assertEqual(dedupe_exact_order_lines(lines), [lines[0], lines[2]])


if __name__ == "__main__":
    unittest.main()
