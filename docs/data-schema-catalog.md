# Data schema catalog

Read-only structural inventory of local business packages. XLSX headers are inferred from the first 15 physical rows; dimensions come from workbook metadata. Verify candidate headers against business README before using them. No source files are modified.

Train labels are used only for representative-question selection. Public-test packages are cataloged for format compatibility only; labels and scores are not used.

## train

### biz_101

- **ban_hang.csv** — CSV, 56501 data rows; columns: `Giá bán` · `Kết quả` · `Nội dung` · `Ngày tháng` · `Đơn vị (tính)` · `so_luong` · `Thanh tien` · `Quy ra ĐV lẻ` · `Mã hóa đơn` · `Đối tác`

### biz_102

- **DanhSachQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
- **DonHang_ChiTiet.xlsx** — 18 sheet(s)
  - `T01_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T02_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T03_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T04_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T05_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T06_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T07_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T08_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T09_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T10_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T11_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T12_2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T01_2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T02_2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T03_2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T04_2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T05_2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T06_2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`

### biz_103

- **DanhSachQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
- **DonHang_ChiTiet.xlsx** — 16 sheet(s)
  - `04.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `05.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `06.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `07.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `08.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `09.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `10.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `11.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `12.2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `01.2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `02.2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `03.2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `04.2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `05.2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `06.2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `07.2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`

### biz_104

- **DanhSachQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
- **DonHang_ChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`

### biz_105

- **BangGia.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày áp dụng` · `ten_hang` · `Giá mới` · `Giá cũ`
- **DanhMuc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên món` · `Đơn vị gốc` · `ĐV nhập` · `Hệ số`
- **SoBanHang_1.xlsx** — 12 sheet(s)
  - `Thang 02 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 03 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 04 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 05 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 06 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 07 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 08 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 09 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 10 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 11 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 12 2025` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 01 2026` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
- **SoBanHang_2026.xlsx** — 5 sheet(s)
  - `Thang 02 2026` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 03 2026` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 04 2026` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 05 2026` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
  - `Thang 06 2026` (dimension unavailable); candidate header: `Hàng` · `so_luong` · `Unit` · `Trị giá` · `Status` · `Giá lẻ` · `Giờ` · `Mã hóa đơn` · `Ngày giao dịch` · `Khách`
- **SoNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Số phiếu` · `Ngày nhập` · `Ghi chu` · `Thành tiền` · `Nhà cung cấp` · `Tên mặt hàng` · `Giá nhập` · `ĐVT` · `SL nhập`
- **TonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Hàng hóa` · `Đơn vị tính` · `Tồn cuối`

### biz_106

- **BaoCaoTonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
- **DanhSachChiTietNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá`
- **DanhSachDonViTinh.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `ĐVT` · `Quy đổi` · `Giá bán`
- **DanhSachHoaDon.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Tổng sau giảm giá` · `Khách đã trả` · `Phương thức thanh toán` · `Trạng thái` · `Thời gian tạo` · `Ghi chú`
- **DanhSachHoaDonChiTiet_1.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `STT` · `Mã hàng` · `Tên hàng` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `Giá vốn`
- **DanhSachHoaDonChiTiet_2.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `STT` · `Mã hàng` · `Tên hàng` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `Giá vốn`
- **DanhSachKhachHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Email` · `Mã khách hàng` · `Trạng thái` · `Tên công ty` · `Ngày sinh` · `Tổng điểm` · `Điểm tích lũy` · `Ghi chú` · `Số CMND/CCCD` · `Tên khách hàng` · `Mã số thuế` · `Người tạo` · `Điện thoại` · `Loại hình khách`
- **DanhSachNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
- **DanhSachSanPham.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Hình ảnh (url1,url2...)` · `Vị trí kệ` · `Ghi chú` · `Được bán trực tiếp` · `Nhóm hàng(3 Cấp)` · `Mã barcode` · `Mã hàng` · `Thương hiệu` · `Tồn lớn nhất` · `Tên hàng` · `Mã HH Liên quan` · `Thuộc tính` · `Giá bán` · `Mô tả sản phẩm` · `Loại hàng hóa` · `Giá vốn` · `ĐVT` · `Bảo hành` · `Đang kinh doanh` · `Trọng lượng` · `Mẫu ghi chú` · `Định mức tồn tối thiểu` · `Thời gian tạo`
- **SoQuy.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã phiếu` · `Thời gian` · `Mã hóa đơn` · `Phương thức thanh toán` · `Giá trị`

### biz_107

- **SoBanHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Trạng thái xử lý` · `Tổng tiền` · `ngay_ban` · `Số lượng` · `Nội dung` · `don_gia` · `Đơn vị (tính)` · `Số lượng lẻ`

### biz_108

- **BaoCaoTonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
- **DanhSachChiTietNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá`
- **DanhSachHoaDon.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ` · `Kênh bán` · `Người bán` · `Trạng thái HĐĐT`
- **DanhSachHoaDonChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `Mã hàng` · `Tên hàng` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `Đơn vị tính` · `STT`
- **DanhSachKhachHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Đối tượng KH` · `Tổng điểm` · `Trạng thái` · `Mã số thuế` · `Mã khách hàng` · `Tên khách hàng` · `Điện thoại` · `Ngày sinh` · `Nhóm khách hàng` · `Địa chỉ` · `Người tạo` · `Giới tính` · `CCCD` · `Tên công ty` · `Điểm hiện tại` · `Ngày tạo`
- **DanhSachNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
- **DanhSachSanPham.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Tên hàng` · `Bảo hành` · `Nhóm hàng(3 Cấp)` · `Mô tả chi tiết` · `Trọng lượng` · `Vị trí` · `Hình ảnh (url1,url2...)` · `Mã barcode` · `Loại hàng hóa` · `Thuộc tính` · `Mẫu ghi chú` · `Giá bán` · `Được bán trực tiếp` · `Ghi chú` · `Mã HH Liên quan` · `ĐVT` · `Định mức tồn tối thiểu`

### biz_109

- **DanhSachHoaDonChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `STT` · `Mã hàng` · `Tên hàng` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `Giá vốn`
- **DuLieuBanHang.xlsx** — 8 sheet(s)
  - `DanhSachHoaDon` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Tổng sau giảm giá` · `Khách đã trả` · `Phương thức thanh toán` · `Trạng thái` · `Thời gian tạo` · `Kênh bán` · `Người bán` · `Trạng thái HĐĐT`
  - `DanhSachSanPham` (dimension unavailable); candidate header: `Tồn lớn nhất` · `Nhóm hàng(3 Cấp)` · `Vị trí` · `Mã hàng` · `Trọng lượng` · `Thuộc tính` · `Tên hàng` · `Mẫu ghi chú` · `Giá bán` · `Hình ảnh (url1,url2...)` · `Bảo hành` · `Định mức tồn tối thiểu` · `Giá vốn` · `Thương hiệu` · `Được bán trực tiếp` · `ĐVT` · `Đang kinh doanh` · `Thời gian tạo`
  - `DanhSachKhachHang` (dimension unavailable); candidate header: `Mã khách hàng` · `Tổng điểm` · `Tên khách hàng` · `Điện thoại` · `MST` · `Trạng thái` · `Loại hình khách` · `Người tạo` · `Ghi chú KH` · `Tên công ty` · `Nhóm khách hàng` · `Ngày tạo` · `Sinh nhật`
  - `BaoCaoTonKho` (dimension unavailable); candidate header: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
  - `DanhSachNhapHang` (dimension unavailable); candidate header: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
  - `DanhSachChiTietNhapHang` (dimension unavailable); candidate header: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá`
  - `SoQuy` (dimension unavailable); candidate header: `Mã phiếu` · `Thời gian` · `Mã hóa đơn` · `Phương thức thanh toán` · `Giá trị`
  - `DanhSachDonViTinh` (dimension unavailable); candidate header: `Mã hàng` · `ĐVT` · `Quy đổi` · `Giá bán`

