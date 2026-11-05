# DataMate · Zalo AI Challenge 2026

Đề xuất cho `query-processing-agent`, cập nhật ngày 05/11/2026 (GMT+7). Mục tiêu là xây một harness chạy được từ dữ liệu thô đến bài nộp, rồi dùng cùng harness để đo tác động của retrieval, reranking và học policy trên các doanh nghiệp chưa thấy trong train.

## Đường đọc

1. [Đề bài và thể lệ](01-competition.md) — I/O, cách chấm, lịch và ràng buộc Docker.
2. [Các bài toán con và thiết kế harness](02-harness.md) — dữ liệu, thời gian, thực thể, SQL, verifier và ví dụ xuyên suốt.
3. [Reranking, decision policy và huấn luyện LM](03-methods.md) — các cơ chế, hàm mục tiêu, dữ liệu học và điều kiện thử RL.
4. [Đánh giá và kế hoạch triển khai](04-workplan.md) — thứ tự thực nghiệm, chỉ số, tiêu chí qua từng mốc và checklist nộp.

## Giả thuyết thiết kế

Một harness giới hạn phạm vi khả thi trong khoảng thời gian còn lại nếu hoàn thành sớm luồng offline từ input đến JSONL và có tài nguyên để thử Docker. Mốc đầu tiên là chạy được `câu hỏi → schema và rule liên quan → một SQL → thực thi chỉ đọc → đáp án có kiểu → chấm local`. Sau đó mở rộng theo lỗi đã đo được. Chưa có số liệu từ bộ kit hay benchmark GPU để ước lượng điểm hoặc thời gian chạy thực tế.

Hướng nghiên cứu phù hợp với Quant AI là **tối ưu quyết định dưới bất định và giới hạn tài nguyên**. Dùng tập ứng viên cố định để phân biệt ba câu hỏi thực nghiệm. Generator có tạo được phương án đúng không? Verifier có nhận ra phương án đúng không? Policy có biết khi nào nên trả lời, thử thêm hay dừng không? Ba câu hỏi này cho ba tín hiệu khác nhau để quyết định nên đầu tư tiếp vào đâu.

## Bắt đầu phiên làm việc đầu tiên

1. Tải bộ kit chính thức qua tab **Data**. Ghi phiên bản/hash, mở rulebook và evaluator. Đọc một gói CSV, một Excel và một SQLite nếu mỗi loại có trong train.
2. Chọn một câu tra cứu và một câu tổng hợp đơn bảng từ train. Viết SQL bằng tay, lưu trace nội bộ, serialize đúng kiểu và đối chiếu điểm bằng evaluator. Thêm một câu `unanswerable` và kiểm tra riêng hành động `abstain`.
3. Đóng băng holdout theo `business_id` trước khi xây prompt hay chọn ví dụ. Sau đó thay SQL viết tay bằng một lần sinh từ model chạy local và đo lại.

Repo lúc khảo sát chưa có dữ liệu hoặc mã nguồn. Các interface, ví dụ và mốc kỹ thuật trong bộ tài liệu này là thiết kế đề xuất.
