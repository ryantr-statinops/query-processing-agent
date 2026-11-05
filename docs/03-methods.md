# Reranking, decision policy và huấn luyện LM

Ba cơ chế tác động lên ba phân phối khác nhau. Reranker sắp xếp tập ứng viên đã có. Decision policy chọn hành động dựa trên trạng thái quan sát được. Huấn luyện LM thay đổi xác suất sinh các chương trình hoặc trajectory. Chúng có thể chia sẻ trace và nhãn, đồng thời triển khai và đo riêng.

| Cơ chế | Quyết định | Tín hiệu học hoặc kiểm tra | Chi phí chính |
| --- | --- | --- | --- |
| Reranking khi inference | Giữ schema/rule nào, chọn ứng viên đầu ra nào | Schema/rule liên quan, tính hợp lệ, đúng sai theo evaluator trên train, chất lượng bằng chứng | Thêm context scoring, lượt sinh và lượt thực thi |
| Decision policy ở harness | Trả đáp án, `unanswerable`, `abstain`, hoặc thử thêm | Xác suất khớp evaluator, thay đổi PA sau hành động và chi phí quan sát được | Thu và hiệu chỉnh trace, rủi ro lệch phân phối |
| Huấn luyện LM | Tăng xác suất sinh plan/SQL/trajectory tốt | Mẫu SFT, cặp preference hoặc reward sau rollout | GPU cho sinh rollout và fine-tune, công xác thực nhãn |

## 1. Reranking ở hai vị trí

