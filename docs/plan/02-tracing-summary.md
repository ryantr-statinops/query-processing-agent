# Báo cáo tổng hợp Task 2 — Truy vết 60 câu train

## 1. Kết quả tổng thể và kiểm tra cuối Phase P1

Theo đúng quy chuẩn của [`docs/plan/02-question-tracing.md`](02-question-tracing.md) và tiêu chí chuyển bước tại [`rebuild.md`](rebuild.md), toàn bộ 60 câu hỏi đại diện trong [`configs/representative_questions.json`](../../configs/representative_questions.json) đã được truy vết, lập phép tính kiểm chứng độc lập trên dữ liệu thực tế tại `train/data/` và thỏa mãn 100% cả 5 tiêu chí cuối phase.

| Chỉ số kiểm tra cuối phase | Yêu cầu kế hoạch | Kết quả thực tế | Trạng thái |
|---|---|---|:---:|
| **1. Số lượng & độ phủ bản ghi** | Đủ 60 record, khớp ID/Business/as_of_date | 60/60 record, 21 trường schema tối thiểu | **ĐẠT** |
| **2. Bằng chứng nguồn trên đĩa** | Khớp 100% file/sheet/bảng/cột thực tế | 95 source refs, 70 sheets/tables, 322/322 column headers xác minh vật lý trên đĩa (0 cột ảo) | **ĐẠT** |
| **3. Tái tính toán độc lập trên đĩa** | Tái tính trên đĩa đủ các answer type & edge cases | 10 mẫu độc lập phủ đủ 8 answer types (relative date, unit, hierarchy, SQLite FIFO, ranking, percent, abstain, string, table, peak date) | **ĐẠT** |
| **4. Phân tách tập Development / Holdout** | 48 câu dev, 12 câu holdout cách ly tuyệt đối | 48 dev (24 biz), 12 holdout (6 biz: `biz_103, 106, 107, 109, 113, 127`) | **ĐẠT** |
| **5. Quy trình Review hai cấp** | Người 1 xác nhận schema; Lead review discrepancy | Hoàn tất sign-off: Người 1 (catalog/schema) + Nam (auditor) + Lead | **ĐẠT** |

---

## 2. Phân bổ theo kiểu đáp án (`answer_type`)

| Answer Type | Số câu | Đặc điểm & Phép toán chính |
|---|:---:|---|
| **`date`** | 20 | Xếp hạng ngày doanh thu cao nhất trong tháng (`daily_revenue_ranking`), so sánh tháng cao nhất (`period_comparison`), hạn sử dụng lô thuốc gần nhất (`lot_expiry`). |
| **`number`** | 13 | Tổng doanh thu tháng/ngày, doanh thu theo hoạt chất, số đợt giao hàng, giá nhập bình quân gia quyền, số lượng bán của mặt hàng, đếm đơn hàng. |
| **`percent`** | 6 | Tỉ lệ huỷ đơn, tăng trưởng doanh thu so với tháng trước (MoM), tỉ trọng nhóm hàng/nhóm khách so với toàn shop. |
| **`boolean`** | 5 | Kiểm tra xu hướng doanh thu 3 tháng liên tiếp có tăng trưởng nghiêm ngặt (`m1 < m2 < m3`). |
| **`table`** | 5 | Bảng xếp hạng Top N khách hàng nợ nhiều nhất (`columns: ['khach_hang', 'so_tien_no']`). |
| **`list`** | 4 | Top 3/5 mặt hàng bán chạy nhất; chuỗi doanh thu 3 tháng liên tiếp; phân bổ doanh thu theo kênh bán (Zalo OA vs tại quầy). |
| **`unanswerable`** | 5 | Các câu hỏi thiếu bằng chứng trong dữ liệu nguồn (không có sổ kho, không theo dõi công nợ, không lưu địa chỉ khách hàng). |
| **`string`** | 2 | Tên mặt hàng bán chạy nhất trong tháng. |

---

## 3. Bàn giao cho Người 3 — Tóm tắt các Pattern lặp lại (Agentic RAG)

Người 3 cần đưa các quy ước sau vào prompt context và tool schema:

1. **Chuẩn hóa mốc thời gian tương đối (`as_of_date`):**
   - Mọi câu hỏi có yếu tố "tháng này", "tuần này", "hôm nay", "hôm qua", "bữa qua" phải resolve tuyệt đối dựa trên `as_of_date` của câu hỏi.
   - "Tháng này" = từ ngày 1 đến hết `as_of_date`.
   - "Tuần này" = từ thứ Hai của tuần chứa `as_of_date` đến hết `as_of_date`.
   - "Hôm qua / bữa qua" = ngày liền trước `as_of_date`.
   - Tuyệt đối không đọc các bản ghi phát sinh sau `as_of_date`.

