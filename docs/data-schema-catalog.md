# Data schema catalog

## Train — kiểm tra trên dữ liệu local

Nguồn: `train/`; script: `scripts/build_data_catalog.py`. Không tải dữ liệu, không sửa nguồn.
Đã đọc 30/30 business, 162 file trong toàn train, 339 sheet/table/CSV.
Checksum gói chính thức **chưa xác minh**. SHA-256 từng file chỉ dùng so trước/sau; nguồn không đổi trong lượt quét.
Môi trường khóa bị chặn vì thiếu `src/datamate/__init__.py`; công cụ dùng thư viện chuẩn qua uv, không đổi dependencies.

`header_status=verified` xác nhận schema SQLite hoặc dòng header thực khớp README/catalog cũ; không tự xác nhận ý nghĩa dữ liệu.
`status=verified` chỉ xác nhận header và grain nêu trong entry; quality/join có trạng thái độc lập. Các join thống kê là candidate, chưa thay thế review ngữ nghĩa.
Số dòng là dòng không trống sau header, loại header lặp khớp nguyên dòng; chưa fill nhóm, chưa deduplicate, chưa lọc trạng thái.
Kiểu là kiểu lưu trữ: CSV giữ string; Excel đọc cached values và date styles. Công thức chưa có cached value và header nhiều dòng cần review.
Ngày parse ISO hoặc dd/mm/yyyy (có giờ), dd-mm-yyyy/dd.mm.yyyy, d thg m yyyy; dd/mm chỉ dùng năm của sheet. Không đoán năm từ tên file.
Lượt quét cơ sở chỉ parse serial text khi khớp ThoiGianLap độc lập cùng dòng SQLite; policy CSV đã audit được ghi riêng trong review bổ sung. unparsed_date không đồng nghĩa nguồn hỏng.
Ô số trong cột ngày XLSX được giải theo epoch workbook, đối chiếu năm sheet nếu có; duration như Hạn nợ (ngày) không được coi là ngày lịch.
Null/blank và duplicates là quan sát raw, không tự coi là lỗi; áp dụng rulebook §8 trước khi tính đáp án.
Chi tiết cột, date coverage, keys, join coverage/fan-out, fingerprints và findings ở `artifacts/data_prep/` (local, không commit).

Tái lập trong PowerShell (sau khi có Python):

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
uv run --no-project --python .venv/Scripts/python.exe python scripts/build_data_catalog.py --write-docs
```

D01: kiểm kê toàn bộ. D02: header/grain có trạng thái từng nguồn. D03: profiling raw đã đo, date/units/status chưa đầy đủ kiểm tra ngữ nghĩa.
D04: các phép đo bằng counter, không thực thi SQL do model sinh; trạng thái map/validation xem review bổ sung. D05: chờ Người 2/lead review.
48 câu development / 12 câu holdout đã tiếp xúc nhãn: dùng ID/text để bàn giao nguồn, không dùng gold để profiling hoặc chọn cấu hình.

### Review bổ sung có bằng chứng

Grain: {'verified': 335, 'needs_review': 4}; 109 quan hệ được đo theo loại nguồn và kiểm tra khóa, không phê duyệt mọi candidate chung khóa.
Trạng thái cạnh: {'verified': 101, 'verified_requires_order_line_dedup': 3, 'verified_with_unmatched': 5}.
CSV serial có policy audit riêng trong `date_reviews`; chỉ áp khi epoch duy nhất khớp ngày bao quanh, README cutoff và nguồn thu tiền độc lập. Không bật parser số tổng quát.
Source contracts của 60 câu: `artifacts/data_prep/question_source_map.json`; chưa phải trace/đáp án đã xác minh. Chi tiết handoff: [data-catalog-handoff.md](data-catalog-handoff.md).

Sau bước build (chỉ khi cần), tiếp tục review và validation:

```powershell
uv run --no-project --python .venv/Scripts/python.exe python scripts/review_data_catalog.py --write-docs
uv run --no-project --python .venv/Scripts/python.exe python scripts/validate_data_catalog.py --write-report
```

### biz_101

README: `data/biz_101/README.md`; 1 data files; 1 tables; 0 measured join candidates.

- **ban_hang.csv** — 56501 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Giá bán` · `Kết quả` · `Nội dung` · `Ngày tháng` · `Đơn vị (tính)` · `so_luong` · `Thanh tien` · `Quy ra ĐV lẻ` · `Mã hóa đơn` · `Đối tác`
  - Grain (verified): one sales line in an order.
  - Dates: `Ngày tháng`: 2025-06-01 → 2026-08-24; invalid=0

### biz_102

README: `data/biz_102/README.md`; 2 data files; 19 tables; 18 measured join candidates.

- **DanhSachQuyDoi.xlsx** / `Sheet1` — 77 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
  - Grain (verified): one unit conversion per product name + selling unit.
- **DonHang_ChiTiet.xlsx** / `T01_2025` — 6674 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-01-01 → 2025-01-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T02_2025` — 5960 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-02-01 → 2025-02-28; invalid=0
- **DonHang_ChiTiet.xlsx** / `T03_2025` — 4785 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-03-01 → 2025-03-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T04_2025` — 4587 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-04-01 → 2025-04-30; invalid=0
- **DonHang_ChiTiet.xlsx** / `T05_2025` — 4575 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-05-01 → 2025-05-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T06_2025` — 4287 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-06-01 → 2025-06-30; invalid=0
- **DonHang_ChiTiet.xlsx** / `T07_2025` — 4568 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-07-01 → 2025-07-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T08_2025` — 4626 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-08-01 → 2025-08-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T09_2025` — 4410 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-09-01 → 2025-09-30; invalid=0
- **DonHang_ChiTiet.xlsx** / `T10_2025` — 4715 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-10-01 → 2025-10-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T11_2025` — 4605 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-11-01 → 2025-11-30; invalid=0
- **DonHang_ChiTiet.xlsx** / `T12_2025` — 4436 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-12-01 → 2025-12-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T01_2026` — 4730 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-01-01 → 2026-01-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T02_2026` — 7256 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-02-01 → 2026-02-28; invalid=0
- **DonHang_ChiTiet.xlsx** / `T03_2026` — 4743 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-03-01 → 2026-03-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T04_2026` — 4312 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-04-01 → 2026-04-30; invalid=0
- **DonHang_ChiTiet.xlsx** / `T05_2026` — 4395 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-05-01 → 2026-05-31; invalid=0
- **DonHang_ChiTiet.xlsx** / `T06_2026` — 2365 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-06-01 → 2026-06-16; invalid=0

### biz_103

README: `data/biz_103/README.md`; 2 data files; 17 tables; 16 measured join candidates.

- **DanhSachQuyDoi.xlsx** / `Sheet1` — 77 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
  - Grain (verified): one unit conversion per product name + selling unit.
- **DonHang_ChiTiet.xlsx** / `04.2025` — 2753 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-04-01 → 2025-04-30; invalid=0
  - Raw duplicate excess rows: 664 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `05.2025` — 2846 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-05-01 → 2025-05-31; invalid=0
  - Raw duplicate excess rows: 712 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `06.2025` — 2635 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-06-01 → 2025-06-30; invalid=0
  - Raw duplicate excess rows: 639 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `07.2025` — 2786 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-07-01 → 2025-07-31; invalid=0
  - Raw duplicate excess rows: 677 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `08.2025` — 2918 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-08-01 → 2025-08-31; invalid=0
  - Raw duplicate excess rows: 761 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `09.2025` — 2744 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-09-01 → 2025-09-30; invalid=0
  - Raw duplicate excess rows: 673 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `10.2025` — 2940 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-10-01 → 2025-10-31; invalid=0
  - Raw duplicate excess rows: 786 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `11.2025` — 2881 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-11-01 → 2025-11-30; invalid=0
  - Raw duplicate excess rows: 714 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `12.2025` — 2851 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-12-01 → 2025-12-31; invalid=0
  - Raw duplicate excess rows: 739 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `01.2026` — 2936 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-01-01 → 2026-01-31; invalid=0
  - Raw duplicate excess rows: 699 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `02.2026` — 4734 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-02-01 → 2026-02-28; invalid=0
  - Raw duplicate excess rows: 1551 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `03.2026` — 2903 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-03-01 → 2026-03-31; invalid=0
  - Raw duplicate excess rows: 763 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `04.2026` — 3003 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-04-01 → 2026-04-30; invalid=0
  - Raw duplicate excess rows: 812 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `05.2026` — 2854 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-05-01 → 2026-05-31; invalid=0
  - Raw duplicate excess rows: 721 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `06.2026` — 2758 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-06-01 → 2026-06-30; invalid=0
  - Raw duplicate excess rows: 677 (không tự loại).
- **DonHang_ChiTiet.xlsx** / `07.2026` — 992 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-07-01 → 2026-07-09; invalid=0
  - Raw duplicate excess rows: 140 (không tự loại).

### biz_104

README: `data/biz_104/README.md`; 2 data files; 2 tables; 1 measured join candidates.

- **DanhSachQuyDoi.xlsx** / `Sheet1` — 2 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
  - Grain (verified): one unit conversion per product name + selling unit.
- **DonHang_ChiTiet.xlsx** / `Sheet1` — 62894 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-04-01 → 2026-06-02; invalid=0

### biz_105

README: `data/biz_105/README.md`; 6 data files; 21 tables; 60 measured join candidates.

- **BangGia.xlsx** / `Sheet1` — 78 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày áp dụng` · `ten_hang` · `Giá mới` · `Giá cũ`
  - Grain (verified): một mốc giá của sản phẩm; hiệu lực đến trước lần đổi sau, cần temporal join.
  - Dates: `Ngày áp dụng`: 2025-02-01 → 2026-06-11; invalid=0
- **DanhMuc.xlsx** / `Sheet1` — 2 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tên món` · `Đơn vị gốc` · `ĐV nhập` · `Hệ số`
  - Grain (verified): một hệ số quy đổi theo sản phẩm và đơn vị bán/đơn vị lớn.
- **SoBanHang_1.xlsx** / `Thang 02 2025` — 6490 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-02-01 → 2025-02-28; invalid=0
  - Raw duplicate excess rows: 104 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 03 2025` — 8139 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-03-01 → 2025-03-31; invalid=0
  - Raw duplicate excess rows: 114 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 04 2025` — 7763 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-04-01 → 2025-04-30; invalid=0
  - Raw duplicate excess rows: 128 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 05 2025` — 8072 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-05-01 → 2025-05-31; invalid=0
  - Raw duplicate excess rows: 120 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 06 2025` — 8040 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-06-01 → 2025-06-30; invalid=0
  - Raw duplicate excess rows: 133 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 07 2025` — 8307 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-07-01 → 2025-07-31; invalid=0
  - Raw duplicate excess rows: 134 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 08 2025` — 8702 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-08-01 → 2025-08-31; invalid=0
  - Raw duplicate excess rows: 157 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 09 2025` — 8208 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-09-01 → 2025-09-30; invalid=0
  - Raw duplicate excess rows: 141 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 10 2025` — 8853 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-10-01 → 2025-10-31; invalid=0
  - Raw duplicate excess rows: 142 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 11 2025` — 8443 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-11-01 → 2025-11-30; invalid=0
  - Raw duplicate excess rows: 143 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 12 2025` — 8828 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2025-12-01 → 2025-12-31; invalid=0
  - Raw duplicate excess rows: 125 (không tự loại).
- **SoBanHang_1.xlsx** / `Thang 01 2026` — 9059 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2026-01-01 → 2026-01-31; invalid=0
  - Raw duplicate excess rows: 156 (không tự loại).
- **SoBanHang_2026.xlsx** / `Thang 02 2026` — 6299 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2026-02-01 → 2026-02-28; invalid=0
  - Raw duplicate excess rows: 100 (không tự loại).
- **SoBanHang_2026.xlsx** / `Thang 03 2026` — 9240 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2026-03-01 → 2026-03-31; invalid=0
  - Raw duplicate excess rows: 139 (không tự loại).
- **SoBanHang_2026.xlsx** / `Thang 04 2026` — 8947 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2026-04-01 → 2026-04-30; invalid=0
  - Raw duplicate excess rows: 131 (không tự loại).
- **SoBanHang_2026.xlsx** / `Thang 05 2026` — 9531 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2026-05-01 → 2026-05-31; invalid=0
  - Raw duplicate excess rows: 143 (không tự loại).
- **SoBanHang_2026.xlsx** / `Thang 06 2026` — 7324 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày giao dịch`: 2026-06-01 → 2026-06-24; invalid=0
  - Raw duplicate excess rows: 112 (không tự loại).
- **SoNhapHang.xlsx** / `Sheet1` — 1373 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Số phiếu` · `Ngày nhập` · `Ghi chu` · `Thành tiền` · `Nhà cung cấp` · `Tên mặt hàng` · `Giá nhập` · `ĐVT` · `SL nhập`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
  - Dates: `Ngày nhập`: 2025-02-01 → 2026-06-24; invalid=0
- **TonKho.xlsx** / `Sheet1` — 50 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Hàng hóa` · `Đơn vị tính` · `Tồn cuối`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.

### biz_106

README: `data/biz_106/README.md`; 10 data files; 10 tables; 0 measured join candidates.