### biz_110

- **danh_sach_hoa_don.csv** — CSV, 29317 data rows; columns: `Tien hang` · `TongTien` · `Mã bill` · `Bên mua` · `Ngày giao dịch` · `Status` · `Da tra` · `Chưa trả`

### biz_111

- **chi_tiet_don.csv** — CSV, 106585 data rows; columns: `SL quy đổi` · `Thứ tự` · `Giá đơn vị` · `SL` · `T.Tiền` · `ID SP` · `Ma don` · `Đơn vị (tính)`
- **don_hang.csv** — CSV, 66469 data rows; columns: `Số KH` · `Xử lý` · `NgayBan` · `Bán qua` · `Còn lại` · `Khách trả` · `Tổng bill` · `Phương thức TT` · `Mã chứng từ`
- **khach_hang.csv** — CSV, 200 data rows; columns: `ma_kh` · `Điểm tích lũy` · `Nhóm` · `Trạng thái` · `Email` · `Ghi chú KH` · `Mã số thuế` · `Loại hình khách` · `Ngày sinh` · `CCCD` · `Phone` · `Người tạo` · `Addr` · `Khách lẻ/sỉ` · `Tổng điểm`
- **san_pham.csv** — CSV, 50 data rows; columns: `Thuộc tính` · `Được bán trực tiếp` · `Mã barcode` · `SKU` · `Hình ảnh` · `Giá` · `Đơn vị` · `Loại hàng hóa` · `Thương hiệu` · `Nhom hang` · `Trọng lượng` · `Vị trí` · `Mẫu ghi chú` · `Mô tả sản phẩm` · `Bảo hành` · `Tồn nhỏ nhất` · `Mã HH Liên quan` · `Sản phẩm`
- **thanh_toan.csv** — CSV, 66195 data rows; columns: `Thời gian thu` · `Phương thức` · `Tiền` · `Mã phiếu thu` · `Số HĐ`

### biz_112

- **Danh s├ích h├áng h├│a.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng hóa` · `Mã vạch EAN` · `Tồn nhỏ nhất` · `Trọng lượng` · `Ghi chú` · `Loại hàng hóa` · `Mã HH Liên quan` · `Mô tả sản phẩm` · `Bảo hành` · `Tên hàng hóa` · `Vị trí` · `Nhóm hàng hóa` · `Đơn vị tính` · `Giá bán` · `Tồn lớn nhất` · `Giá vốn`
- **So_chi_tiet_ban_hang_1.xlsx** — 14 sheet(s)
  - `T04_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T05_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T06_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T07_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T08_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T09_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T10_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T11_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T12_2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T01_2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T02_2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T03_2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T04_2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T05_2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
- **So_chi_tiet_ban_hang_2026.xlsx** — 2 sheet(s)
  - `T06_2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
  - `T07_2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`

### biz_113

- **SoBanHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `DonVi` · `Ngày mua` · `Số lượng lẻ` · `thanh_tien` · `Đơn giá bán` · `SL bán` · `Ghi chú TT` · `Mặt hàng`

### biz_114

- **ban_hang.csv** — CSV, 26119 data rows; columns: `Giá bán lẻ` · `Đơn vị tính` · `Mã GD` · `Quy ra ĐV lẻ` · `Sluong` · `Sản phẩm` · `Tổng` · `Tên khách` · `Ngày` · `trang_thai`

### biz_115

- **Bß║úng k├¬ phiß║┐u giao h├áng.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày giao hàng` · `Mã đơn hàng` · `Lần giao` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng giao` · `Biển số xe` · `Người giao hàng`
- **Chi tiß║┐t c├┤ng nß╗ú theo hß║ín.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Số ngày được nợ` · `Hạn thanh toán`
- **Danh s├ích h├áng h├│a.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng hóa` · `Được bán trực tiếp` · `Thương hiệu` · `Tên hàng hóa` · `Nhóm hàng hóa` · `Vị trí` · `Mẫu ghi chú` · `Loại hàng hóa` · `Ghi chú` · `Đơn vị tính` · `Bảo hành` · `Giá vốn` · `Mô tả sản phẩm` · `Định mức tồn tối thiểu` · `Trọng lượng`
- **So_chi_tiet_ban_hang.xlsx** — 16 sheet(s)
  - `02.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `03.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `04.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `05.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `06.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `07.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `08.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `09.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `10.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `11.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `12.2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `01.2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `02.2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `03.2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `04.2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `05.2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`

### biz_116

- **Bao_cao_ban_hang.xlsx** — 4 sheet(s)
  - `So_chi_tiet_ban_hang` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `Danh sách hàng hóa` (dimension unavailable); candidate header: `Bảo hành` · `Mã hàng hóa` · `Tên hàng hóa` · `Hình ảnh (url1,url2...)` · `Thuộc tính` · `Mẫu ghi chú` · `Mô tả sản phẩm` · `Nhóm hàng hóa` · `Đơn vị tính` · `Trọng lượng` · `Tồn nhỏ nhất` · `Mã HH Liên quan` · `Ghi chú` · `Được bán trực tiếp` · `Giá vốn` · `Vị trí` · `Tồn lớn nhất`
  - `Bảng kê phiếu giao hàng` (dimension unavailable); candidate header: `Ngày giao hàng` · `Mã đơn hàng` · `Lần giao` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng giao` · `Biển số xe` · `Người giao hàng`
  - `Chi tiết công nợ theo hạn` (dimension unavailable); candidate header: `Mã đơn hàng` · `Số ngày được nợ` · `Hạn thanh toán`

### biz_117

- **BangGia.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày áp dụng` · `Giá cũ` · `Giá mới` · `TenHang`
- **DanhMuc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Hàng` · `ĐV lớn` · `ĐV nhỏ` · `Hệ số QĐ`
- **SoBanHang.xlsx** — 17 sheet(s)
  - `Tháng 01-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 02-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 03-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 04-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 05-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 06-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 07-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 08-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 09-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 10-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 11-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 12-2025` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 01-2026` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 02-2026` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 03-2026` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 04-2026` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
  - `Tháng 05-2026` (dimension unavailable); candidate header: `Giờ` · `Mã phiếu` · `TenKH` · `Ngày lập` · `Tiền` · `Ghi chú TT` · `Giá` · `DonVi` · `Số lượng hàng` · `Tên SP`
- **SoGiaoHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `ĐV gốc` · `Biển số xe` · `Mã bill` · `Lượt giao` · `SL thực giao` · `Tên hàng` · `Ngày chở` · `Người chở`
- **SoHanNo.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `So hoa don` · `Hạn nợ (ngày)` · `Han tra`
- **SoNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Số phiếu` · `Product` · `Ngày nhập` · `ĐVT` · `Thành tiền` · `Nội dung` · `Nhà cung cấp` · `SL nhập` · `Giá nhập`
- **TonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tồn thực` · `Đơn vị` · `Product`

### biz_118

- **Bß║úng k├¬ phiß║┐u giao h├áng.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày giao hàng` · `Mã đơn hàng` · `Lần giao` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng giao` · `Biển số xe` · `Người giao hàng`
- **Chi tiß║┐t c├┤ng nß╗ú theo hß║ín.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Số ngày được nợ` · `Hạn thanh toán`
- **Danh s├ích h├áng h├│a.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Hình ảnh (url1,url2...)` · `Vị trí` · `Trọng lượng` · `Bảo hành` · `Mã hàng hóa` · `Mã barcode` · `Mô tả sản phẩm` · `Tên hàng hóa` · `Loại hàng hóa` · `Nhóm hàng hóa` · `Đơn vị tính` · `Mã HH Liên quan` · `Tồn lớn nhất` · `Ghi chú` · `Mẫu ghi chú` · `Được bán trực tiếp`
- **So_chi_tiet_ban_hang.xlsx** — 20 sheet(s)
  - `T02-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T03-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T04-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T05-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T06-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T07-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T08-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T09-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T10-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T11-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T12-2025` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T01-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T02-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T03-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T04-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T05-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T06-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T07-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T08-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`
  - `T09-2026` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`

### biz_119

- **BaoCaoTonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
- **DanhSachChiTietNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá` · `Lô` · `Hạn sử dụng`
- **DanhSachHoaDon.xlsx** — 19 sheet(s)
  - `T01-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T02-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T03-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T04-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T05-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T06-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T07-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T08-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T09-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T10-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T11-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T12-2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T01-2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T02-2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T03-2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T04-2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T05-2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T06-2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `T07-2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