**Context.** Bắt đầu với lexical retrieval trên tên bảng/cột, README, rule, alias và giá trị mẫu. Chuẩn hóa phục vụ tìm kiếm nhưng giữ giá trị gốc cho output. Giữ các cột bắt buộc và đường join cùng nhau. Đo `recall@k` của tập cột/rule cần thiết trên một tập train được gán evidence. Thử embedding + cross-encoder khi lexical bỏ sót paraphrase và top-K còn đủ recall. Nếu bảng thiếu ngay ở candidate pool, tăng recall trước. `bge-reranker-v2-m3` là một ứng viên từ gợi ý của bạn, cần đo hiệu quả trên tiếng Việt của track, latency và cộng vào ngân sách model. [BAAI BGE](https://bge.baai.ac.cn/)

**Đầu ra.** So greedy với Best-of-N nhỏ. Sinh đa dạng theo cách hiểu có cơ sở, ví dụ kiểm tra `SUM(qty)` với `COUNT(DISTINCT order_id)` hoặc hai giả thuyết schema. Parse và chạy mỗi SQL trong executor. Loại phương án sai kiểu hoặc vi phạm ràng buộc thực thi. Xếp các phương án còn lại theo evidence về thời gian, thực thể, đơn vị, grain, rule và sự đồng thuận giữa truy vấn khác nhau. Kết quả rỗng có thể hợp lệ và nhiều ứng viên giống nhau có thể cùng sai. Khi nhãn có sẵn, đo oracle@N để biết có ít nhất một ứng viên đúng, rồi đo khoảng cách từ oracle đến top-1 để định vị lỗi chọn. Đây là cách áp dụng feedback thực thi cho DataMate, lấy cảm hứng từ execution guidance trong text-to-SQL. [Wang và cộng sự](https://arxiv.org/abs/1807.03100)

## 2. Policy quyết định theo điểm kỳ vọng

Gọi $s$ là trạng thái gồm câu hỏi, evidence, ứng viên, kết quả kiểm tra, lịch sử và ngân sách còn lại. Với mỗi ứng viên đã chuẩn hóa $a$, đặt $p_a(s)$ là xác suất **cả kiểu và giá trị được evaluator chấp nhận** nếu xuất $a$. Với `unanswerable`, $p_U(s)$ là xác suất nhãn tham chiếu là `unanswerable`. Lựa chọn tức thời có utility kỳ vọng:

$$
V_{\text{stop}}(s) = \max\left(0,\ \max_{a \in \mathcal A(s)} [2p_a(s)-1],\ 2p_U(s)-1\right).
$$

Nếu đúng được $R$ và sai mất $C$, trả ứng viên có lợi hơn `abstain` khi $pR - (1-p)C > 0$, tương đương $p > C/(R+C)$. DataMate dùng $R=C=1$, nên ngưỡng lý thuyết là **0,5**. Khi bằng đúng ngưỡng có thể chọn `abstain`. Ví dụ $p_a=0,62$ cho kỳ vọng `+0,24`. Khi mọi ứng viên có $p_a<0,5$ nhưng $p_U=0,70$ có bằng chứng, `unanswerable` cho kỳ vọng `+0,40`. Nếu mọi lựa chọn đều dưới 0,5 thì dừng với `abstain` có kỳ vọng 0. [DataMate · Evaluation](https://challenge.zalo.ai/portal/datamate/)

Dùng logistic regression từ các feature có sẵn lúc inference, chẳng hạn kiểm tra schema, số nhánh đưa cùng giá trị, margin giữa hai ứng viên, dấu hiệu fan-out, coverage evidence, số dòng và logprob nếu backend cung cấp. Học đúng/sai từ evaluator trên train. Với ít nhãn, thử rule-based gate làm đối chứng và dùng GBDT khi có đủ dữ liệu. Hiệu chỉnh trên các business riêng, dùng reliability plot/Brier score và đo riêng sau bước chọn top-1 vì selection làm đổi phân phối confidence. Entropy token chỉ là feature. Xác suất cần dùng là xác suất đáp án đã chọn đúng toàn bộ. Ngưỡng thực nghiệm có thể lệch 0,5 do hiệu chỉnh hữu hạn hoặc dịch chuyển domain. [Guo và cộng sự về calibration](https://proceedings.mlr.press/v70/guo17a.html), [Geifman và El-Yaniv về selective classification](https://papers.nips.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf)

Nếu thêm hành động `expand_schema`, `generate_one_more` hoặc `retry_with_rule`, bài toán trở thành quyết định tuần tự. So sánh giá trị dừng với giá trị kỳ vọng của việc thử thêm, chẳng hạn $\mathbb E[V_{\text{stop}}(S')\mid s,a]-\lambda\Delta t$ với một bước nhìn trước. $\lambda$ là giá tài nguyên nội bộ, còn PA chính thức dùng điểm câu hỏi và giới hạn thời gian tách riêng. Bắt đầu bằng rule và một bước nhìn trước từ trace chạy các nhánh cho cùng câu train. Nếu chỉ route một lần rồi kết thúc, có thể mô hình hóa như contextual bandit. Khi hành động thay đổi evidence và mở thêm lựa chọn, có thể dùng MDP hữu hạn theo ngân sách. Chỉ thử offline RL cho policy nhiều bước khi có đủ trace bao phủ hành động, baseline đơn giản đã đo được và lợi ích của retry xuất hiện nhất quán. Log do một policy cố định sinh ra có thể thiếu quan sát để ước lượng hành động khác.

## 3. Học để generator sinh ứng viên tốt hơn

| Hướng | Bài học cho DataMate |
| --- | --- |
| **SFT / rejection sampling fine-tuning** | Sinh nhiều ứng viên trên tập fit, chạy, chọn trajectory đúng và có evidence hợp lý, rồi SFT trên các mẫu đã lọc. Một vòng là supervised learning trên dữ liệu lọc bằng reward. Lặp sinh–lọc–học tạo thành self-training. |
| **DPO / SimPO / ORPO** | Preference optimization trên cặp cùng prompt. Chọn plan đúng và có căn cứ làm `chosen`, plan sai làm `rejected`. DPO dùng policy tham chiếu, SimPO dùng score theo log-prob chuẩn hóa độ dài và margin, ORPO kết hợp SFT với loss theo odds ratio. Các loss này học offline từ preference. |
| **PPO hoặc RL theo rollout** | Lấy mẫu từ policy, thực thi trong harness, tính reward theo evaluator và cập nhật policy. Với LM, action có thể là token hoặc tool call. Cần quản lý credit assignment, reward thưa và chi phí rollout. Với controller nhỏ, action có thể là chọn một bước tiếp theo, trong khi LM giữ cố định. |

Nguồn thuật toán. [ReST](https://arxiv.org/abs/2308.08998), [DPO](https://arxiv.org/abs/2305.18290), [SimPO](https://arxiv.org/abs/2405.14734), [ORPO](https://arxiv.org/abs/2403.07691), [PPO](https://arxiv.org/abs/1707.06347)

Tạo cặp preference từ lỗi có ý nghĩa như sai khoảng ngày, đếm thay vì tính tổng, join nhân bản hoặc sai đơn vị. Đáp án trùng gold có thể do tình cờ hoặc do chương trình hard-code giá trị. Kiểm chứng plan/SQL trên fixture biến đổi và loại mẫu thiếu căn cứ trước khi dùng làm `chosen`. Theo dõi tỷ lệ câu có ít nhất một mẫu hợp lệ theo nhóm lỗi vì lọc quá mạnh dễ làm bộ SFT chỉ còn câu dễ. Dùng `abstain` là một hành động có utility 0. Nếu cần xếp preference theo điểm, thứ tự là đúng > `abstain` > sai, trong đó dự đoán đúng `unanswerable` thuộc nhóm đúng.

Nếu oracle@N thấp, ưu tiên xem retrieval và generator thiếu gì. Nếu oracle@N cao nhưng top-1 thấp, cùng tập ứng viên đó cho phép thử verifier trước khi tốn GPU fine-tune. Chỉ thử một vòng SFT lọc ở mốc đầu nếu các lỗi lặp lại, có đủ trajectory đúng và gói Docker cơ sở đã chạy. Các số đo sau huấn luyện cần giữ nguyên budget inference và split để phân biệt cải thiện của LM với lợi ích từ thêm lượt sinh.

## Những biến cần quản lý ngoài loss và optimizer

- **Dữ liệu và trạng thái**. Độ phủ schema, nhóm doanh nghiệp và nhóm lỗi, chất lượng nhãn, dữ liệu có sẵn tại inference, action hợp lệ và khả năng replay.
- **Reward và proxy**. PA là mục tiêu thi. SQL chạy được, độ đồng thuận, BCE và loss preference là tín hiệu trung gian. Kiểm tra spurious correctness, reward hacking và lệch do chọn mẫu.
- **Rủi ro và độ bất định**. Xem coverage, calibration, số sai và PA theo nhóm. Một mô hình tự tin trên schema quen có thể mất điểm khi gặp doanh nghiệp mới.
- **Ngân sách và vận hành**. Tổng tham số, token, độ trễ, bộ nhớ, số truy vấn, tính tái lập, khả năng chấm và nộp lại từ Docker đã freeze.