2. **Quy tắc Doanh thu (Rulebook §1):**
   - Đơn tính vào doanh thu: **bỏ toàn bộ đơn bị huỷ hoặc có trả hàng** (kể cả chỉ trả 1 dòng).
   - Doanh thu = tổng thành tiền của các dòng hàng (đã trừ chiết khấu dòng). Không trừ giảm giá cả đơn, không cộng phí giao hàng hay thuế VAT.

3. **Bảng phân cấp và dòng tiếp nối (Archetype E8 — Forward-Fill):**
   - Ở các business dạng bảng phân cấp (`biz_103`, `biz_121`, `biz_122` và public test `dev_004`, `dev_005`, `dev_007`, `dev_013`), mã đơn hàng, ngày đặt, trạng thái và tên khách chỉ xuất hiện ở dòng đầu tiên của đơn, các dòng sản phẩm tiếp theo để trống cột mã đơn.
   - **Xử lý:** Phải forward-fill nhóm cột đơn (mã đơn, ngày, trạng thái, khách), **tuyệt đối không forward-fill** cột sản phẩm/số lượng/thành tiền. Trạng thái sau khi forward-fill quyết định tính hợp lệ của toàn bộ các dòng hàng con.

4. **Quy tắc Bán chạy (Rulebook §3):**
   - Xếp hạng bán chạy dựa trên **số lượng quy đổi về đơn vị cơ bản**, không xếp theo số tiền hay số lần xuất hiện dòng. Dòng phí phục vụ không tính.

5. **Quy tắc Công nợ (Rulebook §4):**
   - Chỉ tính đơn của khách hàng có định danh; **bỏ đơn khách lẻ** khỏi bảng công nợ theo khách.
   - Loại đơn COD và đơn từ kênh sàn TMĐT khỏi công nợ theo Rulebook §4. Tính số dư tại cutoff sau khi tổng hợp payment trước khi join theo khóa cửa hàng + hóa đơn; không giới hạn nguồn thành đơn có nhãn `debt`.

6. **Quy tắc Từ chối trả lời (`unanswerable`, Rulebook §7):**
   - Khi business không lưu trữ loại thông tin được hỏi (không có thẻ kho/sổ tồn, không có sổ công nợ, không lưu địa chỉ khách), hệ thống phải chủ động trả về `unanswerable` với blocker cụ thể, không được suy đoán hoặc trả về 0.

---

## 4. Bàn giao cho Người 4 — Bộ câu đã tái tạo (Baseline Runtime)

Danh sách 60 câu hỏi cùng toàn bộ source reference (bảng, cột, grain) đã được kiểm chứng chuẩn xác:
- **30 Business** phân bổ vào các họ schema vật lý trên đĩa (chuẩn hóa theo [`docs/business-schema-map.md`](../business-schema-map.md)):
  1. **Họ Flat CSV:** `ban_hang.csv` (`biz_101`, `biz_114`, `biz_125`) và `danh_sach_hoa_don.csv` (`biz_110`).
  2. **Họ Relational Multi-CSV:** 5 file CSV quan hệ `don_hang.csv`, `chi_tiet_don.csv`, `san_pham.csv`, `khach_hang.csv`, `thanh_toan.csv` (`biz_111`, `biz_127`, `biz_129`).
  3. **Họ Flat Excel đơn:** `SoBanHang.xlsx` (`biz_107`, `biz_113`, `biz_126`).
  4. **Họ Excel phân kỳ theo tháng (Multi-sheet / Multi-file):** Sheet theo tháng hoặc file theo tháng (`biz_102`, `biz_104`, `biz_105`, `biz_106`, `biz_112`, `biz_115`, `biz_118`, `biz_119`, `biz_120`, `biz_128`, `biz_130`).
  5. **Họ Bảng phân cấp (Hierarchical Continuation Rows - E8):** Dòng con để trống mã đơn (`biz_103`, `biz_121`, `biz_122`).
  6. **Họ Excel Đa bảng / Dược phẩm:** `BanHang_Thuoc.xlsx`, `BanHang_ChiTietHoaDon.xlsx`, `BanHang_HoaDon.xlsx` (`biz_124`).
  7. **Họ Relational SQLite:** `pos.sqlite` chuẩn hoá 17 bảng (`biz_123`).
- **File artifact kết quả:**
  - File canonical duy nhất: [`artifacts/data_prep/question_trace.jsonl`](../../artifacts/data_prep/question_trace.jsonl)
- **Script tái hiện kiểm chứng:**
  - Chạy `python -u scripts/verify_phase_criteria.py` để tự động kiểm chứng toàn bộ 5 tiêu chí cùng 10 bài toán tái tính toán độc lập phủ đủ 8 kiểu đáp án bất kỳ lúc nào.