- **DanhSachHoaDonChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `Mã hàng` · `Tên hàng` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `STT`
- **DanhSachHoaDonChiTietLo.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `STT` · `Lô` · `Số lượng (ĐVT cơ bản)` · `Số lượng trả (ĐVT cơ bản)`
- **DanhSachKhachHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Công ty` · `Tổng điểm` · `Mã khách hàng` · `Ghi chú KH` · `Ngày sinh` · `Tên khách hàng` · `Người tạo` · `Đối tượng KH` · `Điểm tích lũy` · `Điện thoại` · `MST` · `Địa chỉ`
- **DanhSachLoHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `Mã hàng` · `Lô` · `Hạn sử dụng` · `Số lượng (ĐVT cơ bản)`
- **DanhSachNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
- **DanhSachSanPham.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Trọng lượng` · `Mã hàng` · `Loại hàng hóa` · `Tên hàng` · `Tồn nhỏ nhất` · `Bảo hành` · `Ghi chú` · `Được bán trực tiếp` · `Mẫu ghi chú` · `Nhóm hàng(3 Cấp)` · `Vị trí kệ` · `Mô tả chi tiết` · `Thuộc tính` · `Hình ảnh (url1,url2...)` · `Giá bán` · `ĐVT` · `Mã HH Liên quan` · `Thương hiệu` · `Mã vạch EAN` · `Tồn lớn nhất`
- **DanhSachThuoc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Hoạt chất` · `Thuốc kê đơn`

### biz_120

- **BaoCaoTonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
- **DanhSachChiTietNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá` · `Lô` · `Hạn sử dụng`
- **DanhSachHoaDon.xlsx** — 18 sheet(s)
  - `01.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `02.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `03.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `04.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `05.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `06.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `07.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `08.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `09.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `10.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `11.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `12.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `01.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `02.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `03.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `04.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `05.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
  - `06.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Còn nợ` · `Kênh bán` · `Ghi chú`
- **DanhSachHoaDonChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `Mã hàng` · `Tên hàng` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi`
- **DanhSachHoaDonChiTietLo.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `STT` · `Lô` · `Số lượng (ĐVT cơ bản)` · `Số lượng trả (ĐVT cơ bản)`
- **DanhSachKhachHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã khách hàng` · `Ghi chú` · `Mã số thuế` · `Tên khách hàng` · `Người tạo` · `CCCD` · `Ngày sinh` · `E-mail` · `Đối tượng KH` · `Tên công ty` · `Điện thoại` · `Địa chỉ`
- **DanhSachLoHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `Mã hàng` · `Lô` · `Hạn sử dụng` · `Số lượng (ĐVT cơ bản)`
- **DanhSachNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
- **DanhSachSanPham.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Trọng lượng` · `Mã hàng` · `Định mức tồn tối thiểu` · `Tên hàng` · `Mô tả chi tiết` · `Nhóm hàng(3 Cấp)` · `Mẫu ghi chú` · `Định mức tồn tối đa` · `Được bán trực tiếp` · `Bảo hành` · `Mã HH Liên quan` · `Giá bán` · `Loại hàng hóa` · `ĐVT` · `Giá vốn` · `Hình ảnh` · `Thời gian tạo`
- **DanhSachThuoc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Hoạt chất` · `Thuốc kê đơn`

### biz_121

- **DonHang_ChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **DuLieuXuat.xlsx** — 6 sheet(s)
  - `DanhSachQuyDoi` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
  - `DanhSachSanPham` (dimension unavailable); candidate header: `Vị trí` · `Ghi chú` · `Mã SKU` · `Bảo hành` · `Thương hiệu` · `Mẫu ghi chú` · `Tên sản phẩm` · `Trọng lượng` · `Mã barcode` · `Đơn vị` · `Mã HH Liên quan` · `Tồn lớn nhất` · `Hình ảnh (url1,url2...)` · `Thuộc tính` · `Mô tả chi tiết` · `Loại sản phẩm` · `Loại hàng hóa`
  - `DonNhapHang` (dimension unavailable); candidate header: `Mã đơn nhập` · `Ngày nhập` · `Mã nhà cung cấp`
  - `DonNhapHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn nhập` · `Mã SKU` · `Mã lô` · `Hạn sử dụng` · `Số lượng nhập`
  - `DonHang_Lo` (dimension unavailable); candidate header: `Mã đơn hàng` · `Mã lô` · `Số lượng` · `Số lượng trả`
  - `DanhSachThuoc` (dimension unavailable); candidate header: `Mã SKU` · `Hoạt chất` · `Thuốc kê đơn`

### biz_122

- **DanhSachQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
- **DanhSachSanPham.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ghi chú` · `Mô tả sản phẩm` · `Tồn lớn nhất` · `Vị trí` · `Mã SKU` · `Mã HH Liên quan` · `Thương hiệu` · `Thuộc tính` · `Tên sản phẩm` · `Hình ảnh` · `Trọng lượng` · `Mã vạch EAN` · `Bảo hành` · `Đơn vị` · `Định mức tồn tối thiểu` · `Loại hàng hóa` · `Mẫu ghi chú` · `Loại sản phẩm`
- **DanhSachThuoc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã SKU` · `Hoạt chất` · `Thuốc kê đơn`
- **DonHang_ChiTiet_1.xlsx** — 17 sheet(s)
  - `T01-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T02-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T03-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T04-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T05-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T06-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T07-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T08-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T09-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T10-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T11-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T12-2025` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T01-2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T02-2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T03-2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T04-2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T05-2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **DonHang_ChiTiet_2026.xlsx** — 2 sheet(s)
  - `T06-2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
  - `T07-2026` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **DonHang_Lo_1.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Mã lô` · `Số lượng` · `Số lượng trả`
- **DonHang_Lo_2.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Mã lô` · `Số lượng` · `Số lượng trả`
- **DonNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn nhập` · `Ngày nhập` · `Mã nhà cung cấp`
- **DonNhapHang_ChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn nhập` · `Mã SKU` · `Mã lô` · `Hạn sử dụng` · `Số lượng nhập`

