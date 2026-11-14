# Business schema map

Bản đồ ngữ nghĩa **từng business** (30 `biz_*` + 14 `dev_*`), dựng từ 44 `README.md` trong `train/data` + `public_test/data`, đã **đối chiếu với header thật** đọc bằng `openpyxl`/`csv`/`sqlite3`.

Trạng thái cột: **đã xác minh** = tên cột đọc từ file trùng README; **lệch** = README khác header thật (ghi rõ).
Script sinh dữ liệu: `analysis/04_inventory.py`, `05_headers.py`, `06_header_rows.py`, `09_number_style.py`, `10_status_values.py`, `11_products.py`.

> Không sửa file nguồn. Mọi chuẩn hoá làm trong bộ nhớ.

---

## Phần A — 9 archetype dữ liệu

Chỉ có 9 kiểu đóng gói; mọi business là một tổ hợp của chúng.

### A1. Sổ phẳng 1 file (mỗi dòng = 1 dòng hàng)

`biz_101, biz_107, biz_113, biz_114, biz_125, biz_126`; một phần `biz_130`, `dev_001`.

| Vai trò | Cột thật (theo shop) |
|---|---|
| ngày bán | `Ngày tháng` / `ngay_ban` / `Ngày mua` / `Ngày` / `Ngày bán` |
| tên hàng | `Nội dung` / `Mặt hàng` / `Sản phẩm` / `Ten hang` / `Hàng bán` |
| số lượng | `so_luong` / `Số lượng` / `SL bán` |
| đơn vị | `Đơn vị (tính)` / `DonVi` / `dvt` / `Đơn vị tính` |
| **SL quy đổi (ĐV cơ bản)** | `Quy ra ĐV lẻ` / `Số lượng lẻ` / `SL lẻ` / `Số lượng lẻ` |
| đơn giá | `Giá bán` / `don_gia` / `Đơn giá bán` / `Giá 1 đv` / `Price` |
| thành tiền dòng | `Thanh tien` / `Tổng tiền` / `thanh_tien` / `Thành tiền (đ)` / `Amount` |
| mã đơn | `Mã hóa đơn` / (không có) / `Số phiếu` / `Ma don` |
| trạng thái | `Kết quả` / `Trạng thái xử lý` / `Ghi chú TT` / `Trạng thái đơn` |
| khách | `Đối tác` / (không có) / `Khách hàng (tên)` |

Không có bảng quy đổi, không có danh mục, không có tồn kho → câu hỏi tồn kho/nhập/lô ở nhóm này **unanswerable** (đúng như nhãn train).

### A2. `DonHang_ChiTiet` + `DanhSachQuyDoi`

`biz_102, biz_103, biz_104, biz_121, biz_122`; `dev_002, dev_005` (tách mỗi tháng 1 file).

Cột chuẩn (giống nhau gần như tuyệt đối):
`Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`

