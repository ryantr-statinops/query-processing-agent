# Query Processing Agent

**Giai đoạn hiện tại · Planning**

Dự án hướng tới **Track 2 · DataMate** của Zalo AI Challenge 2026. Agent sẽ nhận câu hỏi tiếng Việt và dữ liệu doanh nghiệp dạng CSV, Excel hoặc SQLite, rồi truy vấn dữ liệu để trả về câu trả lời có kiểu. Khi dữ liệu thiếu căn cứ, agent có thể dự đoán `unanswerable`. Khi độ tin cậy thấp, agent có thể chọn `abstain`. [Đề bài DataMate](https://challenge.zalo.ai/portal/datamate/)

## Hướng triển khai

1. Dựng baseline offline để đọc dữ liệu, sinh một truy vấn SQL, thực thi chỉ đọc và xuất JSONL để chấm bằng evaluator của ban tổ chức.
2. Thử reranking ở hai điểm. Chọn schema và quy tắc liên quan trước khi sinh SQL, rồi dùng bằng chứng thực thi để chọn giữa các ứng viên.
3. Hiệu chỉnh policy quyết định khi nào nên trả lời, thử thêm hoặc dừng. Dùng kết quả trên các doanh nghiệp giữ riêng để quyết định có cần fine-tune model sinh SQL hay thử RL cho policy nhiều bước.

## Tiến độ

Repo hiện chứa tài liệu về đề bài, kiến trúc dự kiến và kế hoạch đánh giá. Mốc triển khai đầu tiên là chạy baseline từ một câu hỏi đến một dòng JSONL hợp lệ và đối chiếu điểm bằng evaluator chính thức.

## Tài liệu

- [Mục lục tài liệu](docs/README.md)
- [Đề bài và thể lệ](docs/01-competition.md)
- [Thiết kế agent harness](docs/02-harness.md)
- [Reranking, decision policy và huấn luyện LM](docs/03-methods.md)
- [Kế hoạch triển khai và đánh giá](docs/04-workplan.md)