### biz_123

- **pos.sqlite** — SQLite
  - `chi_nhanh` (1 rows); columns: `IDCuaHang` · `MaChiNhanh` · `TenGoi` · `DiaChiLienHe` · `NgayKhaiTruong`
  - `chi_tiet_don` (64149 rows); columns: `IDCuaHang` · `MaHoaDon` · `SoThuTu` · `MaHangHoa` · `DonViTinh` · `SL` · `SLQuyDoi` · `GiaDonVi` · `ChietKhau` · `TriGia` · `GiaVonLucBan`
  - `chi_tiet_don_lo` (64422 rows); columns: `IDCuaHang` · `MaHoaDon` · `SoThuTu` · `MaLo` · `SLQuyDoi` · `SLTraQuyDoi`
  - `chi_tiet_nhap` (2953 rows); columns: `IDCuaHang` · `MaPhieuNhap` · `SoThuTu` · `MaHangHoa` · `DonViTinh` · `SL` · `DonGiaNhap` · `MaLo` · `HanSuDung`
  - `don_hang` (33630 rows); columns: `IDCuaHang` · `MaHoaDon` · `MaChiNhanh` · `MaKhachHang` · `MaNhanVien` · `MaCaLam` · `KenhBanHang` · `ThoiGianLap` · `NgayLap` · `TinhTrang` · `TongTienHang` · `ChietKhau` · `PhiVanChuyen` · `ThueGTGT` · `TongThanhToan` · `KhachDaTra` · `ConPhaiThu` · `PhuongThucTT` · `SoHoaDonDienTu` · `TinhTrangHDDT` · `MaKhuyenMai` · `DienGiai`
  - `don_vi_sp` (83 rows); columns: `IDCuaHang` · `MaHangHoa` · `DonViTinh` · `HeSoQuyDoi` · `GiaDonVi`
  - `khach_hang` (300 rows); columns: `trang_thai_kh` · `cccd` · `IDCuaHang` · `diem_hien_tai` · `MaKhachHang` · `ghi_chu_kh` · `ngay_sinh` · `email` · `TenGoi` · `SoDienThoai` · `NamNu` · `nguoi_tao` · `LoaiKhachHang` · `cong_ty` · `tong_diem` · `TaoLuc` · `loai_hinh_kh` · `DiaChiLienHe`
  - `lich_su_gia` (109 rows); columns: `IDCuaHang` · `MaHangHoa` · `NgayApDung` · `GiaBanLe`
  - `lo_hang` (2953 rows); columns: `IDCuaHang` · `MaHangHoa` · `MaLo` · `MaPhieuNhap` · `HanSuDung` · `SLNhapQuyDoi` · `DonGiaNhap`
  - `nha_cung_cap` (5 rows); columns: `IDCuaHang` · `MaNhaCungCap` · `TenGoi` · `SoDienThoai` · `DiaChiLienHe`
  - `nhan_vien` (3 rows); columns: `IDCuaHang` · `MaNhanVien` · `TenGoi` · `MaChiNhanh` · `ChucVu` · `NgayNhanViec` · `NgayThoiViec`
  - `phieu_nhap` (540 rows); columns: `IDCuaHang` · `MaPhieuNhap` · `MaNhaCungCap` · `MaChiNhanh` · `NgayNhapKho` · `TinhTrang` · `TongGiaTriNhap` · `DienGiai`
  - `san_pham` (80 rows); columns: `hinh_anh` · `ma_vach_ean` · `bao_hanh` · `ban_truc_tiep` · `IDCuaHang` · `MaHangHoa` · `ghi_chu_hh` · `vi_tri` · `TenGoi` · `DanhMuc` · `loai_hang_hoa` · `ton_nho_nhat` · `thuong_hieu` · `DonViCoSo` · `GiaBanLe` · `GiaVonHang` · `mau_ghi_chu` · `mo_ta` · `TyLeThue` · `ConKinhDoanh` · `TaoLuc` · `ton_lon_nhat`
  - `thanh_toan` (33816 rows); columns: `IDCuaHang` · `MaPhieuThu` · `MaHoaDon` · `NgayGioThu` · `SoTienThu` · `PhuongThuc` · `DienGiai`
  - `the_kho` (65514 rows); columns: `IDCuaHang` · `MaGiaoDichKho` · `MaHangHoa` · `MaChiNhanh` · `NgayGioPhatSinh` · `LoaiGiaoDich` · `SLQuyDoi` · `KieuChungTu` · `MaChungTu` · `TonCuoi`
  - `thong_tin_thuoc` (80 rows); columns: `IDCuaHang` · `MaHangHoa` · `ThanhPhanChinh` · `BanTheoDon`
  - `tra_hang` (273 rows); columns: `IDCuaHang` · `MaPhieuTra` · `MaHoaDon` · `NgayGioTra` · `NguyenNhan` · `TienHoanTra` · `CachHoanTien`

### biz_124

- **BanHang_BanTheoLo.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Lô` · `SL quy ra lẻ` · `SL trả (ĐVT cơ bản)` · `No.` · `Mã hóa đơn`
- **BanHang_ChiTietHoaDon.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Giá vốn lúc bán` · `SL cơ bản` · `Khuyến mãi` · `Giá niêm yết` · `Thanh tien` · `Mã giao dịch` · `Chi tiết hàng` · `Slg` · `TT dòng` · `Ma hang` · `Đ.vị`
- **BanHang_DonViQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Đơn vị` · `Bằng` · `Giá bán theo đơn vị quy đổi` · `Mã sp`
- **BanHang_HangHoa.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Định mức tồn tối thiểu` · `Giá vốn hiện tại` · `Thương hiệu` · `Thuộc tính` · `Phân loại` · `Món` · `Được bán trực tiếp` · `Mã HH Liên quan` · `ma_sp` · `Mô tả sản phẩm` · `Mẫu ghi chú` · `Giá` · `Ghi chú` · `Đơn vị` · `Trọng lượng` · `Loại hàng hóa`
- **BanHang_HoaDon.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Đã thu` · `Tên KH` · `Trạng thái` · `Giờ tạo đơn` · `Mã NV bán` · `Phương thức TT` · `Ngày bán` · `Nguồn đơn` · `Còn nợ` · `Mã KH mua` · `Tiền hàng trước giảm` · `Tong tien` · `Order ID` · `CK`
- **BanHang_KhachHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Điểm tích lũy` · `Công ty` · `Hạng` · `E-mail` · `MST` · `Ngày sinh` · `CCCD` · `Trạng thái` · `ten_kh` · `Người tạo` · `Ghi chú` · `Tổng điểm` · `Loại hình khách` · `Số điện thoại` · `Customer ID`
- **BanHang_LichSuGia.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã sản phẩm` · `Giá mới` · `Ngày áp dụng` · `Sản phẩm` · `Giá cũ`
- **BanHang_LoHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `HSD` · `Mã món` · `SL nhập (ĐVT cơ bản)` · `Mã phiếu nhập` · `Lô`
- **BanHang_PhieuThu.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Số tiền thu` · `Mã bill` · `Phiếu thu` · `Thời gian thu` · `PTTT`
- **BanHang_Thuoc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã HH` · `Hoạt chất` · `Kê đơn`
- **SoTay_ChiPhi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ghi chú` · `Ngày chi` · `Mục` · `So tien`
- **SoTay_NhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `SL nhập` · `Mô tả` · `Product` · `Thành tiền` · `Lô` · `HSD` · `Ngày nhập` · `Nhà cung cấp` · `ĐVT nhập` · `Số phiếu` · `Giá nhập`
- **ton_kho.csv** — CSV, 80 data rows; columns: `ID SP` · `Đơn vị` · `Ton kho` · `Hàng hóa`

