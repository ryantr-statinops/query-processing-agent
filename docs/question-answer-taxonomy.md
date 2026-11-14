# Question & answer taxonomy

Phân tích `train/questions.jsonl` (3.000 câu), `train/answers.jsonl` (3.000 nhãn) và `public_test/questions.jsonl` (1.000 câu).
Trạng thái: **đã xác minh** bằng script trong `analysis/` (chỉ đọc, không sửa dữ liệu nguồn).

## 1. Cấu trúc bản ghi

```json
// questions.jsonl — 4 field, không có field nào khác
{"id": "q_001883280e83", "business_id": "biz_128",
 "question": "tháng này tổng giá trị các phiếu nhập hàng là bao nhiu",
 "as_of_date": "2026-09-07"}

// answers.jsonl — 4 field
{"id": "q_001883280e83", "type": "number", "answer": 89526400, "alias": []}
```

- `as_of_date` là "hôm nay" của từng câu → mọi cách nói tương đối phải quy chiếu theo đây, **không** theo ngày chạy.
- `alias` (167/3000 dòng khác rỗng) là **cách viết thay thế được chấp nhận**: với `string`/`list` là mã hàng / mã khách song song với đáp án chính; với `table` là danh sách mã theo từng dòng.
- `answers.jsonl` chỉ có ở `train`. `public_test` **không có nhãn** → không được dùng để dò đáp án.

## 2. Answer contract (8 type)

| type | Số câu (train) | Format | Ví dụ đúng | Lỗi thường gặp |
|---|---:|---|---|---|
| `number` | 1884 | JSON number, không đơn vị, không phân cách nghìn | `4820000`, `18.6` | `"4.820.000"`, `"4,82 triệu"` |
| `percent` | 578 | JSON number = số %, không ký hiệu `%` | `12.4` | `"12,4%"`, `0.124` |
| `date` | 145 | `"YYYY-MM-DD"`; câu theo tháng → `"YYYY-MM"` | `"2026-08-15"`, `"2025-09"` | `"15/08/2026"` |
| `boolean` | 23 | `true` / `false` | `true` | `"có"`, `1` |
| `string` | 88 | tên **nguyên văn trong dữ liệu**, đủ dấu | `"Sting dâu 330ml"` | sai dấu, bọc trong mảng |
| `list` | 193 | mảng JSON, **có thứ tự**, 1 phần tử vẫn là mảng | `["Cà phê sữa"]`, `[3, 10]` | `"a, b"` |
| `table` | 19 | `{"columns": [...], "rows": [[...]]}`, ô số là number | xem dưới | ô `"3.200.000đ"` |
| `unanswerable` | 70 | `{"type": "unanswerable"}` | | trả `0`/`null` thay vì unanswerable |

Chi tiết cần nhớ:

- **`table` chỉ có đúng một dạng** trong train: `{"columns": ["khach_hang", "so_tien_no"], "rows": [[tên, số_nợ], ...]}` — top-k khách nợ nhiều nhất. Thứ tự dòng không ảnh hưởng chấm.
- **`list`**: chỉ gặp 2, 3, 5, 11 phần tử (11: danh sách mặt hàng theo hạn dùng). Thứ tự là một phần của đáp án: số đo giảm dần, hoà thì theo mã tăng dần.
- **`date` theo tháng** trả `"YYYY-MM"` — đừng trả ngày 1 của tháng.
- **`percent` luôn 2 chữ số thập phân** (2.08, 14.89, -50.0), `number` tiền là **số nguyên VND**.
- Câu nhiều số → `list` theo đúng thứ tự câu hỏi nêu ("nợ thêm, trả được" → `[nợ, trả]`).

## 3. Phân bố theo business

- `train`: 30 biz × ~118 câu; 5 biz chỉ 40 câu (`biz_101, 107, 110, 113, 114, 125, 126` — nhóm dữ liệu phẳng/1 file).
- `public_test`: 14 dev × 21–129 câu.
- Mỗi biz có **cấu trúc file riêng** → không thể một SQL template dùng cho tất cả; xem `business-schema-map.md`.

## 4. Intent taxonomy (phân loại theo từ khoá, train)

| Nhóm ý định | Số câu | % | Answer type thường gặp |
|---|---:|---:|---|
| Doanh thu (ngày/tháng/quý/năm, theo kênh, theo nhóm khách) | 706 | 23.5% | number 624, list 45, boolean 23 |
| % thay đổi / so sánh kỳ trước | 357 | 11.9% | percent 343 |
| Giá trị trung bình một đơn | 197 | 6.6% | number 194 |
| Số đơn | 197 | 6.6% | number 194 |
| Tỉ lệ / số đơn huỷ | 182 | 6.1% | percent 132, number 49 |
| Bán chạy (top / số lượng theo đơn vị) | 148 | 4.9% | number 66, list 55, string 25 |
| Ngày/tháng doanh thu cao nhất | 148 | 4.9% | date 139 |
| Giá bán / hiệu ứng tăng giá | 107 | 3.6% | percent 81 (hiệu ứng), number 26 |
| Công nợ / tuổi nợ / trả nợ | 102 | 3.4% | number 54, list 25, table 19 |
| Nhà thuốc: kê đơn, hoạt chất | 90 | 3.0% | number 68, percent 21 |
| Nhập hàng / nhà cung cấp | 71 | 2.4% | number 63, string 6 |
| Top khách | 70 | 2.3% | list 42, string 21 |
| Tồn kho / hết hàng / hết hạn | 69 | 2.3% | number 42, list 17 |
| Nhân viên bán giỏi | 17 | 0.6% | string 7, number 6 |
| Giao hàng nhiều đợt | 13 | 0.4% | number 12 |
| Lãi gộp / lãi ròng | 15 | 0.5% | string 6, number 5 |
| Lô hàng / hạn dùng | 3 | 0.1% | number 3 |
| **Khác** (chưa khớp từ khoá) | 492 | 16.4% | number 461 |

