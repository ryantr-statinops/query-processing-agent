# Người 1 — Data catalog và chất lượng nguồn

## Mục tiêu và phạm vi

Xác minh cấu trúc dữ liệu thật cho 30 business trong `train/data/`, đối chiếu với README và tạo catalog đủ chính xác để Người 2 truy vết câu hỏi, Người 3 thiết kế retrieval, Người 4 viết loader. Nguồn là read-only; mọi chuẩn hóa chỉ tạo biểu diễn trong bộ nhớ.

Không dùng public-test labels hoặc scores. Có thể ghi nhận cấu trúc public test để kiểm tra định dạng sau này, nhưng kết luận schema và chất lượng cho giai đoạn phát triển phải dựa trên 30 business train.

## Đầu vào

- `train/data/<business_id>/` và README của từng business.
- `train/rulebook.md`, `train/calendar.csv`.
- `docs/data-schema-catalog.md` là bản quét sơ bộ, chưa xác minh đầy đủ.
- `configs/representative_questions.json` để ưu tiên nguồn cần kiểm tra kỹ.

## Thứ tự task

### D01 — Kiểm kê file và sheet

Với từng business, so sánh danh sách file thật với README; ghi file thừa/thiếu, định dạng, workbook, sheet, bảng SQLite và file chia kỳ. Xác nhận những workbook nhiều sheet có cùng schema hay thay đổi theo thời gian.

**Đầu ra:** danh sách nguồn theo business trong `artifacts/data_prep/data_catalog.json`.

### D02 — Xác minh header và grain

Mở từng bảng cần thiết để tìm header thật, header nhiều dòng/lặp, dòng tiêu đề và dòng trống. Ghi tên cột nguyên bản, kiểu dữ liệu quan sát được, số dòng header/data và ý nghĩa một dòng: đơn, dòng hàng, lần thu tiền, lần giao, lô hay snapshot. Không đổi tên cột trong nguồn.

**Đầu ra:** mỗi bảng có cột nguồn, vị trí header, grain, số dòng dữ liệu và trạng thái `verified`/`needs_review`.

### D03 — Kiểm tra độ phủ và chất lượng

Cho các trường ngày, tính min/max sau khi parse và đếm giá trị không parse được. Đếm null/blank trên cột quan trọng; kiểm tra khóa duy nhất ở grain dự kiến, dòng trùng, trạng thái lạ, đơn vị không biết và nguồn có khoảng thời gian chồng lấn. Ghi số đếm và ví dụ ID nội bộ tối thiểu; không chép dòng dữ liệu đầy đủ vào tài liệu.

**Đầu ra:** `artifacts/data_prep/source_quality.csv`, kèm findings có mức ảnh hưởng và cách tái hiện.

### D04 — Kiểm chứng khóa nối

Ghi khóa đơn, khóa dòng và khóa ghép theo README; kiểm tra null/duplicate, coverage hai chiều và cardinality. Nêu rõ quan hệ một-nhiều, nhiều-nhiều và cột tổng ở cấp đơn bị lặp trên dòng hàng. Tạo phép kiểm tra fan-out cho các join dùng bởi 60 câu mẫu.

**Đầu ra:** sơ đồ/ma trận join trong catalog, có mẫu số bản ghi trước/sau và cảnh báo khi phép nối làm nhân dòng.

### D05 — Bàn giao và review

So sánh mọi khác biệt giữa README và dữ liệu thật; đánh dấu rõ quy ước đã xác nhận, giả định, và câu cần hỏi lead. Bàn giao cho Người 2 danh sách source refs ổn định: business, file, sheet/table, cột và grain.

**Đầu ra:** catalog 30 business đã xác minh cùng tóm tắt các họ schema và vấn đề dữ liệu.

## Quy ước artifact và an toàn dữ liệu

- Chi tiết bảng và thống kê phát sinh lưu dưới `artifacts/data_prep/` (đã gitignore); không commit data nguồn, sample giao dịch, weights hay artifacts.
- Tài liệu này và `docs/data-schema-catalog.md` chỉ chứa mô tả schema, thống kê tổng hợp và kết luận cần cho phát triển.
- Nạp file ở chế độ read-only; không sửa workbook/CSV/SQLite gốc, không ghi file chuẩn hóa cạnh dữ liệu nguồn.
- Dùng `uv` và dependency đã khóa nếu chạy code Python; báo lead khi môi trường/package hiện tại không cho chạy script.

## Kiểm tra cuối phase

1. Đủ 30/30 business; số file/sheet/table khớp với gói local hoặc có finding giải thích.
2. Bảng được dùng bởi câu mẫu có header, grain và khóa nối đã xác minh.
3. Row count và date coverage có cách tính tái lập; malformed dates, null keys, duplicates và fan-out được báo cáo.
4. README conflicts và chưa rõ được ghi riêng, không âm thầm chọn một diễn giải.
5. Kiểm tra nguồn không đổi; Người 2 xác nhận catalog đủ để ghi trace.

**Review:** Người 2 kiểm tra tính dùng được cho truy vết; lead/Người 5 review độ phủ và findings. **Bàn giao:** source map đã xác minh cho `02-question-tracing.md`.
