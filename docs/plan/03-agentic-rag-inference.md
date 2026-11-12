# Người 3 — Thiết kế agentic RAG và inference contract

## Mục tiêu

Thiết kế hành vi suy luận từ catalog và trace đã xác minh. Agent truy xuất schema, README/rulebook, entity evidence và dữ liệu liên quan; lập kế hoạch; gọi công cụ truy vấn có giới hạn; kiểm tra kết quả rồi trả typed answer hoặc từ chối có lý do. Tài liệu này quyết định contract v0, không quyết định model trước bằng chứng.

## Đầu vào và phụ thuộc

- Catalog/source refs đã xác minh của Người 1.
- Question traces và issue của Người 2.
- `docs/01-competition.md`, `train/rulebook.md`, answer contract và giới hạn runtime trong repo.
- Có thể soạn khung và ví dụ tổng hợp trong Phase data; chỉ khóa quyết định sau Gate data.

## Task

### I01 — Phân nhóm suy luận

Từ trace, lập ma trận intent × evidence × operations × answer type. Tách điều cần hiểu ngôn ngữ (metric/entity/time/filter) khỏi điều tất định nên thực thi bằng code (calendar resolution, SQL aggregation, unit conversion đã xác nhận, serialization). Bao gồm các lỗi hiểu sai thường gặp.

### I02 — Thiết kế retrieval

Quy định cách lấy context theo câu: business README/rule sections, schema/table/columns, aliases/entities và sample values có giới hạn. Với từng kết quả retrieval, lưu provenance về source ref, section/column và lý do được chọn. Không đưa gold labels/answers vào retrieval.

### I03 — Định nghĩa tool boundary

Mô tả contract cho: lấy catalog/schema; tìm entity/alias; xem mẫu dữ liệu giới hạn; chạy read-only query; kiểm tra kết quả/answer type. Mỗi tool có input/output, timeout/row limit dự kiến, lỗi có cấu trúc và nguồn provenance. Chỉ cấp tool cần thiết cho trace; không cho model chạy shell, Python tùy ý hoặc truy cập mạng.

### I04 — So sánh representation

Trên cùng các trace, so sánh JSON plan có cấu trúc với SQL có ràng buộc. Chấm khả năng parse, grounding vào cột thật, phát hiện thiếu trường, tính đúng, khả năng abstain và chi phí inference. Đưa ví dụ đúng, sai, ambiguous, schema-mismatch và evidence thiếu.

### I05 — Viết inference contract v0

Đặc tả input context, output plan, provenance, assumptions, trạng thái cần thêm evidence/không trả lời, typed answer handoff và error shape. Không cho phép câu trả lời số nếu execution không có bằng chứng. Ghi rõ trường nào bắt buộc/tùy chọn và cách xử lý output hỏng.

### I06 — Giới hạn agent loop

Đề xuất số vòng gọi tool, retry parse, token/context budget, query budget và điều kiện dừng; mỗi lần lặp phải nêu action có ích. Khi hết budget hoặc timeout, trả trạng thái lỗi/abstain theo policy được đánh giá, không bịa kết quả.

### I07 — Đề xuất model và runtime

Sau I01–I06, đề xuất lựa chọn theo chất lượng trên trace development, chạy offline, tổng parameter theo luật, latency, bộ nhớ và khả năng đóng gói. Báo điểm chưa kiểm chứng; không tải weights trong task thiết kế.

## Đầu ra và phiên bản

Đặc tả inference/tool trong tài liệu này; contract machine-readable ở `configs/inference_contract.json` sau khi lead duyệt; bộ ví dụ tổng hợp và train đã trace trong `artifacts/inference/` (local, không commit raw data/gold vào prompt fixtures).

Contract v0 phải có ví dụ JSON hợp lệ, parse failure, unknown column, ambiguous entity, no evidence, query error, budget exhausted và mỗi output answer type được chọn vào baseline. Thay đổi contract tăng version hoặc cập nhật cùng nhóm code phụ thuộc.

## Review và Gate inference

- Người 1 xác nhận mọi source ref/cột có trong catalog.
- Người 2 xác nhận ví dụ thể hiện đúng trace và không lẫn gold vào inference input.
- Người 4 xác nhận tool contracts triển khai được; Người 5 xác nhận có thể chấm và log lỗi.
- Lead chốt contract v0 và các quyết định mở trước khi Người 4 tích hợp model.