- **Không có mã hàng** → nối danh mục qua **tên sản phẩm**.
- `DanhSachQuyDoi`: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản` (chỉ chứa mặt hàng **có đơn vị lớn**; mặt hàng vắng mặt → ĐV cơ bản, hệ số 1).
- `biz_121` gộp các danh sách vào `DuLieuXuat.xlsx` nhiều sheet; `biz_122` tách file rời.

### A3. Bộ POS đầy đủ (Excel)

`biz_106, biz_108, biz_109, biz_128`.

| File | Vai trò | Cột khoá |
|---|---|---|
| `DanhSachHoaDon` | header đơn | `Mã hóa đơn`, `Thời gian`/`Thời gian tạo`, `Mã KH`, `Khách hàng`, `Tổng tiền hàng`, `Giảm giá`, `Tổng sau giảm giá`, `Khách đã trả`, `Trạng thái`, `Còn nợ`, `Phương thức thanh toán`, `Kênh bán`, `Người bán` |
| `DanhSachHoaDonChiTiet` | dòng hàng | `Mã hóa đơn`, `STT`, `Mã hàng`, `Tên hàng`, `Đơn vị tính`, `Số lượng`, `Đơn giá`, `Giảm giá`, `Thành tiền`, `Số lượng quy đổi`, `Giá vốn` |
| `DanhSachSanPham` | danh mục | `Mã hàng`, `Tên hàng`, `Nhóm hàng(3 Cấp)`, `Giá bán`, `ĐVT`, `Giá vốn` (không phải shop nào cũng có) |
| `DanhSachKhachHang` | khách | `Mã khách hàng`, `Tên khách hàng`, `Điện thoại`, `Nhóm khách hàng`, `Địa chỉ` |
| `BaoCaoTonKho` | tồn | `Mã hàng`, `Tên hàng`, `ĐVT`, `Tồn cuối kỳ` |
| `DanhSachNhapHang` / `DanhSachChiTietNhapHang` | nhập | `Mã nhập hàng`, `Thời gian`, `Mã NCC`, `Cần trả NCC`, `Trạng thái` / `Mã hàng`, `ĐVT`, `Số lượng`, `Đơn giá` |
| `DanhSachDonViTinh` | quy đổi | `Mã hàng`, `ĐVT`, `Quy đổi`, `Giá bán` |
| `SoQuy` | phiếu thu | `Mã phiếu`, `Thời gian`, `Mã hóa đơn`, `Phương thức thanh toán`, `Giá trị` |

**Cảnh báo đã xác minh:** `biz_106` có **header ở dòng thứ 3** (2 dòng tiêu đề merge phía trên) cho `DanhSachHoaDon`, `DanhSachHoaDonChiTiet_*`; `DanhSachSanPham` của `biz_106` có ~23 cột (nhiều hơn README). README `biz_106` **không liệt kê cột** → phải đọc header thật.

### A4. POS nhà thuốc (có lô + thuốc)

`biz_119, biz_120, biz_122, biz_123, biz_124`; `dev_005, dev_006`.

Thêm 3 bảng so với A3:

| File / bảng | Cột | Ý nghĩa |
|---|---|---|
| `DanhSachLoHang` / `lo_hang` | `Mã nhập hàng`, `Mã hàng`, `Lô`, `Hạn sử dụng`, `Số lượng (ĐVT cơ bản)` | mỗi dòng nhập = 1 lô, `Lô` không trùng |
| `DanhSachHoaDonChiTietLo` / `chi_tiet_don_lo` | `Mã hóa đơn`, `STT`, `Lô`, `Số lượng (ĐVT cơ bản)`, `Số lượng trả (ĐVT cơ bản)` | 1 dòng bán có thể lấy nhiều lô; **`Số lượng trả > 0` ⇒ đơn có trả hàng** |
| `DanhSachThuoc` / `thong_tin_thuoc` | `Mã hàng`, `Hoạt chất`, `Thuốc kê đơn` | `Thuốc kê đơn` = TRUE/1; hoạt chất nhiều chất nối `" + "`, không kèm hàm lượng |

`biz_123` / `dev_006` là **SQLite** (`pos.sqlite`, 17 bảng) — xem Bảng D.

### A5. Sổ tay chủ tiệm + bảng giá

`biz_105, biz_117`; `dev_004`.

| File | Vai trò | Cột |
|---|---|---|
| `SoBanHang` (+`_1`, `_2026`) | bán | `Ngày giao dịch`, `Mã hóa đơn`, `Khách`, `Hàng`, `so_luong`/`SL bán`, `Unit`/`dvt`, `Giá lẻ`/`Giá 1 đv`, `Trị giá`/`Amount`, `Status`/`Trạng thái xử lý`, `Giờ` |
| `DanhMuc` | quy đổi | `Tên món`/`Hàng`, `Đơn vị gốc`, `ĐV nhập`/`ĐV lớn`, `Hệ số` |
| `TonKho` | tồn | `Hàng hóa`/`Product`, `Đơn vị tính`, `Tồn cuối`/`Tồn thực` |
| `SoNhapHang` | nhập | `Số phiếu`, `Ngày nhập`, `Nhà cung cấp`, `Tên mặt hàng`/`Product`, `ĐVT`, `SL nhập`, `Giá nhập`, `Thành tiền` |
| `BangGia` | lịch sử giá | `Ngày áp dụng`, `ten_hang`/`TenHang`/`Diễn giải`, `Giá mới`, `Giá cũ` |
| `SoGiaoHang` | giao nhiều đợt | `Mã bill`/`Số đơn`, `Ngày chở`/`Thời gian giao`, `Lượt giao`, `Tên hàng`, `SL thực giao`, `Người chở`, `Biển số xe` |
| `SoHanNo` | hạn nợ | `So hoa don`/`Mã đơn hàng`, `Hạn nợ (ngày)`/`Kỳ hạn`, `Han tra`/`Ngày phải trả` |

`biz_105` **không** có `SoGiaoHang`/`SoHanNo` → không hỏi được giao hàng/hạn nợ; `biz_117`/`dev_004` có đủ.

### A6. Bộ CSV quan hệ 5 file

`biz_111, biz_127, biz_129`; `dev_010`.

| File | Vai trò | Cột (khác nhau mỗi shop) |
|---|---|---|
| `don_hang` | header đơn | mã đơn: `Mã chứng từ` / `Số phiếu` / `Số CT`; ngày: `NgayBan` / `Ngày` / `Ngày bán` / `Date`; tổng: `Tổng bill` / `Tổng đơn` / `Phải thu` / `Thành tiền`; nợ: `Còn lại` / `Còn nợ` / `Dư nợ` / `Con no`; trạng thái: `Xử lý` / `Tình trạng` / `Tình trạng đơn` |
| `chi_tiet_don` | dòng hàng | `SL`, `Đơn vị (tính)`, `Giá đơn vị`, `T.Tiền`, `ID SP`/`Mã mặt hàng`/`Mã hàng bán`, `SL quy đổi`/`Số lượng lẻ`/`Quy ra ĐV lẻ` |
| `san_pham` | danh mục | `SKU`/`Mã sản phẩm bán`/`Mã HH`/`Mã vạch`, `Sản phẩm`/`Tên SP`/`Tên sản phẩm`, `Nhóm`/`Danh mục`/`Nhom hang`/`Nhóm hàng`, `Đơn vị`/`Đơn vị cơ bản`/`Đơn vị tính` |
| `khach_hang` | khách | mã: `ma_kh`/`Mã KH`/`Mã khách lẻ/sỉ`; tên: `Khách lẻ/sỉ`/`Khách hàng (tên)`/`KH`; `Nhóm`, `Phone`/`Di động` |
| `thanh_toan` | phiếu thu | `Mã phiếu thu`/`Mã GD`/`Mã TT`, `Số HĐ`/`Số CT`/`Mã giao dịch`/`Mã đơn`, `Tiền`/`Giá trị`/`So tien`, `Thời gian thu`/`Ngày thu`/`Thời điểm` |

`biz_111`/`biz_127`/`biz_129` có cột `Phương thức TT`/`Trả bằng`/`Hình thức thanh toán` với giá trị `cash|transfer|ewallet|cod|debt` (tiếng Anh!), `dev_010` dùng `Phương thức TT`.

### A7. `So_chi_tiet_ban_hang` + danh mục (+ giao hàng, công nợ)

`biz_112, biz_115, biz_116, biz_118, biz_130`; `dev_001`.

| File | Cột |
|---|---|
| `So_chi_tiet_ban_hang(.xlsx)` | `Ngày`, `Mã đơn hàng`, `Tên hàng hóa`, `Đơn vị tính`, `Số lượng`, `Đơn giá`, `Thành tiền`, `Trạng thái`, `Số lượng quy đổi`, `Khách hàng` (chỉ có ở `biz_115/116/118`, `dev_001`) |
| `Danh sách hàng hóa` | `Mã hàng hóa`, `Tên hàng hóa`, `Nhóm hàng hóa`, `Đơn vị tính`, `Giá vốn`, `Giá bán` (không phải shop nào cũng có) |
| `Bảng kê phiếu giao hàng` | `Ngày giao hàng`, `Mã đơn hàng`, `Lần giao`, `Tên hàng hóa`, `Đơn vị tính`, `Số lượng giao`, `Biển số xe`, `Người giao hàng` |
| `Chi tiết công nợ theo hạn` | `Mã đơn hàng`, `Số ngày được nợ`, `Hạn thanh toán` |

`biz_112`/`biz_130` **không** có tên khách trong sổ bán → câu hỏi "khách mua nhiều nhất" là **unanswerable**.
`biz_116` gộp 4 danh sách vào `Bao_cao_ban_hang.xlsx` (mỗi danh sách 1 sheet).

### A8. Chỉ có hoá đơn (1 dòng = 1 đơn, không chi tiết hàng)

`biz_110`, `dev_009`.

| Cột (biz_110 / dev_009) | Ý nghĩa |
|---|---|
| `Mã bill` / `Mã hóa đơn` | mã đơn |
| `Ngày giao dịch` / `Ngày tháng` | ngày bán |
| `Bên mua` / `Đối tác` | khách |
| `Tien hang` / `Giá trị hàng` | tổng dòng hàng, **trước** giảm giá đơn, **chưa** phí giao |
| `TongTien` / `TongTien` | số khách phải trả (**đã** giảm giá đơn **và** gồm phí giao) |
| `Da tra` / `Đã thu` | đã thanh toán |
| `Chưa trả` / `Nợ` | còn nợ (đơn huỷ = 0) |
| `Status` / `Trạng thái đơn` | trạng thái |

Không có mặt hàng → mọi câu hỏi theo mặt hàng/nhóm hàng/tồn kho là **unanswerable**.

### A9. Bộ cột "trăm hoa" (mỗi file một kiểu tên)

| Business | Đặc thù |
|---|---|
| `biz_123`, `dev_006` | SQLite POS 17 bảng, xem Phần D |
| `dev_003` | 4 nguồn: `BanHang_TongHop_2025/2026.xlsx` (sheet `BanHang` gộp đơn + chi tiết, thêm `BanHang_HangHoa`, `BanHang_KhachHang`, `BanHang_DonViQuyDoi`, `BanHang_LichSuGia`), `BanHang_PhieuThu`, `SoTay_NhapHang`, `SoTay_ChiPhi`, `ton_kho.csv`, **`BaoCaoCa`** (tiền mặt theo ca: ngày, ca, mã NV, tiền mặt thu, tiền hoàn, tiền ròng) |
| `dev_007` | 3 CSV: `chi_tiet_hoa_don` (gộp header đơn + dòng hàng, có `Bàn`, `Khu vực`, `Số khách`, `Nhân viên bán`, `Giờ bán`), `danh_muc_hang` (kèm `Tồn cuối`), `chi_tiet_nhap_hang` |
| `dev_008` | 2 `ChiTietHoaDon_*.xlsx` + `DanhMucHang` (kèm `Tồn thực`) + `ChiTietNhapHang`; **nợ nằm trong `Note` dạng chữ** ("khách đã đưa / còn thiếu") |
| `dev_011`, `dev_014` | Cửa hàng điện thoại: sheet `Ghi tắt` (tên đầy đủ + loại hàng), `IMEI` (máy), `Bớt`, `Thu máy cũ`, `Khách trả` (mức **đơn**, lặp mọi dòng); `dev_014` thêm `ThuMayCu.xlsx`, `SoNo.xlsx` (nợ + góp + bảo hành) |
| `dev_012` | Sửa xe: `SoSuaXe` mỗi tháng 1 sheet, `Làm gì` ghi nhiều việc 1 ô, `Tiền` là tổng phiếu; `DanhSachTho` có `Hoa hồng (%)` |
| `dev_013` | Mẹ & bé: header **gộp 2 dòng**, có dòng không phải hàng (`Voucher`, `Dùng N điểm`, `Phí ship`) trong cùng sheet; `QuanLy.xlsx` chứa `DanhMuc`, `KhachHang` (điểm), `NhapHang`, `KhuyenMai`; trạng thái nằm trong `Ghi chú` |

### E8 — Bảng phân cấp: forward-fill nhóm cột đơn, không fill cột sản phẩm/số lượng

Trong một số shop, mỗi đơn hàng có nhiều món nhưng phần mềm xuất Excel/CSV chỉ ghi thông tin cấp đơn (`Mã đơn hàng`, `Ngày đặt hàng`, `Trạng thái đơn hàng`, `Tên khách hàng`, v.v.) ở **dòng đầu tiên** của đơn; các dòng sản phẩm chi tiết tiếp theo bên dưới để **trống** (`None`/rỗng).

**Quy tắc xử lý bắt buộc cho Loader / Runtime (Phase P3 & Người 3/4):**
- **Phải forward-fill:** Các cột cấp đơn (`Mã đơn hàng`, `Ngày đặt hàng`, `Trạng thái đơn hàng`, `Tên khách hàng`, `Nhóm khách`).
- **Tuyệt đối không fill:** Các cột cấp dòng sản phẩm (`Tên sản phẩm`, `Số lượng`, `Giá sản phẩm`, `Tổng tiền`/`Thành tiền`, `Đơn vị tính`).
- **Hậu quả nếu không forward-fill:** Hệ thống sẽ bỏ qua các dòng sản phẩm con (tới 45–61% số dòng body), làm sai lệch hoàn toàn doanh thu và sản lượng (như trường hợp `biz_103` từng gây nhầm lẫn).

**Danh sách 7 business có bảng phân cấp đã xác minh:**
1. `train / biz_103`: `DonHang_ChiTiet.xlsx` (16 sheet tháng; ~59–61% dòng con trống mã đơn).
2. `train / biz_121`: `DonHang_ChiTiet.xlsx :: Sheet1` (46,7% dòng trống).
3. `train / biz_122`: `DonHang_ChiTiet_1.xlsx` và `DonHang_ChiTiet_2026.xlsx` (46–48% dòng trống).
4. `public_test / dev_004`: `SoBanHang.xlsx` (50–54% dòng trống).
5. `public_test / dev_005`: `BanHang_ThangNN_YYYY.xlsx :: DonHang_ChiTiet` (23 file, 45–48% dòng trống).
6. `public_test / dev_013`: `BanHang_2025.xlsx` và `BanHang_2026.xlsx` (34–37% dòng trống).
7. `public_test / dev_007`: `chi_tiet_hoa_don.csv` (10,1% dòng trống).

**Trường hợp phủ định (Cảnh báo không được forward-fill):**
- `biz_111/don_hang.csv`: Cột 0 là `Số KH`, ô trống mang ngữ nghĩa **khách lẻ**, không phải dòng con.
- `biz_124/SoTay_ChiPhi`: Ô trống cột `Ghi chú` là không có ghi chú.
- `dev_004/BangGia`: Ô trống cột `Giá cũ` là giá áp dụng lần đầu, không có giá cũ.
- `biz_102`, `biz_106`: Lặp đầy đủ mã đơn trên mọi dòng (0% trống).

---

## Phần B — Bảng tra theo business

| Biz | Ngành | Cutoff | Archetype | Điểm cần nhớ |
|---|---|---|---|---|
| `biz_101` | bách hóa | 24/08/2026 | A1 | 1 file `ban_hang.csv`; quy đổi ghi trong README (lốc/thùng → lon/chai) |
| `biz_102` | bách hóa | 16/06/2026 | A2 | 18 sheet theo tháng; không mã hàng |
| `biz_103` | bách hóa | 09/07/2026 | A2 | 16 sheet, **header dòng 3**; trạng thái: `đã lấy` / `hủy đơn` / `hàng trả về` |
| `biz_104` | **cà phê** | 02/06/2026 | A2 | có size `(M)/(L)`; sản phẩm: Cà phê sữa/Bạc xỉu/Trà sữa |
| `biz_105` | cà phê | 24/06/2026 | A5 | 6 file; có `BangGia`; **không** có giao hàng/hạn nợ; `Giờ` để tính ca |
| `biz_106` | cà phê | 14/09/2026 | A3 | header dòng 3; có `SoQuy`; có `Topping …` là dòng riêng; `Giá vốn` trên dòng bán |
| `biz_107` | bách hóa | 22/07/2026 | A1 | 1 sheet; **không mã đơn, không khách**; trạng thái `Không giao được` |
| `biz_108` | bách hóa | 29/05/2026 | A3 | có `Nhóm khách hàng`, `Kênh bán`, `Người bán` |
| `biz_109` | bách hóa | 05/08/2026 | A3 | nhiều danh sách gộp 1 workbook; trạng thái **trộn** (`đã lấy`/`Hoàn thành`/`hủy đơn`/`Đã huỷ`) |
| `biz_110` | tổng hợp | 03/07/2026 | A8 | chỉ hoá đơn, không mặt hàng |
| `biz_111` | cà phê + bánh | 19/08/2026 | A6 | `chi_tiet_don` **không có tên hàng** → nối `ID SP` → `san_pham`; trạng thái tiếng Anh |
| `biz_112` | cà phê | 31/07/2026 | A7 | 2 file theo tháng, **header dòng 4**; **không khách**; 2026 có `Đang vận chuyển` |
| `biz_113` | **vật liệu XD** | 09/08/2026 | A1 | 1 sheet; có `Số lượng lẻ`; đơn vị `thiên/xe 4m3/tấn` |
| `biz_114` | vật liệu XD | 21/06/2026 | A1 | 1 CSV; có khách + trạng thái |
| `biz_115` | vật liệu XD | 16/05/2026 | A7 | có `Bảng kê giao hàng` + `Công nợ theo hạn`; `Khách hàng` nằm trong sổ bán |
| `biz_116` | vật liệu XD | 03/09/2026 | A7 | 1 workbook, 4 sheet; cùng bộ cột với 115 |
| `biz_117` | vật liệu XD | 20/05/2026 | A5 | 7 file, đủ giao hàng + hạn nợ + bảng giá; cột tên tiếng Việt không dấu |
| `biz_118` | vật liệu XD | 10/09/2026 | A7 | header dòng 4 ở sổ bán, dòng 4 ở bảng kê giao, dòng 3 ở công nợ |
| `biz_119` | **nhà thuốc** | 13/07/2026 | A4 | đủ lô + thuốc; `DanhSachSanPham` có `ĐVT` |
| `biz_120` | nhà thuốc | 12/06/2026 | A4 | như 119 + `Giá vốn` trong `DanhSachSanPham`; trạng thái trộn `ok`/`Thành công` |
| `biz_121` | nhà thuốc | 20/09/2026 | A2+A4 | `DuLieuXuat.xlsx` gộp `DanhSachQuyDoi/SanPham/DonNhapHang/…/DanhSachThuoc` |
| `biz_122` | nhà thuốc | 17/07/2026 | A2+A4 | `DonHang_ChiTiet_*` header dòng 3; `DonHang_Lo_*` tách riêng |
| `biz_123` | nhà thuốc | 28/06/2026 | **SQLite** | 17 bảng; `the_kho.TonCuoi` là tồn luỹ kế theo dòng |
| `biz_124` | nhà thuốc | 25/05/2026 | A4+A9 | 13 file trộn 3 nguồn (`BanHang_*`, `SoTay_*`, `ton_kho.csv`); `SoTay_ChiPhi` cho lãi ròng |
| `biz_125` | **quán ăn/nhậu** | 11/05/2026 | A1 | 1 CSV; có dòng `Phí phục vụ` |
| `biz_126` | quán ăn | 06/06/2026 | A1 | 1 sheet; có `Phí phục vụ`; **không mã đơn** |
| `biz_127` | quán ăn | 28/07/2026 | A6 | `Diễn giải` trống; có `Phí phục vụ` |
| `biz_128` | quán ăn | 07/09/2026 | A3+A9 | thêm `DanhSachHoaDonPhongBan` (`Phòng/Bàn`, `Khu vực`, `Số khách`) |
| `biz_129` | quán ăn | 14/08/2026 | A6 | `Phải thu` = tổng đơn; có `Phí phục vụ` |
| `biz_130` | quán ăn | 29/08/2026 | A7 | header dòng 4; có `Phí phục vụ` |
| `dev_001` | bách hóa | 08/07/2026 | A7 | header dòng 4; có `Khách hàng` + `Giá bán`/`Giá vốn` |
| `dev_002` | cà phê | 24/05/2026 | A2 | **17 file theo tháng** `BanHang_T<tháng>_<năm>`; **topping ghi chung ô tên món** (`+`, `(tiền)`) |
| `dev_003` | cà phê | 21/08/2026 | A9 | `BanHang_TongHop_*` + `BaoCaoCa` + sổ tay; đơn vị quy đổi ở sheet `BanHang_DonViQuyDoi` |
| `dev_004` | vật liệu XD | 10/06/2026 | A5 | header **dòng 2**; `Tổng phiếu` ở mức đơn; **hàng theo bó** (1 bó = 10 cây) |
| `dev_005` | nhà thuốc | 10/05/2026 | A2+A4 | **23 file** theo tháng; quy đổi **nhiều cấp** (`1 thùng = 12 lốc`, số kèm đơn vị là theo đơn vị đó) |
| `dev_006` | nhà thuốc | 08/08/2026 | **SQLite** | cùng schema `biz_123`; `SoTienThu` lưu TEXT |
| `dev_007` | quán ăn | 19/09/2026 | A9 | 3 CSV; có `Bàn`, `Số khách`, `Nhân viên bán`, `Phí phục vụ` |
| `dev_008` | quán ăn | 22/07/2026 | A9 | 2 file chi tiết + `DanhMucHang` + `ChiTietNhapHang`; nợ nằm trong `Note` (chữ) |
| `dev_009` | tổng hợp | 24/06/2026 | A8 | chỉ hoá đơn |
| `dev_010` | mẹ & bé | 06/09/2026 | A6 | đủ 5 CSV; quy đổi thùng/lốc trong README |
| `dev_011` | **điện thoại** | 31/07/2026 | A9 | 1 file, sheet `Ghi tắt`; `Trả lại` ghi trong `Ghi chú` |
| `dev_012` | **sửa xe** | 31/08/2026 | A9 | mỗi tháng 1 sheet (`T7-2025`…), header **dòng 2**; `Tiền` mức phiếu |
| `dev_013` | **mẹ & bé** | 30/06/2026 | A9 | header gộp 2 dòng; dòng `Voucher`/`Dùng N điểm`/`Phí ship`; trạng thái trong `Ghi chú` |
| `dev_014` | điện thoại | 30/09/2026 | A9 | 3 file; `SoNo` có cả nợ + góp + bảo hành; `IMEI` là khoá nối |

---

## Phần C — Luật riêng theo ngành (đối chiếu rulebook §6)

**Cà phê** (`biz_104, 105, 106, 111, 112, 130, dev_002, dev_003`)
- Size = hậu tố `(M)` / `(L)`, không phân biệt hoa thường.
- `Topping Trân châu đen` là **mặt hàng riêng** ở `biz_106/112`; ở `dev_002` topping **gộp trong ô tên món** kèm `+` và tiền trong ngoặc → phải tách khi xếp hạng.
- `Phí phục vụ` (phòng lạnh) là dòng hàng nhưng **không phải mặt hàng**.

**Nhà thuốc** (`biz_119–124, dev_005, dev_006`)
- `Thuốc kê đơn` TRUE/1; tỉ lệ kê đơn tính **theo doanh thu**.
- Hoạt chất: so khớp **đúng nguyên văn**; thuốc phối hợp (`A + B`) là **loại riêng**, không cộng vào từng chất.
- Hạn dùng: lô còn tồn có `Hạn sử dụng` trong `[D, D+N]`; tiền vốn = giá nhập **của chính lô** × SL còn tồn, không dùng giá vốn bình quân.

**Vật liệu xây dựng** (`biz_113–118, dev_004`)
- Đơn vị lớn: `1 tấn = 20 bao`, `1 xe 4m3 = 4 m3`, `1 thiên = 1000 viên`, `1 cuộn 10m = 10 m`.
- `dev_004`: 3 mặt hàng ống PVC bán **theo bó, 1 bó = 10 cây**.
- Giao nhiều đợt: số đợt = số dòng `Bảng kê giao` có ngày giao trong kỳ, **mỗi đợt mỗi đơn = 1**, kể cả đơn sau đó trả hàng.

**Quán ăn / nhậu** (`biz_125–130, dev_007, dev_008`)
- `Phí phục vụ` = doanh thu nhưng **không xếp hạng, không đếm** (vẫn vào mẫu số tỉ trọng nhóm).
- `Bàn`, `Khu vực`, `Số khách` chỉ có ở `biz_128`, `dev_007`, `dev_008`.
- Đơn giao đi **không có bàn**.

**Điện thoại** (`dev_011, dev_014`)
- `IMEI` phân biệt máy mới/cũ; dòng 2 máy ghi `" / "`.
- `Bớt`, `Thu máy cũ` là mức **đơn**; `Khách trả` đã trừ cả hai.
- Trả lại ghi bằng chữ ở `Ghi chú`.
- `dev_014`: nợ/trả góp/bảo hành ở 3 sheet của `SoNo.xlsx`; kỳ góp đầu rơi vào tháng sau tháng mua.

**Sửa xe** (`dev_012`)
- 1 dòng = 1 phiếu; `Tiền` là tổng phiếu; nhiều việc ghi chung `Làm gì`.
- Hoa hồng = `Tiền` × `Hoa hồng (%)` của thợ, theo tháng.
- `Tiền = 0` + ghi chú bảo hành → phiếu bảo hành, không phải doanh thu mới.

**Mẹ & bé** (`dev_010, dev_013`)
- `dev_013`: `Voucher` và `Dùng N điểm` ghi **số âm** trong `TT`; `Phí ship` là phí giao. Cả ba **không phải mặt hàng**.
- Điểm thành viên chỉ tích từ `Ngày đăng ký`.

---

## Phần D — SQLite POS (`biz_123`, `dev_006`)

17 bảng, cùng schema; khác biệt: `dev_006.thanh_toan.SoTienThu` là **TEXT**.

| Bảng | Vai trò | Cột quan trọng |
|---|---|---|
| `don_hang` (33.6k / 37.8k dòng) | header đơn | `MaHoaDon`, `NgayLap`, `ThoiGianLap`, `TinhTrang`, `TongTienHang`, `ChietKhau`, `PhiVanChuyen`, `TongThanhToan`, `KhachDaTra`, `ConPhaiThu`, `PhuongThucTT`, `MaKhachHang`, `MaNhanVien`, `MaCaLam`, `KenhBanHang`, `MaKhuyenMai` |
| `chi_tiet_don` (64k / 72k) | dòng hàng | `MaHoaDon`, `SoThuTu`, `MaHangHoa`, `DonViTinh`, `SL`, `SLQuyDoi`, `GiaDonVi`, `ChietKhau`, `TriGia`, **`GiaVonLucBan`** |
| `chi_tiet_don_lo` (64k / 73k) | bán theo lô | `MaHoaDon`, `SoThuTu`, `MaLo`, `SLQuyDoi`, **`SLTraQuyDoi`** (>0 ⇒ trả hàng) |
| `lo_hang` | lô nhập | `MaLo`, `MaHangHoa`, `MaPhieuNhap`, `HanSuDung`, `SLNhapQuyDoi`, `DonGiaNhap` |
| `the_kho` (65k / 74k) | thẻ kho | `NgayGioPhatSinh`, `LoaiGiaoDich`, `SLQuyDoi`, `KieuChungTu`, `MaChungTu`, **`TonCuoi`** |
| `thanh_toan` (33.8k / 37.9k) | phiếu thu | `MaHoaDon`, `NgayGioThu`, **`SoTienThu`**, `PhuongThuc` |
| `tra_hang` (273 / 352) | phiếu trả | `MaHoaDon`, `NgayGioTra`, `TienHoanTra`, `CachHoanTien` |
| `phieu_nhap` / `chi_tiet_nhap` | nhập | `TongGiaTriNhap`, `TinhTrang` / `DonGiaNhap`, `MaLo`, `HanSuDung` |
| `san_pham` | danh mục | `TenGoi`, `DanhMuc`, `DonViCoSo`, `GiaBanLe`, `GiaVonHang`, `ConKinhDoanh` |
| `don_vi_sp` (83) | quy đổi | `DonViTinh`, `HeSoQuyDoi` |
| `lich_su_gia` | lịch sử giá | `NgayApDung`, `GiaBanLe` |
| `thong_tin_thuoc` | thuốc | `ThanhPhanChinh`, `BanTheoDon` |
| `khach_hang` / `nhan_vien` / `nha_cung_cap` / `chi_nhanh` | danh mục | `MaKhachHang`, `TenGoi`, `LoaiKhachHang`, `SoDienThoai` / `MaNhanVien`, `TenGoi` |

**Lưu ý tồn kho:** `the_kho.TonCuoi` là tồn **sau từng giao dịch**, không phải tồn cuối kỳ → tồn tại thời điểm D = dòng cuối cùng của mặt hàng có `NgayGioPhatSinh <= D`.

---

## Phần E — Bẫy parse đã xác minh (quan trọng nhất)

### E1. Số lưu dạng TEXT, mỗi shop một kiểu

| Kiểu | Business | Ví dụ |
|---|---|---|
| `1,234,567` (phẩy ngăn nghìn) | `101–104, 106–110, 113–116, 119–121, 124, 125, 128, dev_002, dev_003, dev_005, dev_009` | `560,000` |
| `1.234.567đ` (chấm + hậu tố) | `105, 117, 127, 129, 126, 122, dev_004, dev_007, dev_008, dev_010, dev_012, dev_013, dev_014` | `105.000đ` |
| `1,234,567.0000` (số thực kiểu Excel dạng chuỗi) | `112, 115, 116, 118, 130, dev_001` | `25,000.0000` |
| Trộn cả hai trong cùng shop | `122, 124, 126, dev_002, dev_003` | `1.600đ` **và** `9,200` |
| Object số thật (`int`/`float`) | `106` (`SoQuy` một phần), `123`, `dev_006` (SQLite) | `90000` |

→ Parser phải: bỏ `đ`/`vnđ`/`%`, bỏ `,` khi là phân cách nghìn và `.` khi là phân cách nghìn; **quy tắc quyết định: nếu có cả `.` và `,` → dấu phân cách thập phân là dấu xuất hiện sau cùng**; nếu chỉ có `.` và nhóm cuối ≠ 3 chữ số → thập phân.

### E2. Header không ở dòng 1

Đã đếm 213 file/sheet có header lệch. Quy tắc: **header = dòng đầu tiên có ≥3 ô khác rỗng**.
Ví dụ điển hình: `biz_103` (dòng 3), `biz_112/130/dev_001` (dòng 4), `biz_118` (dòng 4 sổ bán, dòng 3 công nợ), `biz_106` (dòng 3), `biz_121/122` (dòng 3), `dev_002/dev_005` (dòng 4), `dev_004` (dòng 2), `dev_012` (dòng 2), `dev_013` (header gộp 2 dòng).

### E3. Nhiều sheet theo tháng, tên sheet không thống nhất

`T01_2025` / `04.2025` / `Thang 02 2025` / `Tháng 01-2025` / `T02-2025` / `T7-2025` → phải parse cả 5 kiểu.
Có file tách theo **năm** (`_1`, `_2026`) chứ không theo tháng → phải đọc **toàn bộ** sheet, không tin tên file.

### E4. Trạng thái: từ vựng rất khác nhau, có shop trộn nhiều từ đồng nghĩa

| Nhóm chuẩn | Từ thật gặp trong dữ liệu |
|---|---|
| hoàn thành | `Xong`, `xong`, `ok`, `OK`, `đã lấy`, `Đã hoàn thành`, `Hoàn thành`, `đã xong`, `Thành công`, `Đã giao`, `completed`, `Đã giao` |
| huỷ | `Đã hủy`, `hủy đơn`, `Huỷ đơn`, `hủy`, `khách hủy`, `cancel`, `cancelled`, `Đã huỷ`, `Đã hủy đơn` |
| trả hàng | `Đổi trả`, `trả hàng`, `Trả hàng`, `Đã trả hàng`, `Đã hoàn hàng`, `hàng trả về`, `trả lại`, `Hoàn trả`, `Khách trả`, `returned` |
| đang giao / xử lý | `Đang vận chuyển`, `Đang giao dịch`, `Đang xử lý` |
| **mơ hồ** | `Không giao được` (`biz_107`, `biz_124`) — không phải huỷ, không phải trả; xử lý như **đang giao** ⇒ vẫn tính doanh thu |

`biz_109, biz_120, biz_128, dev_005, dev_008` **trộn 4–6 từ đồng nghĩa trong cùng shop** (kể cả trong cùng một cột) → không được so khớp tuyệt đối.

`dev_008` / `dev_011` / `dev_013` / `dev_014` **không có cột trạng thái**: trạng thái nằm trong cột `Note`/`Ghi chú` bằng chữ tự do.

### E5. Dòng không phải hàng lẫn trong sổ bán

| Marker | Business | Xử lý |
|---|---|---|
| `Phí phục vụ` | `125, 126, 127, 128, 129, 130, dev_007, dev_008` | tính doanh thu, **không** xếp hạng/đếm mặt hàng |
| `Voucher`, `Dùng N điểm`, `Phí ship` | `dev_013` | số âm/không phải hàng, trừ vào hoá đơn |
| `Topping … (+ tiền)` gộp ô | `dev_002`, `biz_106/112` | tách topping khỏi tên món |
| Dòng `nhập đầu kỳ` | nhiều shop | vẫn là phiếu nhập bình thường, tính nếu ngày trong kỳ |

### E6. Bản ghi trùng & ô trống kế thừa

- Hai dòng **cùng một đơn** giống nhau mọi ô = lỗi xuất file → tính **1 lần**.
- Ô trống ở các dòng sau của cùng đơn = **kế thừa dòng đầu** (khách, ghi chú, trạng thái), **không** phải "khách lẻ".
- Ngày không ghi năm → năm của **sheet** chứa dòng đó.

### E7. Đơn vị nhiều cấp

`dev_005` ghi `Tỉ lệ quy đổi` kiểu `1 thùng = 12 lốc` (số kèm tên đơn vị = tính theo đơn vị ngay dưới). Tồn theo đơn vị lớn phải trả `[số đơn vị lớn nguyên, số đơn vị cơ bản lẻ]`, phần lẻ **không** đổi sang đơn vị giữa.

---

## Phần F — Mô hình logic chuẩn hoá đề xuất

Để một engine SQL dùng chung, chuẩn hoá mọi archetype về 12 bảng logic:

```
orders(order_id, biz, order_date, status, channel, payment_method,
       customer_id, employee_id, order_total, line_total, discount, ship_fee,
       paid, debt)