### biz_125

- **ban_hang.csv** — CSV, 79052 data rows; columns: `dvt` · `Hàng bán` · `Khách hàng (tên)` · `Số lượng lẻ` · `Amount` · `Trạng thái xử lý` · `SL bán` · `Ngày bán` · `Số phiếu` · `Giá 1 đv`

### biz_126

- **SoBanHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Đơn vị tính` · `Số lượng bán` · `Thành tiền (đ)` · `Ten hang` · `SL lẻ` · `Trạng thái đơn` · `Ngày tháng` · `Price`

### biz_127

- **chi_tiet_don.csv** — CSV, 131192 data rows; columns: `Mã đơn hàng` · `SoLuong` · `No.` · `DVT` · `Amount` · `Số lượng lẻ` · `Mã mặt hàng` · `Đơn giá (đ)`
- **don_hang.csv** — CSV, 33874 data rows; columns: `Còn nợ` · `Diễn giải` · `Tổng đơn` · `Loại bán` · `Ngày` · `Mã chứng từ` · `Customer ID` · `Khách trả` · `Trả bằng` · `Tình trạng`
- **khach_hang.csv** — CSV, 200 data rows; columns: `CCCD` · `Tên công ty` · `Di động` · `Email` · `Sinh nhật` · `Người tạo` · `Tổng điểm` · `Loại hình khách` · `Mã KH` · `Khách hàng (tên)` · `Điểm hiện tại` · `MST` · `Trạng thái` · `Ghi chú`
- **san_pham.csv** — CSV, 61 data rows; columns: `Trọng lượng` · `Giá niêm yết` · `Mô tả chi tiết` · `Danh mục` · `Ghi chú` · `Mã sản phẩm bán` · `Tên SP` · `Mẫu ghi chú` · `Mã barcode` · `Loại hàng hóa` · `Tồn lớn nhất` · `Thương hiệu` · `Thuộc tính` · `Hình ảnh (url1,url2...)` · `Đơn vị cơ bản` · `Được bán trực tiếp` · `Mã HH Liên quan`
- **thanh_toan.csv** — CSV, 33473 data rows; columns: `Số CT` · `Ngày thu` · `Mã GD` · `Giá trị` · `HTTT`

### biz_128

- **BaoCaoTonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Tên hàng` · `ĐVT` · `Tồn cuối kỳ`
- **DanhSachChiTietNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `STT` · `Mã hàng` · `ĐVT` · `Số lượng` · `Đơn giá`
- **DanhSachHoaDon.xlsx** — 18 sheet(s)
  - `04.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `05.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `06.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `07.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `08.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `09.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `10.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `11.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `12.2025` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `01.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `02.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `03.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `04.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `05.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `06.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `07.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `08.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
  - `09.2026` (dimension unavailable); candidate header: `Mã hóa đơn` · `Thời gian` · `Mã KH` · `Khách hàng` · `Tổng tiền hàng` · `Giảm giá` · `Khách đã trả` · `Trạng thái` · `Thời gian tạo` · `Tổng sau giảm giá` · `Còn nợ`
- **DanhSachHoaDonChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `Mã hàng` · `Tên hàng` · `Số lượng` · `Đơn giá` · `Giảm giá` · `Thành tiền` · `Số lượng quy đổi` · `STT`
- **DanhSachHoaDonPhongBan.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hóa đơn` · `Phòng/Bàn` · `Khu vực` · `Số khách`
- **DanhSachKhachHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Sinh nhật` · `Người tạo` · `Mã khách hàng` · `Email` · `Tên khách hàng` · `Điện thoại` · `Nhóm khách hàng` · `Loại hình khách` · `Điểm hiện tại` · `CCCD` · `Ghi chú KH` · `Công ty` · `Địa chỉ` · `Trạng thái` · `Giới tính` · `MST` · `Tổng điểm`
- **DanhSachNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã nhập hàng` · `Thời gian` · `Mã NCC` · `Cần trả NCC` · `Trạng thái` · `Ghi chú`
- **DanhSachSanPham.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng` · `Tồn nhỏ nhất` · `Loại hàng hóa` · `Tồn lớn nhất` · `Tên hàng` · `Nhóm hàng(3 Cấp)` · `Ghi chú` · `Giá bán` · `Thương hiệu` · `Mã HH Liên quan` · `Mẫu ghi chú` · `Mã barcode` · `Vị trí` · `Thuộc tính` · `Hình ảnh` · `ĐVT` · `Mô tả chi tiết` · `Trọng lượng` · `Thời gian tạo`

### biz_129

- **chi_tiet_don.csv** — CSV, 145479 data rows; columns: `Tiền bán` · `TT dòng` · `S.L` · `Mã hàng bán` · `Quy ra ĐV lẻ` · `Số CT` · `Giảm giá` · `Giá 1 đv` · `ĐV tính`
- **don_hang.csv** — CSV, 38499 data rows; columns: `Hình thức thanh toán` · `Dư nợ` · `Thanh toán` · `Tình trạng đơn` · `Số phiếu` · `Mã khách mua` · `Phải thu` · `Ngày bán`
- **khach_hang.csv** — CSV, 220 data rows; columns: `Ghi chú KH` · `Ngày sinh` · `Điểm hiện tại` · `Nhóm` · `Tổng điểm` · `KH` · `Email` · `Mã số thuế` · `Người tạo` · `Công ty` · `Số điện thoại` · `Số CMND/CCCD` · `Đối tượng KH` · `Trạng thái` · `Mã khách lẻ/sỉ`
- **san_pham.csv** — CSV, 61 data rows; columns: `Bảo hành` · `Giá hiện tại` · `Mã vạch EAN` · `Mã HH Liên quan` · `Đơn vị tính` · `Tên sản phẩm` · `Vị trí kệ` · `Nhom hang` · `Mô tả chi tiết` · `Ghi chú` · `Mẫu ghi chú` · `Được bán trực tiếp` · `Mã HH` · `Loại hàng hóa` · `Thuộc tính` · `Thương hiệu` · `Hình ảnh` · `Định mức tồn tối đa`
- **thanh_toan.csv** — CSV, 38072 data rows; columns: `Mã GD` · `PTTT` · `Tiền` · `Mã giao dịch` · `Thời điểm`

### biz_130

- **Danh s├ích h├áng h├│a.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã hàng hóa` · `Mô tả sản phẩm` · `Bảo hành` · `Được bán trực tiếp` · `Loại hàng hóa` · `Mã HH Liên quan` · `Mẫu ghi chú` · `Tên hàng hóa` · `Nhóm hàng hóa` · `Thương hiệu` · `Định mức tồn tối thiểu` · `Vị trí kệ` · `Đơn vị tính` · `Định mức tồn tối đa` · `Ghi chú` · `Giá vốn`
- **So_chi_tiet_ban_hang_1.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`
- **So_chi_tiet_ban_hang_2.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi`

## public_test

### dev_001

- **Danh s├ích h├áng h├│a.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Vị trí` · `Mã hàng hóa` · `Định mức tồn tối đa` · `Được bán trực tiếp` · `Ghi chú` · `Thuộc tính` · `Tên hàng hóa` · `Mã barcode` · `Mô tả sản phẩm` · `Mã HH Liên quan` · `Bảo hành` · `Nhóm hàng hóa` · `Đơn vị tính` · `Trọng lượng` · `Định mức tồn tối thiểu` · `Mẫu ghi chú` · `Giá bán` · `Hình ảnh` · `Giá vốn`
- **So_chi_tiet_ban_hang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày` · `Mã đơn hàng` · `Tên hàng hóa` · `Đơn vị tính` · `Số lượng` · `Đơn giá` · `Thành tiền` · `Trạng thái` · `Số lượng quy đổi` · `Khách hàng`

### dev_002

- **BanHang_T10_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T11_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T12_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T1_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T1_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T2_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T2_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T3_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T3_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T4_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T4_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T5_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T5_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T6_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T7_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T8_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_T9_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **DanhSachQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`