---

## 5. Bàn giao cho Lead & Người 5 — Discrepancies & Blocker đã xử lý

1. **Giải quyết câu nghi ngờ nhãn ở bảng phân cấp (`biz_103`, `q_b4a4c7135e0a`):**
   - *Vấn đề ban đầu:* Nghi ngờ label noise khi tính tổng không forward-fill ra 63.2M / 62.1M / 69.5M (False).
   - *Thực tế xác minh:* `DonHang_ChiTiet.xlsx` có 59-61% dòng con để trống mã đơn. Khi áp dụng chuẩn forward-fill theo Archetype E8, doanh thu thực tế là:
     - Tháng 11/2025: 156.289.700 đ
     - Tháng 12/2025: 158.205.600 đ
     - Tháng 01/2026: 176.720.800 đ
     - `156.289.700 < 158.205.600 < 176.720.800` $\rightarrow$ **`True`**. Khớp 100% với đáp án Gold. Kết luận: Nhãn Gold hoàn toàn chính xác, không có label noise.

2. **Giải mã câu hỏi hạn sử dụng lô thuốc tại `biz_123` (`q_09ac426d8fa6`):**
   - *Vấn đề nghi ngờ:* Câu hỏi hỏi "Lô Oresol 245 DHG hộp 20 gói gần hết hạn nhất", Gold ghi nhận `2029-04-20`, khiến kiểm toán ban đầu nghi ngờ câu hỏi lấy nhầm lô nhập mới nhất thay vì lô hạn ngắn nhất (vì có các lô hạn 2026-2028).
   - *Thực tế xuất nhập tồn (FIFO) xác minh từ SQLite:*
     - Kiểm tra toàn bộ lịch sử xuất bán qua bảng `lo_hang`, `phieu_nhap` và `chi_tiet_don_lo` cho thấy: Tất cả các lô nhập trước ngày 18/06/2026 (kể cả các lô có hạn 2026 hay 2027-2028) đều đã được xuất bán sạch hoàn toàn (Số lượng bán = Số lượng nhập, tồn kho cuối bằng 0).
     - Tại thời điểm `as_of_date = 2026-06-28`, trong kho **chỉ còn duy nhất một lô còn tồn hàng** là lô `U2606422` (nhập 160 hộp ngày 18/06/2026, đã bán 81 hộp, còn tồn 79 hộp).
     - Áp dụng Rulebook §6 (Nhà thuốc): "Lô gần hết hạn nhất của một thuốc = trong các lô **còn tồn chưa quá hạn tại hôm nay**, lô có hạn sớm nhất". Vì chỉ còn duy nhất lô `U2606422` còn tồn trong kho, hạn sử dụng của lô này (`2029-04-20`) hiển nhiên là đáp án duy nhất đúng. Đây không phải label noise mà là phép tính tồn kho theo lô (batch inventory balance) hoàn toàn chuẩn xác.

3. **Đối chiếu doanh thu header/chi tiết tại `biz_106` (`q_00c4e64fe706`):**
   - Tại `DanhSachHoaDon.xlsx`, cột header `Tổng tiền hàng` tháng 5/2025 đạt đúng `271.866.000` (khớp Gold).
   - Header `Tổng sau giảm giá` là `277.641.000`; detail thô là `279.060.500`. Sau exact dedup trong từng đơn (không dedup qua các đơn khác nhau), tổng detail còn `271.866.000`, khớp header và Gold. Verifier có regression trên dữ liệu nguồn.

4. **Ghi nhận độ lệch cutoff thời gian tại `biz_124` (`q_00195e1e4049`):**
   - Thuốc hoạt chất Natri clorid (`SP0005`, `SP0039`) trong tháng 5/2026 đến hết ngày 24/05/2026 đạt 168 dòng hợp lệ lũy kế 2.899.800đ; giao dịch buổi sáng ngày 25/05/2026 (2 dòng) đưa tổng dòng lên 170 dòng với 2.958.600đ trước chiết khấu dòng, và 2.954.200đ sau chiết khấu dòng (khớp chính xác Gold). Đã ghi nhận trong `uncertainty`.

5. **Các câu thiếu bằng chứng nguồn (Unanswerable) có blocker cụ thể:**
   - `q_22f59bab1075` (`biz_112`): Hỏi tồn kho bánh croissant nhưng shop chỉ có các file doanh số bán hàng `BanHang_Thang*.xlsx`, hoàn toàn không có sổ kho/thẻ kho.
   - `q_4333ad0589a1` (`biz_117`): Hỏi Top 3 khách nợ nhưng shop không lưu trữ sổ theo dõi công nợ hay lịch sử thanh toán khách hàng.
   - `q_05a8b30443a1` (`biz_130`): Hỏi tỉ lệ khách mua >= 8 đơn nhưng shop không lưu định danh khách hàng (toàn bộ là khách vãng lai).
   - `q_04128078842a` (`biz_118`): Hỏi khách ở đường Hai Bà Trưng nhưng dữ liệu không lưu trường địa chỉ chi tiết.
   - `q_3ad4ff264376` (`biz_105`): Hỏi nhân viên được khen nhiều nhất nhưng dữ liệu chỉ có đơn hàng, không có bảng ghi nhận đánh giá/feedback nhân viên.

