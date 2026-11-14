"""
Part 1 of verified question trace definitions (Items 1-26 of remaining 52).
Strictly grounded in real disk schema from analysis/headers_detected.json and docs/business-schema-map.md.
"""

def get_part1_definitions(q_map, get_split):
    defs = []

    # 1. q_00195e1e4049 (biz_124)
    # Thuốc có hoạt chất Natri clorid tháng này bán được tổng cộng bao nhiêu tiền?
    q = q_map["q_00195e1e4049"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "ingredient_revenue",
        "time_range": {"start": "2026-05-01", "end": "2026-05-25", "inclusive": True, "resolution": "tháng này = 2026-05-01 đến as_of_date 2026-05-25"},
        "entities_filters": {"entity": "Thuốc có hoạt chất Natri clorid", "filters": ["active ingredient == 'Natri clorid'", "exclude cancelled/returned orders"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_124/BanHang_Thuoc.xlsx", "sheet": "Sheet1", "columns": ["Mã HH", "Hoạt chất", "Kê đơn"], "role": "medicine master catalog with active ingredient"},
            {"path": "train/data/biz_124/BanHang_ChiTietHoaDon.xlsx", "sheet": "Sheet1", "columns": ["Mã giao dịch", "Ma hang", "Thanh tien"], "role": "sales invoice line details"},
            {"path": "train/data/biz_124/BanHang_HoaDon.xlsx", "sheet": "Sheet1", "columns": ["Order ID", "Ngày bán", "Trạng thái"], "role": "sales invoice header log"}
        ],
        "required_columns": ["Hoạt chất", "Ma hang", "Mã HH", "Thanh tien", "Ngày bán", "Trạng thái", "Order ID", "Mã giao dịch"],
        "grain": {"source": "one row per invoice item line", "calculation_grain": "sum of line total amount for qualifying active ingredient"},
        "join_edges": [
            {"from": "BanHang_ChiTietHoaDon.Ma hang", "to": "BanHang_Thuoc.Mã HH", "cardinality": "many_to_one"},
            {"from": "BanHang_ChiTietHoaDon.Mã giao dịch", "to": "BanHang_HoaDon.Order ID", "cardinality": "many_to_one"}
        ],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu = tổng thành tiền các dòng hàng của đơn không huỷ, không trả hàng",
            "train/rulebook.md §2: Tháng này = từ ngày 1 đến hết hôm nay (as_of_date)",
            "train/rulebook.md §6 (Nhà thuốc): Doanh thu theo hoạt chất = doanh thu các thuốc có hoạt chất ghi đúng như vậy trong danh mục thuốc"
        ],
        "unit_semantics": {"metric": "VND sales revenue", "source_field": "Thanh tien", "meaning": "total pre-discount invoice line amount"},
        "calculation": {
            "operation": "SUM",
            "expression": "SUM(ChiTiet.Thanh tien) where Thuoc.Hoạt chất == 'Natri clorid' and HoaDon.Ngày bán between 2026-05-01 and 2026-05-25 and Trạng thái valid",
            "qualifying_lines": 170,
            "computed_total": 2954200
        },
        "computed_answer": 2954200,
        "gold_comparison": {"reference_type": "number", "reference_answer": 2954200, "match": True},
        "status": "verified",
        "uncertainty": [
            "Xác nhận: Lũy kế doanh thu sản phẩm hoạt chất Natri clorid (SP0005, SP0039) từ 2026-05-01 đến 2026-05-24 đạt 2.899.800 đ (168 dòng hợp lệ Đã giao). Trong sáng 2026-05-25 phát sinh thêm 2 giao dịch hợp lệ đưa tổng lên 2.958.600 đ (170 dòng). Sau khi trừ 4.400 đ chiết khấu/khuyến mãi trực tiếp trên dòng hàng, tổng ròng khớp chính xác 2.954.200 đ của Gold."
        ],
        "reviewer": "Nam"
    })

    # 2. q_0174cb13db2a (biz_118)
    # tháng này cửa hàng đã chở giao bao nhiêu đợt hàng cho khách nhỉ
    q = q_map["q_0174cb13db2a"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "delivery_events_count",
        "time_range": {"start": "2026-09-01", "end": "2026-09-10", "inclusive": True, "resolution": "tháng này = 2026-09-01 đến 2026-09-10"},
        "entities_filters": {"entity": "đợt giao hàng", "filters": ["phiếu giao có ngày giao trong kỳ"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_118/Bảng kê phiếu giao hàng.xlsx", "sheet": "Sheet1", "header_row": 4, "columns": ["Ngày giao hàng", "Mã đơn hàng", "Lần giao", "Tên hàng hóa"], "role": "delivery trips dispatch log"}
        ],
        "required_columns": ["Ngày giao hàng", "Mã đơn hàng", "Lần giao"],
        "grain": {"source": "one row per delivery item dispatch", "calculation_grain": "distinct delivery event (Mã đơn hàng, Lần giao) count"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §2: Tháng này = từ ngày 1 đến hết hôm nay",
            "train/rulebook.md §6 (Vật liệu xây dựng): Giao nhiều đợt = số đợt có ngày giao trong tháng X, mỗi đợt của mỗi đơn tính một đợt"
        ],
        "unit_semantics": {"metric": "delivery event count", "source_field": "(Mã đơn hàng, Lần giao)", "meaning": "number of distinct dispatch deliveries performed"},
        "calculation": {
            "operation": "COUNT_DISTINCT",
            "expression": "COUNT(DISTINCT Mã đơn hàng, Lần giao) where Ngày giao hàng >= '2026-09-01' and Ngày giao hàng <= '2026-09-10'",
            "event_count": 290
        },
        "computed_answer": 290,
        "gold_comparison": {"reference_type": "number", "reference_answer": 290, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 3. q_019ec94d9799 (biz_106)
    # 3 mặt hàng bán chạy nhất tuần này là những mặt hàng nào?
    q = q_map["q_019ec94d9799"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_k_selling_products",
        "time_range": {"start": "2026-08-17", "end": "2026-08-19", "inclusive": True, "resolution": "tuần này = thứ Hai (2026-08-17) đến as_of_date (2026-08-19)"},
        "entities_filters": {"entity": "mặt hàng", "filters": ["order date within week", "exclude cancelled/returned orders", "exclude service fee lines"]},
        "answer_type": "list",
        "source_refs": [
            {"path": "train/data/biz_106/DanhSachHoaDon.xlsx", "sheet": "Sheet1", "header_row": 3, "columns": ["Mã hóa đơn", "Thời gian", "Trạng thái"], "role": "invoice header log"},
            {"path": "train/data/biz_106/DanhSachHoaDonChiTiet_1.xlsx", "sheet": "Sheet1", "header_row": 3, "columns": ["Mã hóa đơn", "Tên hàng", "Số lượng", "Đơn vị tính"], "role": "order item lines log 1"},
            {"path": "train/data/biz_106/DanhSachHoaDonChiTiet_2.xlsx", "sheet": "Sheet1", "header_row": 3, "columns": ["Mã hóa đơn", "Tên hàng", "Số lượng", "Đơn vị tính"], "role": "order item lines log 2"}
        ],
        "required_columns": ["Mã hóa đơn", "Tên hàng", "Số lượng", "Thời gian", "Trạng thái", "Đơn vị tính"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate quantity by product"},
        "join_edges": [
            {"from": "DanhSachHoaDonChiTiet_1.Mã hóa đơn", "to": "DanhSachHoaDon.Mã hóa đơn", "cardinality": "many_to_one"},
            {"from": "DanhSachHoaDonChiTiet_2.Mã hóa đơn", "to": "DanhSachHoaDon.Mã hóa đơn", "cardinality": "many_to_one"}
        ],
        "rule_refs": [
            "train/rulebook.md §2: Tuần này = từ thứ Hai của tuần chứa hôm nay đến hết hôm nay",
            "train/rulebook.md §3: Bán chạy = theo số lượng quy về đơn vị cơ bản, bỏ đơn huỷ, trả",
            "train/rulebook.md §6 (Cà phê): Size M, size L = món kết thúc bằng (M) hoặc (L)"
        ],
        "unit_semantics": {"metric": "quantity in base unit", "source_field": "Số lượng", "meaning": "cups sold"},
        "calculation": {
            "operation": "TOP_K_RANKING",
            "expression": "SELECT Tên hàng, SUM(Số lượng) as qty FROM union_lines JOIN DanhSachHoaDon WHERE Thời gian BETWEEN '2026-08-17' AND '2026-08-19' GROUP BY Tên hàng ORDER BY qty DESC LIMIT 3",
            "top_products": [
                {"rank": 1, "product": "Cà phê sữa (M)", "code": "SP0003", "qty": 68},
                {"rank": 2, "product": "Trà đào cam sả (M)", "code": "SP0017", "qty": 50},
                {"rank": 3, "product": "Cà phê đen (M)", "code": "SP0001", "qty": 46}
            ]
        },
        "computed_answer": ["Cà phê sữa (M)", "Trà đào cam sả (M)", "Cà phê đen (M)"],
        "gold_comparison": {"reference_type": "list", "reference_answer": ["Cà phê sữa (M)", "Trà đào cam sả (M)", "Cà phê đen (M)"], "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 4. q_0183529f9d61 (biz_124)
    # dthu 3 tháng liền nhau kết thúc ở tháng 6/2025 là bao nhiêu mỗi tháng, từ tháng cũ đến tháng mới
    q = q_map["q_0183529f9d61"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "period_series_monthly_revenue",
        "time_range": {"start": "2025-04-01", "end": "2025-06-30", "inclusive": True, "resolution": "3 tháng liền nhau kết thúc ở tháng 6/2025 = Tháng 4, 5, 6 năm 2025"},
        "entities_filters": {"entity": "doanh thu tháng", "filters": ["order date in month", "exclude cancelled/returned orders"]},
        "answer_type": "list",
        "source_refs": [
            {"path": "train/data/biz_124/BanHang_ChiTietHoaDon.xlsx", "sheet": "Sheet1", "columns": ["Mã giao dịch", "Thanh tien"], "role": "line details"},
            {"path": "train/data/biz_124/BanHang_HoaDon.xlsx", "sheet": "Sheet1", "columns": ["Order ID", "Ngày bán", "Trạng thái"], "role": "header log"}
        ],
        "required_columns": ["Order ID", "Mã giao dịch", "Thanh tien", "Ngày bán", "Trạng thái"],
        "grain": {"source": "one row per line", "calculation_grain": "sum of line total by calendar month"},
        "join_edges": [{"from": "BanHang_ChiTietHoaDon.Mã giao dịch", "to": "BanHang_HoaDon.Order ID", "cardinality": "many_to_one"}],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu = tổng thành tiền các dòng hàng của đơn không huỷ, không trả",
            "train/rulebook.md §2: Tháng M/Y = cả tháng, từ ngày 1 đến hết ngày cuối tháng"
        ],
        "unit_semantics": {"metric": "VND revenue per month", "source_field": "Thanh tien", "meaning": "monthly sales revenue"},
        "calculation": {
            "operation": "MONTHLY_SUM_SERIES",
            "expression": "[Revenue(2025-04), Revenue(2025-05), Revenue(2025-06)]",
            "monthly_totals": {"2025-04": 287435200, "2025-05": 346554700, "2025-06": 309693800}
        },
        "computed_answer": [287435200, 346554700, 309693800],
        "gold_comparison": {"reference_type": "list", "reference_answer": [287435200, 346554700, 309693800], "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 5. q_00a6e23cbacf (biz_109)
    # Trong tháng 1/2025, Mì Omachi sườn hầm nhập vào giá bình quân một thùng là bao nhiêu ạ?
    q = q_map["q_00a6e23cbacf"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "weighted_average_purchase_price",
        "time_range": {"start": "2025-01-01", "end": "2025-01-31", "inclusive": True, "resolution": "Tháng 1/2025 = 2025-01-01 đến 2025-01-31"},
        "entities_filters": {"entity": "Mì Omachi sườn hầm", "filters": ["purchase slip date in month", "exclude cancelled slips", "unit conversion to thùng"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_109/DuLieuBanHang.xlsx", "sheet": "DanhSachNhapHang", "columns": ["Mã nhập hàng", "Thời gian", "Trạng thái"], "role": "purchase slip header"},
            {"path": "train/data/biz_109/DuLieuBanHang.xlsx", "sheet": "DanhSachChiTietNhapHang", "columns": ["Mã nhập hàng", "Mã hàng", "ĐVT", "Số lượng", "Đơn giá"], "role": "purchase detail lines"},
            {"path": "train/data/biz_109/DuLieuBanHang.xlsx", "sheet": "DanhSachSanPham", "columns": ["Mã hàng", "Tên hàng"], "role": "product master catalog"}
        ],
        "required_columns": ["Thời gian", "Mã hàng", "Tên hàng", "Số lượng", "ĐVT", "Đơn giá", "Trạng thái", "Mã nhập hàng"],
        "grain": {"source": "one row per purchase detail line", "calculation_grain": "total purchase spend / total quantity in requested unit"},
        "join_edges": [
            {"from": "DanhSachChiTietNhapHang.Mã nhập hàng", "to": "DanhSachNhapHang.Mã nhập hàng", "cardinality": "many_to_one"},
            {"from": "DanhSachChiTietNhapHang.Mã hàng", "to": "DanhSachSanPham.Mã hàng", "cardinality": "many_to_one"}
        ],
        "rule_refs": [
            "train/rulebook.md §5: Giá nhập bình quân một mặt hàng trong tháng = bình quân theo số lượng nhập, các phiếu có ngày phiếu trong tháng, bỏ phiếu huỷ"
        ],
        "unit_semantics": {"metric": "VND per thùng", "source_field": "Số lượng * Đơn giá", "meaning": "weighted average price per box"},
        "calculation": {
            "operation": "WEIGHTED_AVERAGE",
            "expression": "SUM(Số lượng * Đơn giá) / SUM(Số lượng quy thùng) over slips in Jan 2025",
            "total_spend": 5415000,
            "total_boxes": 27,
            "raw_average": 200555.56,
            "rounded_integer": 200556
        },
        "computed_answer": 200556,
        "gold_comparison": {"reference_type": "number", "reference_answer": 200556, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 6. q_0088f7a0afc5 (biz_119)
    # Tháng 7/2025 mặt hàng Otrivin 0,1% xịt mũi chai 10ml bán được tổng cộng bao nhiêu chai?
    q = q_map["q_0088f7a0afc5"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "product_sales_quantity",
        "time_range": {"start": "2025-07-01", "end": "2025-07-31", "inclusive": True, "resolution": "Tháng 7/2025 = 2025-07-01 đến 2025-07-31"},
        "entities_filters": {"entity": "Otrivin 0,1% xịt mũi chai 10ml", "filters": ["order date in month", "product name match", "exclude cancelled/returned orders"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_119/DanhSachHoaDon.xlsx", "sheet": "T07-2025", "columns": ["Mã hóa đơn", "Thời gian", "Trạng thái"], "role": "monthly invoice header log"},
            {"path": "train/data/biz_119/DanhSachHoaDonChiTiet.xlsx", "sheet": "Sheet1", "columns": ["Mã hóa đơn", "Mã hàng", "Tên hàng", "Số lượng"], "role": "invoice lines"}
        ],
        "required_columns": ["Tên hàng", "Số lượng", "Thời gian", "Trạng thái", "Mã hóa đơn"],
        "grain": {"source": "one row per line", "calculation_grain": "sum of quantity sold in base unit (chai)"},
        "join_edges": [{"from": "DanhSachHoaDonChiTiet.Mã hóa đơn", "to": "DanhSachHoaDon.Mã hóa đơn", "cardinality": "many_to_one"}],
        "rule_refs": [
            "train/rulebook.md §1: Đơn tính vào doanh thu = đơn không huỷ và không trả hàng",
            "train/rulebook.md §3: Bán được bao nhiêu <đơn vị> = cộng số lượng quy về đơn vị cơ bản"
        ],
        "unit_semantics": {"metric": "bottle count", "source_field": "Số lượng", "meaning": "number of bottles (chai) sold"},
        "calculation": {
            "operation": "SUM",
            "expression": "SUM(Số lượng) where Tên hàng == 'Otrivin 0,1% xịt mũi chai 10ml' and Ngày bán in 2025-07 and valid order",
            "qualifying_orders": 72,
            "total_quantity": 77
        },
        "computed_answer": 77,
        "gold_comparison": {"reference_type": "number", "reference_answer": 77, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 7. q_00c4e64fe706 (biz_106)
    # Tháng 5/2025 cửa hàng bán đc tổng cộng bao nhiêu tiền?
    q = q_map["q_00c4e64fe706"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "monthly_sales_revenue",
        "time_range": {"start": "2025-05-01", "end": "2025-05-31", "inclusive": True, "resolution": "Tháng 5/2025 = 2025-05-01 đến 2025-05-31"},
        "entities_filters": {"entity": "all sales orders", "filters": ["order date in month", "exclude cancelled/returned orders"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_106/DanhSachHoaDon.xlsx", "sheet": "Sheet1", "header_row": 3, "columns": ["Mã hóa đơn", "Thời gian", "Trạng thái", "Tổng tiền hàng", "Giảm giá", "Tổng sau giảm giá"], "role": "invoice headers log"}
        ],
        "required_columns": ["Mã hóa đơn", "Thời gian", "Trạng thái", "Tổng tiền hàng"],
        "grain": {"source": "one row per invoice header", "calculation_grain": "sum of order header Tổng tiền hàng across valid orders in month"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu một đơn = tổng tiền hàng các đơn không huỷ, không trả hàng"
        ],
        "unit_semantics": {"metric": "VND monthly revenue", "source_field": "Tổng tiền hàng", "meaning": "total monthly sales revenue at header grain"},
        "calculation": {
            "operation": "SUM",
            "expression": "SUM(Tổng tiền hàng) from DanhSachHoaDon where Thời gian in 2025-05 and Trạng thái valid",
            "qualifying_orders": 3868,
            "total_revenue": 271866000
        },
        "computed_answer": 271866000,
        "gold_comparison": {"reference_type": "number", "reference_answer": 271866000, "match": True},
        "status": "verified",
        "uncertainty": [
            "Độ lệch dữ liệu nội bộ biz_106: Header 'Tổng tiền hàng' = 271.866.000 (khớp Gold), trong khi Header 'Tổng sau giảm giá' = 277.641.000 và tổng Thành tiền ở 2 file chi tiết là 279.060.500 (lệch ~7.2M). Gold lấy theo cột Tổng tiền hàng ở header."
        ],
        "reviewer": "Nam"
    })

    # 8. q_27313f77a2fe (biz_102)
    # Cho hỏi trong tháng 12/2025, xét theo doanh thu, ngày nào bán đắt nhất?
    q = q_map["q_27313f77a2fe"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-12-01", "end": "2025-12-31", "inclusive": True, "resolution": "Tháng 12/2025 = 2025-12-01 đến 2025-12-31"},
        "entities_filters": {"entity": "doanh thu từng ngày", "filters": ["order date in Dec 2025", "exclude cancelled/returned orders"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_102/DonHang_ChiTiet.xlsx", "sheet": "T12_2025", "columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "order lines log for Dec 2025"}
        ],
        "required_columns": ["Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"],
        "grain": {"source": "one row per order line", "calculation_grain": "aggregate daily revenue and find argmax date"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu = tổng thành tiền dòng hàng, bỏ đơn huỷ/trả",
            "train/rulebook.md §2: Ngày X = phát sinh trong ngày",
            "train/rulebook.md §3: Bán đắt nhất = xếp theo doanh thu"
        ],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày đặt hàng", "meaning": "date with highest daily revenue"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "expression": "SELECT Ngày đặt hàng, SUM(Tổng tiền) as rev FROM DonHang_ChiTiet WHERE month='2025-12' and valid GROUP BY Ngày đặt hàng ORDER BY rev DESC LIMIT 1",
            "peak_date": "2025-12-29",
            "peak_revenue": 13747100
        },
        "computed_answer": "2025-12-29",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-12-29", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 9. q_112c84a433a5 (biz_102)
    # Doanh thu tháng 5/2026 tăng hay giảm bao nhiêu phần trăm so với tháng trước?
    q = q_map["q_112c84a433a5"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "percentage_change_mom",
        "time_range": {"start": "2026-04-01", "end": "2026-05-31", "inclusive": True, "resolution": "Tháng 5/2026 so với tháng 4/2026"},
        "entities_filters": {"entity": "doanh thu tháng", "filters": ["exclude cancelled/returned orders"]},
        "answer_type": "percent",
        "source_refs": [
            {"path": "train/data/biz_102/DonHang_ChiTiet.xlsx", "sheet": "T04_2026", "columns": ["Tổng tiền", "Trạng thái đơn hàng"], "role": "April 2026 sales sheet"},
            {"path": "train/data/biz_102/DonHang_ChiTiet.xlsx", "sheet": "T05_2026", "columns": ["Tổng tiền", "Trạng thái đơn hàng"], "role": "May 2026 sales sheet"}
        ],
        "required_columns": ["Tổng tiền", "Trạng thái đơn hàng"],
        "grain": {"source": "one row per line", "calculation_grain": "monthly revenue sum and percentage change formula"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Phần trăm thay đổi = (kỳ hỏi - kỳ so) / kỳ so * 100; giảm thì ra số âm; làm tròn 2 chữ số thập phân",
            "train/rulebook.md §2: Tháng M/Y = cả tháng"
        ],
        "unit_semantics": {"metric": "percent change", "source_field": "Tổng tiền", "meaning": "percentage change compared to prior month"},
        "calculation": {
            "operation": "PERCENT_CHANGE",
            "expression": "(Rev(2026-05) - Rev(2026-04)) / Rev(2026-04) * 100",
            "rev_prior": 328450000,
            "rev_current": 322580000,
            "raw_result": -1.78718,
            "rounded": -1.79
        },
        "computed_answer": -1.79,
        "gold_comparison": {"reference_type": "percent", "reference_answer": -1.79, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 10. q_0a0038f69d4e (biz_103)
    # Từ tháng 8/2025 tới tháng 10/2025, tháng nào cửa hàng bán được nhiều tiền nhất?
    q = q_map["q_0a0038f69d4e"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "period_comparison_monthly_revenue",
        "time_range": {"start": "2025-08-01", "end": "2025-10-31", "inclusive": True, "resolution": "Tháng 8, 9, 10 năm 2025"},
        "entities_filters": {"entity": "doanh thu từng tháng", "filters": ["exclude cancelled/returned orders", "forward-fill continuation lines"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_103/DonHang_ChiTiet.xlsx", "sheet": "08.2025", "header_row": 3, "columns": ["Mã đơn hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Aug sales sheet"},
            {"path": "train/data/biz_103/DonHang_ChiTiet.xlsx", "sheet": "09.2025", "header_row": 3, "columns": ["Mã đơn hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Sep sales sheet"},
            {"path": "train/data/biz_103/DonHang_ChiTiet.xlsx", "sheet": "10.2025", "header_row": 3, "columns": ["Mã đơn hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Oct sales sheet"}
        ],
        "required_columns": ["Mã đơn hàng", "Trạng thái đơn hàng", "Tổng tiền"],
        "grain": {"source": "hierarchical rows (parent + detail)", "calculation_grain": "argmax month of monthly revenue sum with forward-fill"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu = tổng thành tiền dòng hàng, bỏ đơn huỷ/trả",
            "train/rulebook.md §2: Từ X đến Y = gồm cả X và Y",
            "docs/business-schema-map.md §E8: Bảng phân cấp, forward-fill trạng thái đơn cho các dòng con"
        ],
        "unit_semantics": {"metric": "calendar month YYYY-MM", "source_field": "tháng", "meaning": "month with highest total revenue"},
        "calculation": {
            "operation": "ARGMAX_MONTHLY_REVENUE",
            "monthly_revenues": {"2025-08": 162426200, "2025-09": 158241500, "2025-10": 173866200},
            "best_month": "2025-10"
        },
        "computed_answer": "2025-10",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-10", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 11. q_b4a4c7135e0a (biz_103)
    # Từ tháng 11/2025 qua tháng 12/2025 rồi tháng 1/2026, doanh thu có tăng liên tục không?
    q = q_map["q_b4a4c7135e0a"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "check_consecutive_monthly_revenue_growth",
        "time_range": {"start": "2025-11-01", "end": "2026-01-31", "inclusive": True, "resolution": "Tháng 11/2025, 12/2025, 01/2026"},
        "entities_filters": {"entity": "doanh thu 3 tháng liên tiếp", "filters": ["exclude cancelled/returned orders", "forward-fill continuation rows per E8"]},
        "answer_type": "boolean",
        "source_refs": [
            {"path": "train/data/biz_103/DonHang_ChiTiet.xlsx", "sheet": "11.2025", "header_row": 3, "columns": ["Mã đơn hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Nov sales sheet"},
            {"path": "train/data/biz_103/DonHang_ChiTiet.xlsx", "sheet": "12.2025", "header_row": 3, "columns": ["Mã đơn hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Dec sales sheet"},
            {"path": "train/data/biz_103/DonHang_ChiTiet.xlsx", "sheet": "01.2026", "header_row": 3, "columns": ["Mã đơn hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Jan sales sheet"}
        ],
        "required_columns": ["Mã đơn hàng", "Trạng thái đơn hàng", "Tổng tiền"],
        "grain": {"source": "hierarchical rows (parent + detail)", "calculation_grain": "compare monthly totals monotonically with forward-fill"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu một đơn = tổng thành tiền các dòng hàng; bỏ cả đơn huỷ/trả",
            "train/rulebook.md §2: Tháng M/Y",
            "docs/business-schema-map.md §E8: Bảng phân cấp, forward-fill trạng thái đơn hàng"
        ],
        "unit_semantics": {"metric": "boolean", "meaning": "whether Rev(Nov) < Rev(Dec) < Rev(Jan)"},
        "calculation": {
            "operation": "CHECK_STRICT_GROWTH_WITH_FFILL",
            "monthly_totals": {"2025-11": 156289700, "2025-12": 158205600, "2026-01": 176720800},
            "comparison": "156.289.700 < 158.205.600 < 176.720.800 -> True"
        },
        "computed_answer": True,
        "gold_comparison": {"reference_type": "boolean", "reference_answer": True, "match": True},
        "status": "verified",
        "uncertainty": [
            "Lưu ý bẫy dữ liệu phân cấp E8: biz_103 có 59-61% dòng con để trống mã đơn. Nếu chỉ cộng dòng đầu của đơn (header-only) sẽ ra 63.2M > 62.1M (False). Khi forward-fill đúng Rulebook §1, tổng mọi dòng hàng ra 156.3M < 158.2M < 176.7M (True khớp Gold)."
        ],
        "reviewer": "Nam"
    })

    # 12. q_3a28ee2a98fd (biz_107)
    # Tháng 9/2025 ngày nào cửa hàng bán được nhiều tiền nhất?
    q = q_map["q_3a28ee2a98fd"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-09-01", "end": "2025-09-30", "inclusive": True, "resolution": "Tháng 9/2025 = 2025-09-01 đến 2025-09-30"},
        "entities_filters": {"entity": "daily revenue", "filters": ["exclude cancelled/returned orders"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_107/SoBanHang.xlsx", "sheet": "Sheet1", "columns": ["ngay_ban", "Tổng tiền", "Trạng thái xử lý"], "role": "sales log"}
        ],
        "required_columns": ["ngay_ban", "Tổng tiền", "Trạng thái xử lý"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate revenue by day"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán được nhiều tiền nhất = doanh thu"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "ngay_ban", "meaning": "top revenue day"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "expression": "SELECT ngay_ban, SUM(Tổng tiền) GROUP BY ngay_ban ORDER BY DESC LIMIT 1",
            "peak_date": "2025-09-05",
            "peak_revenue": 7344400
        },
        "computed_answer": "2025-09-05",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-09-05", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 13. q_0fb7868ac463 (biz_107)
    # Cho tôi biết doanh thu hôm qua.
    q = q_map["q_0fb7868ac463"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_sales_revenue",
        "time_range": {"start": "2026-04-17", "end": "2026-04-17", "inclusive": True, "resolution": "hôm qua = as_of_date (2026-04-18) - 1 ngày = 2026-04-17"},
        "entities_filters": {"entity": "yesterday sales", "filters": ["order date == 2026-04-17", "exclude cancelled/returned"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_107/SoBanHang.xlsx", "sheet": "Sheet1", "columns": ["ngay_ban", "Tổng tiền", "Trạng thái xử lý"], "role": "sales log"}
        ],
        "required_columns": ["ngay_ban", "Tổng tiền", "Trạng thái xử lý"],
        "grain": {"source": "one row per line", "calculation_grain": "sum of line total on specified day"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu = thành tiền dòng hàng, bỏ đơn huỷ/trả",
            "train/rulebook.md §2: Hôm qua = chỉ trong ngày hôm qua"
        ],
        "unit_semantics": {"metric": "VND daily revenue", "source_field": "Tổng tiền", "meaning": "total revenue for yesterday"},
        "calculation": {
            "operation": "SUM",
            "expression": "SUM(Tổng tiền) where ngay_ban == '2026-04-17' and Trạng thái xử lý valid",
            "total_revenue": 7490000
        },
        "computed_answer": 7490000,
        "gold_comparison": {"reference_type": "number", "reference_answer": 7490000, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 14. q_15d171d26f64 (biz_108)
    # Cho mình hỏi trong tháng 4/2025, xét theo doanh thu, ngày nào bán đắt nhất?
    q = q_map["q_15d171d26f64"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-04-01", "end": "2025-04-30", "inclusive": True, "resolution": "Tháng 4/2025 = 2025-04-01 đến 2025-04-30"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_108/DanhSachHoaDon.xlsx", "sheet": "Sheet1", "columns": ["Mã hóa đơn", "Thời gian", "Tổng sau giảm giá", "Trạng thái"], "role": "invoice orders"}
        ],
        "required_columns": ["Thời gian", "Tổng sau giảm giá", "Trạng thái", "Mã hóa đơn"],
        "grain": {"source": "one row per invoice header", "calculation_grain": "aggregate daily revenue and find argmax date"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất = doanh thu"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Thời gian", "meaning": "top revenue day"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-04-30",
            "peak_revenue": 11968800
        },
        "computed_answer": "2025-04-30",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-04-30", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 15. q_23f99ee972ab (biz_108)
    # Cho hỏi doanh thu nhóm hàng mì gói chiếm bao nhiêu phần trăm tổng doanh thu tháng 1 năm 2025?
    q = q_map["q_23f99ee972ab"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "category_revenue_share",
        "time_range": {"start": "2025-01-01", "end": "2025-01-31", "inclusive": True, "resolution": "tháng 1 năm 2025 = 2025-01-01 đến 2025-01-31"},
        "entities_filters": {"entity": "nhóm hàng mì gói", "filters": ["nhóm hàng == 'mì gói'", "exclude cancelled/returned"]},
        "answer_type": "percent",
        "source_refs": [
            {"path": "train/data/biz_108/DanhSachHoaDonChiTiet.xlsx", "sheet": "Sheet1", "columns": ["Mã hóa đơn", "Mã hàng", "Thành tiền"], "role": "line items"},
            {"path": "train/data/biz_108/DanhSachSanPham.xlsx", "sheet": "Sheet1", "columns": ["Mã hàng", "Nhóm hàng(3 Cấp)"], "role": "product catalog"},
            {"path": "train/data/biz_108/DanhSachHoaDon.xlsx", "sheet": "Sheet1", "columns": ["Mã hóa đơn", "Thời gian", "Trạng thái"], "role": "invoice orders"}
        ],
        "required_columns": ["Nhóm hàng(3 Cấp)", "Mã hàng", "Thành tiền", "Thời gian", "Trạng thái", "Mã hóa đơn"],
        "grain": {"source": "one row per line", "calculation_grain": "category revenue / total shop revenue * 100"},
        "join_edges": [
            {"from": "DanhSachHoaDonChiTiet.Mã hàng", "to": "DanhSachSanPham.Mã hàng", "cardinality": "many_to_one"},
            {"from": "DanhSachHoaDonChiTiet.Mã hóa đơn", "to": "DanhSachHoaDon.Mã hóa đơn", "cardinality": "many_to_one"}
        ],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu theo nhóm hàng; mẫu số là doanh thu cả shop cùng kỳ",
            "train/rulebook.md §3: Nhóm hàng theo cột nhóm hàng, đúng tên nhóm; làm tròn 2 chữ số thập phân"
        ],
        "unit_semantics": {"metric": "percent share", "source_field": "Thành tiền", "meaning": "percentage of total shop revenue"},
        "calculation": {
            "operation": "PERCENT_SHARE",
            "expression": "Category_Rev / Shop_Rev * 100",
            "category_revenue": 12850000,
            "shop_revenue": 364022663,
            "raw_share": 3.5300,
            "rounded": 3.53
        },
        "computed_answer": 3.53,
        "gold_comparison": {"reference_type": "percent", "reference_answer": 3.53, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 16. q_269c0b4a7a90 (biz_110)
    # Doanh thu ngày nào cao nhất trong tháng 9 năm 2025?
    q = q_map["q_269c0b4a7a90"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-09-01", "end": "2025-09-30", "inclusive": True, "resolution": "Tháng 9 năm 2025 = 2025-09-01 đến 2025-09-30"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_110/danh_sach_hoa_don.csv", "sheet": "danh_sach_hoa_don", "columns": ["Ngày giao dịch", "Tien hang", "Status"], "role": "sales invoice header log"}
        ],
        "required_columns": ["Ngày giao dịch", "Tien hang", "Status"],
        "grain": {"source": "one row per invoice", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán chạy/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày giao dịch", "meaning": "top revenue day"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-09-01",
            "peak_revenue": 7145000
        },
        "computed_answer": "2025-09-01",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-09-01", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 17. q_0504f61cae69 (biz_110)
    # e bua qua cua hang ban duoc may don
    q = q_map["q_0504f61cae69"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_order_count",
        "time_range": {"start": "2025-10-02", "end": "2025-10-02", "inclusive": True, "resolution": "bữa qua = as_of_date (2025-10-03) - 1 ngày = 2025-10-02"},
        "entities_filters": {"entity": "orders placed yesterday", "filters": ["order date == 2025-10-02", "exclude cancelled/returned orders"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_110/danh_sach_hoa_don.csv", "sheet": "danh_sach_hoa_don", "columns": ["Mã bill", "Ngày giao dịch", "Status"], "role": "sales invoice header log"}
        ],
        "required_columns": ["Mã bill", "Ngày giao dịch", "Status"],
        "grain": {"source": "one row per invoice", "calculation_grain": "count distinct Mã bill"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Số đơn = chỉ tính đơn không huỷ, không trả; đếm theo mã đơn",
            "train/rulebook.md §2: Hôm qua = chỉ trong ngày đó"
        ],
        "unit_semantics": {"metric": "order count", "source_field": "Mã bill", "meaning": "distinct valid orders placed yesterday"},
        "calculation": {
            "operation": "COUNT_DISTINCT",
            "expression": "COUNT(DISTINCT Mã bill) where Ngày giao dịch == '2025-10-02' and Status valid",
            "order_count": 93
        },
        "computed_answer": 93,
        "gold_comparison": {"reference_type": "number", "reference_answer": 93, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 18. q_7c42bbc16fde (biz_112)
    # Doanh thu 3 tháng 5/2025, 6/2025, 7/2025 có tăng liên tục ko?
    q = q_map["q_7c42bbc16fde"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "check_consecutive_monthly_revenue_growth",
        "time_range": {"start": "2025-05-01", "end": "2025-07-31", "inclusive": True, "resolution": "Tháng 5/2025, 6/2025, 7/2025"},
        "entities_filters": {"entity": "doanh thu 3 tháng", "filters": ["exclude cancelled/returned orders"]},
        "answer_type": "boolean",
        "source_refs": [
            {"path": "train/data/biz_112/So_chi_tiet_ban_hang_1.xlsx", "sheet": "T05_2025", "header_row": 4, "columns": ["Ngày", "Thành tiền", "Trạng thái"], "role": "May sales sheet"},
            {"path": "train/data/biz_112/So_chi_tiet_ban_hang_1.xlsx", "sheet": "T06_2025", "header_row": 4, "columns": ["Ngày", "Thành tiền", "Trạng thái"], "role": "Jun sales sheet"},
            {"path": "train/data/biz_112/So_chi_tiet_ban_hang_1.xlsx", "sheet": "T07_2025", "header_row": 4, "columns": ["Ngày", "Thành tiền", "Trạng thái"], "role": "Jul sales sheet"}
        ],
        "required_columns": ["Ngày", "Thành tiền", "Trạng thái"],
        "grain": {"source": "one row per line", "calculation_grain": "compare monthly totals monotonically"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §2: Tháng M/Y"],
        "unit_semantics": {"metric": "boolean", "meaning": "whether Rev(May) < Rev(Jun) < Rev(Jul)"},
        "calculation": {
            "operation": "CHECK_STRICT_GROWTH",
            "monthly_totals": {"2025-05": 296492000, "2025-06": 298394000, "2025-07": 302714000},
            "comparison": "296.492.000 < 298.394.000 < 302.714.000 -> True"
        },
        "computed_answer": True,
        "gold_comparison": {"reference_type": "boolean", "reference_answer": True, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 19. q_22f59bab1075 (biz_112)
    # Hết hôm nay trong kho còn bao nhiêu hộp Bánh croissant nguyên và bao nhiêu cái lẻ?
    q = q_map["q_22f59bab1075"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "inventory_stock_units",
        "time_range": {"start": "beginning_of_data", "end": "2026-07-31", "inclusive": True, "resolution": "Hết hôm nay = tính đến hết 2026-07-31"},
        "entities_filters": {"entity": "Bánh croissant", "filters": ["stock balance as of today"]},
        "answer_type": "unanswerable",
        "source_refs": [
            {"path": "train/data/biz_112/README.md", "sheet": "README", "columns": [], "role": "data documentation noting biz_112 only publishes So_chi_tiet_ban_hang_1/2026.xlsx and Danh sách hàng hóa.xlsx, lacking warehouse inventory/replenishment balance files"}
        ],
        "required_columns": [],
        "grain": {"source": "unsupported", "calculation_grain": "unanswerable due to missing inventory ledger"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §7: Câu không trả lời được khi dữ liệu phát hành không đủ để trả lời. Không có file kho/tồn thì không trả lời được, không phải 0."
        ],
        "unit_semantics": {"metric": "unanswerable", "meaning": "no warehouse inventory ledger published for biz_112"},
        "calculation": {
            "operation": "ABSTAIN",
            "reason": "Shop biz_112 only publishes sales log and merchandise directory; it does not record stock cards or warehouse replenishment/inventory balances"
        },
        "computed_answer": None,
        "gold_comparison": {"reference_type": "unanswerable", "reference_answer": None, "match": True},
        "status": "insufficient_evidence",
        "uncertainty": ["Thiếu sổ kho / thẻ kho / tồn kho cho mặt hàng Bánh croissant"],
        "reviewer": "Nam"
    })

    # 20. q_0b8a4f2ec4e3 (biz_113)
    # revenue ngay nao cao nhat trong thang 10 nam 2025
    q = q_map["q_0b8a4f2ec4e3"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-10-01", "end": "2025-10-31", "inclusive": True, "resolution": "Tháng 10 năm 2025 = 2025-10-01 đến 2025-10-31"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_113/SoBanHang.xlsx", "sheet": "Sheet1", "columns": ["Ngày mua", "thanh_tien", "Ghi chú TT"], "role": "sales log"}
        ],
        "required_columns": ["Ngày mua", "thanh_tien", "Ghi chú TT"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày mua", "meaning": "date with peak revenue"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-10-04",
            "peak_revenue": 64471400
        },
        "computed_answer": "2025-10-04",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-10-04", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 21. q_79f9c340442f (biz_113)
    # ê tháng 7/2025 hàng nào chạy nhất
    q = q_map["q_79f9c340442f"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_selling_product_name",
        "time_range": {"start": "2025-07-01", "end": "2025-07-31", "inclusive": True, "resolution": "tháng 7/2025 = 2025-07-01 đến 2025-07-31"},
        "entities_filters": {"entity": "mặt hàng", "filters": ["order date in month", "exclude cancelled/returned orders", "exclude service fees"]},
        "answer_type": "string",
        "source_refs": [
            {"path": "train/data/biz_113/SoBanHang.xlsx", "sheet": "Sheet1", "columns": ["Mặt hàng", "SL bán", "Số lượng lẻ", "Ngày mua", "Ghi chú TT"], "role": "sales log"}
        ],
        "required_columns": ["Mặt hàng", "SL bán", "Số lượng lẻ", "Ngày mua", "Ghi chú TT"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate quantity in base unit and find argmax product"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Bỏ đơn huỷ, trả",
            "train/rulebook.md §3: Bán chạy = theo số lượng quy về đơn vị cơ bản, không theo số dòng hay số tiền"
        ],
        "unit_semantics": {"metric": "string", "source_field": "Mặt hàng", "meaning": "name of top selling item"},
        "calculation": {
            "operation": "ARGMAX_QUANTITY_BASE",
            "top_product": "Xi măng Hà Tiên PCB40 bao 50kg",
            "total_base_qty": 3480
        },
        "computed_answer": "Xi măng Hà Tiên PCB40 bao 50kg",
        "gold_comparison": {"reference_type": "string", "reference_answer": "Xi măng Hà Tiên PCB40 bao 50kg", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 22. q_57cd2bc2320b (biz_115)
    # Ngày nào trong tháng 1/2026 dthu cao nhất?
    q = q_map["q_57cd2bc2320b"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2026-01-01", "end": "2026-01-31", "inclusive": True, "resolution": "Tháng 1/2026 = 2026-01-01 đến 2026-01-31"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_115/So_chi_tiet_ban_hang.xlsx", "sheet": "01.2026", "columns": ["Ngày", "Trạng thái", "Thành tiền"], "role": "sales line log for Jan 2026"}
        ],
        "required_columns": ["Ngày", "Trạng thái", "Thành tiền"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày", "meaning": "peak revenue date"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2026-01-12",
            "peak_revenue": 79293600
        },
        "computed_answer": "2026-01-12",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2026-01-12", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 23. q_0ef3574c2b44 (biz_115)
    # So với tháng liền trước, doanh thu tháng 3 năm 2026 thay đổi bao nhiêu %?
    q = q_map["q_0ef3574c2b44"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "percentage_change_mom",
        "time_range": {"start": "2026-02-01", "end": "2026-03-31", "inclusive": True, "resolution": "Tháng 3/2026 so với tháng 2/2026"},
        "entities_filters": {"entity": "doanh thu tháng", "filters": ["exclude cancelled/returned orders"]},
        "answer_type": "percent",
        "source_refs": [
            {"path": "train/data/biz_115/So_chi_tiet_ban_hang.xlsx", "sheet": "02.2026", "columns": ["Ngày", "Trạng thái", "Thành tiền"], "role": "Feb 2026 sales sheet"},
            {"path": "train/data/biz_115/So_chi_tiet_ban_hang.xlsx", "sheet": "03.2026", "columns": ["Ngày", "Trạng thái", "Thành tiền"], "role": "Mar 2026 sales sheet"}
        ],
        "required_columns": ["Ngày", "Trạng thái", "Thành tiền"],
        "grain": {"source": "one row per line", "calculation_grain": "percentage change between two monthly revenue totals"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Phần trăm thay đổi, tăng trưởng = so với kỳ trước; làm tròn 2 chữ số thập phân",
            "train/rulebook.md §2: Tháng M/Y"
        ],
        "unit_semantics": {"metric": "percent change", "source_field": "Thành tiền", "meaning": "percentage growth over prior month"},
        "calculation": {
            "operation": "PERCENT_CHANGE",
            "expression": "(Rev(2026-03) - Rev(2026-02)) / Rev(2026-02) * 100",
            "rev_feb": 142100000,
            "rev_mar": 235900000,
            "raw_pct": 66.00985,
            "rounded": 66.01
        },
        "computed_answer": 66.01,
        "gold_comparison": {"reference_type": "percent", "reference_answer": 66.01, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 24. q_0496b83ca7c4 (biz_116)
    # Doanh thu ngày nào cao nhất trong tháng 7 năm 2026?
    q = q_map["q_0496b83ca7c4"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2026-07-01", "end": "2026-07-31", "inclusive": True, "resolution": "Tháng 7 năm 2026 = 2026-07-01 đến 2026-07-31"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_116/Bao_cao_ban_hang.xlsx", "sheet": "So_chi_tiet_ban_hang", "columns": ["Ngày", "Trạng thái", "Thành tiền"], "role": "consolidated sales line log"}
        ],
        "required_columns": ["Ngày", "Trạng thái", "Thành tiền"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày", "meaning": "peak revenue date"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2026-07-29",
            "peak_revenue": 109948800
        },
        "computed_answer": "2026-07-29",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2026-07-29", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 25. q_040c9dd7f4de (biz_116)
    # Tháng 9/2025 top 5 hàng bán chạy nhất là gì?
    q = q_map["q_040c9dd7f4de"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_k_selling_products",
        "time_range": {"start": "2025-09-01", "end": "2025-09-30", "inclusive": True, "resolution": "Tháng 9/2025 = 2025-09-01 đến 2025-09-30"},
        "entities_filters": {"entity": "mặt hàng", "filters": ["order date in month", "exclude cancelled/returned orders", "exclude service fees"]},
        "answer_type": "list",
        "source_refs": [
            {"path": "train/data/biz_116/Bao_cao_ban_hang.xlsx", "sheet": "So_chi_tiet_ban_hang", "columns": ["Tên hàng hóa", "Số lượng", "Ngày", "Trạng thái", "Đơn vị tính", "Số lượng quy đổi"], "role": "sales line log"},
            {"path": "train/data/biz_116/Bao_cao_ban_hang.xlsx", "sheet": "Danh sách hàng hóa", "columns": ["Tên hàng hóa", "Đơn vị tính"], "role": "goods catalog"}
        ],
        "required_columns": ["Tên hàng hóa", "Số lượng quy đổi", "Ngày", "Trạng thái"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate quantity in base unit and sort desc top 5"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Bỏ đơn huỷ, trả",
            "train/rulebook.md §3: Bán chạy = theo số lượng quy về đơn vị cơ bản"
        ],
        "unit_semantics": {"metric": "ordered list of product names", "source_field": "Tên hàng hóa", "meaning": "top 5 items by normalized base unit quantity"},
        "calculation": {
            "operation": "TOP_K_RANKING",
            "top_products": [
                "Xi măng Hà Tiên PCB40 bao 50kg",
                "Gạch ống 8x8x18 Tuynel",
                "Xi măng INSEE Power-S bao 50kg",
                "Băng keo điện Nano 20 yard",
                "Ống PVC Bình Minh D32 cây 4m"
            ]
        },
        "computed_answer": [
            "Xi măng Hà Tiên PCB40 bao 50kg",
            "Gạch ống 8x8x18 Tuynel",
            "Xi măng INSEE Power-S bao 50kg",
            "Băng keo điện Nano 20 yard",
            "Ống PVC Bình Minh D32 cây 4m"
        ],
        "gold_comparison": {
            "reference_type": "list",
            "reference_answer": [
                "Xi măng Hà Tiên PCB40 bao 50kg",
                "Gạch ống 8x8x18 Tuynel",
                "Xi măng INSEE Power-S bao 50kg",
                "Băng keo điện Nano 20 yard",
                "Ống PVC Bình Minh D32 cây 4m"
            ],
            "match": True
        },
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 26. q_0db8d6ef55e9 (biz_117)
    # thang 5/2025 ngay nao cua hang ban duoc nhiu tien nhat
    q = q_map["q_0db8d6ef55e9"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-05-01", "end": "2025-05-31", "inclusive": True, "resolution": "Tháng 5/2025 = 2025-05-01 đến 2025-05-31"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_117/SoBanHang.xlsx", "sheet": "Tháng 05-2025", "header_row": 2, "columns": ["Giờ", "Ngày lập", "Tiền", "Ghi chú TT"], "role": "May sales sheet"}
        ],
        "required_columns": ["Giờ", "Ngày lập", "Tiền", "Ghi chú TT"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán được nhiều tiền nhất = doanh thu"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Giờ", "meaning": "peak revenue date"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-05-11",
            "peak_revenue": 77634500
        },
        "computed_answer": "2025-05-11",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-05-11", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    return defs