### dev_003

- **BanHang_PhieuThu.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `PTTT` · `Mã thanh toán` · `Ngày TT` · `Ma don` · `Tiền thu`
- **BanHang_TongHop_2025.xlsx** — 5 sheet(s)
  - `BanHang` (dimension unavailable); candidate header: `Đơn số` · `Phí ship` · `Công nợ` · `Tiền hàng trước giảm` · `Nguồn` · `Tiền giảm` · `Tổng thanh toán` · `Mã NV bán` · `Da tra` · `Ngày HĐ` · `Trạng thái giao` · `Giờ tạo đơn` · `Khách hàng (tên)` · `Mã khách` · `Hình thức thanh toán` · `SĐT` · `Dòng` · `ĐV` · `Hàng hóa` · `Giảm (đ)` · `Thành tiền (đ)` · `Giá 1 đv` · `Barcode` · `SL (ĐV cơ bản)` · `Giá vốn lúc bán` · `S.L`
  - `BanHang_HangHoa` (dimension unavailable); candidate header: `Thuộc tính` · `Trọng lượng` · `Nhóm hàng` · `Giá lẻ` · `Mã H.hóa` · `Được bán trực tiếp` · `Giá vốn hiện tại` · `Hình ảnh (url1,url2...)` · `DVT` · `Bảo hành` · `Mô tả sản phẩm` · `Loại hàng hóa` · `Tồn lớn nhất` · `Định mức tồn tối thiểu` · `Vị trí kệ` · `Mã barcode` · `Mẫu ghi chú` · `Tên hàng hóa`
  - `BanHang_KhachHang` (dimension unavailable); candidate header: `Người tạo` · `Email` · `SĐT` · `Địa chỉ` · `Khách hàng mua` · `Đối tượng KH` · `Ghi chú` · `Mã KH mua` · `MST` · `Kiểu khách` · `Tổng điểm` · `CCCD` · `Điểm hiện tại` · `Sinh nhật` · `Trạng thái` · `Công ty` · `Tra cứu thông tin bổ sung`
  - `BanHang_DonViQuyDoi` (dimension unavailable); candidate header: `Giá bán theo đơn vị quy đổi` · `Mã vạch` · `Bằng` · `Quy cách`
  - `BanHang_LichSuGia` (dimension unavailable); candidate header: `Giá cũ` · `Item` · `Mã H.hóa` · `Ngày áp dụng` · `Giá mới`
- **BanHang_TongHop_2026.xlsx** — 1 sheet(s)
  - `BanHang` (dimension unavailable); candidate header: `Đơn số` · `Phí ship` · `Công nợ` · `Tiền hàng trước giảm` · `Nguồn` · `Tiền giảm` · `Tổng thanh toán` · `Mã NV bán` · `Da tra` · `Ngày HĐ` · `Trạng thái giao` · `Giờ tạo đơn` · `Khách hàng (tên)` · `Mã khách` · `Hình thức thanh toán` · `SĐT` · `Dòng` · `ĐV` · `Hàng hóa` · `Giảm (đ)` · `Thành tiền (đ)` · `Giá 1 đv` · `Barcode` · `SL (ĐV cơ bản)` · `Giá vốn lúc bán` · `S.L`
