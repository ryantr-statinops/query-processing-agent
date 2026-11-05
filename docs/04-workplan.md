# Đánh giá và kế hoạch triển khai

## Thiết kế đánh giá nội bộ

Chia dữ liệu **theo doanh nghiệp** trong train. Tập `fit` dùng xây prompt, index few-shot, học reranker/policy và fine-tune. Tập `calibration` dùng hiệu chỉnh confidence và chọn ngưỡng. Tập `holdout` dành cho so sánh đã định trước và kiểm tra bản chốt. Khi ít business, dùng group cross-validation trong phần phát triển để sinh dự đoán out-of-fold cho verifier và policy, rồi giữ riêng một holdout. Ghi số business, số câu và phân bố nhóm lỗi/kiểu đáp án từng phần. Mọi biến thể của một câu và mọi bảng của cùng doanh nghiệp đi cùng nhóm. Mỗi câu khi chạy vẫn được truy cập gói dữ liệu và rule của nó theo đề.

| Chỉ số | Dùng để quyết định |
| --- | --- |
| PA và số đúng/sai/abstain | Chọn cấu hình theo điểm thi. Tách riêng `unanswerable` đúng, dự đoán nhầm và các câu bị bỏ qua. |
| Coverage và accuracy khi trả lời | Coverage là tỷ lệ dự đoán khác `abstain`, gồm cả `unanswerable`. Với coverage dương, `PA = coverage × (2 × accuracy_khi_trả_lời − 1)`. Vẽ PA và tỷ lệ sai theo coverage khi quét ngưỡng. |
| Evidence recall@k và context tokens | Đo schema/rule cần thiết đã vào prompt hay chưa. Đo trên tập có nhãn evidence riêng. |
| Oracle@N, top-1 và chênh lệch | Oracle tính tỷ lệ câu có ứng viên đúng theo evaluator trước gate. Chênh với top-1 trên cùng candidate pool đo phần có thể cải thiện bằng xếp hạng. Theo dõi thêm trên các câu có đáp án thông thường. |
| Hợp lệ, chạy được, đúng ngữ nghĩa | Tách tỷ lệ parse lỗi, SQL lỗi/timeout, output lỗi và SQL chạy nhưng ra đáp án sai. |
| Calibration | Brier score, reliability bins và độ đúng thực tế quanh ngưỡng, phân theo loại câu hoặc định dạng file nếu đủ mẫu. |
| Tài nguyên | p50/p95 latency, số lượt sinh và execute, token, peak VRAM, thời gian ingest/load, throughput và tổng wall-clock. Đo cả lượt chạy cold start trong Docker. |

Ví dụ cấu hình A có 60 đúng, 20 sai, 20 abstain trên 100 câu thì PA = 0,40. Nếu B chuyển 10 câu sai và 3 câu đúng của A thành `abstain`, PA tăng lên 0,47. Báo cả ba bộ đếm để phân biệt cải thiện ở chọn đáp án, giảm lỗi hay đổi coverage. So sánh PA theo cặp trên cùng câu. Khi đủ doanh nghiệp, bootstrap theo business để ước lượng bất định vì lỗi trong cùng gói dữ liệu có tương quan. Tách kết quả theo nguồn CSV/Excel/SQLite, kiểu đáp án, nhóm nghiệp vụ và nhóm lỗi.

## Chuỗi thực nghiệm

Chạy mỗi hàng với cùng split và evaluator. Cố định seed, checkpoint, prompt, ngân sách và candidate pool khi biến đang thử cho phép. Lưu cấu hình và bảng thay đổi theo từng câu.

| Thử nghiệm | Thay đổi | Điều kiện đi tiếp |
| --- | --- | --- |
| B0 | SQL viết tay trên fixture tự tạo và vài câu train, đối chiếu evaluator | Xác nhận loader, hợp đồng JSONL, và đúng/sai/abstain cho cả nhãn thiếu căn cứ. |
| B1 | LM local, schema gọn, một lần sinh SQL và executor chỉ đọc | Có điểm local theo business và trace đủ để gán lỗi theo stage. |
| E1 | Lexical retrieval có join closure, sau đó thử context reranking nếu cần | Recall tăng hoặc giữ ổn định, token/latency giảm hoặc PA tăng trên câu cần retrieval. |
| E2 | `N=1` so với `N=2–3` để ước lượng oracle, rồi heuristic/learned verifier trên cùng pool | Oracle tăng đủ để bù chi phí và verifier thu được cải thiện PA. |
| E3 | Gate dựa trên luật so với logistic được hiệu chỉnh | So PA, số sai, coverage và độ ổn định theo business, gồm cả dự đoán `unanswerable`. |
| E4 | Retry có điều kiện so với cố định, cùng ngân sách tính toán | Chỉ giữ nếu cải thiện PA ổn định, có thể tái lập và còn dư thời gian trong Docker. |
| E5 | Một vòng SFT lọc hoặc một phương pháp preference, nếu có dữ liệu và thời gian | Oracle/top-1 hoặc PA tăng dưới cùng budget. Kiểm tra lại calibration nếu đổi generator. |