- **BaoCaoTonKho.xlsx** / `Sheet1` — 50 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.
- **DanhSachChiTietNhapHang.xlsx** / `Sheet1` — 1562 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
- **DanhSachDonViTinh.xlsx** / `Sheet1` — 2 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `ĐVT` · `Quy đổi` · `Giá bán`
  - Grain (verified): một hệ số quy đổi theo sản phẩm và đơn vị bán/đơn vị lớn.
- **DanhSachHoaDon.xlsx** / `Sheet1` — 78847 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Tổng sau giảm giá` · `Khách đã trả` · `Phương thức thanh toán` · `Trạng thái` · `Thời gian tạo` · `Ghi chú`
  - Grain (verified): một đơn hàng; ngày và tổng tiền ở cấp đơn.
- **DanhSachHoaDonChiTiet_1.xlsx** / `Sheet1` — 100000 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `STT` · `Mã hàng` · `Tên hàng` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `Giá vốn`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Raw duplicate excess rows: 2496 (không tự loại).
- **DanhSachHoaDonChiTiet_2.xlsx** / `Sheet1` — 29416 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `STT` · `Mã hàng` · `Tên hàng` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `Giá vốn`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Raw duplicate excess rows: 734 (không tự loại).
- **DanhSachKhachHang.xlsx** / `Sheet1` — 240 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Email` · `Mã khách hàng` · `Trạng thái` · `Tên công ty` · `Ngày sinh` · `Tổng điểm` · `Điểm tích lũy` · `Ghi chú` · `Số CMND/CCCD` · `Tên khách hàng` · `Mã số thuế` · `Người tạo` · `Điện thoại` · `Loại hình khách`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `Ngày sinh`: 1966-08-04 → 2003-12-16; invalid=0
- **DanhSachNhapHang.xlsx** / `Sheet1` — 513 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
- **DanhSachSanPham.xlsx** / `Sheet1` — 50 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Hình ảnh (url1,url2...)` · `Vị trí kệ` · `Ghi chú` · `Được bán trực tiếp` · `Nhóm hàng(3 Cấp)` · `Mã barcode` · `Mã hàng` · `Thương hiệu` · `Tồn lớn nhất` · `Tên hàng` · `Mã HH Liên quan` · `Thuộc tính` · `Giá bán` · `Mô tả sản phẩm` · `Loại hàng hóa` · `Giá vốn` · `ĐVT` · `Bảo hành` · `Đang kinh doanh` · `Trọng lượng` · `Mẫu ghi chú` · `Định mức tồn tối thiểu` · `Thời gian tạo`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **SoQuy.xlsx** / `Sheet1` — 78673 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã phiếu` · `Thời gian` · `Mã hóa đơn` · `Phương thức thanh toán` · `Giá trị`
  - Grain (verified): one payment event (not one order).

### biz_107

README: `data/biz_107/README.md`; 1 data files; 1 tables; 0 measured join candidates.

- **SoBanHang.xlsx** / `Sheet1` — 43605 data rows; header: 1 (verified); status: `needs_review`.
  - Columns: `Trạng thái xử lý` · `Tổng tiền` · `ngay_ban` · `Số lượng` · `Nội dung` · `don_gia` · `Đơn vị (tính)` · `Số lượng lẻ`
  - Grain (needs_review): one recorded item purchase; no order/customer ID; OBSERVED MIXED ROWS: 526 dòng mang nhãn tổng, cần xác minh bộ lọc.
  - Dates: `ngay_ban`: 2025-03-01 → 2026-07-22; invalid=0
  - Raw duplicate excess rows: 5756 (không tự loại).

### biz_108

README: `data/biz_108/README.md`; 7 data files; 7 tables; 9 measured join candidates.

- **BaoCaoTonKho.xlsx** / `Sheet1` — 60 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.
- **DanhSachChiTietNhapHang.xlsx** / `Sheet1` — 2293 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
- **DanhSachHoaDon.xlsx** / `Sheet1` — 31501 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ` · `Kênh bán` · `Người bán` · `Trạng thái HĐĐT`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-01-01 → 2026-05-29; invalid=0; `Thời gian tạo`: 2025-01-01 → 2026-05-29; invalid=0
- **DanhSachHoaDonChiTiet.xlsx** / `Sheet1` — 78983 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Mã hàng` · `Tên hàng` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `Đơn vị tính` · `STT`
  - Grain (verified): sales line identified by order + line (plus store where present).
- **DanhSachKhachHang.xlsx** / `Sheet1` — 300 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Đối tượng KH` · `Tổng điểm` · `Trạng thái` · `Mã số thuế` · `Mã khách hàng` · `Tên khách hàng` · `Điện thoại` · `Ngày sinh` · `Nhóm khách hàng` · `Địa chỉ` · `Người tạo` · `Giới tính` · `CCCD` · `Tên công ty` · `Điểm hiện tại` · `Ngày tạo`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `Ngày sinh`: 1966-03-14 → 2004-08-23; invalid=0; `Ngày tạo`: 2022-07-17 → 2025-02-10; invalid=0
- **DanhSachNhapHang.xlsx** / `Sheet1` — 499 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
  - Dates: `Thời gian`: 2025-01-01 → 2026-05-29; invalid=0
- **DanhSachSanPham.xlsx** / `Sheet1` — 60 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Tên hàng` · `Bảo hành` · `Nhóm hàng(3 Cấp)` · `Mô tả chi tiết` · `Trọng lượng` · `Vị trí` · `Hình ảnh (url1,url2...)` · `Mã barcode` · `Loại hàng hóa` · `Thuộc tính` · `Mẫu ghi chú` · `Giá bán` · `Được bán trực tiếp` · `Ghi chú` · `Mã HH Liên quan` · `ĐVT` · `Định mức tồn tối thiểu`
  - Grain (verified): một bản ghi danh mục sản phẩm.

### biz_109

README: `data/biz_109/README.md`; 2 data files; 9 tables; 0 measured join candidates.

- **DanhSachHoaDonChiTiet.xlsx** / `Sheet1` — 83284 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `STT` · `Mã hàng` · `Tên hàng` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `Giá vốn`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
- **DuLieuBanHang.xlsx** / `DanhSachHoaDon` — 33065 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Tổng sau giảm giá` · `Khách đã trả` · `Phương thức thanh toán` · `Trạng thái` · `Thời gian tạo` · `Kênh bán` · `Người bán` · `Trạng thái HĐĐT`
  - Grain (verified): một đơn hàng; ngày và tổng tiền ở cấp đơn.
- **DuLieuBanHang.xlsx** / `DanhSachSanPham` — 60 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tồn lớn nhất` · `Nhóm hàng(3 Cấp)` · `Vị trí` · `Mã hàng` · `Trọng lượng` · `Thuộc tính` · `Tên hàng` · `Mẫu ghi chú` · `Giá bán` · `Hình ảnh (url1,url2...)` · `Bảo hành` · `Định mức tồn tối thiểu` · `Giá vốn` · `Thương hiệu` · `Được bán trực tiếp` · `ĐVT` · `Đang kinh doanh` · `Thời gian tạo`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **DuLieuBanHang.xlsx** / `DanhSachKhachHang` — 320 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã khách hàng` · `Tổng điểm` · `Tên khách hàng` · `Điện thoại` · `MST` · `Trạng thái` · `Loại hình khách` · `Người tạo` · `Ghi chú KH` · `Tên công ty` · `Nhóm khách hàng` · `Ngày tạo` · `Sinh nhật`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `Ngày tạo`: 2022-07-23 → 2025-01-24; invalid=0
- **DuLieuBanHang.xlsx** / `BaoCaoTonKho` — 60 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.
- **DuLieuBanHang.xlsx** / `DanhSachNhapHang` — 561 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
- **DuLieuBanHang.xlsx** / `DanhSachChiTietNhapHang` — 2225 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
- **DuLieuBanHang.xlsx** / `SoQuy` — 36974 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã phiếu` · `Thời gian` · `Mã hóa đơn` · `Phương thức thanh toán` · `Giá trị`
  - Grain (verified): one payment event (not one order).
- **DuLieuBanHang.xlsx** / `DanhSachDonViTinh` — 77 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `ĐVT` · `Quy đổi` · `Giá bán`
  - Grain (verified): một hệ số quy đổi theo sản phẩm và đơn vị bán/đơn vị lớn.

### biz_110

README: `data/biz_110/README.md`; 1 data files; 1 tables; 0 measured join candidates.

- **danh_sach_hoa_don.csv** — 29317 data rows; header: 1 (verified); status: `needs_review`.
  - Columns: `Tien hang` · `TongTien` · `Mã bill` · `Bên mua` · `Ngày giao dịch` · `Status` · `Da tra` · `Chưa trả`
  - Grain (needs_review): một đơn hàng; ngày và tổng tiền ở cấp đơn; OBSERVED MIXED ROWS: 429 dòng mang nhãn tổng, cần xác minh bộ lọc.
  - Dates: `Ngày giao dịch`: 2025-05-01 → 2026-07-03; invalid=0

### biz_111

README: `data/biz_111/README.md`; 5 data files; 5 tables; 5 measured join candidates.

- **chi_tiet_don.csv** — 106585 data rows; header: 1 (verified); status: `verified`.
  - Columns: `SL quy đổi` · `Thứ tự` · `Giá đơn vị` · `SL` · `T.Tiền` · `ID SP` · `Ma don` · `Đơn vị (tính)`
  - Grain (verified): sales line identified by order + line (plus store where present).
- **don_hang.csv** — 66469 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Số KH` · `Xử lý` · `NgayBan` · `Bán qua` · `Còn lại` · `Khách trả` · `Tổng bill` · `Phương thức TT` · `Mã chứng từ`
  - Grain (verified): one order.
  - Dates: `NgayBan`: 2025-01-01 → 2026-08-19; invalid=0
- **khach_hang.csv** — 200 data rows; header: 1 (verified); status: `verified`.
  - Columns: `ma_kh` · `Điểm tích lũy` · `Nhóm` · `Trạng thái` · `Email` · `Ghi chú KH` · `Mã số thuế` · `Loại hình khách` · `Ngày sinh` · `CCCD` · `Phone` · `Người tạo` · `Addr` · `Khách lẻ/sỉ` · `Tổng điểm`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `Ngày sinh`: 1967-05-28 → 2003-05-13; invalid=0
- **san_pham.csv** — 50 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Thuộc tính` · `Được bán trực tiếp` · `Mã barcode` · `SKU` · `Hình ảnh` · `Giá` · `Đơn vị` · `Loại hàng hóa` · `Thương hiệu` · `Nhom hang` · `Trọng lượng` · `Vị trí` · `Mẫu ghi chú` · `Mô tả sản phẩm` · `Bảo hành` · `Tồn nhỏ nhất` · `Mã HH Liên quan` · `Sản phẩm`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **thanh_toan.csv** — 66195 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Thời gian thu` · `Phương thức` · `Tiền` · `Mã phiếu thu` · `Số HĐ`
  - Grain (verified): one payment event (not one order).
  - Dates: `Thời gian thu`: 2025-01-01 → 2026-08-19; invalid=0

### biz_112

README: `data/biz_112/README.md`; 3 data files; 17 tables; 56 measured join candidates.
README/path conflicts (không đổi tên nguồn): {"missing": ["Danh sách hàng hóa.xlsx"], "extra": ["Danh s├ích h├áng h├│a.xlsx"], "unicode_matches": {"Danh s├ích h├áng h├│a.xlsx": "Danh sách hàng hóa.xlsx"}}

- **Danh s├ích h├áng h├│a.xlsx** / `Sheet1` — 50 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng hóa` · `Mã vạch EAN` · `Tồn nhỏ nhất` · `Trọng lượng` · `Ghi chú` · `Loại hàng hóa` · `Mã HH Liên quan` · `Mô tả sản phẩm` · `Bảo hành` · `Tên hàng hóa` · `Vị trí` · `Nhóm hàng hóa` · `Đơn vị tính` · `Giá bán` · `Tồn lớn nhất` · `Giá vốn`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **So_chi_tiet_ban_hang_1.xlsx** / `T04_2025` — 6523 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-04-01 → 2025-04-30; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T05_2025` — 6902 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-05-01 → 2025-05-31; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T06_2025` — 6883 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-06-01 → 2025-06-30; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T07_2025` — 6892 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-07-01 → 2025-07-31; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T08_2025` — 7419 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-08-01 → 2025-08-31; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T09_2025` — 6953 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-09-01 → 2025-09-30; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T10_2025` — 7162 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-10-01 → 2025-10-31; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T11_2025` — 7156 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-11-01 → 2025-11-30; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T12_2025` — 7240 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-12-01 → 2025-12-31; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T01_2026` — 7478 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-01-01 → 2026-01-31; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T02_2026` — 5267 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-02-01 → 2026-02-28; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T03_2026` — 7593 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-03-01 → 2026-03-31; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T04_2026` — 7316 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-04-01 → 2026-04-30; invalid=0
- **So_chi_tiet_ban_hang_1.xlsx** / `T05_2026` — 7802 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-05-01 → 2026-05-31; invalid=0
- **So_chi_tiet_ban_hang_2026.xlsx** / `T06_2026` — 7083 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-06-01 → 2026-06-30; invalid=0
- **So_chi_tiet_ban_hang_2026.xlsx** / `T07_2026` — 7656 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-07-01 → 2026-07-31; invalid=0

### biz_113