order_lines(order_id, line_no, product_id, product_name, qty, unit,
            qty_base, unit_price, line_discount, line_total, cost_unit, cost_total)
products(product_id, name, group, base_unit, sale_price, cost_price)
units(product_id, unit, factor, base_unit)      -- hệ số về đơn vị cơ bản
customers(customer_id, name, phone, group, address)
employees(employee_id, name)
payments(order_id, paid_at, amount, method)
purchases(purchase_id, purchase_date, supplier_id, status, total)
purchase_lines(purchase_id, line_no, product_id, qty, unit, unit_price, lot_id, expiry)
stock(product_id, as_of, qty_base)
lots(lot_id, product_id, purchase_id, expiry, qty_base, cost_unit)
price_history(product_id, effective_from, price)
deliveries(order_id, delivery_no, delivery_date, product_id, qty_base, driver, plate)
```

Ánh xạ archetype → bảng:

| Archetype | orders | order_lines | products/units | customers | stock | purchases | payments | lots |
|---|---|---|---|---|---|---|---|---|
| A1 | suy từ `Mã hóa đơn` (có thể rỗng) | ✓ | `units` từ README | nếu có cột khách | ✗ | ✗ | ✗ | ✗ |
| A2 | derive từ dòng (distinct mã đơn) | ✓ | `units` từ `DanhSachQuyDoi` | tên khách | ✗ | ✗ (trừ 121/122) | ✗ | 121/122 |
| A3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `SoQuy` | 119/120 |
| A5 | derive | ✓ | `DanhMuc` | tên khách | `TonKho` | `SoNhapHang` | ✗ (nợ theo đơn) | ✗ |
| A6 | ✓ | ✓ | `san_pham` | `khach_hang` | ✗ | ✗ | `thanh_toan` | ✗ |
| A7 | derive | ✓ | `Danh sách hàng hóa` | nếu có | ✗ | ✗ | ✗ | ✗ |
| A8 | ✓ | ✗ | ✗ | tên khách | ✗ | ✗ | ✗ | ✗ |
| SQLite | `don_hang` | `chi_tiet_don` | `san_pham`+`don_vi_sp` | `khach_hang` | `the_kho` | `phieu_nhap` | `thanh_toan` | `lo_hang` |
