# Báo cáo Issues, Discrepancies & Blockers (Task 2 — Truy vết 60 câu train)

Tài liệu này tổng hợp toàn bộ danh sách issues, các điểm bất thường dữ liệu (discrepancies), bẫy cấu trúc bảng (data traps), và các lý do thiếu bằng chứng dẫn đến quyết định từ chối trả lời (`insufficient_evidence`) được phát hiện trong quá trình thực hiện **Task 2 (Người 2)** theo đặc tả tại [`docs/plan/02-question-tracing.md`](02-question-tracing.md).

Tài liệu không chứa các đáp án nhạy cảm, phục vụ bàn giao trực tiếp cho **Người 3 (Agentic RAG / Prompt)**, **Người 4 (SQL Solver / Runtime)** và **Lead / Người 5 (Review & Sign-off)**.

---

## 1. Bảng Tổng quan 10 Issues Ghi nhận trong Question Trace

Toàn bộ 10 issues dưới đây đã được lập trình và gán tường minh thuộc tính `"decision_owner": "Lead / Người 5"` trong file canonical [`artifacts/data_prep/question_trace.jsonl`](../../artifacts/data_prep/question_trace.jsonl):

| STT | Question ID | Business | Nhóm Issue | Answer Type | Trạng thái Trace | Quyết định & Người chịu trách nhiệm |
|:---:|---|:---:|---|:---:|:---:|---|
| 1 | `q_22f59bab1075` | `biz_112` | Missing Evidence (Blocker) | `unanswerable` | `insufficient_evidence` | **ABSTAIN:** Shop không có sổ kho/thẻ kho (Lead / Người 5) |
| 2 | `q_4333ad0589a1` | `biz_117` | Missing Evidence (Blocker) | `unanswerable` | `insufficient_evidence` | **ABSTAIN:** Shop không theo dõi sổ công nợ (Lead / Người 5) |
| 3 | `q_05a8b30443a1` | `biz_130` | Missing Evidence (Blocker) | `unanswerable` | `insufficient_evidence` | **ABSTAIN:** Toàn bộ là khách vãng lai, không định danh (Lead / Người 5) |
| 4 | `q_04128078842a` | `biz_118` | Missing Evidence (Blocker) | `unanswerable` | `insufficient_evidence` | **ABSTAIN:** Không lưu địa chỉ đường phố chi tiết (Lead / Người 5) |
| 5 | `q_3ad4ff264376` | `biz_105` | Missing Evidence (Blocker) | `unanswerable` | `insufficient_evidence` | **ABSTAIN:** Không có bảng nhận xét/khen ngợi nhân viên (Lead / Người 5) |
| 6 | `q_b4a4c7135e0a` | `biz_103` | Structural Trap (Archetype E8) | `boolean` | `verified` | **FORWARD-FILL:** Bảng phân cấp để trống mã đơn (59-61%) (Lead / Người 5) |
| 7 | `q_09ac426d8fa6` | `biz_123` | Inventory Logic (FIFO) | `date` | `verified` | **FIFO BALANCE:** Đã bán hết 53 lô trước, chỉ còn lô U2606422 tồn 79 hộp (Lead / Người 5) |
| 8 | `q_00c4e64fe706` | `biz_106` | Header vs Line Discrepancy | `number` | `verified` | **PRIORITIZE HEADER:** Lấy cột 'Tổng tiền hàng' thay vì file chi tiết (Lead / Người 5) |
| 9 | `q_00195e1e4049` | `biz_124` | Cutoff & Line Discount | `number` | `verified` | **LINE DISCOUNT:** Trừ chiết khấu dòng hàng; gồm cả đơn sáng ngày as_of_date (Lead / Người 5) |
| 10 | `q_0a76d3680594` | `biz_123` | Payment Method Semantics | `table` | `verified` | **DEBT METHOD ONLY:** COD và chuyển khoản chưa thu không tính nợ (Lead / Người 5) |

---

## 2. Chi tiết 5 Issues Dẫn đến Quyết định Từ chối Trả lời (`unanswerable`)

Theo **Rulebook §7**, hệ thống phải chủ động từ chối trả lời (`ABSTAIN`) khi dữ liệu nguồn không cung cấp bằng chứng, tuyệt đối không được tự suy đoán hoặc trả về `0` / giá trị ngẫu nhiên.