Nhóm "khác" không phải loại câu mới — chủ yếu là **cùng ý định nhưng viết telex/viết tắt** ("check gium hnay cua hang co bao nhiu don", "tong revenue trong ngay hom nay"), hoặc câu hỏi rất đặc thù:
`số mặt hàng ế`, `số mặt hàng xuất hiện ở ≥N đơn`, `số khách mua ≥N đơn`, `số ngày bán ≥X đồng`, `số cục xà bông bán ra`, `tiền thu máy cũ`, `hoa hồng thợ`.

→ Bộ phân loại ý định phải chịu được **tiếng Việt không dấu + sai chính tả**, không chỉ regex có dấu.

## 5. Văn phong câu hỏi

- **2.875/3.000 câu (95,8%) viết không dấu / telex / sai chính tả**: `bnhiu`, `nhiu`, `dc`, `ko`, `hqua`, `hnay`, `cuwar hàng`, `thangs`, `nowj`.
- Độ dài trung bình 63 ký tự; nhiều câu trộn Anh–Việt: `total`, `revenue`, `size m`, `top`, `total bn tien`.
- Cùng một ý có 10+ cách diễn đạt ("doanh thu", "dthu", "bán được bao nhiêu tiền", "thu về bao nhiêu", "tổng cộng bao nhiêu tiền") → **không** map 1-1 theo từ khoá; cần lớp chuẩn hoá.
- 1.547 câu (51,6%) nêu `tháng M/YYYY` tường minh; 323 câu (10,8%) nêu `tháng M` không năm (phải suy ra năm theo luật rulebook §2).

## 6. Mốc thời gian xuất hiện (đếm câu, train)

| Cách nói | Số câu | % |
|---|---:|---:|
| `tháng M/YYYY` | 1547 | 51.6% |
| `tháng M` (không năm) | 323 | 10.8% |
| `hôm nay` / `hnay` | 249 | 8.3% |
| ngày cụ thể `dd/mm/yyyy` | 248 | 8.3% |
| `tháng này` | 151 | 5.0% |
| `hôm qua` | 139 | 4.6% |
| `quý Q` | 81 | 2.7% |
| khoảng `từ X đến Y` | 35 | 1.2% |
| `đến hết ngày X` / `tính đến` | 32 | 1.1% |
| `tuần trước/rồi` | 27 | 0.9% |
| `N ngày kể từ <ngày tăng giá>` | 19 | 0.6% |
| `từ đầu năm` | 11 | 0.4% |
| `N ngày gần nhất` | 11 | 0.4% |
| `tuần này` | 7 | 0.2% |
| `Tết` | 1 | 0.03% |

`public_test` nghiêng về ngày cụ thể và tuần hơn, nhưng cùng bộ mốc.

Lưu ý phân biệt ngữ nghĩa (rulebook §2):
- "Ngày X …" → **phát sinh trong ngày**.
- "đến hết ngày X" / "tính đến hôm nay" → **tồn tại thời điểm** (nợ, tồn kho), cộng dồn từ đầu dữ liệu.
- "`tháng này`" → từ 1 đến **hết hôm nay**, không phải cả tháng.

## 7. Vì sao có 70 câu `unanswerable`

Bốn nhóm nguyên nhân (đã đối chiếu mẫu):

1. **Kỳ nằm hoàn toàn ngoài khoảng dữ liệu** của shop. Ví dụ shop có dữ liệu từ 05/2025 nhưng hỏi "tháng 2/2025", "tháng 3/2025", "tháng 1 năm 2025" → không phải 0.
2. **Shop không ghi loại thông tin đó**: hỏi tồn kho / giá vốn / tồn theo lô / nhập hàng ở shop chỉ có file bán hàng; hỏi "tỉ lệ huỷ" ở shop không có cột trạng thái.
3. **Thông tin chủ quan, không có trong file**: "ai là người lành nghề nhất", "khách hay khen nhân viên nào nhất", "lê phúc đạt có lễ phép không", "ai được khách quý mến nhất", "thời tiết".
4. **Không thể suy ra từ cột khác**: địa chỉ khách ("mấy khách nhà ở đường Hai Bà Trưng") khi shop không có danh sách khách hàng.

Ngược lại, **kỳ chỉ nằm một phần trong dữ liệu thì vẫn phải tính** trên phần có dữ liệu (không được abstain).

## 8. Hệ quả cho solver

1. **Chốt `type` trước, tính `answer` sau.** Sai format = sai, kể cả giá trị đúng.
2. **Chuẩn hoá câu hỏi** (bỏ dấu, sửa telex, tách số/ngày) trước khi phân loại ý định.
3. **Mỗi biz cần một "hồ sơ schema"**: cột ngày, cột doanh thu, cột trạng thái, bảng quy đổi, bảng khách/nhân viên, tồn kho, công nợ. Đây là thứ `business-schema-map.md` cung cấp.
4. **Luôn kiểm tra độ phủ ngày** trước khi trả số: nếu kỳ ⊄ [min_date, cutoff] → `unanswerable`, nhưng nếu giao một phần → tính phần giao.
5. **Không bịa đơn vị**: câu hỏi "bao nhiêu <đơn vị>" phải cộng theo `SL quy đổi` của các mặt hàng có đơn vị cơ bản = đơn vị đó.
6. **Loại dòng không phải hàng** (`Phí phục vụ`, `Voucher`, `Dùng N điểm`, `Phí ship`, `Topping` ghi chung ô) khi xếp hạng/đếm mặt hàng, nhưng vẫn tính vào doanh thu (trừ Voucher/Dùng điểm ghi số âm).
