# Đề bài và thể lệ DataMate

## Phạm vi

Agent nhận câu hỏi tiếng Việt, `business_id`, `as_of_date` và gói dữ liệu tương ứng gồm CSV, Excel hoặc SQLite, kèm README mô tả doanh nghiệp. Rulebook và lịch dương–âm dùng chung trong split. Dùng `as_of_date` để giải nghĩa thời gian tương đối. Bài nộp là câu trả lời cuối có kiểu, định danh bằng `id` của câu hỏi. [DataMate · Description](https://challenge.zalo.ai/portal/datamate/)

Ví dụ minh họa tự tạo về input và output tương ứng:

```jsonl
{"id":"demo_01","business_id":"demo_shop","question":"Tháng trước bán được mấy ly trà đào?","as_of_date":"2026-03-04"}
```

```jsonl
{"id":"demo_01","type":"number","answer":5}
```

## Cách chấm

`PA = (số đúng − số sai) / tổng số câu`. Mỗi câu có trọng số bằng nhau. Đúng được `+1`, sai `−1`, `abstain` hoặc thiếu đáp án được `0`. Một đáp án thông thường phải khớp cả kiểu lẫn giá trị. Không có điểm một phần. `unanswerable` là dự đoán dữ liệu thiếu căn cứ và được `+1` khi khớp nhãn đó. Nó bị `−1` khi câu có thể trả lời. Nếu hòa điểm, BTC xét thời gian inference khi chạy lại, rồi thời điểm nộp. [DataMate · Evaluation](https://challenge.zalo.ai/portal/datamate/)

| Kiểu | Điều cần kiểm tra trước khi nộp |
| --- | --- |
| `number` | Khớp giá trị tham chiếu. Dùng đúng đơn vị và làm tròn theo quy ước của evaluator. |
| `percent` | Dùng đơn vị phần trăm, ví dụ `12.5` cho 12,5%. Khớp sau khi làm tròn hai chữ số thập phân, gồm cả dấu. |
| `string` | So khớp sau chuẩn hóa. Giữ dấu tiếng Việt trong đáp án. BTC có thể chấp nhận các biến thể tên xuất hiện trong gói dữ liệu và mã tương ứng. |
| `date` | Chuỗi ISO `YYYY-MM-DD`, hoặc `YYYY-MM` với câu hỏi về tháng. |
| `boolean` | JSON `true` hoặc `false`. |
| `list` | So khớp theo vị trí, giữ thứ tự được yêu cầu hoặc thứ tự mặc định. |
| `table` | Gồm `columns` và `rows`. Cột khớp theo tên đã chuẩn hóa, có fallback theo vị trí. Hàng so theo tập hợp. |
| `unanswerable` | Khớp nhãn thiếu căn cứ. |
| `abstain` | Hành động bỏ qua câu, luôn 0 điểm. |

Với câu xếp hạng, dùng tiêu chí đề nêu hoặc mặc định trong rulebook, xếp giảm dần trên đơn hợp lệ và dùng mã tăng dần để phá hòa. BTC loại khỏi test những câu có hòa ngay ranh giới top-k hoặc hạng nhất với câu hỏi “nhất”. Nếu ít hơn k ứng viên thì trả toàn bộ theo thứ tự. Các chi tiết về matching và payload nên được khóa bằng fixture chạy trên evaluator chính thức. [DataMate · Evaluation](https://challenge.zalo.ai/portal/datamate/)

## Ràng buộc ảnh hưởng trực tiếp đến thiết kế

- **Model**. Trần **15B tham số cộng gộp** cho tất cả model inference, gồm LM, embedding, reranker và classifier, kể cả chạy luân phiên. MoE tính toàn bộ tham số. Được lượng tử hóa và fine-tune. Weights gốc phải được công bố trước 26/10/2026 với giấy phép phù hợp. Khai báo model trong README của bài nộp. [DataMate · Rule](https://challenge.zalo.ai/portal/datamate/)
- **Inference**. Docker chạy offline, mount test tại `/data` chỉ đọc và thu `/result/submission.jsonl`. Agent có thể thực thi code trong container. Kết quả phải tự sinh. BTC cấm hard-code câu trả lời và logic đặc thù theo ID câu hỏi hoặc doanh nghiệp. Dùng `business_id` để tìm gói dữ liệu tương ứng. [DataMate · Rule](https://challenge.zalo.ai/portal/datamate/)
- **Dữ liệu phát triển**. Được dùng train, dữ liệu tự tổng hợp và nguồn công khai phù hợp thể lệ. BTC cấm dùng public/private test để train hoặc thu thập đáp án test. Dành holdout nội bộ từ train cho hiệu chỉnh và chọn cấu hình. [DataMate · Rule](https://challenge.zalo.ai/portal/datamate/), [Thể lệ chung](https://challenge.zalo.ai/regulations)
- **Tài nguyên và tái lập**. Máy tham chiếu có 2 RTX 5090 (32 GB VRAM mỗi card) và 512 GB RAM. Giới hạn **6 giờ toàn bộ private test**, kể cả load model. BTC dùng điểm Docker chạy lại làm điểm cuối, với ngưỡng chênh PA cho tính tái lập là `0.03`. Nếu dừng sớm, các câu chưa ghi được tính `abstain`. [DataMate · Rule](https://challenge.zalo.ai/portal/datamate/)

## Mốc nộp (GMT+7)

| Mốc | Việc của đội |
| --- | --- |
| 26/10–16/11 | Chạy public test và nộp JSONL để tham khảo leaderboard. Portal nêu tối đa 5 lượt/ngày. |
| 16/11 lúc 23:59 | Nộp Docker và đóng băng giải pháp. Submission Guidance yêu cầu checksum và link Drive công khai để BTC tải. Tối đa 2 lượt, BTC lấy lượt cuối. |
| 20/11 | Private test được mở. Tab Submission Guidance ghi 09:00, timeline trang chủ ghi 11:00. Xác nhận giờ trên portal trước ngày chạy. |
| 23/11 lúc 23:59 | Hạn nộp JSONL private do Docker đã đóng băng tạo ra. |

Nguồn lịch và quy cách nộp. [DataMate · Submission Guidance](https://challenge.zalo.ai/portal/datamate/), [Timeline chung](https://challenge.zalo.ai/#timeline)

Tab **Data** yêu cầu đăng nhập. Repo hiện chưa có bộ kit. Link PDF Docker Guide được xác định qua portal, nhưng chưa đọc được PDF trong phiên khảo sát. Khi lấy kit, xác nhận layout train/test, phiên bản evaluator, danh sách kiểu và trường bắt buộc trong JSONL, quy cách log, image gốc, lệnh chạy và cách đóng gói. Dùng tài liệu BTC cho các chi tiết này. [Docker Guide của DataMate](https://dl-challenge.zalo.ai/2026/datamate_dkewxftdzo/zac2026_DataMate_docker_guideline_final.pdf)