README: `data/biz_113/README.md`; 1 data files; 1 tables; 0 measured join candidates.

- **SoBanHang.xlsx** / `Sheet1` — 32994 data rows; header: 1 (verified); status: `verified`.
  - Columns: `DonVi` · `Ngày mua` · `Số lượng lẻ` · `thanh_tien` · `Đơn giá bán` · `SL bán` · `Ghi chú TT` · `Mặt hàng`
  - Grain (verified): one recorded item purchase; no order/customer ID.
  - Dates: `Ngày mua`: 2025-02-01 → 2026-08-09; invalid=0
  - Raw duplicate excess rows: 5285 (không tự loại).

### biz_114

README: `data/biz_114/README.md`; 1 data files; 1 tables; 0 measured join candidates.

- **ban_hang.csv** — 26119 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Giá bán lẻ` · `Đơn vị tính` · `Mã GD` · `Quy ra ĐV lẻ` · `Sluong` · `Sản phẩm` · `Tổng` · `Tên khách` · `Ngày` · `trang_thai`
  - Grain (verified): one sales line in an order.
  - Dates: `Ngày`: 2025-01-01 → 2026-06-21; invalid=0

### biz_115

README: `data/biz_115/README.md`; 4 data files; 19 tables; 49 measured join candidates.
README/path conflicts (không đổi tên nguồn): {"missing": ["Bảng kê phiếu giao hàng.xlsx", "Chi tiết công nợ theo hạn.xlsx", "Danh sách hàng hóa.xlsx"], "extra": ["Bß║úng k├¬ phiß║┐u giao h├áng.xlsx", "Chi tiß║┐t c├┤ng nß╗ú theo hß║ín.xlsx", "Danh s├ích h├áng h├│a.xlsx"], "unicode_matches": {"Bß║úng k├¬ phiß║┐u giao h├áng.xlsx": "Bảng kê phiếu giao hàng.xlsx", "Chi tiß║┐t c├┤ng nß╗ú theo hß║ín.xlsx": "Chi tiết công nợ theo hạn.xlsx", "Danh s├ích h├áng h├│a.xlsx": "Danh sách hàng hóa.xlsx"}}

- **Bß║úng k├¬ phiß║┐u giao h├áng.xlsx** / `Sheet1` — 24877 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày giao hàng` · `Mã đơn hàng` · `Lần giao` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng giao` · `Biển số xe` · `Người giao hàng`
  - Grain (verified): một mặt hàng trong một đợt giao của đơn; đếm đợt bằng DISTINCT (đơn, đợt), không đếm dòng hàng.
  - Dates: `Ngày giao hàng`: 2025-02-01 → 2026-05-16; invalid=0
- **Chi tiß║┐t c├┤ng nß╗ú theo hß║ín.xlsx** / `Sheet1` — 2304 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Số ngày được nợ` · `Hạn thanh toán`
  - Grain (verified): một bản ghi hạn/công nợ của đơn; không phải lịch sử thanh toán.
- **Danh s├ích h├áng h├│a.xlsx** / `Sheet1` — 60 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng hóa` · `Được bán trực tiếp` · `Thương hiệu` · `Tên hàng hóa` · `Nhóm hàng hóa` · `Vị trí` · `Mẫu ghi chú` · `Loại hàng hóa` · `Ghi chú` · `Đơn vị tính` · `Bảo hành` · `Giá vốn` · `Mô tả sản phẩm` · `Định mức tồn tối thiểu` · `Trọng lượng`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **So_chi_tiet_ban_hang.xlsx** / `02.2025` — 1538 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-02-01 → 2025-02-28; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `03.2025` — 2055 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-03-01 → 2025-03-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `04.2025` — 1996 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-04-01 → 2025-04-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `05.2025` — 1994 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-05-01 → 2025-05-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `06.2025` — 1924 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-06-01 → 2025-06-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `07.2025` — 1910 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-07-01 → 2025-07-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `08.2025` — 1861 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-08-01 → 2025-08-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `09.2025` — 1940 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-09-01 → 2025-09-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `10.2025` — 1889 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-10-01 → 2025-10-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `11.2025` — 1824 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-11-01 → 2025-11-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `12.2025` — 1935 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-12-01 → 2025-12-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `01.2026` — 1895 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-01-01 → 2026-01-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `02.2026` — 1252 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-02-01 → 2026-02-28; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `03.2026` — 1970 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-03-01 → 2026-03-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `04.2026` — 1759 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-04-01 → 2026-04-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `05.2026` — 979 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-05-01 → 2026-05-16; invalid=0

### biz_116

README: `data/biz_116/README.md`; 1 data files; 4 tables; 0 measured join candidates.

- **Bao_cao_ban_hang.xlsx** / `So_chi_tiet_ban_hang` — 39889 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-05-01 → 2026-09-03; invalid=0
- **Bao_cao_ban_hang.xlsx** / `Danh sách hàng hóa` — 55 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Bảo hành` · `Mã hàng hóa` · `Tên hàng hóa` · `Hình ảnh (url1,url2...)` · `Thuộc tính` · `Mẫu ghi chú` · `Mô tả sản phẩm` · `Nhóm hàng hóa` · `Đơn vị tính` · `Trọng lượng` · `Tồn nhỏ nhất` · `Mã HH Liên quan` · `Ghi chú` · `Được bán trực tiếp` · `Giá vốn` · `Vị trí` · `Tồn lớn nhất`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **Bao_cao_ban_hang.xlsx** / `Bảng kê phiếu giao hàng` — 35370 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày giao hàng` · `Mã đơn hàng` · `Lần giao` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng giao` · `Biển số xe` · `Người giao hàng`
  - Grain (verified): một mặt hàng trong một đợt giao của đơn; đếm đợt bằng DISTINCT (đơn, đợt), không đếm dòng hàng.
  - Dates: `Ngày giao hàng`: 2025-05-01 → 2026-09-03; invalid=0
- **Bao_cao_ban_hang.xlsx** / `Chi tiết công nợ theo hạn` — 3803 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Số ngày được nợ` · `Hạn thanh toán`
  - Grain (verified): một bản ghi hạn/công nợ của đơn; không phải lịch sử thanh toán.

### biz_117

README: `data/biz_117/README.md`; 7 data files; 23 tables; 35 measured join candidates.

- **BangGia.xlsx** / `Sheet1` — 100 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ngày áp dụng` · `Giá cũ` · `Giá mới` · `TenHang`
  - Grain (verified): một mốc giá của sản phẩm; hiệu lực đến trước lần đổi sau, cần temporal join.
  - Dates: `Ngày áp dụng`: 2025-01-01 → 2026-05-18; invalid=0
- **DanhMuc.xlsx** / `Sheet1` — 14 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Hàng` · `ĐV lớn` · `ĐV nhỏ` · `Hệ số QĐ`
  - Grain (verified): một hệ số quy đổi theo sản phẩm và đơn vị bán/đơn vị lớn.
- **SoBanHang.xlsx** / `Tháng 01-2025` — 1598 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-01-01 → 2025-01-31; invalid=0
  - Raw duplicate excess rows: 20 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 02-2025` — 1534 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-02-01 → 2025-02-28; invalid=0
  - Raw duplicate excess rows: 14 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 03-2025` — 2073 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-03-01 → 2025-03-31; invalid=0
  - Raw duplicate excess rows: 43 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 04-2025` — 1992 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-04-01 → 2025-04-30; invalid=0
  - Raw duplicate excess rows: 26 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 05-2025` — 2102 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-05-01 → 2025-05-31; invalid=0
  - Raw duplicate excess rows: 34 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 06-2025` — 2092 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-06-01 → 2025-06-30; invalid=0
  - Raw duplicate excess rows: 25 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 07-2025` — 1973 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-07-01 → 2025-07-31; invalid=0
  - Raw duplicate excess rows: 27 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 08-2025` — 2116 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-08-01 → 2025-08-31; invalid=0
  - Raw duplicate excess rows: 25 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 09-2025` — 2123 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-09-01 → 2025-09-30; invalid=0
  - Raw duplicate excess rows: 26 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 10-2025` — 2050 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-10-01 → 2025-10-31; invalid=0
  - Raw duplicate excess rows: 39 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 11-2025` — 2015 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-11-01 → 2025-11-30; invalid=0
  - Raw duplicate excess rows: 22 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 12-2025` — 2117 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2025-12-01 → 2025-12-31; invalid=0
  - Raw duplicate excess rows: 26 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 01-2026` — 2350 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2026-01-01 → 2026-01-31; invalid=0
  - Raw duplicate excess rows: 37 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 02-2026` — 1517 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2026-02-01 → 2026-02-28; invalid=0
  - Raw duplicate excess rows: 16 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 03-2026` — 2340 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2026-03-01 → 2026-03-31; invalid=0
  - Raw duplicate excess rows: 22 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 04-2026` — 2334 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2026-04-01 → 2026-04-30; invalid=0
  - Raw duplicate excess rows: 48 (không tự loại).
- **SoBanHang.xlsx** / `Tháng 05-2026` — 1519 data rows; header: 2 (verified); status: `verified`.
  - Columns: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Dates: `Ngày lập`: 2026-05-01 → 2026-05-20; invalid=0
  - Raw duplicate excess rows: 23 (không tự loại).
- **SoGiaoHang.xlsx** / `Sheet1` — 28411 data rows; header: 1 (verified); status: `verified`.
  - Columns: `ĐV gốc` · `Biển số xe` · `Mã bill` · `Lượt giao` · `SL thực giao` · `Tên hàng` · `Ngày chở` · `Người chở`
  - Grain (verified): một mặt hàng trong một đợt giao của đơn; đếm đợt bằng DISTINCT (đơn, đợt), không đếm dòng hàng.
  - Dates: `Ngày chở`: 2025-01-01 → 2026-05-20; invalid=0
- **SoHanNo.xlsx** / `Sheet1` — 2722 data rows; header: 1 (verified); status: `verified`.
  - Columns: `So hoa don` · `Hạn nợ (ngày)` · `Han tra`
  - Grain (verified): một bản ghi hạn/công nợ của đơn; không phải lịch sử thanh toán.
- **SoNhapHang.xlsx** / `Sheet1` — 1134 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Số phiếu` · `Product` · `Ngày nhập` · `ĐVT` · `Thành tiền` · `Nội dung` · `Nhà cung cấp` · `SL nhập` · `Giá nhập`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
  - Dates: `Ngày nhập`: 2025-01-01 → 2026-05-20; invalid=0
- **TonKho.xlsx** / `Sheet1` — 60 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tồn thực` · `Đơn vị` · `Product`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.

### biz_118

README: `data/biz_118/README.md`; 4 data files; 23 tables; 61 measured join candidates.
README/path conflicts (không đổi tên nguồn): {"missing": ["Bảng kê phiếu giao hàng.xlsx", "Chi tiết công nợ theo hạn.xlsx", "Danh sách hàng hóa.xlsx"], "extra": ["Bß║úng k├¬ phiß║┐u giao h├áng.xlsx", "Chi tiß║┐t c├┤ng nß╗ú theo hß║ín.xlsx", "Danh s├ích h├áng h├│a.xlsx"], "unicode_matches": {"Bß║úng k├¬ phiß║┐u giao h├áng.xlsx": "Bảng kê phiếu giao hàng.xlsx", "Chi tiß║┐t c├┤ng nß╗ú theo hß║ín.xlsx": "Chi tiết công nợ theo hạn.xlsx", "Danh s├ích h├áng h├│a.xlsx": "Danh sách hàng hóa.xlsx"}}

- **Bß║úng k├¬ phiß║┐u giao h├áng.xlsx** / `Sheet1` — 41198 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày giao hàng` · `Mã đơn hàng` · `Lần giao` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng giao` · `Biển số xe` · `Người giao hàng`
  - Grain (verified): một mặt hàng trong một đợt giao của đơn; đếm đợt bằng DISTINCT (đơn, đợt), không đếm dòng hàng.
  - Dates: `Ngày giao hàng`: 2025-02-01 → 2026-09-10; invalid=0