- **BaoCaoCa.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày` · `Ca` · `Mã NV` · `Tiền mặt thu` · `Tiền mặt hoàn khách` · `Tiền mặt ròng của ca`
- **SoTay_ChiPhi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày mua` · `Lưu ý` · `Tiền chi` · `Nhóm`
- **SoTay_NhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Số phiếu` · `Product` · `Nhà cung cấp` · `Thành tiền` · `Lưu ý` · `Giá nhập` · `SL nhập` · `ĐVT nhập` · `Ngày nhập`
- **ton_kho.csv** — CSV, 50 data rows; columns: `Ton kho` · `ma_sp` · `ten_hang` · `ĐVT`

### dev_004

- **BangGia.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Giá cũ` · `Ngày áp dụng` · `Giá mới` · `Diễn giải`
- **DanhMuc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Hàng` · `Hệ số` · `ĐV gốc` · `Loại ĐV`
- **SoBanHang.xlsx** — 18 sheet(s)
  - `T01-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T02-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T03-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T04-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T05-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T06-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T07-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T08-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T09-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T10-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T11-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T12-2025` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T01-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T02-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T03-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T04-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T05-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
  - `T06-2026` (dimension unavailable); candidate header: `Khách hàng (tên)` · `Giờ` · `Thời gian` · `Ma don` · `SL bán` · `dvt` · `Hàng bán` · `Trạng thái xử lý` · `Giá 1 đv` · `Amount` · `Tổng phiếu`
- **SoGiaoHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Số lượng giao` · `Biển số xe` · `Lượt giao` · `Số đơn` · `Thời gian giao` · `Hàng hóa` · `Lái xe` · `ĐV gốc`
- **SoHanNo.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Kỳ hạn` · `Ngày phải trả`
- **SoNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Product` · `ĐVT` · `Số phiếu` · `Ghi chú` · `Nhà cung cấp` · `Thành tiền` · `Giá nhập` · `Ngày nhập` · `SL nhập`
- **TonKho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tồn cuối` · `ĐV gốc` · `Tên sản phẩm`

### dev_005

- **BanHang_Thang01_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang01_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang02_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang02_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang03_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang03_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang04_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang04_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang05_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang05_2026.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang06_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang07_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang08_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang09_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang10_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang11_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **BanHang_Thang12_2025.xlsx** — 1 sheet(s)
  - `DonHang_ChiTiet` (dimension unavailable); candidate header: `Mã đơn hàng` · `Ngày đặt hàng` · `Trạng thái đơn hàng` · `Tên khách hàng` · `Tên sản phẩm` · `Số lượng sản phẩm` · `Giá sản phẩm` · `Tổng tiền` · `Đơn vị tính`
- **DanhSachQuyDoi.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Tên sản phẩm` · `Đơn vị quy đổi` · `Tỉ lệ quy đổi` · `Đơn vị cơ bản`
- **DanhSachSanPham.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Định mức tồn tối thiểu` · `Mã SKU` · `Được bán trực tiếp` · `Ghi chú` · `Mẫu ghi chú` · `Bảo hành` · `Tên sản phẩm` · `Mã HH Liên quan` · `Mô tả chi tiết` · `Thương hiệu` · `Tồn lớn nhất` · `Đơn vị` · `Thuộc tính` · `Mã vạch EAN` · `Loại sản phẩm` · `Trọng lượng` · `Vị trí` · `Loại hàng hóa`
- **DanhSachThuoc.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã SKU` · `Hoạt chất` · `Thuốc kê đơn`
- **DonHang_Lo.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn hàng` · `Mã lô` · `Số lượng` · `Số lượng trả`
- **DonNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn nhập` · `Ngày nhập` · `Mã nhà cung cấp`
- **DonNhapHang_ChiTiet.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Mã đơn nhập` · `Mã SKU` · `Mã lô` · `Hạn sử dụng` · `Số lượng nhập`

### dev_006

- **pos.sqlite** — SQLite
  - `chi_nhanh` (1 rows); columns: `IDCuaHang` · `MaChiNhanh` · `TenGoi` · `DiaChiLienHe` · `NgayKhaiTruong`
  - `chi_tiet_don` (72411 rows); columns: `IDCuaHang` · `MaHoaDon` · `SoThuTu` · `MaHangHoa` · `DonViTinh` · `SL` · `SLQuyDoi` · `GiaDonVi` · `ChietKhau` · `TriGia` · `GiaVonLucBan`
  - `chi_tiet_don_lo` (72710 rows); columns: `IDCuaHang` · `MaHoaDon` · `SoThuTu` · `MaLo` · `SLQuyDoi` · `SLTraQuyDoi`
  - `chi_tiet_nhap` (3234 rows); columns: `IDCuaHang` · `MaPhieuNhap` · `SoThuTu` · `MaHangHoa` · `DonViTinh` · `SL` · `DonGiaNhap` · `MaLo` · `HanSuDung`
  - `don_hang` (37833 rows); columns: `IDCuaHang` · `MaHoaDon` · `MaChiNhanh` · `MaKhachHang` · `MaNhanVien` · `MaCaLam` · `KenhBanHang` · `ThoiGianLap` · `NgayLap` · `TinhTrang` · `TongTienHang` · `ChietKhau` · `PhiVanChuyen` · `ThueGTGT` · `TongThanhToan` · `KhachDaTra` · `ConPhaiThu` · `PhuongThucTT` · `SoHoaDonDienTu` · `TinhTrangHDDT` · `MaKhuyenMai` · `DienGiai`
  - `don_vi_sp` (83 rows); columns: `IDCuaHang` · `MaHangHoa` · `DonViTinh` · `HeSoQuyDoi` · `GiaDonVi`
  - `khach_hang` (320 rows); columns: `IDCuaHang` · `MaKhachHang` · `TenGoi` · `trang_thai_kh` · `tong_diem` · `diem_hien_tai` · `loai_hinh_kh` · `cccd` · `SoDienThoai` · `email` · `ghi_chu_kh` · `NamNu` · `LoaiKhachHang` · `cong_ty` · `TaoLuc` · `ma_so_thue` · `DiaChiLienHe` · `nguoi_tao`
  - `lich_su_gia` (120 rows); columns: `IDCuaHang` · `MaHangHoa` · `NgayApDung` · `GiaBanLe`
  - `lo_hang` (3234 rows); columns: `IDCuaHang` · `MaHangHoa` · `MaLo` · `MaPhieuNhap` · `HanSuDung` · `SLNhapQuyDoi` · `DonGiaNhap`
  - `nha_cung_cap` (5 rows); columns: `email` · `IDCuaHang` · `nhom_ncc` · `MaNhaCungCap` · `ma_so_thue` · `nguoi_tao` · `trang_thai_ncc` · `TenGoi` · `SoDienThoai` · `DiaChiLienHe`
  - `nhan_vien` (3 rows); columns: `IDCuaHang` · `MaNhanVien` · `TenGoi` · `MaChiNhanh` · `ChucVu` · `NgayNhanViec` · `NgayThoiViec`
  - `phieu_nhap` (494 rows); columns: `IDCuaHang` · `MaPhieuNhap` · `MaNhaCungCap` · `MaChiNhanh` · `NgayNhapKho` · `TinhTrang` · `TongGiaTriNhap` · `DienGiai`
  - `san_pham` (80 rows); columns: `mo_ta` · `ghi_chu_hh` · `IDCuaHang` · `MaHangHoa` · `ma_hh_lien_quan` · `thuoc_tinh` · `ban_truc_tiep` · `mau_ghi_chu` · `vi_tri` · `trong_luong` · `ton_nho_nhat` · `TenGoi` · `ma_vach_ean` · `DanhMuc` · `DonViCoSo` · `GiaBanLe` · `hinh_anh` · `GiaVonHang` · `ton_lon_nhat` · `TyLeThue` · `bao_hanh` · `thuong_hieu` · `loai_hang_hoa` · `ConKinhDoanh` · `TaoLuc`
  - `thanh_toan` (37939 rows); columns: `IDCuaHang` · `MaPhieuThu` · `MaHoaDon` · `NgayGioThu` · `SoTienThu` · `PhuongThuc` · `DienGiai`
  - `the_kho` (73901 rows); columns: `IDCuaHang` · `MaGiaoDichKho` · `MaHangHoa` · `MaChiNhanh` · `NgayGioPhatSinh` · `LoaiGiaoDich` · `SLQuyDoi` · `KieuChungTu` · `MaChungTu` · `TonCuoi`
  - `thong_tin_thuoc` (80 rows); columns: `IDCuaHang` · `MaHangHoa` · `ThanhPhanChinh` · `BanTheoDon`
  - `tra_hang` (352 rows); columns: `IDCuaHang` · `MaPhieuTra` · `MaHoaDon` · `NgayGioTra` · `NguyenNhan` · `TienHoanTra` · `CachHoanTien`

### dev_007

- **chi_tiet_hoa_don.csv** — CSV, 121067 data rows; columns: `Bàn` · `Thành tiền` · `Nhóm khách hàng` · `Mặt hàng` · `Khu vực` · `Nguồn` · `Nội dung` · `Giờ bán` · `Giới tính` · `No.` · `Ngày giao dịch` · `Tiến độ` · `Trạng thái HĐĐT` · `Mã vạch` · `Khách trả` · `Họ tên khách` · `Mã khách mua` · `Còn nợ` · `Tiền giảm` · `Mã bill` · `Số khách` · `Sluong` · `Nhân viên bán` · `Phone` · `Tổng tiền hàng` · `Giảm giá HĐ` · `Addr` · `Phân loại` · `Số lượng lẻ` · `Đơn giá (đ)`
- **chi_tiet_nhap_hang.csv** — CSV, 1731 data rows; columns: `Mã NCC` · `Tổng tiền phiếu` · `SL nhập` · `Hàng hóa` · `STT` · `ĐVT nhập` · `Mã hàng bán` · `Giá nhập` · `Note` · `Ngày nhập` · `Thành tiền` · `Mã phiếu nhập` · `Trạng thái phiếu`
- **danh_muc_hang.csv** — CSV, 61 data rows; columns: `Tra cứu thông tin bổ sung` · `Đang kinh doanh` · `ĐVT` · `Giá vốn` · `Hàng bán` · `Nhóm` · `Giá` · `Tồn cuối` · `Mã SKU`

### dev_008

- **ChiTietHoaDon_1.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Bill` · `Trạng thái HĐĐT` · `Mã người mua` · `Bàn` · `Đơn vị (tính)` · `Phi ship` · `Thành tiền` · `Giảm (đ)` · `Giờ bán` · `Tổng tiền hàng` · `Addr` · `Giới tính` · `Giảm giá HĐ` · `Nhóm hàng` · `Khách` · `Số dòng` · `Tên hàng` · `Nhóm khách hàng` · `Số ĐT` · `SL lẻ` · `TT đơn` · `SLg` · `Note` · `Ngày xuất` · `Nhân viên bán` · `Tong tien` · `Kênh bán` · `Đơn giá (đ)` · `Ma hang` · `Thanh toán bằng` · `Số khách` · `Khu vực`
- **ChiTietHoaDon_2.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Bill` · `Trạng thái HĐĐT` · `Mã người mua` · `Bàn` · `Đơn vị (tính)` · `Phi ship` · `Thành tiền` · `Giảm (đ)` · `Giờ bán` · `Tổng tiền hàng` · `Addr` · `Giới tính` · `Giảm giá HĐ` · `Nhóm hàng` · `Khách` · `Số dòng` · `Tên hàng` · `Nhóm khách hàng` · `Số ĐT` · `SL lẻ` · `TT đơn` · `SLg` · `Note` · `Ngày xuất` · `Nhân viên bán` · `Tong tien` · `Kênh bán` · `Đơn giá (đ)` · `Ma hang` · `Thanh toán bằng` · `Số khách` · `Khu vực`
- **ChiTietNhapHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Giá nhập` · `Mã NCC` · `Trạng thái phiếu` · `Ngày nhập` · `STT` · `Mã phiếu nhập` · `Tổng tiền phiếu` · `Lưu ý` · `Tên mặt hàng` · `Mã vạch` · `Thành tiền` · `SL nhập` · `ĐVT nhập`
- **DanhMucHang.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Hàng` · `Đang kinh doanh` · `Mã sản phẩm bán` · `DVT` · `Tồn thực` · `Loại hàng` · `Giá vốn` · `Giá hiện tại`

### dev_009

- **danh_sach_hoa_don.csv** — CSV, 23338 data rows; columns: `Ngày tháng` · `Trạng thái đơn` · `TongTien` · `Mã hóa đơn` · `Nợ` · `Đã thu` · `Đối tác` · `Giá trị hàng`

### dev_010

- **chi_tiet_don.csv** — CSV, 45251 data rows; columns: `Mã bill` · `Cộng` · `CK` · `SoLuong` · `Mã H.hóa` · `SL quy đổi` · `No.` · `Đơn giá (đ)` · `dvt`
- **don_hang.csv** — CSV, 25702 data rows; columns: `Kênh đặt` · `Thành tiền` · `Số CT` · `Con no` · `Date` · `Phương thức TT` · `Tiền giảm` · `Phí vận chuyển` · `Khách trả` · `Mã thẻ` · `Xử lý`
- **khach_hang.csv** — CSV, 260 data rows; columns: `Người tạo` · `Ghi chú KH` · `Khách lẻ/sỉ` · `Loại khách` · `Mã số thuế` · `Loại hình khách` · `Mã khách` · `Email` · `Tổng điểm` · `Trạng thái` · `Số CMND/CCCD` · `Phone` · `Công ty`
- **san_pham.csv** — CSV, 60 data rows; columns: `Mô tả chi tiết` · `Mẫu ghi chú` · `Loại hàng hóa` · `Thương hiệu` · `Đơn vị tính` · `Ghi chú` · `Bảo hành` · `Nhóm hàng` · `Mã vạch EAN` · `Hình ảnh (url1,url2...)` · `ten_hang` · `Thuộc tính` · `Trọng lượng` · `Giá bán` · `Mã vạch` · `Được bán trực tiếp` · `Mã HH Liên quan`
- **thanh_toan.csv** — CSV, 26246 data rows; columns: `Loại TT` · `Ngay thu` · `So tien` · `Mã đơn` · `Mã TT`

### dev_011

- **SoBanHang.xlsx** — 2 sheet(s)
  - `Ghi tắt` (dimension unavailable); candidate header: `Ghi tắt` · `Tên hàng` · `Loại`
  - `Sổ bán hàng` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Thu máy cũ` · `Khách trả` · `Ghi chú`

