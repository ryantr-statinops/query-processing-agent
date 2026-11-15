# Hướng dẫn đọc tài liệu DataMate

Tài liệu này dành cho mentor và thành viên mới. Repo đang trong giai đoạn rebuild: solver cũ đã được gỡ, catalog và tracing đã có công cụ xác minh; inference contract v0 và guardrails đã được merge. Hiện có lát cắt runtime synthetic dùng fake planner; model inference và đánh giá hiệu năng thực tế vẫn chưa có.

## Lộ trình đọc cho mentor

1. [README dự án](../README.md) — mục tiêu, trạng thái hiện tại và những gì chưa chạy được.
2. [Luật cuộc thi và answer contract](01-competition.md) — giới hạn phải tuân thủ khi thiết kế hệ thống.
3. [Data inventory](data-inventory.md), rồi [schema catalog ban đầu](data-schema-catalog.md) — quy mô data và phần cấu trúc cần xác minh. Xem thêm handoff catalog và tracing để biết bằng chứng và giới hạn kiểm tra.
4. [Bộ 60 câu train đại diện](../configs/representative_questions.json) — phạm vi câu hỏi được chọn; có 12 câu thuộc holdout đã tiếp xúc nhãn, nên không đại diện cho đánh giá holdout độc lập.
5. [Kiến trúc agentic RAG đề xuất](architecture/agentic-rag.md) — graph thành phần, sequence của một lượt hỏi đáp, ranh giới dữ liệu và các quyết định còn mở.
6. [Kế hoạch rebuild theo team](plan/rebuild.md) — các phase, ownership và gate.
7. Mở brief theo vai trò cần review: [Người 1 — data catalog](plan/01-data-catalog.md), [Người 2 — truy vết](plan/02-question-tracing.md), [Người 3 — inference](plan/03-agentic-rag-inference.md), [Người 4 — runtime](plan/04-baseline-runtime.md), [Người 5 — đánh giá và tích hợp](plan/05-evaluation-integration.md).

## Kiến trúc package hiện hành

[Package structure](architecture/package-structure.md) mô tả code hiện có, hướng phụ thuộc và các phần runtime còn thiếu. Tài liệu trong archive là thiết kế solver cũ.

Tra cứu lệnh đang hỗ trợ trong [script index](../scripts/README.md). Các implementation solver cũ được giữ trong `scripts/legacy/` và chưa chạy được nếu thiếu runtime.

## Các điểm nên review

- Catalog và kế hoạch trace có đủ bằng chứng để hiểu schema, khóa nối, grain và quy tắc tính không?
- Dòng agent có giới hạn rõ giữa retrieval, model planning, tool execution và verification không?
- Các trường hợp thiếu nguồn, dữ liệu rỗng, giá trị zero, lỗi query, timeout và abstain có được phân biệt không?
- Holdout exposure, business-level split và cách báo cáo kết quả có được trình bày trung thực không?
- Những gì đang được đề xuất đã được phân biệt rõ với những gì đã chạy thật chưa?

GGUF model adapter, vector index, semantic source mapping và ranking vẫn đang mở. CLI hiện abstain an toàn khi chưa có planner; kết quả fake-planner chỉ xác nhận luồng kỹ thuật, không đo chất lượng dự đoán.

## Tài liệu bổ sung

[Harness responsibilities](02-harness.md) mô tả stage và evidence states dưới dạng checklist ngắn. [Archive index](archive/README.md) dẫn tới thiết kế và kết quả của solver cũ; không cần đọc trong lượt đầu và không dùng làm mô tả runtime hiện tại.

## Quy ước tài liệu

- Đánh dấu rõ nội dung là **đề xuất**, **đã xác minh** hay **đã chạy**.
- Không commit competition data, gold answers chi tiết, model weights hoặc experiment artifacts.
- Chỉ thêm lệnh chạy sau khi đã kiểm tra lệnh đó với runtime hiện hành.