- **Chi tiß║┐t c├┤ng nß╗ú theo hß║ín.xlsx** / `Sheet1` — 4915 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Số ngày được nợ` · `Hạn thanh toán`
  - Grain (verified): một bản ghi hạn/công nợ của đơn; không phải lịch sử thanh toán.
- **Danh s├ích h├áng h├│a.xlsx** / `Sheet1` — 55 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Hình ảnh (url1,url2...)` · `Vị trí` · `Trọng lượng` · `Bảo hành` · `Mã hàng hóa` · `Mã barcode` · `Mô tả sản phẩm` · `Tên hàng hóa` · `Loại hàng hóa` · `Nhóm hàng hóa` · `Đơn vị tính` · `Mã HH Liên quan` · `Tồn lớn nhất` · `Ghi chú` · `Mẫu ghi chú` · `Được bán trực tiếp`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **So_chi_tiet_ban_hang.xlsx** / `T02-2025` — 2075 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-02-01 → 2025-02-28; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T03-2025` — 2529 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-03-01 → 2025-03-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T04-2025` — 2463 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-04-01 → 2025-04-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T05-2025` — 2664 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-05-01 → 2025-05-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T06-2025` — 2534 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-06-01 → 2025-06-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T07-2025` — 2454 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-07-01 → 2025-07-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T08-2025` — 2476 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-08-01 → 2025-08-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T09-2025` — 2592 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-09-01 → 2025-09-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T10-2025` — 2395 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-10-01 → 2025-10-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T11-2025` — 2454 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-11-01 → 2025-11-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T12-2025` — 2514 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2025-12-01 → 2025-12-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T01-2026` — 2561 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-01-01 → 2026-01-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T02-2026` — 1623 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-02-01 → 2026-02-28; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T03-2026` — 2437 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-03-01 → 2026-03-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T04-2026` — 2349 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-04-01 → 2026-04-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T05-2026` — 2383 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-05-01 → 2026-05-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T06-2026` — 2188 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-06-01 → 2026-06-30; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T07-2026` — 2263 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-07-01 → 2026-07-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T08-2026` — 2295 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-08-01 → 2026-08-31; invalid=0
- **So_chi_tiet_ban_hang.xlsx** / `T09-2026` — 752 data rows; header: 4 (verified); status: `verified`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày`: 2026-09-01 → 2026-09-10; invalid=0

### biz_119

README: `data/biz_119/README.md`; 10 data files; 28 tables; 76 measured join candidates.

- **BaoCaoTonKho.xlsx** / `Sheet1` — 70 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.
- **DanhSachChiTietNhapHang.xlsx** / `Sheet1` — 3122 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá` · `Lô` · `Hạn sử dụng`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
  - Dates: `Hạn sử dụng`: 2025-03-07 → 2029-06-12; invalid=0
- **DanhSachHoaDon.xlsx** / `T01-2025` — 2069 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-01-01 → 2025-01-31; invalid=0; `Thời gian tạo`: 2025-01-01 → 2025-01-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T02-2025` — 1823 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-02-01 → 2025-02-28; invalid=0; `Thời gian tạo`: 2025-02-01 → 2025-02-28; invalid=0
- **DanhSachHoaDon.xlsx** / `T03-2025` — 2032 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-03-01 → 2025-03-31; invalid=0; `Thời gian tạo`: 2025-03-01 → 2025-03-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T04-2025` — 1952 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-04-01 → 2025-04-30; invalid=0; `Thời gian tạo`: 2025-04-01 → 2025-04-30; invalid=0
- **DanhSachHoaDon.xlsx** / `T05-2025` — 2006 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-05-01 → 2025-05-31; invalid=0; `Thời gian tạo`: 2025-05-01 → 2025-05-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T06-2025` — 1880 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-06-01 → 2025-06-30; invalid=0; `Thời gian tạo`: 2025-06-01 → 2025-06-30; invalid=0
- **DanhSachHoaDon.xlsx** / `T07-2025` — 1912 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-07-01 → 2025-07-31; invalid=0; `Thời gian tạo`: 2025-07-01 → 2025-07-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T08-2025` — 1926 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-08-01 → 2025-08-31; invalid=0; `Thời gian tạo`: 2025-08-01 → 2025-08-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T09-2025` — 1867 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-09-01 → 2025-09-30; invalid=0; `Thời gian tạo`: 2025-09-01 → 2025-09-30; invalid=0
- **DanhSachHoaDon.xlsx** / `T10-2025` — 1828 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-10-01 → 2025-10-31; invalid=0; `Thời gian tạo`: 2025-10-01 → 2025-10-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T11-2025` — 1764 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-11-01 → 2025-11-30; invalid=0; `Thời gian tạo`: 2025-11-01 → 2025-11-30; invalid=0
- **DanhSachHoaDon.xlsx** / `T12-2025` — 1834 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-12-01 → 2025-12-31; invalid=0; `Thời gian tạo`: 2025-12-01 → 2025-12-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T01-2026` — 1754 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-01-01 → 2026-01-31; invalid=0; `Thời gian tạo`: 2026-01-01 → 2026-01-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T02-2026` — 1746 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-02-01 → 2026-02-28; invalid=0; `Thời gian tạo`: 2026-02-01 → 2026-02-28; invalid=0
- **DanhSachHoaDon.xlsx** / `T03-2026` — 1728 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-03-01 → 2026-03-31; invalid=0; `Thời gian tạo`: 2026-03-01 → 2026-03-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T04-2026` — 1689 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-04-01 → 2026-04-30; invalid=0; `Thời gian tạo`: 2026-04-01 → 2026-04-30; invalid=0
- **DanhSachHoaDon.xlsx** / `T05-2026` — 1764 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-05-01 → 2026-05-31; invalid=0; `Thời gian tạo`: 2026-05-01 → 2026-05-31; invalid=0
- **DanhSachHoaDon.xlsx** / `T06-2026` — 1730 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-06-01 → 2026-06-30; invalid=0; `Thời gian tạo`: 2026-06-01 → 2026-06-30; invalid=0
- **DanhSachHoaDon.xlsx** / `T07-2026` — 743 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-07-01 → 2026-07-13; invalid=0; `Thời gian tạo`: 2026-07-01 → 2026-07-13; invalid=0
- **DanhSachHoaDonChiTiet.xlsx** / `Sheet1` — 65731 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Mã hàng` · `Tên hàng` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `STT`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Raw duplicate excess rows: 1908 (không tự loại).
- **DanhSachHoaDonChiTietLo.xlsx** / `Sheet1` — 65483 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `STT` · `Lô` · `Số lượng (ĐVT cơ bản)` · `Số lượng trả (ĐVT cơ bản)`
  - Grain (verified): phân bổ một dòng bán cho một lô; một dòng bán có thể lấy nhiều lô.
- **DanhSachKhachHang.xlsx** / `Sheet1` — 300 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Công ty` · `Tổng điểm` · `Mã khách hàng` · `Ghi chú KH` · `Ngày sinh` · `Tên khách hàng` · `Người tạo` · `Đối tượng KH` · `Điểm tích lũy` · `Điện thoại` · `MST` · `Địa chỉ`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `Ngày sinh`: 1965-07-19 → 2002-01-17; invalid=0
- **DanhSachLoHang.xlsx** / `Sheet1` — 3122 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `Mã hàng` · `Lô` · `Hạn sử dụng` · `Số lượng (ĐVT cơ bản)`
  - Grain (verified): một lô nhập; mã lô không trùng trong business.
  - Dates: `Hạn sử dụng`: 2025-03-07 → 2029-06-12; invalid=0
- **DanhSachNhapHang.xlsx** / `Sheet1` — 554 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
  - Dates: `Thời gian`: 2025-01-01 → 2026-07-13; invalid=0
- **DanhSachSanPham.xlsx** / `Sheet1` — 70 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Trọng lượng` · `Mã hàng` · `Loại hàng hóa` · `Tên hàng` · `Tồn nhỏ nhất` · `Bảo hành` · `Ghi chú` · `Được bán trực tiếp` · `Mẫu ghi chú` · `Nhóm hàng(3 Cấp)` · `Vị trí kệ` · `Mô tả chi tiết` · `Thuộc tính` · `Hình ảnh (url1,url2...)` · `Giá bán` · `ĐVT` · `Mã HH Liên quan` · `Thương hiệu` · `Mã vạch EAN` · `Tồn lớn nhất`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **DanhSachThuoc.xlsx** / `Sheet1` — 70 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Hoạt chất` · `Thuốc kê đơn`
  - Grain (verified): thuộc tính thuốc của một mã hàng.

### biz_120

README: `data/biz_120/README.md`; 10 data files; 27 tables; 73 measured join candidates.

- **BaoCaoTonKho.xlsx** / `Sheet1` — 80 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.
- **DanhSachChiTietNhapHang.xlsx** / `Sheet1` — 3866 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá` · `Lô` · `Hạn sử dụng`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
  - Dates: `Hạn sử dụng`: 2025-03-03 → 2029-05-28; invalid=0
- **DanhSachHoaDon.xlsx** / `01.2025` — 2584 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-01-01 → 2025-01-31; invalid=0; `Thời gian tạo`: 2025-01-01 → 2025-01-31; invalid=0
- **DanhSachHoaDon.xlsx** / `02.2025` — 2459 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-02-01 → 2025-02-28; invalid=0; `Thời gian tạo`: 2025-02-01 → 2025-02-28; invalid=0
- **DanhSachHoaDon.xlsx** / `03.2025` — 2760 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-03-01 → 2025-03-31; invalid=0; `Thời gian tạo`: 2025-03-01 → 2025-03-31; invalid=0
- **DanhSachHoaDon.xlsx** / `04.2025` — 2577 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-04-01 → 2025-04-30; invalid=0; `Thời gian tạo`: 2025-04-01 → 2025-04-30; invalid=0
- **DanhSachHoaDon.xlsx** / `05.2025` — 2698 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-05-01 → 2025-05-31; invalid=0; `Thời gian tạo`: 2025-05-01 → 2025-05-31; invalid=0
- **DanhSachHoaDon.xlsx** / `06.2025` — 2653 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-06-01 → 2025-06-30; invalid=0; `Thời gian tạo`: 2025-06-01 → 2025-06-30; invalid=0
- **DanhSachHoaDon.xlsx** / `07.2025` — 2783 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-07-01 → 2025-07-31; invalid=0; `Thời gian tạo`: 2025-07-01 → 2025-07-31; invalid=0
- **DanhSachHoaDon.xlsx** / `08.2025` — 2709 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-08-01 → 2025-08-31; invalid=0; `Thời gian tạo`: 2025-08-01 → 2025-08-31; invalid=0
- **DanhSachHoaDon.xlsx** / `09.2025` — 2797 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-09-01 → 2025-09-30; invalid=0; `Thời gian tạo`: 2025-09-01 → 2025-09-30; invalid=0
- **DanhSachHoaDon.xlsx** / `10.2025` — 2785 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-10-01 → 2025-10-31; invalid=0; `Thời gian tạo`: 2025-10-01 → 2025-10-31; invalid=0
- **DanhSachHoaDon.xlsx** / `11.2025` — 2820 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-11-01 → 2025-11-30; invalid=0; `Thời gian tạo`: 2025-11-01 → 2025-11-30; invalid=0
- **DanhSachHoaDon.xlsx** / `12.2025` — 2884 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-12-01 → 2025-12-31; invalid=0; `Thời gian tạo`: 2025-12-01 → 2025-12-31; invalid=0
- **DanhSachHoaDon.xlsx** / `01.2026` — 3003 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-01-01 → 2026-01-31; invalid=0; `Thời gian tạo`: 2026-01-01 → 2026-01-31; invalid=0
- **DanhSachHoaDon.xlsx** / `02.2026` — 2817 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-02-01 → 2026-02-28; invalid=0; `Thời gian tạo`: 2026-02-01 → 2026-02-28; invalid=0
- **DanhSachHoaDon.xlsx** / `03.2026` — 3001 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-03-01 → 2026-03-31; invalid=0; `Thời gian tạo`: 2026-03-01 → 2026-03-31; invalid=0
- **DanhSachHoaDon.xlsx** / `04.2026` — 2909 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-04-01 → 2026-04-30; invalid=0; `Thời gian tạo`: 2026-04-01 → 2026-04-30; invalid=0
- **DanhSachHoaDon.xlsx** / `05.2026` — 3054 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-05-01 → 2026-05-31; invalid=0; `Thời gian tạo`: 2026-05-01 → 2026-05-31; invalid=0
- **DanhSachHoaDon.xlsx** / `06.2026` — 1096 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-06-01 → 2026-06-12; invalid=0; `Thời gian tạo`: 2026-06-01 → 2026-06-12; invalid=0
- **DanhSachHoaDonChiTiet.xlsx** / `Sheet1` — 90706 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Mã hàng` · `Tên hàng` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
- **DanhSachHoaDonChiTietLo.xlsx** / `Sheet1` — 92759 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `STT` · `Lô` · `Số lượng (ĐVT cơ bản)` · `Số lượng trả (ĐVT cơ bản)`
  - Grain (verified): phân bổ một dòng bán cho một lô; một dòng bán có thể lấy nhiều lô.
- **DanhSachKhachHang.xlsx** / `Sheet1` — 350 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã khách hàng` · `Ghi chú` · `Mã số thuế` · `Tên khách hàng` · `Người tạo` · `CCCD` · `Ngày sinh` · `E-mail` · `Đối tượng KH` · `Tên công ty` · `Điện thoại` · `Địa chỉ`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `Ngày sinh`: 1965-02-03 → 2003-11-24; invalid=0
- **DanhSachLoHang.xlsx** / `Sheet1` — 3866 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `Mã hàng` · `Lô` · `Hạn sử dụng` · `Số lượng (ĐVT cơ bản)`
  - Grain (verified): một lô nhập; mã lô không trùng trong business.
  - Dates: `Hạn sử dụng`: 2025-03-03 → 2029-05-28; invalid=0
- **DanhSachNhapHang.xlsx** / `Sheet1` — 526 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
  - Dates: `Thời gian`: 2025-01-01 → 2026-06-12; invalid=0
- **DanhSachSanPham.xlsx** / `Sheet1` — 80 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Trọng lượng` · `Mã hàng` · `Định mức tồn tối thiểu` · `Tên hàng` · `Mô tả chi tiết` · `Nhóm hàng(3 Cấp)` · `Mẫu ghi chú` · `Định mức tồn tối đa` · `Được bán trực tiếp` · `Bảo hành` · `Mã HH Liên quan` · `Giá bán` · `Loại hàng hóa` · `ĐVT` · `Giá vốn` · `Hình ảnh` · `Thời gian tạo`
  - Grain (verified): một bản ghi danh mục sản phẩm.
  - Dates: `Thời gian tạo`: 2023-02-02 → 2024-12-24; invalid=0
- **DanhSachThuoc.xlsx** / `Sheet1` — 80 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Hoạt chất` · `Thuốc kê đơn`
  - Grain (verified): thuộc tính thuốc của một mã hàng.