### Issue 1: Không có thẻ kho / sổ tồn kho (`q_22f59bab1075` — `biz_112`)
- **Câu hỏi:** Hỏi số lượng tồn kho của mặt hàng bánh croissant.
- **Hiện trạng vật lý trên đĩa:** Thư mục `train/data/biz_112/` chỉ chứa duy nhất các file doanh số bán hàng theo tháng `So_chi_tiet_ban_hang_*.xlsx` và danh mục sản phẩm, hoàn toàn không có bất kỳ file thẻ kho, sổ kho hay phiếu nhập hàng nào.
- **Kết luận Người 1 & Người 2:** Người 1 ghi nhận `Missing source role: stock_snapshot`. Người 2 kết luận: Thiếu bằng chứng nguồn vật lý $\rightarrow$ `status: "insufficient_evidence"`, `operation: "ABSTAIN"`.

### Issue 2: Không theo dõi sổ công nợ khách hàng (`q_4333ad0589a1` — `biz_117`)
- **Câu hỏi:** Hỏi Top 3 khách hàng nợ tiền nhiều nhất.
- **Hiện trạng vật lý trên đĩa:** Dữ liệu `biz_117` chỉ ghi nhận file bán hàng `SoBanHang.xlsx`. Cột thanh toán chỉ ghi nhận phương thức thanh toán tiền mặt/chuyển khoản tại quầy, không có bảng theo dõi các khoản nợ phải thu (accounts receivable) hay lịch sử thu nợ của khách hàng.
- **Kết luận Người 1 & Người 2:** Người 1 ghi nhận `Missing source role: customers, orders, payments`. Người 2 kết luận: `status: "insufficient_evidence"`, `operation: "ABSTAIN"`.

### Issue 3: Không lưu định danh khách hàng (`q_05a8b30443a1` — `biz_130`)
- **Câu hỏi:** Hỏi tỷ lệ khách hàng mua hàng từ 8 đơn trở lên.
- **Hiện trạng vật lý trên đĩa:** Các file `So_chi_tiet_ban_hang_1/2.xlsx` của `biz_130` chỉ lưu mã đơn và thông tin hàng bán, cột khách hàng để trống hoặc mặc định là khách vãng lai mua tại quầy. Không có mã định danh duy nhất (Customer ID / Phone) để liên kết các lần mua của cùng một khách hàng.
- **Kết luận Người 1 & Người 2:** Người 1 ghi nhận `Khách vãng lai, không định danh`. Người 2 kết luận: Không thể tính số lần mua lặp lại của từng khách $\rightarrow$ `status: "insufficient_evidence"`, `operation: "ABSTAIN"`.

### Issue 4: Không lưu địa chỉ chi tiết đường phố (`q_04128078842a` — `biz_118`)
- **Câu hỏi:** Hỏi doanh thu từ khách hàng sinh sống tại đường Hai Bà Trưng.
- **Hiện trạng vật lý trên đĩa:** File giao hàng `Bảng kê phiếu giao hàng.xlsx` và danh mục khách hàng không lưu trường địa chỉ chi tiết theo số nhà/tên đường; chỉ lưu khu vực quận/huyện hoặc để trống trường địa chỉ.
- **Kết luận Người 1 & Người 2:** Người 1 ghi nhận `Missing source role: customers (thiếu địa chỉ)`. Người 2 kết luận: Không thể lọc khách theo tên đường $\rightarrow$ `status: "insufficient_evidence"`, `operation: "ABSTAIN"`.

### Issue 5: Không có bảng nhận xét / feedback nhân viên (`q_3ad4ff264376` — `biz_105`)
- **Câu hỏi:** Hỏi nhân viên nào được khách hàng khen ngợi nhiều nhất.
- **Hiện trạng vật lý trên đĩa:** `biz_105` chỉ có các file `SoBanHang_*.xlsx` ghi nhận doanh thu bán hàng. Hoàn toàn không có bảng khảo sát ý kiến khách hàng, không có cột feedback hoặc khen ngợi nhân viên phục vụ.
- **Kết luận Người 1 & Người 2:** Người 1 ghi nhận `Không có nguồn nhận xét/khen nhân viên`. Người 2 kết luận: `status: "insufficient_evidence"`, `operation: "ABSTAIN"`.

---

## 3. Chi tiết 5 Issues Bất thường Dữ liệu & Bẫy Cấu trúc (Data Traps)

