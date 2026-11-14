# Bàn giao Data Catalog D01–D05

Báo cáo kỹ thuật dựa trên train local; chưa thay thế xác nhận nghiệm thu của Người 2/lead.

## Kết quả và coverage

| Hạng mục | Kết quả |
|---|---|
| D01 | Đủ 30 business, 30 README, 162 file; 339 nguồn bảng, kiểm kê tái sử dụng từ lượt trước |
| D02 | Grain verified 335/339 (98.82%); needs_review 4/339 (1.18%); đã review lại 143 nguồn mở |
| D03 | Profiling raw có số đếm; date audit riêng bên dưới; alias trạng thái/đơn vị chưa phải mapping runtime được duyệt |
| D04 | 366 cặp nguồn và 109 quan hệ sau union partitions; trạng thái union: {'verified': 101, 'verified_requires_order_line_dedup': 3, 'verified_with_unmatched': 5}; không dùng mọi candidate chung khóa |
| D05 | Có 60 source contracts, {'source_contract_ready': 22, 'source_contract_ready_with_caveats': 28, 'needs_review': 10}; chưa phải 60 trace tính đáp án; chờ Người 2/lead review |

`verified` của bảng chỉ có nghĩa header + grain có bằng chứng; không có nghĩa mọi phép tính hay dữ liệu sạch. Header 339/339 được validator đọc lại từ CSV/OOXML/SQLite schema.

## Ngày biz_111

Nguồn `biz_111/don_hang.csv`, cột `NgayBan`. Phân loại: `{'d_thg_m_yyyy': 16590, 'excel_serial_candidate': 16594, 'day_first': 33285}`.
Epoch duy nhất thỏa kiểm tra: `excel_1900`. Giải quyết 16594 giá trị; unresolved 0.
```json
{
  "excel_1900": {
    "serial_rows": 16594,
    "bracket_range_matches": 16594,
    "exact_same_day_brackets": 16180,
    "independent_payment_same_day": 15456,
    "payments_other_days": 798,
    "no_parsed_payment": 340
  },
  "excel_1904": {
    "serial_rows": 16594,
    "bracket_or_coverage_conflicts": 16594,
    "payments_other_days": 16254,
    "no_parsed_payment": 340
  }
}
```
Bằng chứng: README cutoff, ngày rõ ràng hai phía của từng serial, và ngày thu tiền theo mã đơn từ nguồn độc lập. Không suy ngày đơn bằng ngày thu tiền; khoản thu khác ngày là hợp lệ với công nợ. Scalar parser vẫn từ chối numeric string khi thiếu bằng chứng.

## Việc chưa hoàn tất và quyết định cần lead

- Người 2 xác nhận source contracts đủ cho trace và sửa lựa chọn nguồn nếu cách hiểu câu hỏi khác. Không đưa gold vào catalog/retrieval.
- Lead duyệt policy serial CSV chỉ áp cho export đã audit; bằng chứng ngữ cảnh không bảo đảm file khác luôn sắp xếp theo ngày.
- Duyệt mapping trạng thái như Không giao được, Đang xử lý, Chờ giao; không âm thầm coi là hoàn thành/huỷ.
- Xác nhận xử lý grouped blanks và dedup trong cùng đơn theo rulebook §8; không dedup sổ không có đơn.
- Không suy lịch sử tồn/công nợ từ snapshot cuối kỳ. Tên không unique hoặc thiếu khóa phải giữ blocker.
- Môi trường uv sync --locked/test chung vẫn bị thiếu src/datamate/__init__.py; thuộc preflight Người 4, không sửa trong phần việc này.
- Checksum gói chính thức chưa xác minh; fingerprint chỉ chứng minh nguồn local không đổi.

## Source contracts còn cần review