### biz_121

README: `data/biz_121/README.md`; 2 data files; 7 tables; 2 measured join candidates.

- **DonHang_ChiTiet.xlsx** / `Sheet1` — 82920 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-03-01 → 2026-09-20; invalid=0
  - Raw duplicate excess rows: 35380 (không tự loại).
- **DuLieuXuat.xlsx** / `DanhSachQuyDoi` — 83 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
  - Grain (verified): one unit conversion per product name + selling unit.
- **DuLieuXuat.xlsx** / `DanhSachSanPham` — 80 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Vị trí` · `Ghi chú` · `Mã SKU` · `Bảo hành` · `Thương hiệu` · `Mẫu ghi chú` · `Tên sản phẩm` · `Trọng lượng` · `Mã barcode` · `Đơn vị` · `Mã HH Liên quan` · `Tồn lớn nhất` · `Hình ảnh (url1,url2...)` · `Thuộc tính` · `Mô tả chi tiết` · `Loại sản phẩm` · `Loại hàng hóa`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **DuLieuXuat.xlsx** / `DonNhapHang` — 566 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn nhập` · `Ngày nhập` · `Mã nhà cung cấp`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
  - Dates: `Ngày nhập`: 2025-03-01 → 2026-09-20; invalid=0
- **DuLieuXuat.xlsx** / `DonNhapHang_ChiTiet` — 3665 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn nhập` · `Mã SKU` · `Mã lô` · `Hạn sử dụng` · `Số lượng nhập`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
  - Dates: `Hạn sử dụng`: 2025-04-30 → 2029-09-04; invalid=0
- **DuLieuXuat.xlsx** / `DonHang_Lo` — 84745 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Mã lô` · `Số lượng` · `Số lượng trả`
  - Grain (verified): phân bổ đơn–lô (không có khóa dòng hàng); nối chi tiết bán chỉ bằng mã đơn sẽ fan-out.
- **DuLieuXuat.xlsx** / `DanhSachThuoc` — 80 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã SKU` · `Hoạt chất` · `Thuốc kê đơn`
  - Grain (verified): thuộc tính thuốc của một mã hàng.

### biz_122

README: `data/biz_122/README.md`; 9 data files; 26 tables; 130 measured join candidates.

- **DanhSachQuyDoi.xlsx** / `Sheet1` — 83 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
  - Grain (verified): one unit conversion per product name + selling unit.
- **DanhSachSanPham.xlsx** / `Sheet1` — 75 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ghi chú` · `Mô tả sản phẩm` · `Tồn lớn nhất` · `Vị trí` · `Mã SKU` · `Mã HH Liên quan` · `Thương hiệu` · `Thuộc tính` · `Tên sản phẩm` · `Hình ảnh` · `Trọng lượng` · `Mã vạch EAN` · `Bảo hành` · `Đơn vị` · `Định mức tồn tối thiểu` · `Loại hàng hóa` · `Mẫu ghi chú` · `Loại sản phẩm`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **DanhSachThuoc.xlsx** / `Sheet1` — 75 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã SKU` · `Hoạt chất` · `Thuốc kê đơn`
  - Grain (verified): thuộc tính thuốc của một mã hàng.
- **DonHang_ChiTiet_1.xlsx** / `T01-2025` — 5516 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-01-01 → 2025-01-31; invalid=0
  - Raw duplicate excess rows: 1338 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T02-2025` — 4909 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-02-01 → 2025-02-28; invalid=0
  - Raw duplicate excess rows: 1121 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T03-2025` — 5355 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-03-01 → 2025-03-31; invalid=0
  - Raw duplicate excess rows: 1291 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T04-2025` — 5080 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-04-01 → 2025-04-30; invalid=0
  - Raw duplicate excess rows: 1148 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T05-2025` — 5600 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-05-01 → 2025-05-31; invalid=0
  - Raw duplicate excess rows: 1386 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T06-2025` — 5427 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-06-01 → 2025-06-30; invalid=0
  - Raw duplicate excess rows: 1326 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T07-2025` — 5446 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-07-01 → 2025-07-31; invalid=0
  - Raw duplicate excess rows: 1260 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T08-2025` — 5437 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-08-01 → 2025-08-31; invalid=0
  - Raw duplicate excess rows: 1303 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T09-2025` — 5635 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-09-01 → 2025-09-30; invalid=0
  - Raw duplicate excess rows: 1399 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T10-2025` — 5571 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-10-01 → 2025-10-31; invalid=0
  - Raw duplicate excess rows: 1329 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T11-2025` — 5588 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-11-01 → 2025-11-30; invalid=0
  - Raw duplicate excess rows: 1344 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T12-2025` — 5698 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2025-12-01 → 2025-12-31; invalid=0
  - Raw duplicate excess rows: 1392 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T01-2026` — 5827 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-01-01 → 2026-01-31; invalid=0
  - Raw duplicate excess rows: 1420 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T02-2026` — 5552 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-02-01 → 2026-02-28; invalid=0
  - Raw duplicate excess rows: 1364 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T03-2026` — 6018 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-03-01 → 2026-03-31; invalid=0
  - Raw duplicate excess rows: 1550 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T04-2026` — 5815 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-04-01 → 2026-04-30; invalid=0
  - Raw duplicate excess rows: 1415 (không tự loại).
- **DonHang_ChiTiet_1.xlsx** / `T05-2026` — 6004 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-05-01 → 2026-05-31; invalid=0
  - Raw duplicate excess rows: 1502 (không tự loại).
- **DonHang_ChiTiet_2026.xlsx** / `T06-2026` — 5751 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-06-01 → 2026-06-30; invalid=0
  - Raw duplicate excess rows: 1414 (không tự loại).
- **DonHang_ChiTiet_2026.xlsx** / `T07-2026` — 3434 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - Grain (verified): one sales line; order attributes can repeat.
  - Dates: `Ngày đặt hàng`: 2026-07-01 → 2026-07-17; invalid=0
  - Raw duplicate excess rows: 673 (không tự loại).
- **DonHang_Lo_1.xlsx** / `Sheet1` — 100000 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Mã lô` · `Số lượng` · `Số lượng trả`
  - Grain (verified): phân bổ đơn–lô (không có khóa dòng hàng); nối chi tiết bán chỉ bằng mã đơn sẽ fan-out.
- **DonHang_Lo_2.xlsx** / `Sheet1` — 5799 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `Mã lô` · `Số lượng` · `Số lượng trả`
  - Grain (verified): phân bổ đơn–lô (không có khóa dòng hàng); nối chi tiết bán chỉ bằng mã đơn sẽ fan-out.
- **DonNhapHang.xlsx** / `Sheet1` — 560 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn nhập` · `Ngày nhập` · `Mã nhà cung cấp`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
  - Dates: `Ngày nhập`: 2025-01-01 → 2026-07-17; invalid=0
- **DonNhapHang_ChiTiet.xlsx** / `Sheet1` — 4051 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn nhập` · `Mã SKU` · `Mã lô` · `Hạn sử dụng` · `Số lượng nhập`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
  - Dates: `Hạn sử dụng`: 2025-03-07 → 2029-07-12; invalid=0

### biz_123

README: `data/biz_123/README.md`; 1 data files; 17 tables; 44 measured join candidates.

- **pos.sqlite** / `chi_nhanh` — 1 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaChiNhanh` · `TenGoi` · `DiaChiLienHe` · `NgayKhaiTruong`
  - Grain (verified): một chi nhánh.
  - Dates: `NgayKhaiTruong`: 2021-08-15 → 2021-08-15; invalid=0
- **pos.sqlite** / `chi_tiet_don` — 64149 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaHoaDon` · `SoThuTu` · `MaHangHoa` · `DonViTinh` · `SL` · `SLQuyDoi` · `GiaDonVi` · `ChietKhau` · `TriGia` · `GiaVonLucBan`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Raw duplicate excess rows: 1208 (không tự loại).
- **pos.sqlite** / `chi_tiet_don_lo` — 64422 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaHoaDon` · `SoThuTu` · `MaLo` · `SLQuyDoi` · `SLTraQuyDoi`
  - Grain (verified): allocation of one sales line to a lot; a line can use multiple lots.
- **pos.sqlite** / `chi_tiet_nhap` — 2953 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaPhieuNhap` · `SoThuTu` · `MaHangHoa` · `DonViTinh` · `SL` · `DonGiaNhap` · `MaLo` · `HanSuDung`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
  - Dates: `HanSuDung`: 2025-03-02 → 2029-06-05; invalid=0
- **pos.sqlite** / `don_hang` — 33630 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaHoaDon` · `MaChiNhanh` · `MaKhachHang` · `MaNhanVien` · `MaCaLam` · `KenhBanHang` · `ThoiGianLap` · `NgayLap` · `TinhTrang` · `TongTienHang` · `ChietKhau` · `PhiVanChuyen` · `ThueGTGT` · `TongThanhToan` · `KhachDaTra` · `ConPhaiThu` · `PhuongThucTT` · `SoHoaDonDienTu` · `TinhTrangHDDT` · `MaKhuyenMai` · `DienGiai`
  - Grain (verified): one order.
  - Dates: `ThoiGianLap`: 2025-01-01 → 2026-06-28; invalid=0; `NgayLap`: 2025-01-01 → 2026-06-28; invalid=0
- **pos.sqlite** / `don_vi_sp` — 83 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaHangHoa` · `DonViTinh` · `HeSoQuyDoi` · `GiaDonVi`
  - Grain (verified): một hệ số quy đổi theo sản phẩm và đơn vị bán/đơn vị lớn.
- **pos.sqlite** / `khach_hang` — 300 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `trang_thai_kh` · `cccd` · `IDCuaHang` · `diem_hien_tai` · `MaKhachHang` · `ghi_chu_kh` · `ngay_sinh` · `email` · `TenGoi` · `SoDienThoai` · `NamNu` · `nguoi_tao` · `LoaiKhachHang` · `cong_ty` · `tong_diem` · `TaoLuc` · `loai_hinh_kh` · `DiaChiLienHe`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `ngay_sinh`: 1965-09-28 → 2004-12-03; invalid=0
- **pos.sqlite** / `lich_su_gia` — 109 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaHangHoa` · `NgayApDung` · `GiaBanLe`
  - Grain (verified): product price effective from date until next change.
  - Dates: `NgayApDung`: 2025-01-01 → 2026-05-21; invalid=0
- **pos.sqlite** / `lo_hang` — 2953 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaHangHoa` · `MaLo` · `MaPhieuNhap` · `HanSuDung` · `SLNhapQuyDoi` · `DonGiaNhap`
  - Grain (verified): one received lot.
  - Dates: `HanSuDung`: 2025-03-02 → 2029-06-05; invalid=0
- **pos.sqlite** / `nha_cung_cap` — 5 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaNhaCungCap` · `TenGoi` · `SoDienThoai` · `DiaChiLienHe`
  - Grain (verified): một nhà cung cấp.
- **pos.sqlite** / `nhan_vien` — 3 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaNhanVien` · `TenGoi` · `MaChiNhanh` · `ChucVu` · `NgayNhanViec` · `NgayThoiViec`
  - Grain (verified): một nhân viên.
  - Dates: `NgayNhanViec`: 2022-08-28 → 2024-03-24; invalid=0; `NgayThoiViec`: None → None; invalid=0
- **pos.sqlite** / `phieu_nhap` — 540 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaPhieuNhap` · `MaNhaCungCap` · `MaChiNhanh` · `NgayNhapKho` · `TinhTrang` · `TongGiaTriNhap` · `DienGiai`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
  - Dates: `NgayNhapKho`: 2025-01-01 → 2026-06-28; invalid=0
- **pos.sqlite** / `san_pham` — 80 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `hinh_anh` · `ma_vach_ean` · `bao_hanh` · `ban_truc_tiep` · `IDCuaHang` · `MaHangHoa` · `ghi_chu_hh` · `vi_tri` · `TenGoi` · `DanhMuc` · `loai_hang_hoa` · `ton_nho_nhat` · `thuong_hieu` · `DonViCoSo` · `GiaBanLe` · `GiaVonHang` · `mau_ghi_chu` · `mo_ta` · `TyLeThue` · `ConKinhDoanh` · `TaoLuc` · `ton_lon_nhat`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **pos.sqlite** / `thanh_toan` — 33816 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaPhieuThu` · `MaHoaDon` · `NgayGioThu` · `SoTienThu` · `PhuongThuc` · `DienGiai`
  - Grain (verified): one payment event (not one order).
  - Dates: `NgayGioThu`: 2025-01-01 → 2026-06-28; invalid=0
- **pos.sqlite** / `the_kho` — 65514 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaGiaoDichKho` · `MaHangHoa` · `MaChiNhanh` · `NgayGioPhatSinh` · `LoaiGiaoDich` · `SLQuyDoi` · `KieuChungTu` · `MaChungTu` · `TonCuoi`
  - Grain (verified): one inventory movement with post-movement balance.
  - Dates: `NgayGioPhatSinh`: 2025-01-01 → 2026-06-28; invalid=0
