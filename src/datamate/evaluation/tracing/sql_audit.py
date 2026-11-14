"""Read-only SQL used by the inventory and receivable audit samples."""

def dedupe_exact_order_lines(rows):
    """Remove exact duplicate line rows within one order, preserving row order."""
    seen = set()
    unique = []
    for row in rows:
        row = tuple(row)
        key = (row[0], row)
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique

INVENTORY_LOT_BALANCE_SQL = """
WITH valid_receipts AS (
    SELECT pn.IDCuaHang, pn.MaPhieuNhap
    FROM phieu_nhap pn
    WHERE pn.NgayNhapKho <= :cutoff
      AND lower(coalesce(pn.TinhTrang, '')) NOT LIKE '%hủy%'
      AND lower(coalesce(pn.TinhTrang, '')) NOT LIKE '%cancel%'
), valid_orders AS (
    SELECT dh.IDCuaHang, dh.MaHoaDon
    FROM don_hang dh
    WHERE dh.ThoiGianLap <= :cutoff
      AND lower(coalesce(dh.TinhTrang, '')) NOT LIKE '%hủy%'
      AND lower(coalesce(dh.TinhTrang, '')) NOT LIKE '%cancel%'
), lot_sales AS (
    SELECT cld.IDCuaHang, cld.MaLo,
           SUM(cld.SLQuyDoi) AS sold,
           SUM(cld.SLTraQuyDoi) AS returned
    FROM chi_tiet_don_lo cld
    JOIN valid_orders vo
      ON vo.IDCuaHang = cld.IDCuaHang AND vo.MaHoaDon = cld.MaHoaDon
    GROUP BY cld.IDCuaHang, cld.MaLo
)
SELECT l.IDCuaHang, l.MaLo, l.HanSuDung,
       l.SLNhapQuyDoi - coalesce(ls.sold, 0) + coalesce(ls.returned, 0) AS ton_kho
FROM lo_hang l
JOIN valid_receipts vr
  ON vr.IDCuaHang = l.IDCuaHang AND vr.MaPhieuNhap = l.MaPhieuNhap
LEFT JOIN lot_sales ls
  ON ls.IDCuaHang = l.IDCuaHang AND ls.MaLo = l.MaLo
"""

OUTSTANDING_DEBT_SQL = """
WITH payment_totals AS (
    SELECT IDCuaHang, MaHoaDon, SUM(SoTienThu) AS paid
    FROM thanh_toan
    WHERE NgayGioThu <= :cutoff
    GROUP BY IDCuaHang, MaHoaDon
), customer_debt AS (
    SELECT dh.IDCuaHang, dh.MaKhachHang,
           SUM(dh.TongThanhToan - coalesce(pt.paid, 0)) AS balance
    FROM don_hang dh
    LEFT JOIN payment_totals pt
      ON pt.IDCuaHang = dh.IDCuaHang AND pt.MaHoaDon = dh.MaHoaDon
    WHERE dh.ThoiGianLap <= :cutoff
      AND lower(coalesce(dh.TinhTrang, '')) NOT LIKE '%hủy%'
      AND lower(coalesce(dh.TinhTrang, '')) NOT LIKE '%cancel%'
      AND dh.MaKhachHang IS NOT NULL AND trim(dh.MaKhachHang) <> ''
      AND lower(trim(coalesce(dh.PhuongThucTT, ''))) NOT LIKE '%cod%'
      AND lower(trim(coalesce(dh.PhuongThucTT, ''))) NOT LIKE '%tmdt%'
      AND lower(trim(coalesce(dh.PhuongThucTT, ''))) NOT LIKE '%sàn%'
      AND lower(trim(coalesce(dh.KenhBanHang, ''))) NOT LIKE '%tmdt%'
      AND lower(trim(coalesce(dh.KenhBanHang, ''))) NOT LIKE '%sàn%'
      AND lower(trim(coalesce(dh.KenhBanHang, ''))) NOT LIKE '%marketplace%'
    GROUP BY dh.IDCuaHang, dh.MaKhachHang
)
SELECT cd.IDCuaHang, cd.MaKhachHang, kh.TenGoi,
       CAST(cd.balance AS INTEGER) AS so_tien_no
FROM customer_debt cd
JOIN khach_hang kh
  ON kh.IDCuaHang = cd.IDCuaHang AND kh.MaKhachHang = cd.MaKhachHang
WHERE cd.balance > 0
ORDER BY cd.balance DESC
"""