### dev_012

- **DanhSachTho.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Họ tên` · `Ngày vào làm` · `Hoa hồng (%)`
- **SoSuaXe.xlsx** — 14 sheet(s)
  - `T7-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T8-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T9-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T10-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T11-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T12-2025` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T1-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T2-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T3-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T4-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T5-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T6-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T7-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`
  - `T8-2026` (dimension unavailable); candidate header: `Ngày` · `Xe` · `Làm gì` · `Thợ` · `Tiền` · `Ghi chú`

### dev_013

- **BanHang_2025.xlsx** — 8 sheet(s)
  - `T05-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T06-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T07-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T08-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T09-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T10-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T11-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T12-2025` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
- **BanHang_2026.xlsx** — 6 sheet(s)
  - `T01-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T02-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T03-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T04-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T05-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
  - `T06-2026` (dimension unavailable); candidate header: `ĐG` · `TT` · `SL` · `ĐVT` · `Tên hàng` · `HĐ` · `Ngày` · `Khách` · `Kênh` · `Ghi chú`
- **QuanLy.xlsx** — 4 sheet(s)
  - `DanhMuc` (dimension unavailable); candidate header: `Tên hàng` · `Tên gọi khác` · `Nhóm` · `Hãng` · `Số / Size` · `ĐVT` · `Quy đổi`
  - `KhachHang` (dimension unavailable); candidate header: `Tên KH` · `SĐT` · `Tên bé` · `Ngày đăng ký` · `Điểm hiện có`
  - `NhapHang` (dimension unavailable); candidate header: `Ngày` · `Số phiếu` · `Nhà cung cấp` · `Hàng` · `SL` · `ĐVT` · `Đơn giá` · `Thành tiền` · `Ghi chú`
  - `KhuyenMai` (dimension unavailable); candidate header: `Chương trình` · `Hàng áp dụng` · `Từ ngày` · `Đến ngày`

### dev_014

- **SoBanHang.xlsx** — 16 sheet(s)
  - `Ghi tắt` (dimension unavailable); candidate header: `Ghi tắt` · `Tên hàng` · `Loại`
  - `T7-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T8-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T9-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T10-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T11-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T12-2025` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T1-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T2-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T3-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T4-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T5-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T6-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T7-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T8-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
  - `T9-2026` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `Hàng` · `IMEI` · `SL` · `Giá` · `Thành tiền` · `Bớt` · `Khách trả` · `Ghi chú`
- **SoNo.xlsx** — 3 sheet(s)
  - `Sổ nợ` (dimension unavailable); candidate header: `Ngày` · `Khách` · `SĐT` · `Nợ` · `Đã trả` · `Ngày trả` · `Ghi chú`
  - `Trả góp` (dimension unavailable); candidate header: `Ngày` · `STT` · `Khách` · `SĐT` · `Máy` · `Giá` · `Trả trước` · `Số kỳ` · `Góp/tháng` · `Hạn góp (ngày)` · `Ngày góp` · `Đã góp`
  - `Bảo hành` (dimension unavailable); candidate header: `Ngày nhận` · `Khách` · `SĐT` · `Máy` · `IMEI` · `Ngày mua` · `Lỗi` · `Xử lý`
- **ThuMayCu.xlsx** — 1 sheet(s)
  - `Sheet1` (dimension unavailable); candidate header: `Ngày` · `Khách` · `SĐT` · `Máy thu` · `Tình trạng` · `IMEI` · `Giá thu` · `Trừ vào (STT sổ bán)`

## Follow-up

- Confirm inferred spreadsheet header rows against README; workbooks may have title rows, multi-row headers, repeated headers, or blank rows.
- Map all representative questions to source sheets, fields, joins, date semantics, units, and rulebook clauses.
- Record data quality findings without rewriting competition source files.