### Issue 6: Bẫy bảng phân cấp dòng tiếp nối E8 (`q_b4a4c7135e0a` — `biz_103`)
- **Mô tả:** File `DonHang_ChiTiet.xlsx` có 59% đến 61% dòng con để trống cột Mã đơn hàng và Ngày bán.
- **Nguy cơ sai lệch:** Nếu parser chỉ đọc các dòng có đầy đủ mã đơn (header-only), hệ thống sẽ bỏ qua 60% mặt hàng, dẫn đến tính tổng doanh thu 3 tháng là `63.2M > 62.1M` (kết luận xu hướng `False`).
- **Khắc phục:** Bắt buộc áp dụng **Forward-Fill (Archetype E8)** cho nhóm cột `[Mã đơn hàng, Ngày đặt, Trạng thái, Khách hàng]` xuống các dòng con trước khi lọc trạng thái theo Rulebook §1. Sau forward-fill, doanh thu thực tế là `156.3M < 158.2M < 176.7M` (kết luận `True`, khớp chính xác 100% với Gold).

### Issue 7: Nhầm lẫn lô nhập mới nhất với lô gần hết hạn nhất (`q_09ac426d8fa6` — `biz_123`)
- **Mô tả:** Câu hỏi hỏi "Lô Oresol 245 DHG hộp 20 gói gần hết hạn nhất". Gold ghi nhận ngày `2029-04-20`, khiến ban đầu nghi ngờ Gold bị noise vì trên đĩa có các lô nhập có hạn 2026-2028.
- **Phân tích xuất nhập tồn FIFO:** Khi tính cân đối tồn kho theo từng lô:
  $$\text{Tồn kho lô} = \text{SLNhapQuyDoi} - \sum \text{SLQuyDoi (đã bán)} + \sum \text{SLTraQuyDoi (trả)}$$
  cho thấy toàn bộ 53 lô nhập trước ngày 18/06/2026 đều đã được xuất bán sạch hoàn toàn (số tồn = 0). Tại `as_of_date = 2026-06-28`, trong kho **chỉ còn duy nhất một lô còn hàng tồn kho** là lô `U2606422` (nhập 160 hộp, bán 81, còn tồn 79 hộp).
- **Khắc phục:** Áp dụng Rulebook §6 (chỉ xét các lô còn tồn kho tại hôm nay), hạn sử dụng của lô này (`2029-04-20`) là đáp án duy nhất đúng. Runtime bắt buộc phải tính balance tồn kho theo lô trước khi tìm `MIN(HanSuDung)`.

### Issue 8: Lệch số liệu giữa Header và Dòng chi tiết (`q_00c4e64fe706` — `biz_106`)
- **Mô tả:** Tại `biz_106`, doanh thu tháng 5/2025 có sự bất nhất nội bộ:
  - Header `DanhSachHoaDon.xlsx`, cột `Tổng tiền hàng`: `271.866.000 đ` (khớp Gold).
  - Header `DanhSachHoaDon.xlsx`, cột `Tổng sau giảm giá`: `277.641.000 đ`.
  - Tổng dòng chi tiết thô ban đầu: `279.060.500 đ`.
- **Tái kiểm tra:** Exact dedup các dòng giống hệt chỉ trong cùng mã đơn (giữ dòng giống hệt nếu thuộc đơn khác). Tổng chi tiết sau dedup là `271.866.000 đ`, khớp cột `Tổng tiền hàng` và Gold. Verifier có regression trên nguồn cho kết luận này.
- **Kết luận:** Không dùng ưu tiên header để che độ lệch; dedup chi tiết đúng grain trước khi tổng hợp. Reviewer confirmation được theo dõi riêng với kiểm tra kỹ thuật.

### Issue 9: Cutoff thời gian và Chiết khấu dòng hàng (`q_00195e1e4049` — `biz_124`)
- **Mô tả:** Doanh thu thuốc Natri clorid tháng 5/2026: Đến hết ngày 24/05/2026 đạt 168 dòng hợp lệ lũy kế 2.899.800 đ. Buổi sáng ngày `as_of_date = 2026-05-25` phát sinh thêm 2 dòng hợp lệ đưa tổng lên 170 dòng với 2.958.600 đ.
- **Khắc phục:** Sau khi trừ 4.400 đ tiền chiết khấu/khuyến mãi trực tiếp trên dòng hàng, doanh thu ròng đạt đúng `2.954.200 đ` (khớp 100% với Gold). Runtime phải tính cả các đơn hàng phát sinh trong ngày `as_of_date` và trừ chiết khấu dòng hàng theo Rulebook §1.