Một log thực nghiệm tối thiểu gồm `run_id`, commit, data/split hash, prompt/model/config revision, seed, N và budget, PA, các bộ đếm, p95, tổng thời gian, lỗi lớn nhất và quyết định giữ hay bỏ. Với giả thuyết RL, trước hết replay nhánh `stop`, `expand` và `retry` trên cùng câu fit để đo giá trị bổ sung và chi phí. Nếu log chỉ có một hành động trên mỗi trạng thái, ghi rõ phần phản thực tế chưa quan sát được.

## Lịch đề xuất từ 05/11 đến 16/11 (GMT+7)

| Mốc | Phạm vi | Đầu ra để chốt mốc |
| --- | --- | --- |
| 05–06/11 | Đọc kit/rulebook/Docker Guide, kiểm kê train, dựng split và B0 | Evaluator chạy local, fixture qua các kiểu trọng yếu, danh mục nhóm câu và lỗi. |
| 07–09/11 | Loader, catalog, một model offline, một query/câu, chuẩn hóa, writer | B1 chạy đầu cuối. Có bản Docker smoke test đọc mount chỉ đọc và ghi JSONL. |
| 10–12/11 | Sửa các lỗi lớn nhất, thêm retrieval, Best-of-N nhỏ và verifier | Báo cáo PA, oracle gap và chi phí trước/sau. Chọn một cấu hình triển vọng. |
| 13–14/11 | Hiệu chỉnh gate và kiểm tra ngân sách. Thử retry hoặc SFT nếu qua mốc trước và còn thời gian | PA/coverage trên holdout, time budget với cold start và hai lượt replay. |
| 15–16/11 | Chốt cấu hình, dựng lại Docker sạch, kiểm kê weights, log, checksum và nộp | Image offline cùng lệnh chạy đã kiểm tra, đầy đủ tài liệu và artifact theo hướng dẫn BTC. |
| 20–23/11 | Chạy private bằng image đã nộp, kiểm tra file rồi nộp JSONL | Kết quả sinh từ cấu hình đã freeze, có trace để đối chiếu. |

Nếu tiến độ chậm, ưu tiên B1, khả năng tái lập và kiểm tra output. Có thể cắt cross-encoder, tăng N, fine-tuning và policy tuần tự theo chi phí đo được. Khi đã biết kích thước workload, dự trù từ `thời gian load + ingest + inference + serialize` đo trên batch đại diện. Dành dư địa cho câu chậm, dữ liệu lớn và lỗi có thể phục hồi. Chạy nhiều câu song song chỉ khi giới hạn tài nguyên và cách ghi kết quả đã kiểm tra.

## Checklist trước khi đóng băng

- [ ] So lại bản thể lệ và Docker Guide, gồm lệnh chạy, đường dẫn, quy cách log và artefact cần nộp. [Portal DataMate](https://challenge.zalo.ai/portal/datamate/)
- [ ] Khai báo tên, phiên bản weights, ngày phát hành, giấy phép, số tham số và quantization của từng model. Tổng số tham số đáp ứng giới hạn track.
- [ ] Dựng image sạch, chạy không có mạng và với dữ liệu mount chỉ đọc. Kiểm tra input có đủ schema, rulebook và lịch, rồi xác nhận output JSONL và log.
- [ ] Kiểm tra ID trùng/thiếu, type, format và encoding. Chạy evaluator local, mô phỏng một timeout và kiểm tra bài nộp vẫn đọc được.
- [ ] Replay để kiểm tra độ tái lập, cold start và dự báo wall-clock. Lưu checksum image, commit, phiên bản dữ liệu và cấu hình chạy.
- [ ] Đối chiếu thành phần được phép đưa vào gói và quyền truy cập link tải theo BTC trước khi nộp. Chốt artifact trước 23:59 ngày 16/11 (GMT+7).