| Question ID | Business | Lý do |
|---|---|---|
| `q_3a28ee2a98fd` | biz_107 | biz_107/SoBanHang.xlsx#Sheet1 |
| `q_0fb7868ac463` | biz_107 | biz_107/SoBanHang.xlsx#Sheet1 |
| `q_269c0b4a7a90` | biz_110 | biz_110/danh_sach_hoa_don.csv |
| `q_0504f61cae69` | biz_110 | biz_110/danh_sach_hoa_don.csv |
| `q_22f59bab1075` | biz_112 | Missing source role: conversions; Missing source role: stock_snapshot |
| `q_4333ad0589a1` | biz_117 | Missing source role: customers; Missing source role: orders; Missing source role: payments |
| `q_70d78d0a36ff` | biz_130 | biz_130/So_chi_tiet_ban_hang_1.xlsx#Sheet1; biz_130/So_chi_tiet_ban_hang_2.xlsx#Sheet1 |
| `q_05a8b30443a1` | biz_130 | biz_130/So_chi_tiet_ban_hang_1.xlsx#Sheet1; biz_130/So_chi_tiet_ban_hang_2.xlsx#Sheet1 |
| `q_3ad4ff264376` | biz_105 | Không có nguồn nhận xét/khen nhân viên trong catalog; cần Người 2 xác nhận evidence requirement. |
| `q_04128078842a` | biz_118 | Missing source role: customers |

Source contract ready chỉ xác nhận đường dẫn/cột/grain/quan hệ nguồn; không xác nhận đủ evidence tại ngày hỏi hoặc đúng đáp án. `with_caveats` yêu cầu xử lý quality được nêu trong từng record.

## Nguồn còn needs_review

| Source ref | Grain/Blocker |
|---|---|
| `biz_107/SoBanHang.xlsx#Sheet1` | Bảng trộn dòng giao dịch với dòng nhãn tổng; chưa duyệt filter để loại cộng đôi, raw row count chưa phải số giao dịch. |
| `biz_110/danh_sach_hoa_don.csv` | Bảng trộn dòng giao dịch với dòng nhãn tổng; chưa duyệt filter để loại cộng đôi, raw row count chưa phải số giao dịch. |
| `biz_130/So_chi_tiet_ban_hang_1.xlsx#Sheet1` | Bảng trộn dòng giao dịch với dòng nhãn tổng; chưa duyệt filter để loại cộng đôi, raw row count chưa phải số giao dịch. |
| `biz_130/So_chi_tiet_ban_hang_2.xlsx#Sheet1` | Bảng trộn dòng giao dịch với dòng nhãn tổng; chưa duyệt filter để loại cộng đôi, raw row count chưa phải số giao dịch. |

## Vấn đề chất lượng cần chú ý

Có 80 nguồn có dòng raw giống nhau; xem số đếm riêng, không gọi mọi trường hợp là lỗi.
Fan-out hợp lệ một-nhiều vẫn gây sai số nếu cộng tổng đơn. Payment phải aggregate theo đơn trước; phân bổ lô phải nối (đơn, dòng), không nối đơn đơn thuần.
Phân bổ đơn–lô không có khóa dòng (biz_121/biz_122) được mô tả riêng; không áp quy tắc join theo line ID không tồn tại.
Lookup sản phẩm–đơn vị chỉ liệt kê đơn vị lớn: unmatched cần kiểm chứng đơn vị cơ bản, không tự loại giao dịch. Khóa raw null phải được báo riêng trước mọi fill nhóm.

| Nguồn có nhãn tổng, cần duyệt filter | Số dòng | Trong đó không có mã đơn |
|---|---:|---:|
| `biz_107/SoBanHang.xlsx#Sheet1` | 526 | 526 |
| `biz_110/danh_sach_hoa_don.csv` | 429 | 429 |
| `biz_130/So_chi_tiet_ban_hang_1.xlsx#Sheet1` | 347 | 347 |
| `biz_130/So_chi_tiet_ban_hang_2.xlsx#Sheet1` | 247 | 247 |

Tổng **1,549** dòng mang nhãn tổng trong bốn nguồn trên (dấu phẩy phân tách hàng nghìn).
Các dòng này vẫn nằm trong raw row count và dữ liệu nguồn, không bị tự động xóa. Grain được giữ needs_review cho đến khi xác minh bộ lọc dòng giao dịch.

