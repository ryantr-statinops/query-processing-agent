# Người 4 — Môi trường, baseline và runtime

## Mục tiêu

Khôi phục một đường chạy sạch sau khi source solver cũ được gỡ; xây baseline agentic RAG nhỏ có thể truy vết lỗi theo từng chặng. Không tái sử dụng handler cũ như hành vi đã được xác nhận. Chưa nối inference plan cuối cho đến khi Người 3 khóa contract v0.

## Giao diện và đầu vào

- Input cuối: câu hỏi có `id`, `business_id`, `question`, `as_of_date`; business package tương ứng; rulebook/calendar dùng chung.
- Output cuối: một typed answer cho mỗi ID trong `/result/submission.jsonl`; diagnostic JSONL riêng trong `/result/logs/`.
- Nguồn data read-only. Luồng: question → retrieve context/evidence → model plan → validate → read-only tool execution → evidence check → answer serialize.

## Task

### R01 — Preflight môi trường

Kiểm tra `uv sync --locked`, package metadata/build, entrypoint, `predict.sh`, Docker và tests cũ. Ghi command/stack trace có thể tái hiện; phân loại lỗi do package đã xóa, dependency hay host. Tạo scaffold Python tối thiểu cần để project cài đặt/chạy module; không khôi phục solver cũ. Giữ `pyproject.toml` và `uv.lock` đồng bộ nếu đổi dependencies.

**Gate R01:** có một lệnh setup được xác minh và một smoke path không gọi model; nếu có blocker môi trường, lead nhận log và quyết định trước khi phụ thuộc khác chờ.

### R02 — Loader chỉ đọc

Triển khai theo các nguồn đã xác minh; bắt đầu CSV, Excel, SQLite. Giữ cột gốc và source provenance; đăng ký bảng trong memory. Tạo structured data errors cho file/sheet/table thiếu, header không khớp, parse/date/unit bất thường. Chưa chuẩn hóa source tại chỗ.

### R03 — Contract tạm cho integration

Trước inference contract, dùng fake planner và synthetic fixture để kết nối loader → query interface → answer writer. Fake plan phải bị validate như plan thật. Không hardcode question/business ID hoặc expected answer.

### R04 — Executor an toàn

Tích hợp read-only DataFusion theo `AGENTS.md`: chấp nhận query được phép, từ chối DDL/DML/multiple statements/external readers, giới hạn rows/time/resources; trả typed rows, schema, error, latency và source refs. Query có timeout/cancellation rõ; timeout không được biến thành rỗng hợp lệ.

### R05 — RAG và model adapter

Sau Gate inference, thêm retrieval schema/rule/entity, adapter model offline tuần tự, parse/validate kế hoạch và bounded tool loop. Mọi bảng/cột phải được grounding vào catalog; query chỉ chạy sau validation. Ghi model/version, prompt/config hashes và token/latency nếu có.

### R06 — Evidence, answer và logs

Kiểm tra nguồn hỗ trợ metric, date range, filters, unit, row grain và answer type; phân biệt kết quả 0 với thiếu data, lỗi parse, lỗi query và timeout. Writer giữ typed answer; diagnostics riêng, có ID/trace nhưng hạn chế raw data.

### R07 — Baseline và đóng gói

Chạy vài câu đã trace qua một business mỗi định dạng; sau đó mở rộng theo lỗi. Giữ `python -m datamate`, `predict.sh` không đối số, đọc `/data` read-only và ghi kết quả `/result/`. Thêm Docker/offline smoke sau khi baseline qua local gate.

## Kiểm tra và bàn giao

- Unit/integration cases dùng synthetic data: ba định dạng; header lệch; missing table; duplicate join; malformed date; unit conversion; zero vs no evidence; invalid SQL; timeout; row cap; malformed model output; typed serialization và log separation.
- Người 3 review plan/tool contract; Người 2 cung cấp trace/expected result; Người 1 review loader/source mapping; Người 5 review output/evaluation.
- Chạy suite đã thống nhất cuối mỗi phase. Khi test cũ còn import package đã xóa, không ghi chúng là pass; cập nhật hoặc thay bằng kiểm tra phù hợp ở task implementation.

**Đầu ra:** source code, lệnh setup/run, baseline traces, Docker smoke và hướng dẫn tái hiện lỗi; execution artifacts vẫn local.
