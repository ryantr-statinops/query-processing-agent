# Người 2 — Truy vết 60 câu train

## Mục tiêu và phạm vi

Tạo lời giải có thể kiểm tra cho từng câu trong `configs/representative_questions.json`: từ ngôn ngữ câu hỏi tới nguồn, quy tắc, phép tính và đáp án train. Đọc đủ 60 câu theo lựa chọn của lead; trong đó 12 câu thuộc holdout theo manifest và nhãn đã xuất hiện trong bộ mẫu. Vì vậy đây là tập khám phá, không phải đánh giá holdout độc lập.

Gold chỉ dùng để đối chiếu sau khi ghi cách tính; không đưa answer/reference vào prompt, retrieval context hay runtime inference.

## Đầu vào và phối hợp

- 60 mẫu trong `configs/representative_questions.json`, `train/questions.jsonl`, `train/answers.jsonl`.
- Catalog đã xác minh từ Người 1; `train/rulebook.md`, README từng business và `train/calendar.csv`.
- Nếu catalog chưa xong, bắt đầu bằng câu có source ref ổn định; ghi `blocked_on_catalog` cho phần phụ thuộc header/keys chưa xác minh.

## Quy trình cho mỗi câu

### Q01 — Chuẩn hóa yêu cầu ngôn ngữ

Ghi intent/metric, entity, thời gian tuyệt đối sau khi resolve relative date theo `as_of_date`, filter, grouping/ranking, unit và answer type. Giữ nguyên câu gốc; không suy diễn phần câu hỏi không nói.

### Q02 — Tìm bằng chứng và luật

Liệt kê source refs chính xác: business/file/sheet/table/columns; chỉ ra README/rulebook/calendar clause và lý do nguồn đó cần thiết. Phân biệt bằng chứng có trong data với quy tắc do rulebook định nghĩa.

### Q03 — Viết phép tính trước khi đọc gold

Ghi grain từng nguồn, join keys/cardinality, status/date filters, entity matching, unit conversion, công thức, thứ tự aggregation và serialization. Với ranking, ghi criterion, tie-break và top-k; với percent, ghi tử số/mẫu số và xử lý denominator zero.

### Q04 — Tính, so sánh, điều tra

Thực hiện tính toán read-only trên nguồn. Ghi kết quả độc lập rồi đối chiếu `train/answers.jsonl`; kiểm tra type, precision, alias và ordering theo contract. Nếu lệch, tìm nguyên nhân ở source, rule, join, date, unit, công thức hoặc serialization; không đổi trace chỉ để ép khớp.

### Q05 — Ghi trạng thái và tổng hợp

Mỗi câu có một trạng thái: `verified`, `unresolved`, `insufficient_evidence`, `source_missing`, `execution_error` hoặc `blocked_on_catalog`. Câu chưa tái tạo phải ghi điều còn thiếu và người cần quyết định. Không gán `unanswerable` chỉ vì chưa viết được phép tính.

## Record schema và nơi lưu

Lưu mỗi câu thành một record JSONL tại `artifacts/data_prep/question_trace.jsonl`, với trường tối thiểu:

`question_id`, `business_id`, `split_group`, `intent`, `time_range`, `entities_filters`, `answer_type`, `source_refs`, `required_columns`, `grain`, `join_edges`, `rule_refs`, `unit_semantics`, `calculation`, `computed_answer`, `gold_comparison`, `status`, `uncertainty`, `reviewer`.

`source_refs` dùng đường dẫn tương đối, sheet/table và cột nguyên bản; `gold_comparison` tách khỏi nội dung suy luận. Không chép data giao dịch. Tóm tắt pattern và issue không chứa đáp án nhạy cảm trong `docs/plan/`.

## Kiểm tra cuối phase

1. Có đúng 60 record, mỗi ID khớp câu/business/as_of_date trong nguồn train.
2. Mỗi record có source/rule/calculation hoặc trạng thái chưa giải thích cùng blocker cụ thể.
3. Tái tính riêng một mẫu mỗi answer type và mẫu có unit conversion, relative date, ranking, join fan-out, thiếu bằng chứng.
4. Báo cáo riêng 48 câu development và 12 câu holdout đã tiếp xúc; không dùng holdout để chọn prompt, threshold hoặc cấu hình.
5. Người 1 xác nhận source refs; lead/Người 5 review kết quả và discrepancies.

**Đầu ra:** JSONL trace cục bộ, danh sách issue, tóm tắt các pattern lặp lại cho Người 3 và bộ câu đã tái tạo được cho Người 4.
