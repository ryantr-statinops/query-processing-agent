# Người 5 — Đánh giá, review và tích hợp

## Vai trò

Bạn kiêm Người 5 và lead tích hợp. Giữ các phần dùng chung nhất quán, review theo gate, quản lý decision/issue log và báo cáo kết quả có giới hạn rõ. Không gọi kết quả holdout là độc lập: bộ 60 câu khám phá chứa 12 câu thuộc holdout và label của chúng đã được dùng trong sample file.

## Task và bàn giao

### E01 — Xác nhận evaluation contract

Đối chiếu `docs/01-competition.md` với evaluator/official kit sẵn có. Chốt scorer local cho number, percent, string/alias, date, boolean, list, table, unanswerable và abstain; lưu test cases synthetic và ghi rõ khác biệt nếu chưa có official evaluator. Công thức PA dùng `(correct - wrong) / total`.

### E02 — Lập evaluation manifest

Dùng `configs/splits/seed_2026.json` làm source of truth. Kiểm tra disjoint development/holdout business và số câu khớp manifest. Gắn split group vào từng record. 60 câu representative được dùng để hiểu/trace; tách kết quả development (48) khỏi 12 holdout đã tiếp xúc. Không dùng holdout để chọn prompt, model, thresholds hoặc cấu hình.

### E03 — Chuẩn hóa issue/trace review

Mỗi issue có ID/câu repro, split, business, stage (`retrieval`, `interpretation`, `planning`, `execution`, `evidence`, `serialization`, `runtime`), expected/actual, evidence refs, severity, owner, status và decision. Gold chỉ để scorer/review sau prediction.

### E04 — Review data gate

Soát 30 business catalog, trạng thái header verified, row counts/date ranges, join tests và findings; soát đủ 60 trace có source/calculation/status. Reject silent assumptions, gold leakage, nguồn không có provenance hoặc câu chưa tái tạo mà không có blocker.

### E05 — Review inference/runtime contract

Kiểm tra contract parseable, source refs có trong catalog, tool failures phân biệt, bounded loop, read-only execution, answer type và logs riêng. Đảm bảo Người 3/4 thống nhất cùng version trước khi merge.

### E06 — Phase evaluation

Chạy kiểm tra tại cuối mỗi phase theo lựa chọn của lead. Báo PA, correct/wrong/abstain/unanswerable, coverage, latency và lỗi theo business/intent/source/stage. Giữ command, commit SHA, manifest SHA, config/model hash và environment metadata để tái lập. Không chấm/so điểm public-test để ra quyết định thiết kế.

### E07 — Ưu tiên và tích hợp

Xếp lỗi theo ảnh hưởng, khả năng tái hiện và độ phủ. Giao task nhỏ có regression case; review diff/dependencies, test boundary và việc vô tình đưa data/artifacts vào Git. Tích hợp từng phase sau khi gate đạt.

### E08 — Acceptance và bàn giao

Kiểm tra JSONL một đáp án/question ID, typed answer hợp lệ, không diagnostics trong submission, `predict.sh` argument-free, `/data` read-only, `/result/logs/`, offline Docker và quy trình resume/reproducibility theo kit hiện hành. Sau code/config freeze mới chạy holdout theo kế hoạch; ghi rõ giới hạn độc lập do các câu mẫu đã tiếp xúc.

## Deliverables

- `artifacts/evaluation/` local: predictions, report theo ID, summary, metadata và logs.
- Issue/decision log dùng chung; summary trong tài liệu, không commit raw trace hoặc data.
- Checklist review cho data, inference, runtime và acceptance.
- CI hiện chưa có workflow trong repo; ghi trạng thái “unavailable” nếu không có remote CI để theo dõi.

## Gate và owner review

Người 1 ký xác nhận source findings; Người 2 xác nhận trace/expected answer; Người 3 xác nhận inference contract; Người 4 xác nhận runtime output và execution records. Bạn quyết định pass/fail gate và lưu lý do. Không merge phase nếu test boundary chưa chạy hoặc kết quả chưa được lưu.