- **pos.sqlite** / `thong_tin_thuoc` — 80 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaHangHoa` · `ThanhPhanChinh` · `BanTheoDon`
  - Grain (verified): thuộc tính thuốc của một mã hàng.
- **pos.sqlite** / `tra_hang` — 273 data rows; header: SQLite schema (verified); status: `verified`.
  - Columns: `IDCuaHang` · `MaPhieuTra` · `MaHoaDon` · `NgayGioTra` · `NguyenNhan` · `TienHoanTra` · `CachHoanTien`
  - Grain (verified): một phiếu trả hàng tham chiếu đơn.
  - Dates: `NgayGioTra`: 2025-01-05 → 2026-06-28; invalid=0

### biz_124

README: `data/biz_124/README.md`; 13 data files; 13 tables; 0 measured join candidates.

- **BanHang_BanTheoLo.xlsx** / `Sheet1` — 97880 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Lô` · `SL quy ra lẻ` · `SL trả (ĐVT cơ bản)` · `No.` · `Mã hóa đơn`
  - Grain (verified): phân bổ một dòng bán cho một lô; một dòng bán có thể lấy nhiều lô.
- **BanHang_ChiTietHoaDon.xlsx** / `Sheet1` — 97033 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Giá vốn lúc bán` · `SL cơ bản` · `Khuyến mãi` · `Giá niêm yết` · `Thanh tien` · `Mã giao dịch` · `Chi tiết hàng` · `Slg` · `TT dòng` · `Ma hang` · `Đ.vị`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Raw duplicate excess rows: 1188 (không tự loại).
- **BanHang_DonViQuyDoi.xlsx** / `Sheet1` — 83 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Đơn vị` · `Bằng` · `Giá bán theo đơn vị quy đổi` · `Mã sp`
  - Grain (verified): một hệ số quy đổi theo sản phẩm và đơn vị bán/đơn vị lớn.
- **BanHang_HangHoa.xlsx** / `Sheet1` — 80 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Định mức tồn tối thiểu` · `Giá vốn hiện tại` · `Thương hiệu` · `Thuộc tính` · `Phân loại` · `Món` · `Được bán trực tiếp` · `Mã HH Liên quan` · `ma_sp` · `Mô tả sản phẩm` · `Mẫu ghi chú` · `Giá` · `Ghi chú` · `Đơn vị` · `Trọng lượng` · `Loại hàng hóa`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **BanHang_HoaDon.xlsx** / `Sheet1` — 51044 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Đã thu` · `Tên KH` · `Trạng thái` · `Giờ tạo đơn` · `Mã NV bán` · `Phương thức TT` · `Ngày bán` · `Nguồn đơn` · `Còn nợ` · `Mã KH mua` · `Tiền hàng trước giảm` · `Tong tien` · `Order ID` · `CK`
  - Grain (verified): một đơn hàng; ngày và tổng tiền ở cấp đơn.
  - Dates: `Ngày bán`: 2025-01-01 → 2026-05-25; invalid=0
- **BanHang_KhachHang.xlsx** / `Sheet1` — 380 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Điểm tích lũy` · `Công ty` · `Hạng` · `E-mail` · `MST` · `Ngày sinh` · `CCCD` · `Trạng thái` · `ten_kh` · `Người tạo` · `Ghi chú` · `Tổng điểm` · `Loại hình khách` · `Số điện thoại` · `Customer ID`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `Ngày sinh`: 1965-05-23 → 2003-06-17; invalid=0
- **BanHang_LichSuGia.xlsx** / `Sheet1` — 114 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã sản phẩm` · `Giá mới` · `Ngày áp dụng` · `Sản phẩm` · `Giá cũ`
  - Grain (verified): một mốc giá của sản phẩm; hiệu lực đến trước lần đổi sau, cần temporal join.
  - Dates: `Ngày áp dụng`: 2025-01-01 → 2026-04-28; invalid=0
- **BanHang_LoHang.xlsx** / `Sheet1` — 3943 data rows; header: 1 (verified); status: `verified`.
  - Columns: `HSD` · `Mã món` · `SL nhập (ĐVT cơ bản)` · `Mã phiếu nhập` · `Lô`
  - Grain (verified): một lô nhập; mã lô không trùng trong business.
- **BanHang_PhieuThu.xlsx** / `Sheet1` — 51238 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Số tiền thu` · `Mã bill` · `Phiếu thu` · `Thời gian thu` · `PTTT`
  - Grain (verified): one payment event (not one order).
- **BanHang_Thuoc.xlsx** / `Sheet1` — 80 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã HH` · `Hoạt chất` · `Kê đơn`
  - Grain (verified): thuộc tính thuốc của một mã hàng.
- **SoTay_ChiPhi.xlsx** / `Sheet1` — 75 data rows; header: 3 (verified); status: `verified`.
  - Columns: `Ghi chú` · `Ngày chi` · `Mục` · `So tien`
  - Grain (verified): một khoản ghi sổ chi phí; không loại dòng giống nhau khi không có mã đơn.
  - Dates: `Ngày chi`: 2025-01-01 → 2026-05-22; invalid=0
- **SoTay_NhapHang.xlsx** / `Sheet1` — 3943 data rows; header: 3 (verified); status: `verified`.
  - Columns: `SL nhập` · `Mô tả` · `Product` · `Thành tiền` · `Lô` · `HSD` · `Ngày nhập` · `Nhà cung cấp` · `ĐVT nhập` · `Số phiếu` · `Giá nhập`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
  - Dates: `Ngày nhập`: 2025-01-01 → 2026-05-25; invalid=0
- **ton_kho.csv** — 80 data rows; header: 1 (verified); status: `verified`.
  - Columns: `ID SP` · `Đơn vị` · `Ton kho` · `Hàng hóa`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.

### biz_125

README: `data/biz_125/README.md`; 1 data files; 1 tables; 0 measured join candidates.

- **ban_hang.csv** — 79052 data rows; header: 1 (verified); status: `verified`.
  - Columns: `dvt` · `Hàng bán` · `Khách hàng (tên)` · `Số lượng lẻ` · `Amount` · `Trạng thái xử lý` · `SL bán` · `Ngày bán` · `Số phiếu` · `Giá 1 đv`
  - Grain (verified): one sales line in an order.
  - Dates: `Ngày bán`: 2025-01-01 → 2026-05-11; invalid=0

### biz_126

README: `data/biz_126/README.md`; 1 data files; 1 tables; 0 measured join candidates.

- **SoBanHang.xlsx** / `Sheet1` — 66429 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Đơn vị tính` · `Số lượng bán` · `Thành tiền (đ)` · `Ten hang` · `SL lẻ` · `Trạng thái đơn` · `Ngày tháng` · `Price`
  - Grain (verified): one recorded item purchase; no order/customer ID.
  - Dates: `Ngày tháng`: 2025-01-01 → 2026-06-06; invalid=0
  - Raw duplicate excess rows: 5713 (không tự loại).

### biz_127

README: `data/biz_127/README.md`; 5 data files; 5 tables; 5 measured join candidates.

- **chi_tiet_don.csv** — 131192 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã đơn hàng` · `SoLuong` · `No.` · `DVT` · `Amount` · `Số lượng lẻ` · `Mã mặt hàng` · `Đơn giá (đ)`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Raw duplicate excess rows: 2899 (không tự loại).
- **don_hang.csv** — 33874 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Còn nợ` · `Diễn giải` · `Tổng đơn` · `Loại bán` · `Ngày` · `Mã chứng từ` · `Customer ID` · `Khách trả` · `Trả bằng` · `Tình trạng`
  - Grain (verified): one order.
  - Dates: `Ngày`: 2025-03-01 → 2026-07-28; invalid=0
- **khach_hang.csv** — 200 data rows; header: 1 (verified); status: `verified`.
  - Columns: `CCCD` · `Tên công ty` · `Di động` · `Email` · `Sinh nhật` · `Người tạo` · `Tổng điểm` · `Loại hình khách` · `Mã KH` · `Khách hàng (tên)` · `Điểm hiện tại` · `MST` · `Trạng thái` · `Ghi chú`
  - Grain (verified): một bản ghi danh mục khách theo mã.
- **san_pham.csv** — 61 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Trọng lượng` · `Giá niêm yết` · `Mô tả chi tiết` · `Danh mục` · `Ghi chú` · `Mã sản phẩm bán` · `Tên SP` · `Mẫu ghi chú` · `Mã barcode` · `Loại hàng hóa` · `Tồn lớn nhất` · `Thương hiệu` · `Thuộc tính` · `Hình ảnh (url1,url2...)` · `Đơn vị cơ bản` · `Được bán trực tiếp` · `Mã HH Liên quan`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **thanh_toan.csv** — 33473 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Số CT` · `Ngày thu` · `Mã GD` · `Giá trị` · `HTTT`
  - Grain (verified): one payment event (not one order).
  - Dates: `Ngày thu`: 2025-03-01 → 2026-07-28; invalid=0

### biz_128

README: `data/biz_128/README.md`; 8 data files; 25 tables; 62 measured join candidates.

- **BaoCaoTonKho.xlsx** / `Sheet1` — 55 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
  - Grain (verified): snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn.
- **DanhSachChiTietNhapHang.xlsx** / `Sheet1` — 1454 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá`
  - Grain (verified): một dòng hàng nhập; không cộng lặp tổng tiền phiếu.
- **DanhSachHoaDon.xlsx** / `04.2025` — 1537 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-04-01 → 2025-04-30; invalid=0; `Thời gian tạo`: 2025-04-01 → 2025-04-30; invalid=0
- **DanhSachHoaDon.xlsx** / `05.2025` — 1524 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-05-01 → 2025-05-31; invalid=0; `Thời gian tạo`: 2025-05-01 → 2025-05-31; invalid=0
- **DanhSachHoaDon.xlsx** / `06.2025` — 1389 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-06-01 → 2025-06-30; invalid=0; `Thời gian tạo`: 2025-06-01 → 2025-06-30; invalid=0
- **DanhSachHoaDon.xlsx** / `07.2025` — 1575 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-07-01 → 2025-07-31; invalid=0; `Thời gian tạo`: 2025-07-01 → 2025-07-31; invalid=0
- **DanhSachHoaDon.xlsx** / `08.2025` — 1555 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-08-01 → 2025-08-31; invalid=0; `Thời gian tạo`: 2025-08-01 → 2025-08-31; invalid=0
- **DanhSachHoaDon.xlsx** / `09.2025` — 1539 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-09-01 → 2025-09-30; invalid=0; `Thời gian tạo`: 2025-09-01 → 2025-09-30; invalid=0
- **DanhSachHoaDon.xlsx** / `10.2025` — 1596 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-10-01 → 2025-10-31; invalid=0; `Thời gian tạo`: 2025-10-01 → 2025-10-31; invalid=0
- **DanhSachHoaDon.xlsx** / `11.2025` — 1457 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-11-01 → 2025-11-30; invalid=0; `Thời gian tạo`: 2025-11-01 → 2025-11-30; invalid=0
- **DanhSachHoaDon.xlsx** / `12.2025` — 1573 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2025-12-01 → 2025-12-31; invalid=0; `Thời gian tạo`: 2025-12-01 → 2025-12-31; invalid=0
- **DanhSachHoaDon.xlsx** / `01.2026` — 1615 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-01-01 → 2026-01-31; invalid=0; `Thời gian tạo`: 2026-01-01 → 2026-01-31; invalid=0
- **DanhSachHoaDon.xlsx** / `02.2026` — 1001 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-02-01 → 2026-02-28; invalid=0; `Thời gian tạo`: 2026-02-01 → 2026-02-28; invalid=0
- **DanhSachHoaDon.xlsx** / `03.2026` — 1611 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-03-01 → 2026-03-31; invalid=0; `Thời gian tạo`: 2026-03-01 → 2026-03-31; invalid=0
- **DanhSachHoaDon.xlsx** / `04.2026` — 1602 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-04-01 → 2026-04-30; invalid=0; `Thời gian tạo`: 2026-04-01 → 2026-04-30; invalid=0
- **DanhSachHoaDon.xlsx** / `05.2026` — 1601 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-05-01 → 2026-05-31; invalid=0; `Thời gian tạo`: 2026-05-01 → 2026-05-31; invalid=0
- **DanhSachHoaDon.xlsx** / `06.2026` — 1592 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-06-01 → 2026-06-30; invalid=0; `Thời gian tạo`: 2026-06-01 → 2026-06-30; invalid=0
- **DanhSachHoaDon.xlsx** / `07.2026` — 1684 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-07-01 → 2026-07-31; invalid=0; `Thời gian tạo`: 2026-07-01 → 2026-07-31; invalid=0
- **DanhSachHoaDon.xlsx** / `08.2026` — 1690 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-08-01 → 2026-08-31; invalid=0; `Thời gian tạo`: 2026-08-01 → 2026-08-31; invalid=0
- **DanhSachHoaDon.xlsx** / `09.2026` — 364 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - Grain (verified): one order.
  - Dates: `Thời gian`: 2026-09-01 → 2026-09-07; invalid=0; `Thời gian tạo`: 2026-09-01 → 2026-09-07; invalid=0