| Nguồn đơn có khóa null | Cột | Số dòng |
|---|---|---|
| `biz_110/danh_sach_hoa_don.csv` | Mã bill | 429 |

| Union relation có fan-out | Matched left | Inner join rows | Hệ số |
|---|---:|---:|---:|
| `biz_123:lot_allocations->sales_lines[order_line]` | 64422 | 65655 | 1.019139 |
| `biz_119:lot_allocations->sales_lines[order_line]` | 65483 | 67419 | 1.029565 |
| `biz_124:lot_allocations->sales_lines[order_line]` | 97880 | 99098 | 1.012444 |

| Name join | Raw unmatched | Chuẩn hóa khớp thêm | Còn unmatched | Collision ở danh mục |
|---|---:|---:|---:|---:|
| `biz_112:sales_lines->products[product_name]` | 3299 | 3299 | 0 | 0 |
| `biz_116:sales_lines->products[product_name]` | 1434 | 1434 | 0 | 0 |
| `biz_121:sales_lines->products[product_name]` | 1931 | 1931 | 0 | 0 |
| `biz_122:sales_lines->products[product_name]` | 3654 | 3654 | 0 | 0 |
| `biz_130:sales_lines->products[product_name]` | 594 | 0 | 594 | 0 |

Chuẩn hóa chỉ là lookup trong memory theo rulebook §8: chữ thường, bỏ dấu, gộp khoảng trắng; giữ chữ/số/dấu câu. Chỉ cho phép khi danh mục không collision; không fuzzy-match hoặc sửa tên nguồn.

## Source refs bàn giao Người 2

Chi tiết 60 câu và columns/edges nằm trong `artifacts/data_prep/question_source_map.json`; đây là source handoff, không viết đè question_trace của Người 2.

| Business | Các source refs quan trọng |
|---|---|
| biz_101 | `biz_101/ban_hang.csv` |
| biz_102 | `biz_102/DonHang_ChiTiet.xlsx#T01_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T01_2026`<br>`biz_102/DonHang_ChiTiet.xlsx#T02_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T02_2026`<br>`biz_102/DonHang_ChiTiet.xlsx#T03_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T03_2026`<br>`biz_102/DonHang_ChiTiet.xlsx#T04_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T04_2026`<br>`biz_102/DonHang_ChiTiet.xlsx#T05_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T05_2026`<br>`biz_102/DonHang_ChiTiet.xlsx#T06_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T06_2026`<br>`biz_102/DonHang_ChiTiet.xlsx#T07_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T08_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T09_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T10_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T11_2025`<br>`biz_102/DonHang_ChiTiet.xlsx#T12_2025` |
| biz_111 | `biz_111/don_hang.csv`<br>`biz_111/khach_hang.csv`<br>`biz_111/thanh_toan.csv` |
| biz_123 | `biz_123/pos.sqlite#chi_tiet_don`<br>`biz_123/pos.sqlite#chi_tiet_don_lo`<br>`biz_123/pos.sqlite#don_hang`<br>`biz_123/pos.sqlite#khach_hang`<br>`biz_123/pos.sqlite#lo_hang`<br>`biz_123/pos.sqlite#san_pham`<br>`biz_123/pos.sqlite#thanh_toan` |
| biz_124 | `biz_124/BanHang_ChiTietHoaDon.xlsx#Sheet1`<br>`biz_124/BanHang_HangHoa.xlsx#Sheet1`<br>`biz_124/BanHang_HoaDon.xlsx#Sheet1`<br>`biz_124/BanHang_Thuoc.xlsx#Sheet1` |
| biz_128 | `biz_128/DanhSachHoaDon.xlsx#01.2026`<br>`biz_128/DanhSachHoaDon.xlsx#02.2026`<br>`biz_128/DanhSachHoaDon.xlsx#03.2026`<br>`biz_128/DanhSachHoaDon.xlsx#04.2025`<br>`biz_128/DanhSachHoaDon.xlsx#04.2026`<br>`biz_128/DanhSachHoaDon.xlsx#05.2025`<br>`biz_128/DanhSachHoaDon.xlsx#05.2026`<br>`biz_128/DanhSachHoaDon.xlsx#06.2025`<br>`biz_128/DanhSachHoaDon.xlsx#06.2026`<br>`biz_128/DanhSachHoaDon.xlsx#07.2025`<br>`biz_128/DanhSachHoaDon.xlsx#07.2026`<br>`biz_128/DanhSachHoaDon.xlsx#08.2025`<br>`biz_128/DanhSachHoaDon.xlsx#08.2026`<br>`biz_128/DanhSachHoaDon.xlsx#09.2025`<br>`biz_128/DanhSachHoaDon.xlsx#09.2026`<br>`biz_128/DanhSachHoaDon.xlsx#10.2025`<br>`biz_128/DanhSachHoaDon.xlsx#11.2025`<br>`biz_128/DanhSachHoaDon.xlsx#12.2025`<br>`biz_128/DanhSachHoaDonChiTiet.xlsx#Sheet1`<br>`biz_128/DanhSachKhachHang.xlsx#Sheet1`<br>`biz_128/DanhSachNhapHang.xlsx#Sheet1` |