---

## 6. Nhật ký Tái tính toán Độc lập trên Dữ liệu Đĩa (Phase Check #3)

Được thực thi trực tiếp bởi script [`scripts/verify_phase_criteria.py`](../../scripts/verify_phase_criteria.py) phủ đủ cả 8 loại đáp án:

| STT | Câu hỏi / Business | Answer Type | Phép toán & Đặc trưng kỹ thuật | Kết quả tái tính | Kết quả Gold | Trạng thái |
|---|---|:---:|---|:---:|:---:|:---:|
| 1 | `q_0fb7868ac463` (`biz_107`) | `number` | **Relative Date:** Doanh thu ngày hôm qua (2026-04-17), trừ đơn trả hàng 30k | 7.490.000 | 7.490.000 | **PASS** |
| 2 | `q_00a6e23cbacf` (`biz_109`) | `number` | **Unit Conversion:** Giá nhập bình quân mì Omachi thùng = 5.415.000đ / 27 thùng | 200.556 | 200.556 | **PASS** |
| 3 | `q_b4a4c7135e0a` (`biz_103`) | `boolean` | **Hierarchical Forward-Fill:** 156.3M < 158.2M < 176.7M | True | True | **PASS** |
| 4 | `q_00558c1410ef` (`biz_105`) | `percent` | **Percent Share:** Tỷ lệ hủy đơn T6/2025 = 103 / 4.948 đơn | 2.08% | 2.08% | **PASS** |
| 5 | `q_09ac426d8fa6` (`biz_123`) | `date` | **FIFO Inventory Balance:** Hạn sử dụng lô Oresol duy nhất còn tồn kho (lô U2606422 còn 79 hộp) | 2029-04-20 | 2029-04-20 | **PASS** |
| 6 | `q_019ec94d9799` (`biz_106`) | `list` | **Top-K Ranking:** Top 3 đồ uống tuần này (68, 50, 46 ly) | Cà phê sữa, Trà đào, Cà phê đen | Cà phê sữa, Trà đào, Cà phê đen | **PASS** |
| 7 | `q_22f59bab1075` (`biz_112`) | `unanswerable` | **Missing Evidence:** Xác thực hoàn toàn không có file/sổ kho | None (Abstain) | None (Abstain) | **PASS** |
| 8 | `q_0e0d5a37fc1c` (`biz_114`) | `string` | **Top Product Base Unit:** Mặt hàng bán chạy nhất T6/2025 theo ĐV cơ bản | Gạch ống 8x8x18 Tuynel | Gạch ống 8x8x18 Tuynel | **PASS** |
| 9 | `q_25732168db6e` (`biz_123`) | `table` | **Multi-table Debt Balance:** Bảng top 5 khách nợ nhiều nhất | Đỗ Đức An (404.5k), Dương Tâm Bích (158.6k)... | Đỗ Đức An (404.5k), Dương Tâm Bích (158.6k)... | **PASS** |
| 10 | `q_d68a91438a2e` (`biz_117`) | `date` | **Daily Peak / VND Parser:** Ngày doanh thu cao nhất T5/2025 (parse '6tr270', '10tr750') | 2025-05-11 (77.634.500) | 2025-05-11 | **PASS** |

---

## 7. Ký duyệt Hai cấp (Two-Tier Sign-off)

- **Cấp 1 — Người 1 (Catalog & Data Schema Verification):**
  - Xác nhận 95/95 source references và 322/322 tên cột khớp chính xác 100% với cấu trúc vật lý trên đĩa (đã kiểm tra header_row thực tế) và profile tại [`docs/business-schema-map.md`](../business-schema-map.md).
- **Cấp 2 — Người 2 (Auditor) & Người 5 (Lead Sign-off):**
  - Xác nhận bộ 60 trace records tại [`artifacts/data_prep/question_trace.jsonl`](../../artifacts/data_prep/question_trace.jsonl) độc lập, không có số liệu trung gian tự biên, 100% câu unanswerable có blocker rõ ràng và trạng thái `insufficient_evidence` với `operation = ABSTAIN`, giải quyết triệt để tất cả phản hồi kiểm toán và sẵn sàng bàn giao cho Người 3 và Người 4.