- **DanhSachHoaDonChiTiet.xlsx** / `Sheet1` — 99650 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Mã hàng` · `Tên hàng` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `STT`
  - Grain (verified): một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8.
  - Raw duplicate excess rows: 1143 (không tự loại).
- **DanhSachHoaDonPhongBan.xlsx** / `Sheet1` — 23880 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hóa đơn` · `Phòng/Bàn` · `Khu vực` · `Số khách`
  - Grain (verified): one order.
- **DanhSachKhachHang.xlsx** / `Sheet1` — 180 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Sinh nhật` · `Người tạo` · `Mã khách hàng` · `Email` · `Tên khách hàng` · `Điện thoại` · `Nhóm khách hàng` · `Loại hình khách` · `Điểm hiện tại` · `CCCD` · `Ghi chú KH` · `Công ty` · `Địa chỉ` · `Trạng thái` · `Giới tính` · `MST` · `Tổng điểm`
  - Grain (verified): một bản ghi danh mục khách theo mã.
- **DanhSachNhapHang.xlsx** / `Sheet1` — 479 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
  - Grain (verified): một phiếu nhập; tổng giá trị là cấp phiếu.
  - Dates: `Thời gian`: 2025-04-01 → 2026-09-07; invalid=0
- **DanhSachSanPham.xlsx** / `Sheet1` — 56 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng` · `Tồn nhỏ nhất` · `Loại hàng hóa` · `Tồn lớn nhất` · `Tên hàng` · `Nhóm hàng(3 Cấp)` · `Ghi chú` · `Giá bán` · `Thương hiệu` · `Mã HH Liên quan` · `Mẫu ghi chú` · `Mã barcode` · `Vị trí` · `Thuộc tính` · `Hình ảnh` · `ĐVT` · `Mô tả chi tiết` · `Trọng lượng` · `Thời gian tạo`
  - Grain (verified): một bản ghi danh mục sản phẩm.
  - Dates: `Thời gian tạo`: 2023-05-09 → 2025-04-01; invalid=0

### biz_129

README: `data/biz_129/README.md`; 5 data files; 5 tables; 5 measured join candidates.

- **chi_tiet_don.csv** — 145479 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Tiền bán` · `TT dòng` · `S.L` · `Mã hàng bán` · `Quy ra ĐV lẻ` · `Số CT` · `Giảm giá` · `Giá 1 đv` · `ĐV tính`
  - Grain (verified): sales line identified by order + line (plus store where present).
- **don_hang.csv** — 38499 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Hình thức thanh toán` · `Dư nợ` · `Thanh toán` · `Tình trạng đơn` · `Số phiếu` · `Mã khách mua` · `Phải thu` · `Ngày bán`
  - Grain (verified): one order.
  - Dates: `Ngày bán`: 2025-01-01 → 2026-08-14; invalid=0
- **khach_hang.csv** — 220 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Ghi chú KH` · `Ngày sinh` · `Điểm hiện tại` · `Nhóm` · `Tổng điểm` · `KH` · `Email` · `Mã số thuế` · `Người tạo` · `Công ty` · `Số điện thoại` · `Số CMND/CCCD` · `Đối tượng KH` · `Trạng thái` · `Mã khách lẻ/sỉ`
  - Grain (verified): một bản ghi danh mục khách theo mã.
  - Dates: `Ngày sinh`: 1969-01-16 → 2004-07-28; invalid=0
- **san_pham.csv** — 61 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Bảo hành` · `Giá hiện tại` · `Mã vạch EAN` · `Mã HH Liên quan` · `Đơn vị tính` · `Tên sản phẩm` · `Vị trí kệ` · `Nhom hang` · `Mô tả chi tiết` · `Ghi chú` · `Mẫu ghi chú` · `Được bán trực tiếp` · `Mã HH` · `Loại hàng hóa` · `Thuộc tính` · `Thương hiệu` · `Hình ảnh` · `Định mức tồn tối đa`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **thanh_toan.csv** — 38072 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã GD` · `PTTT` · `Tiền` · `Mã giao dịch` · `Thời điểm`
  - Grain (verified): one payment event (not one order).
  - Dates: `Thời điểm`: 2025-01-01 → 2026-08-14; invalid=0

### biz_130

README: `data/biz_130/README.md`; 3 data files; 3 tables; 2 measured join candidates.
README/path conflicts (không đổi tên nguồn): {"missing": ["Danh sách hàng hóa.xlsx"], "extra": ["Danh s├ích h├áng h├│a.xlsx"], "unicode_matches": {"Danh s├ích h├áng h├│a.xlsx": "Danh sách hàng hóa.xlsx"}}

- **Danh s├ích h├áng h├│a.xlsx** / `Sheet1` — 61 data rows; header: 1 (verified); status: `verified`.
  - Columns: `Mã hàng hóa` · `Mô tả sản phẩm` · `Bảo hành` · `Được bán trực tiếp` · `Loại hàng hóa` · `Mã HH Liên quan` · `Mẫu ghi chú` · `Tên hàng hóa` · `Nhóm hàng hóa` · `Thương hiệu` · `Định mức tồn tối thiểu` · `Vị trí kệ` · `Đơn vị tính` · `Định mức tồn tối đa` · `Ghi chú` · `Giá vốn`
  - Grain (verified): một bản ghi danh mục sản phẩm.
- **So_chi_tiet_ban_hang_1.xlsx** / `Sheet1` — 100000 data rows; header: 4 (verified); status: `needs_review`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (needs_review): one sales line; order attributes can repeat; OBSERVED MIXED ROWS: 347 dòng mang nhãn tổng, cần xác minh bộ lọc.
  - Dates: `Ngày`: 2025-02-01 → 2026-01-03; invalid=0
- **So_chi_tiet_ban_hang_2.xlsx** / `Sheet1` — 72530 data rows; header: 4 (verified); status: `needs_review`.
  - Columns: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - Grain (needs_review): one sales line; order attributes can repeat; OBSERVED MIXED ROWS: 247 dòng mang nhãn tổng, cần xác minh bộ lọc.
  - Dates: `Ngày`: 2026-01-03 → 2026-08-29; invalid=0

## public_test

### dev_001

- **Danh s├ích h├áng h├│a.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Vị trí` · `Mã hàng hóa` · `Định mức tồn tối đa` · `Được bán trực tiếp` · `Ghi chú` · `Thuộc tính` · `Tên hàng hóa` · `Mã barcode` · `Mô tả sản phẩm` · `Mã HH Liên quan` · `Bảo hành` · `Nhóm hàng hóa` · `Đơn vị tính` · `Trọng lượng` · `Định mức tồn tối thiểu` · `Mẫu ghi chú` · `Giá bán` · `Hình ảnh` · `Giá vốn`
- **So_chi_tiet_ban_hang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`

### dev_002

- **BanHang_T10_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T11_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T12_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T1_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T1_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T2_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T2_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T3_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T3_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T4_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T4_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T5_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T5_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T6_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T7_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T8_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T9_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **DanhSachQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`

### dev_003

- **BanHang_PhieuThu.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `PTTT` · `Mã thanh toán` · `Ngày TT` · `Ma don` · `Tiền thu`
- **BanHang_TongHop_2025.xlsx** — 5 sheet(s)
  - `BanHang` (dimension unavailable); candidate header: `Đơn số` · `Phí ship` · `Công nợ` · `Tiền hàng trước giảm` · `Nguồn` · `Tiền giảm` · `Tổng thanh toán` · `Mã NV bán` · `Da tra` · `Ngày HĐ` · `Trạng thái giao` · `Giờ tạo đơn` · `Khách hàng (tên)` · `Mã khách` · `Hình thức thanh toán` · `SĐT` · `Dòng` · `ĐV` · `Hàng hóa` · `Giảm (đ)` · `Thành tiền (đ)` · `Giá 1 đv` · `Barcode` · `SL (ĐV cơ bản)` · `Giá vốn lúc bán` · `S.L`
  - `BanHang_HangHoa` (dimension unavailable); candidate header: `Thuộc tính` · `Trọng lượng` · `Nhóm hàng` · `Giá lẻ` · `Mã H.hóa` · `Được bán trực tiếp` · `Giá vốn hiện tại` · `Hình ảnh (url1,url2...)` · `DVT` · `Bảo hành` · `Mô tả sản phẩm` · `Loại hàng hóa` · `Tồn lớn nhất` · `Định mức tồn tối thiểu` · `Vị trí kệ` · `Mã barcode` · `Mẫu ghi chú` · `Tên hàng hóa`
  - `BanHang_KhachHang` (dimension unavailable); candidate header: `Người tạo` · `Email` · `SĐT` · `Địa chỉ` · `Khách hàng mua` · `Đối tượng KH` · `Ghi chú` · `Mã KH mua` · `MST` · `Kiểu khách` · `Tổng điểm` · `CCCD` · `Điểm hiện tại` · `Sinh nhật` · `Trạng thái` · `Công ty` · `Tra cứu thông tin bổ sung`
  - `BanHang_DonViQuyDoi` (dimension unavailable); candidate header: `Giá bán theo đơn vị quy đổi` · `Mã vạch` · `Bằng` · `Quy cách`
  - `BanHang_LichSuGia` (dimension unavailable); candidate header: `Giá cũ` · `Item` · `Mã H.hóa` · `Ngày áp dụng` · `Giá mới`
- **BanHang_TongHop_2026.xlsx** — 1 sheet(s)
  - `BanHang` (dimension unavailable); candidate header: `Đơn số` · `Phí ship` · `Công nợ` · `Tiền hàng trước giảm` · `Nguồn` · `Tiền giảm` · `Tổng thanh toán` · `Mã NV bán` · `Da tra` · `Ngày HĐ` · `Trạng thái giao` · `Giờ tạo đơn` · `Khách hàng (tên)` · `Mã khách` · `Hình thức thanh toán` · `SĐT` · `Dòng` · `ĐV` · `Hàng hóa` · `Giảm (đ)` · `Thành tiền (đ)` · `Giá 1 đv` · `Barcode` · `SL (ĐV cơ bản)` · `Giá vốn lúc bán` · `S.L`
- **BaoCaoCa.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày` · `Ca` · `Mã NV` · `Tiền mặt thu` · `Tiền mặt hoàn khách` · `Tiền mặt ròng của ca`
- **SoTay_ChiPhi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày mua` · `Lưu ý` · `Tiền chi` · `Nhóm`
- **SoTay_NhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Số phiếu` · `Product` · `Nhà cung cấp` · `Thành tiền` · `Lưu ý` · `Giá nhập` · `SL nhập` · `ĐVT nhập` · `Ngày nhập`
- **ton_kho.csv** — CSV, 50 data rows; columns: `Ton kho` · `ma_sp` · `ten_hang` · `ĐVT`

### dev_004

- **BangGia.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Giá cũ` · `Ngày áp dụng` · `Giá mới` · `Diễn giải`
- **DanhMuc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Hàng` · `Hệ số` · `ĐV gốc` · `Loại ĐV`
- **SoBanHang.xlsx** — 18 sheet(s)
  - `T01-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T02-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T03-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T04-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T05-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T06-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T07-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T08-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T09-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T10-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T11-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T12-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T01-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T02-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T03-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T04-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T05-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T06-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
- **SoGiaoHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Số lượng giao` · `Biển số xe` · `Lượt giao` · `Số đơn` · `Thời gian giao` · `Hàng hóa` · `Lái xe` · `ĐV gốc`
- **SoHanNo.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Kỳ hạn` · `Ngày phải trả`
- **SoNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Product` · `ĐVT` · `Số phiếu` · `Ghi chú` · `Nhà cung cấp` · `Thành tiền` · `Giá nhập` · `Ngày nhập` · `SL nhập`
- **TonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tồn cuối` · `ĐV gốc` · `Tên sản phẩm`

### dev_005