## Tái lập

Không cần quét lại D01 nếu fingerprints còn khớp:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
uv run --no-project --python .venv/Scripts/python.exe python scripts/review_data_catalog.py --write-docs
uv run --no-project --python .venv/Scripts/python.exe python -m unittest discover -s tests -p '*catalog*.py' -v
uv run --no-project --python .venv/Scripts/python.exe python scripts/validate_data_catalog.py --write-report
git diff --check
```

Nếu chưa có artifact ban đầu, chạy build_data_catalog.py trước. Review giữ data_catalog.initial.json làm baseline bất biến; nếu nguồn khác fingerprint thì dừng, không âm thầm tái sử dụng số cũ.

## Validation

```json
{
  "status": "passed",
  "businesses": 30,
  "tables": 339,
  "physical_header_checks": 339,
  "quality_schema": [
    "business_id",
    "source_ref",
    "column",
    "metric",
    "value",
    "denominator",
    "status"
  ],
  "quality_records": 11466,
  "question_source_records": 60,
  "strict_json_no_duplicate_keys": true,
  "source_refs_reachable": true,
  "fingerprints_before_after_match": true,
  "source_file_count": 162,
  "public_test_document_unchanged": true,
  "synthetic_tests": {
    "status": "passed",
    "count": 21,
    "log": "artifacts/data_prep/catalog_tests.log"
  },
  "git_diff_check": "passed",
  "official_archive_checksum": "not_verified",
  "review_acceptance": "Person 2 / lead pending"
}
```

Synthetic tests kiểm tra serial có/không đủ bằng chứng, sai epoch/ngày, duplicate JSON keys, bảng không liên quan chung khóa, header/OOXML/duration, SQLite handle và source fingerprint.
Lỗi console Unicode cũ được tránh bằng JSON ensure_ascii khi log; validator mở được tên file/sheet thật. Hủy/hủy là hai key JSON hợp lệ khác hoa thường; không dùng PowerShell ConvertFrom-Json để kết luận duplicate keys.

## File và Git

Phạm vi tạo/sửa: scripts/build_data_catalog.py (render catalog), scripts/review_data_catalog.py, scripts/validate_data_catalog.py; tests/*catalog*.py; docs/data-schema-catalog.md; báo cáo này. Artifact chi tiết ở artifacts/data_prep/ và vẫn gitignore.
Không sửa train, không sửa package/runtime/trace của thành viên khác, không commit/push.

Git status ghi trước khi xuất báo cáo:

```text
M docs/data-schema-catalog.md
?? docs/data-catalog-delivery.md
?? docs/data-catalog-handoff.md
?? scripts/build_data_catalog.py
?? scripts/review_data_catalog.py
?? scripts/validate_data_catalog.py
?? tests/test_catalog_review.py
?? tests/test_data_catalog.py
```