### Issue 10: Phân biệt Phương thức Thanh toán Công nợ (`q_0a76d3680594` — `biz_123`)
- **Mô tả:** Câu hỏi yêu cầu số dư khách hàng còn phải thu tại ngày 12/07/2025. Cách cũ chỉ giữ `PhuongThucTT = 'debt'`, trái Rulebook §4.
- **Tái tính:** Cộng payment theo khóa cửa hàng + hóa đơn đến cutoff trước khi join vào đơn; loại đơn hủy, COD và đơn từ kênh sàn TMĐT; giữ số dư chưa thu khác theo rulebook. Top 5 tái tính từ SQLite khớp Gold.
- **Kết luận:** Trace được tái tính và so sánh kỹ thuật pass. Reviewer vẫn cần xác nhận kết luận nghiệp vụ độc lập.

## Trạng thái kiểm tra và bàn giao

- **Kiểm tra kỹ thuật:** regression typed answer, metadata/ID/split, tồn kho và công nợ chạy độc lập; generator so sánh `computed_answer` với reference thay vì tin cờ `match` có sẵn.
- **Discrepancy còn mở:** verifier phải kết thúc khác 0 nếu có trace `unresolved`. Lần nghiệm thu hiện tại: 60 trace khớp reference, 322/322 cột nguồn hợp lệ, 10 phép tính live pass, không còn discrepancy kỹ thuật.
- **Lỗi kỹ thuật baseline:** `uv sync --locked` không thể build package do checkout thiếu `src/datamate/__init__.py`; full unittest giữ nguyên 4 lỗi import `datamate` từ baseline. 6 regression tracing mới pass.
- **Reviewer:** tên reviewer trong trace không phải xác nhận mới. Chưa có xác nhận người review cho hai kết luận đã tái tính; cần hoàn tất sign-off trước khi báo PR sẵn sàng merge.

---

## 4. Issues Phối hợp Kỹ thuật với Người 1 (Data Catalog)

Hai issue kỹ thuật được Người 1 ghi nhận tại [`docs/data-catalog-handoff.md`](../data-catalog-handoff.md) đã được Người 2 kiểm chứng và xác nhận giải pháp:

1. **Bẫy 1.549 dòng nhãn tổng cộng tại `biz_107`, `biz_110`, `biz_130`:**
   - Người 1 cảnh báo bảng tính trộn lẫn dòng dữ liệu và dòng tổng cộng ("Tổng", "Tổng cộng", "Ngày...").
   - Người 2 xác nhận: Runtime phải luôn có bước lọc dòng: kiểm tra cột mã đơn/ngày hợp lệ và loại bỏ các dòng có text tổng cộng. Đồng thời, đối với `biz_130` và `biz_112`, header thật nằm ở dòng 4 (sau 3 dòng tiêu đề báo cáo).
2. **Cột ngày số serial Excel 1900 tại `biz_111` (`don_hang.csv`):**
   - 16.594 dòng trong cột `NgayBan` là số nguyên serial Excel (vd: 45789) trộn lẫn với ngày chuỗi (`d_thg_m_yyyy`).
   - Người 2 xác nhận: Parser ngày bắt buộc phải nhận diện cả định dạng numeric string và convert theo epoch 1900 (`datetime(1899, 12, 30) + timedelta(days=val)`).

---

## 5. Hướng dẫn Bàn giao cho Phase P2 (Runtime & Inference)

- **Người 3 (Agentic RAG):** Đưa các định nghĩa blocker của 5 câu `unanswerable` vào prompt instructions để agent biết chủ động từ chối khi thiếu nguồn, không rơi vào bẫy hallucinate (bịa số).
- **Người 4 (DataFusion / SQL Solver):**
  - Cài đặt pipeline tiền xử lý cho họ bảng phân cấp Archetype E8 (`biz_103`, `biz_121`, `biz_122` và public test `dev_004, dev_005, dev_007, dev_013`).
  - Viết câu lệnh truy vấn tồn kho FIFO tính balance cho các câu hỏi dược phẩm hạn dùng tại `biz_123`.
- **Người 5 (Evaluation & Lead):** Duyệt danh mục 10 issues và nghiệm thu Phase P1 Task 2.