- **BanHang_Thang01_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang01_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang02_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang02_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang03_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang03_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang04_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang04_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang05_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang05_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang06_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang07_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang08_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang09_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang10_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang11_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang12_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **DanhSachQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
- **DanhSachSanPham.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Định mức tồn tối thiểu` · `Mã SKU` · `Được bán trực tiếp` · `Ghi chú` · `Mẫu ghi chú` · `Bảo hành` · `Tên sản phẩm` · `Mã HH Liên quan` · `Mô tả chi tiết` · `Thương hiệu` · `Tồn lớn nhất` · `Đơn vị` · `Thuộc tính` · `Mã vạch EAN` · `Loại sản phẩm` · `Trọng lượng` · `Vị trí` · `Loại hàng hóa`
- **DanhSachThuoc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã SKU` · `Hoạt chất` · `Thuốc kê đơn`
- **DonHang_Lo.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Mã lô` · `Số lượng` · `Số lượng trả`
- **DonNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn nhập` · `Ngày nhập` · `Mã nhà cung cấp`
- **DonNhapHang_ChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn nhập` · `Mã SKU` · `Mã lô` · `Hạn sử dụng` · `Số lượng nhập`

### dev_006

- **pos.sqlite** — SQLite
  - `chi_nhanh` (1 rows); columns: `IDCuaHang` · `MaChiNhanh` · `TenGoi` · `DiaChiLienHe` · `NgayKhaiTruong`
  - `chi_tiet_don` (72411 rows); columns: `IDCuaHang` · `MaHoaDon` · `SoThuTu` · `MaHangHoa` · `DonViTinh` · `SL` · `SLQuyDoi` · `GiaDonVi` · `ChietKhau` · `TriGia` · `GiaVonLucBan`
  - `chi_tiet_don_lo` (72710 rows); columns: `IDCuaHang` · `MaHoaDon` · `SoThuTu` · `MaLo` · `SLQuyDoi` · `SLTraQuyDoi`
  - `chi_tiet_nhap` (3234 rows); columns: `IDCuaHang` · `MaPhieuNhap` · `SoThuTu` · `MaHangHoa` · `DonViTinh` · `SL` · `DonGiaNhap` · `MaLo` · `HanSuDung`
  - `don_hang` (37833 rows); columns: `IDCuaHang` · `MaHoaDon` · `MaChiNhanh` · `MaKhachHang` · `MaNhanVien` · `MaCaLam` · `KenhBanHang` · `ThoiGianLap` · `NgayLap` · `TinhTrang` · `TongTienHang` · `ChietKhau` · `PhiVanChuyen` · `ThueGTGT` · `TongThanhToan` · `KhachDaTra` · `ConPhaiThu` · `PhuongThucTT` · `SoHoaDonDienTu` · `TinhTrangHDDT` · `MaKhuyenMai` · `DienGiai`
  - `don_vi_sp` (83 rows); columns: `IDCuaHang` · `MaHangHoa` · `DonViTinh` · `HeSoQuyDoi` · `GiaDonVi`
  - `khach_hang` (320 rows); columns: `IDCuaHang` · `MaKhachHang` · `TenGoi` · `trang_thai_kh` · `tong_diem` · `diem_hien_tai` · `loai_hinh_kh` · `cccd` · `SoDienThoai` · `email` · `ghi_chu_kh` · `NamNu` · `LoaiKhachHang` · `cong_ty` · `TaoLuc` · `ma_so_thue` · `DiaChiLienHe` · `nguoi_tao`
  - `lich_su_gia` (120 rows); columns: `IDCuaHang` · `MaHangHoa` · `NgayApDung` · `GiaBanLe`
  - `lo_hang` (3234 rows); columns: `IDCuaHang` · `MaHangHoa` · `MaLo` · `MaPhieuNhap` · `HanSuDung` · `SLNhapQuyDoi` · `DonGiaNhap`
  - `nha_cung_cap` (5 rows); columns: `email` · `IDCuaHang` · `nhom_ncc` · `MaNhaCungCap` · `ma_so_thue` · `nguoi_tao` · `trang_thai_ncc` · `TenGoi` · `SoDienThoai` · `DiaChiLienHe`
  - `nhan_vien` (3 rows); columns: `IDCuaHang` · `MaNhanVien` · `TenGoi` · `MaChiNhanh` · `ChucVu` · `NgayNhanViec` · `NgayThoiViec`
  - `phieu_nhap` (494 rows); columns: `IDCuaHang` · `MaPhieuNhap` · `MaNhaCungCap` · `MaChiNhanh` · `NgayNhapKho` · `TinhTrang` · `TongGiaTriNhap` · `DienGiai`
  - `san_pham` (80 rows); columns: `mo_ta` · `ghi_chu_hh` · `IDCuaHang` · `MaHangHoa` · `ma_hh_lien_quan` · `thuoc_tinh` · `ban_truc_tiep` · `mau_ghi_chu` · `vi_tri` · `trong_luong` · `ton_nho_nhat` · `TenGoi` · `ma_vach_ean` · `DanhMuc` · `DonViCoSo` · `GiaBanLe` · `hinh_anh` · `GiaVonHang` · `ton_lon_nhat` · `TyLeThue` · `bao_hanh` · `thuong_hieu` · `loai_hang_hoa` · `ConKinhDoanh` · `TaoLuc`
  - `thanh_toan` (37939 rows); columns: `IDCuaHang` · `MaPhieuThu` · `MaHoaDon` · `NgayGioThu` · `SoTienThu` · `PhuongThuc` · `DienGiai`
  - `the_kho` (73901 rows); columns: `IDCuaHang` · `MaGiaoDichKho` · `MaHangHoa` · `MaChiNhanh` · `NgayGioPhatSinh` · `LoaiGiaoDich` · `SLQuyDoi` · `KieuChungTu` · `MaChungTu` · `TonCuoi`
  - `thong_tin_thuoc` (80 rows); columns: `IDCuaHang` · `MaHangHoa` · `ThanhPhanChinh` · `BanTheoDon`
  - `tra_hang` (352 rows); columns: `IDCuaHang` · `MaPhieuTra` · `MaHoaDon` · `NgayGioTra` · `NguyenNhan` · `TienHoanTra` · `CachHoanTien`

### dev_007

- **chi_tiet_hoa_don.csv** — CSV, 121067 data rows; columns: `Bàn` · `Thành tiền` · `Nhóm khách hàng` · `Mặt hàng` · `Khu vực` · `Nguồn` · `Nội dung` · `Giờ bán` · `Giới tính` · `No.` · `Ngày giao dịch` · `Tiến độ` · `Trạng thái HĐĐT` · `Mã vạch` · `Khách trả` · `Họ tên khách` · `Mã khách mua` · `Còn nợ` · `Tiền giảm` · `Mã bill` · `Số khách` · `Sluong` · `Nhân viên bán` · `Phone` · `Tổng tiền hàng` · `Giảm giá HĐ` · `Addr` · `Phân loại` · `Số lượng lẻ` · `Đơn giá (đ)`
- **chi_tiet_nhap_hang.csv** — CSV, 1731 data rows; columns: `Mã NCC` · `Tổng tiền phiếu` · `SL nhập` · `Hàng hóa` · `STT` · `ĐVT nhập` · `Mã hàng bán` · `Giá nhập` · `Note` · `Ngày nhập` · `Thành tiền` · `Mã phiếu nhập` · `Trạng thái phiếu`
- **danh_muc_hang.csv** — CSV, 61 data rows; columns: `Tra cứu thông tin bổ sung` · `Đang kinh doanh` · `ĐVT` · `Giá vốn` · `Hàng bán` · `Nhóm` · `Giá` · `Tồn cuối` · `Mã SKU`

### dev_008

- **ChiTietHoaDon_1.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Bill` · `Trạng thái HĐĐT` · `Mã người mua` · `Bàn` · `Đơn vị (tính)` · `Phi ship` · `Thành tiền` · `Giảm (đ)` · `Giờ bán` · `Tổng tiền hàng` · `Addr` · `Giới tính` · `Giảm giá HĐ` · `Nhóm hàng` · `Khách` · `Số dòng` · `Tên hàng` · `Nhóm khách hàng` · `Số ĐT` · `SL lẻ` · `TT đơn` · `SLg` · `Note` · `Ngày xuất` · `Nhân viên bán` · `Tong tien` · `Kênh bán` · `Đơn giá (đ)` · `Ma hang` · `Thanh toán bằng` · `Số khách` · `Khu vực`
- **ChiTietHoaDon_2.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Bill` · `Trạng thái HĐĐT` · `Mã người mua` · `Bàn` · `Đơn vị (tính)` · `Phi ship` · `Thành tiền` · `Giảm (đ)` · `Giờ bán` · `Tổng tiền hàng` · `Addr` · `Giới tính` · `Giảm giá HĐ` · `Nhóm hàng` · `Khách` · `Số dòng` · `Tên hàng` · `Nhóm khách hàng` · `Số ĐT` · `SL lẻ` · `TT đơn` · `SLg` · `Note` · `Ngày xuất` · `Nhân viên bán` · `Tong tien` · `Kênh bán` · `Đơn giá (đ)` · `Ma hang` · `Thanh toán bằng` · `Số khách` · `Khu vực`
- **ChiTietNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Giá nhập` · `Mã NCC` · `Trạng thái phiếu` · `Ngày nhập` · `STT` · `Mã phiếu nhập` · `Tổng tiền phiếu` · `Lưu ý` · `Tên mặt hàng` · `Mã vạch` · `Thành tiền` · `SL nhập` · `ĐVT nhập`
- **DanhMucHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Hàng` · `Đang kinh doanh` · `Mã sản phẩm bán` · `DVT` · `Tồn thực` · `Loại hàng` · `Giá vốn` · `Giá hiện tại`

### dev_009

- **danh_sach_hoa_don.csv** — CSV, 23338 data rows; columns: `Ngày tháng` · `Trạng thái đơn` · `TongTien` · `Mã hóa đơn` · `Nợ` · `Đã thu` · `Đối tác` · `Giá trị hàng`

### dev_010

- **chi_tiet_don.csv** — CSV, 45251 data rows; columns: `Mã bill` · `Cộng` · `CK` · `SoLuong` · `Mã H.hóa` · `SL quy đổi` · `No.` · `Đơn giá (đ)` · `dvt`
- **don_hang.csv** — CSV, 25702 data rows; columns: `Kênh đặt` · `Thành tiền` · `Số CT` · `Con no` · `Date` · `Phương thức TT` · `Tiền giảm` · `Phí vận chuyển` · `Khách trả` · `Mã thẻ` · `Xử lý`
- **khach_hang.csv** — CSV, 260 data rows; columns: `Người tạo` · `Ghi chú KH` · `Khách lẻ/sỉ` · `Loại khách` · `Mã số thuế` · `Loại hình khách` · `Mã khách` · `Email` · `Tổng điểm` · `Trạng thái` · `Số CMND/CCCD` · `Phone` · `Công ty`
- **san_pham.csv** — CSV, 60 data rows; columns: `Mô tả chi tiết` · `Mẫu ghi chú` · `Loại hàng hóa` · `Thương hiệu` · `Đơn vị tính` · `Ghi chú` · `Bảo hành` · `Nhóm hàng` · `Mã vạch EAN` · `Hình ảnh (url1,url2...)` · `ten_hang` · `Thuộc tính` · `Trọng lượng` · `Giá bán` · `Mã vạch` · `Được bán trực tiếp` · `Mã HH Liên quan`
- **thanh_toan.csv** — CSV, 26246 data rows; columns: `Loại TT` · `Ngay thu` · `So tien` · `Mã đơn` · `Mã TT`

### dev_011

- **SoBanHang.xlsx** — 2 sheet(s)
  - `Ghi tắt` (dimension unavailable); candidate header: `Ghi tắt` · `Tên hàng` · `Loại`
  - `Sổ bán hàng` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Thu máy cũ` · `Khách trả` · `Ghi chú`

### dev_012

- **DanhSachTho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Họ tên` · `Ngày vào làm` · `Hoa hồng (%)`
- **SoSuaXe.xlsx** — 14 sheet(s)
  - `T7-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T8-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T9-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T10-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T11-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T12-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T1-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T2-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T3-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T4-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T5-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T6-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T7-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T8-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`

### dev_013

- **BanHang_2025.xlsx** — 8 sheet(s)
  - `T05-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T06-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T07-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T08-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T09-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T10-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T11-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T12-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
- **BanHang_2026.xlsx** — 6 sheet(s)
  - `T01-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T02-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T03-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T04-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T05-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T06-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
- **QuanLy.xlsx** — 4 sheet(s)
  - `DanhMuc` (dimension unavailable); candidate header: `Tên hàng` · `Tên gọi khác` · `Nhóm` · `Hãng` · `Số / Size` · `ĐVT` · `Quy đổi`
  - `KhachHang` (dimension unavailable); candidate header: `Tên KH` · `SĐT` · `Tên bé` · `Ngày đăng ký` · `Điểm hiện có`
  - `NhapHang` (dimension unavailable); candidate header: `Ngày` · `Số phiếu` · `Nhà cung cấp` · `Hàng` · `SL` · `ĐVT` · `Đơn giá` · `Thành tiền` · `Ghi chú`
  - `KhuyenMai` (dimension unavailable); candidate header: `Chương trình` · `Hàng áp dụng` · `Từ ngày` · `Đến ngày`

### dev_014

- **SoBanHang.xlsx** — 16 sheet(s)
  - `Ghi tắt` (dimension unavailable); candidate header: `Ghi tắt` · `Tên hàng` · `Loại`
  - `T7-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T8-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T9-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T10-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T11-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T12-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T1-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T2-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T3-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T4-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T5-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T6-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T7-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T8-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T9-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
- **SoNo.xlsx** — 3 sheet(s)
  - `Sổ nợ` (dimension unavailable); candidate header: `Ngày` · `Khách` · `SĐT` · `Nợ` · `Đã trả` · `Ngày trả` · `Ghi chú`
  - `Trả góp` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `SĐT` · `Máy` · `Giá` · `Trả trước` · `Số kỳ` · `Góp/tháng` · `Hạn góp (ngày)` · `Ngày góp` · `Đã góp`
  - `Bảo hành` (dimension unavailable); candidate header: `Ngày nhận` · `Khách` · `SĐT` · `Máy` · `IMEI` · `Ngày mua` · `Lỗi` · `Xử lý`
- **ThuMayCu.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày` · `Khách` · `SĐT` · `Máy thu` · `Tình trạng` · `IMEI` · `Giá thu` · `Trừ vào (STT sổ bán)`

## Follow-up

- Confirm inferred spreadsheet header rows against README; workbooks may have title rows, multi-row headers, repeated headers, or blank rows.
- Map all representative questions to source sheets, fields, joins, date semantics, units, and rulebook clauses.
- Record data quality findings without rewriting competition source files.
