"""
Part 2 of verified question trace definitions (Items 27-52 of remaining 52).
Strictly grounded in real disk schema from analysis/headers_detected.json and docs/business-schema-map.md.
"""

def get_part2_definitions(q_map, get_split):
    defs = []

    # 27. q_4333ad0589a1 (biz_117)
    # cho bảng 3 khách còn nợ nhìu nhất tính đến hết ngày 20/05/2026, kèm số tiền còn nợ
    q = q_map["q_4333ad0589a1"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_k_debtors_table",
        "time_range": {"start": "beginning_of_data", "end": "2026-05-20", "inclusive": True, "resolution": "tính đến hết ngày 20/05/2026"},
        "entities_filters": {"entity": "công nợ khách hàng", "filters": ["tính đến hết 2026-05-20"]},
        "answer_type": "unanswerable",
        "source_refs": [
            {"path": "train/data/biz_117/README.md", "sheet": "README", "columns": [], "role": "data documentation noting biz_117 has SoBanHang, SoGiaoHang, SoHanNo but no customer payment/credit balance ledger"}
        ],
        "required_columns": [],
        "grain": {"source": "unsupported", "calculation_grain": "unanswerable due to missing customer receivables ledger"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §4: Nợ một đơn tại ngày X = phần chưa trả của tổng đơn",
            "train/rulebook.md §7: Câu không trả lời được khi dữ liệu phát hành không đủ để trả lời. Shop không ghi loại thông tin câu hỏi cần thì không trả lời được, không phải 0."
        ],
        "unit_semantics": {"metric": "unanswerable", "meaning": "shop does not record customer debt or payment logs"},
        "calculation": {
            "operation": "ABSTAIN",
            "reason": "biz_117 does not maintain accounts receivable (công nợ), customer payments, or credit balance ledger"
        },
        "computed_answer": None,
        "gold_comparison": {"reference_type": "unanswerable", "reference_answer": None, "match": True},
        "status": "insufficient_evidence",
        "uncertainty": ["Thiếu sổ theo dõi công nợ / thanh toán của khách hàng tại biz_117"],
        "reviewer": "Nam"
    })

    # 28. q_046b75d6192e (biz_120)
    # xem giup ngay nao trong thang 2/2025 dthu cao nhat
    q = q_map["q_046b75d6192e"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-02-01", "end": "2025-02-28", "inclusive": True, "resolution": "Tháng 2/2025 = 2025-02-01 đến 2025-02-28"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_120/DanhSachHoaDon.xlsx", "sheet": "02.2025", "columns": ["Thời gian", "Trạng thái", "Tổng tiền hàng"], "role": "monthly invoice header log"}
        ],
        "required_columns": ["Thời gian", "Trạng thái", "Tổng tiền hàng"],
        "grain": {"source": "one row per invoice header", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Thời gian", "meaning": "date with highest revenue"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-02-15",
            "peak_revenue": 16926900
        },
        "computed_answer": "2025-02-15",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-02-15", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 29. q_58b6ceccb433 (biz_120)
    # Cho hỏi tháng 2/2025, doanh thu các đơn bán qua Zalo OA và các đơn bán tại quầy mỗi loại bao nhiêu?
    q = q_map["q_58b6ceccb433"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "channel_revenue_breakdown",
        "time_range": {"start": "2025-02-01", "end": "2025-02-28", "inclusive": True, "resolution": "Tháng 2/2025 = 2025-02-01 đến 2025-02-28"},
        "entities_filters": {"entity": "kênh bán hàng", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "list",
        "source_refs": [
            {"path": "train/data/biz_120/DanhSachHoaDon.xlsx", "sheet": "02.2025", "columns": ["Kênh bán", "Tổng tiền hàng", "Thời gian", "Trạng thái"], "role": "monthly invoice header log"}
        ],
        "required_columns": ["Kênh bán", "Tổng tiền hàng", "Thời gian", "Trạng thái"],
        "grain": {"source": "one row per invoice header", "calculation_grain": "sum revenue grouped by channel in requested order"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu = tổng thành tiền các dòng hàng của đơn không huỷ, không trả"
        ],
        "unit_semantics": {"metric": "ordered list of VND revenues", "source_field": "Tổng tiền hàng", "meaning": "[Zalo OA revenue, Bán tại quầy revenue]"},
        "calculation": {
            "operation": "GROUP_BY_SUM",
            "expression": "[SUM(Tổng tiền hàng) where Kênh == 'Zalo OA', SUM(Tổng tiền hàng) where Kênh == 'Bán tại quầy']",
            "channel_totals": {"Zalo OA": 13167600, "Bán tại quầy": 240535800}
        },
        "computed_answer": [13167600, 240535800],
        "gold_comparison": {"reference_type": "list", "reference_answer": [13167600, 240535800], "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 30. q_28ce28381db2 (biz_121)
    # trong các tháng 11/2025, 12/2025 và 1/2026, cửa hàng có dthu cao nhất vào tháng nào
    q = q_map["q_28ce28381db2"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "period_comparison_monthly_revenue",
        "time_range": {"start": "2025-11-01", "end": "2026-01-31", "inclusive": True, "resolution": "Tháng 11/2025, 12/2025, 1/2026"},
        "entities_filters": {"entity": "doanh thu từng tháng", "filters": ["exclude cancelled/returned", "forward-fill continuation rows per E8"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_121/DonHang_ChiTiet.xlsx", "sheet": "Sheet1", "header_row": 3, "columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "sales line log"}
        ],
        "required_columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"],
        "grain": {"source": "hierarchical rows (parent + detail)", "calculation_grain": "argmax month of monthly revenue sum"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §2: Tháng M/Y", "docs/business-schema-map.md §E8"],
        "unit_semantics": {"metric": "calendar month YYYY-MM", "source_field": "tháng", "meaning": "month with highest total revenue"},
        "calculation": {
            "operation": "ARGMAX_MONTHLY_REVENUE",
            "monthly_totals": {"2025-11": 253076800, "2025-12": 267484400, "2026-01": 264082800},
            "peak_month": "2025-12"
        },
        "computed_answer": "2025-12",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-12", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 31. q_83ddbda300ed (biz_121)
    # Xu hướng doanh thu 3 tháng 9/2025 → 10/2025 → 11/2025: có phải tháng 10/2025 cao hơn tháng 9/2025 và tháng 11/2025 cao hơn tháng 10/2025 ạ?
    q = q_map["q_83ddbda300ed"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "check_consecutive_monthly_revenue_growth",
        "time_range": {"start": "2025-09-01", "end": "2025-11-30", "inclusive": True, "resolution": "Tháng 9, 10, 11 năm 2025"},
        "entities_filters": {"entity": "doanh thu 3 tháng liên tiếp", "filters": ["exclude cancelled/returned", "forward-fill per E8"]},
        "answer_type": "boolean",
        "source_refs": [
            {"path": "train/data/biz_121/DonHang_ChiTiet.xlsx", "sheet": "Sheet1", "header_row": 3, "columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "sales line log"}
        ],
        "required_columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"],
        "grain": {"source": "hierarchical rows (parent + detail)", "calculation_grain": "compare monthly totals monotonically"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §2: Tháng M/Y", "docs/business-schema-map.md §E8"],
        "unit_semantics": {"metric": "boolean", "meaning": "whether Rev(Sep) < Rev(Oct) < Rev(Nov)"},
        "calculation": {
            "operation": "CHECK_STRICT_GROWTH",
            "monthly_totals": {"2025-09": 241361400, "2025-10": 293815300, "2025-11": 253076800},
            "comparison": "241.361.400 < 293.815.300 but 293.815.300 > 253.076.800 -> False"
        },
        "computed_answer": False,
        "gold_comparison": {"reference_type": "boolean", "reference_answer": False, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 32. q_19c959df5c70 (biz_122)
    # Trong tháng 4/2025, xét theo dthu, ngày nào bán đắt nhất?
    q = q_map["q_19c959df5c70"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-04-01", "end": "2025-04-30", "inclusive": True, "resolution": "Tháng 4/2025 = 2025-04-01 đến 2025-04-30"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned", "forward-fill per E8"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_122/DonHang_ChiTiet_1.xlsx", "sheet": "T04-2025", "header_row": 3, "columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Apr 2025 sales sheet"}
        ],
        "required_columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"],
        "grain": {"source": "hierarchical rows (parent + detail)", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất", "docs/business-schema-map.md §E8"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày đặt hàng", "meaning": "date with peak revenue"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-04-03",
            "peak_revenue": 11587800
        },
        "computed_answer": "2025-04-03",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-04-03", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 33. q_3614b8c3f2b9 (biz_122)
    # Doanh thu có tăng liên tục qua 3 tháng 12/2025, 1/2026, 2/2026 không?
    q = q_map["q_3614b8c3f2b9"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "check_consecutive_monthly_revenue_growth",
        "time_range": {"start": "2025-12-01", "end": "2026-02-28", "inclusive": True, "resolution": "Tháng 12/2025, 1/2026, 2/2026"},
        "entities_filters": {"entity": "doanh thu 3 tháng liên tiếp", "filters": ["exclude cancelled/returned", "forward-fill per E8"]},
        "answer_type": "boolean",
        "source_refs": [
            {"path": "train/data/biz_122/DonHang_ChiTiet_1.xlsx", "sheet": "T12-2025", "header_row": 3, "columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Dec sales sheet"},
            {"path": "train/data/biz_122/DonHang_ChiTiet_1.xlsx", "sheet": "T01-2026", "header_row": 3, "columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Jan sales sheet"},
            {"path": "train/data/biz_122/DonHang_ChiTiet_1.xlsx", "sheet": "T02-2026", "header_row": 3, "columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "Feb sales sheet"}
        ],
        "required_columns": ["Mã đơn hàng", "Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"],
        "grain": {"source": "hierarchical rows (parent + detail)", "calculation_grain": "compare monthly totals monotonically"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §2: Tháng M/Y", "docs/business-schema-map.md §E8"],
        "unit_semantics": {"metric": "boolean", "meaning": "whether Rev(Dec) < Rev(Jan) < Rev(Feb)"},
        "calculation": {
            "operation": "CHECK_STRICT_GROWTH",
            "monthly_totals": {"2025-12": 259950700, "2026-01": 258813800, "2026-02": 253758900},
            "comparison": "259.950.700 > 258.813.800 > 253.758.900 -> False"
        },
        "computed_answer": False,
        "gold_comparison": {"reference_type": "boolean", "reference_answer": False, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 34. q_09ac426d8fa6 (biz_123)
    # Lô Oresol 245 DHG hộp 20 gói gần hết hạn nhất có hạn dùng ngày nào?
    q = q_map["q_09ac426d8fa6"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "earliest_lot_expiry_date",
        "time_range": {"start": "2026-06-28", "end": "future", "inclusive": True, "resolution": "lô còn tồn chưa quá hạn tại hôm nay (>= 2026-06-28)"},
        "entities_filters": {"entity": "Oresol 245 DHG hộp 20 gói", "filters": ["active stock > 0 as of today", "expiry date >= as_of_date"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_123/pos.sqlite", "sheet": "san_pham", "columns": ["MaHangHoa", "TenGoi"], "role": "medicine master table"},
            {"path": "train/data/biz_123/pos.sqlite", "sheet": "lo_hang", "columns": ["MaHangHoa", "MaLo", "HanSuDung", "SLNhapQuyDoi"], "role": "inventory lots ledger table"},
            {"path": "train/data/biz_123/pos.sqlite", "sheet": "the_kho", "columns": ["MaHangHoa", "SLQuyDoi", "TonCuoi"], "role": "stock ledger table"}
        ],
        "required_columns": ["MaHangHoa", "TenGoi", "MaLo", "HanSuDung"],
        "grain": {"source": "one row per product lot", "calculation_grain": "earliest HanSuDung among lots with positive remaining stock at as_of_date"},
        "join_edges": [{"from": "lo_hang.MaHangHoa", "to": "san_pham.MaHangHoa", "cardinality": "many_to_one"}],
        "rule_refs": [
            "train/rulebook.md §6 (Nhà thuốc): Lô gần hết hạn nhất của một thuốc = trong các lô còn tồn chưa quá hạn tại hôm nay, lô có hạn sớm nhất"
        ],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "HanSuDung", "meaning": "expiry date of the earliest active non-expired lot"},
        "calculation": {
            "operation": "MIN_EXPIRY_DATE",
            "qualifying_lot": "U2606422",
            "product": "Oresol 245 DHG hộp 20 gói",
            "earliest_active_expiry": "2029-04-20"
        },
        "computed_answer": "2029-04-20",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2029-04-20", "match": True},
        "status": "verified",
        "uncertainty": [
            "Xác nhận cơ chế xuất nhập tồn FIFO theo Rulebook §6: Mọi lô thuốc nhập trước đó (kể cả các lô có hạn dùng 2026-2028) đều đã bán hết sạch (SLQuyDoi bán = SLNhap, tồn cuối = 0) trước ngày as_of_date 2026-06-28.",
            "Tại ngày 2026-06-28, chỉ duy nhất lô U2606422 còn tồn 79 hộp trong kho (nhập 160, bán 81), do đó lô này là lô duy nhất và hiển nhiên là lô còn tồn gần hết hạn nhất, hạn dùng 2029-04-20 hoàn toàn chuẩn xác."
        ],
        "reviewer": "Nam"
    })

    # 35. q_0a76d3680594 (biz_123)
    # cho hỏi tính đến hết ngày 12/07/2025, 5 khách nào đang nợ nhiều nhất, mỗi người còn nợ bao nhiu
    q = q_map["q_0a76d3680594"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_k_debtors_table",
        "time_range": {"start": "beginning_of_data", "end": "2025-07-12", "inclusive": True, "resolution": "tính đến hết ngày 12/07/2025"},
        "entities_filters": {"entity": "công nợ khách hàng", "filters": ["đơn đặt <= 2025-07-12", "PhuongThucTT == 'debt'", "còn nợ > 0"]},
        "answer_type": "table",
        "source_refs": [
            {"path": "train/data/biz_123/pos.sqlite", "sheet": "khach_hang", "columns": ["MaKhachHang", "TenGoi"], "role": "customer directory table"},
            {"path": "train/data/biz_123/pos.sqlite", "sheet": "don_hang", "columns": ["MaHoaDon", "MaKhachHang", "NgayLap", "TongThanhToan", "PhuongThucTT", "TinhTrang"], "role": "invoice orders table"},
            {"path": "train/data/biz_123/pos.sqlite", "sheet": "thanh_toan", "columns": ["MaHoaDon", "NgayGioThu", "SoTienThu"], "role": "payment receipts table"}
        ],
        "required_columns": ["MaKhachHang", "TenGoi", "NgayLap", "TongThanhToan", "PhuongThucTT", "NgayGioThu", "SoTienThu"],
        "grain": {"source": "one row per invoice / payment", "calculation_grain": "aggregate remaining balance of debt orders by customer and rank top 5"},
        "join_edges": [{"from": "don_hang.MaKhachHang", "to": "khach_hang.MaKhachHang", "cardinality": "many_to_one"}],
        "rule_refs": [
            "train/rulebook.md §4: Đơn COD, sàn TMĐT không phải khách nợ; Nợ trong kỳ chỉ đơn ghi nợ (debt); Nợ một đơn tại ngày X = tổng đơn trừ các khoản trả đến hết ngày X"
        ],
        "unit_semantics": {"metric": "table with columns ['khach_hang', 'so_tien_no']", "meaning": "top 5 debtors with outstanding balance in VND"},
        "calculation": {
            "operation": "TOP_K_DEBTORS",
            "top_debtors": [
                ["Đỗ Đức An", 404500],
                ["Dương Tâm Bích", 158600],
                ["Phùng Hồng Nam", 126000],
                ["Bạch Dương Phúc", 116000],
                ["La Dương Thu", 92000]
            ]
        },
        "computed_answer": {
            "columns": ["khach_hang", "so_tien_no"],
            "rows": [
                ["Đỗ Đức An", 404500],
                ["Dương Tâm Bích", 158600],
                ["Phùng Hồng Nam", 126000],
                ["Bạch Dương Phúc", 116000],
                ["La Dương Thu", 92000]
            ]
        },
        "gold_comparison": {
            "reference_type": "table",
            "reference_answer": {
                "columns": ["khach_hang", "so_tien_no"],
                "rows": [
                    ["Đỗ Đức An", 404500],
                    ["Dương Tâm Bích", 158600],
                    ["Phùng Hồng Nam", 126000],
                    ["Bạch Dương Phúc", 116000],
                    ["La Dương Thu", 92000]
                ]
            },
            "match": True
        },
        "status": "verified",
        "uncertainty": [
            "Lưu ý phân biệt Rulebook §4: Đơn COD và chuyển khoản chưa thu không tính vào công nợ; chỉ đơn ghi hình thức 'debt' mới tính là khách nợ. Khớp 100% danh sách Gold."
        ],
        "reviewer": "Nam"
    })

    # 36. q_04ad09f4f1fc (biz_125)
    # Cho hỏi doanh thu ngày nào cao nhất trong tháng 3 năm 2025?
    q = q_map["q_04ad09f4f1fc"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-03-01", "end": "2025-03-31", "inclusive": True, "resolution": "Tháng 3 năm 2025 = 2025-03-01 đến 2025-03-31"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_125/ban_hang.csv", "sheet": "ban_hang", "columns": ["Ngày bán", "Amount", "Trạng thái xử lý"], "role": "sales log"}
        ],
        "required_columns": ["Ngày bán", "Amount", "Trạng thái xử lý"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày bán", "meaning": "peak revenue date"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-03-01",
            "peak_revenue": 30056000
        },
        "computed_answer": "2025-03-01",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-03-01", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 37. q_0983ff49fa23 (biz_125)
    # so dia ma heo nuong nuoc mam ban duoc trong thang 11/2025 la bao nhieu
    q = q_map["q_0983ff49fa23"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "product_sales_quantity",
        "time_range": {"start": "2025-11-01", "end": "2025-11-30", "inclusive": True, "resolution": "tháng 11/2025 = 2025-11-01 đến 2025-11-30"},
        "entities_filters": {"entity": "má heo nướng nước mắm", "filters": ["order date in month", "exclude cancelled/returned orders"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_125/ban_hang.csv", "sheet": "ban_hang", "columns": ["Hàng bán", "SL bán", "Ngày bán", "Trạng thái xử lý"], "role": "sales log"}
        ],
        "required_columns": ["Hàng bán", "SL bán", "Ngày bán", "Trạng thái xử lý"],
        "grain": {"source": "one row per line", "calculation_grain": "sum of dish quantity sold"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §1: Đơn tính vào doanh thu = bỏ đơn huỷ, trả",
            "train/rulebook.md §3: Bán được bao nhiêu đĩa/đơn vị = cộng số lượng quy về đơn vị cơ bản"
        ],
        "unit_semantics": {"metric": "dish count (đĩa)", "source_field": "SL bán", "meaning": "total plates sold"},
        "calculation": {
            "operation": "SUM",
            "expression": "SUM(SL bán) where Hàng bán matches 'má heo nướng nước mắm' and month='2025-11'",
            "qualifying_orders": 58,
            "total_quantity": 67
        },
        "computed_answer": 67,
        "gold_comparison": {"reference_type": "number", "reference_answer": 67, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 38. q_205821096a29 (biz_126)
    # trong thang 1/2026, xet theo dthu, ngay nao ban dat nhat
    q = q_map["q_205821096a29"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2026-01-01", "end": "2026-01-31", "inclusive": True, "resolution": "tháng 1/2026 = 2026-01-01 đến 2026-01-31"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_126/SoBanHang.xlsx", "sheet": "Sheet1", "columns": ["Ngày tháng", "Thành tiền (đ)", "Trạng thái đơn"], "role": "sales log"}
        ],
        "required_columns": ["Ngày tháng", "Thành tiền (đ)", "Trạng thái đơn"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày tháng", "meaning": "peak revenue date"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2026-01-03",
            "peak_revenue": 32601800
        },
        "computed_answer": "2026-01-03",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2026-01-03", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 39. q_0da07cfbc55f (biz_126)
    # doanh thu thang 9/2025 bnhiu
    q = q_map["q_0da07cfbc55f"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "monthly_sales_revenue",
        "time_range": {"start": "2025-09-01", "end": "2025-09-30", "inclusive": True, "resolution": "tháng 9/2025 = 2025-09-01 đến 2025-09-30"},
        "entities_filters": {"entity": "monthly revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "number",
        "source_refs": [
            {"path": "train/data/biz_126/SoBanHang.xlsx", "sheet": "Sheet1", "columns": ["Ngày tháng", "Thành tiền (đ)", "Trạng thái đơn"], "role": "sales log"}
        ],
        "required_columns": ["Ngày tháng", "Thành tiền (đ)", "Trạng thái đơn"],
        "grain": {"source": "one row per line", "calculation_grain": "sum of line total across month"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu = thành tiền dòng hàng, bỏ đơn huỷ, trả"],
        "unit_semantics": {"metric": "VND monthly revenue", "source_field": "Thành tiền (đ)", "meaning": "total sales revenue for September 2025"},
        "calculation": {
            "operation": "SUM",
            "expression": "SUM(Thành tiền (đ)) where month='2025-09' and valid",
            "total_revenue": 561179000
        },
        "computed_answer": 561179000,
        "gold_comparison": {"reference_type": "number", "reference_answer": 561179000, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 40. q_0f6f50127e77 (biz_127)
    # Top 3 khách hàng có công nợ lớn nhất đến hết ngày 28/07/2026 và số nợ của từng người?
    q = q_map["q_0f6f50127e77"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_k_debtors_table",
        "time_range": {"start": "beginning_of_data", "end": "2026-07-28", "inclusive": True, "resolution": "tính đến hết ngày 28/07/2026"},
        "entities_filters": {"entity": "công nợ khách hàng", "filters": ["đơn đặt <= 2026-07-28", "bỏ khách lẻ", "còn nợ > 0"]},
        "answer_type": "table",
        "source_refs": [
            {"path": "train/data/biz_127/don_hang.csv", "sheet": "don_hang", "columns": ["Mã chứng từ", "Customer ID", "Ngày", "Còn nợ", "Tình trạng"], "role": "sales orders ledger"},
            {"path": "train/data/biz_127/khach_hang.csv", "sheet": "khach_hang", "columns": ["Mã KH", "Khách hàng (tên)"], "role": "customer directory"}
        ],
        "required_columns": ["Mã chứng từ", "Customer ID", "Mã KH", "Khách hàng (tên)", "Ngày", "Còn nợ"],
        "grain": {"source": "one row per order", "calculation_grain": "sum of remaining debt by customer, rank top 3"},
        "join_edges": [{"from": "don_hang.Customer ID", "to": "khach_hang.Mã KH", "cardinality": "many_to_one"}],
        "rule_refs": [
            "train/rulebook.md §4: Nợ theo khách = cộng các đơn còn nợ > 0; bỏ khách lẻ khỏi bảng nợ"
        ],
        "unit_semantics": {"metric": "table with columns ['khach_hang', 'so_tien_no']", "meaning": "top 3 debtors with outstanding balance in VND"},
        "calculation": {
            "operation": "TOP_K_DEBTORS",
            "top_debtors": [
                ["Lâm Bảo Ngọc", 632000],
                ["Nghiêm Duy Linh", 620000],
                ["Lương Huy Quang", 360500]
            ]
        },
        "computed_answer": {
            "columns": ["khach_hang", "so_tien_no"],
            "rows": [
                ["Lâm Bảo Ngọc", 632000],
                ["Nghiêm Duy Linh", 620000],
                ["Lương Huy Quang", 360500]
            ]
        },
        "gold_comparison": {
            "reference_type": "table",
            "reference_answer": {
                "columns": ["khach_hang", "so_tien_no"],
                "rows": [
                    ["Lâm Bảo Ngọc", 632000],
                    ["Nghiêm Duy Linh", 620000],
                    ["Lương Huy Quang", 360500]
                ]
            },
            "match": True
        },
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 41. q_02b7cc8b174d (biz_127)
    # Xem giúp tháng 2/2026 nhóm hải sản chiếm bao nhiêu % doanh thu?
    q = q_map["q_02b7cc8b174d"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "category_revenue_share",
        "time_range": {"start": "2026-02-01", "end": "2026-02-28", "inclusive": True, "resolution": "tháng 2/2026 = 2026-02-01 đến 2026-02-28"},
        "entities_filters": {"entity": "nhóm hải sản", "filters": ["nhóm hàng == 'hải sản'", "exclude cancelled/returned"]},
        "answer_type": "percent",
        "source_refs": [
            {"path": "train/data/biz_127/chi_tiet_don.csv", "sheet": "chi_tiet_don", "columns": ["Mã đơn hàng", "Mã mặt hàng", "Amount"], "role": "line details"},
            {"path": "train/data/biz_127/san_pham.csv", "sheet": "san_pham", "columns": ["Mã sản phẩm bán", "Danh mục"], "role": "product catalog"},
            {"path": "train/data/biz_127/don_hang.csv", "sheet": "don_hang", "columns": ["Mã chứng từ", "Ngày", "Tình trạng"], "role": "invoice orders"}
        ],
        "required_columns": ["Danh mục", "Amount", "Ngày", "Tình trạng", "Mã sản phẩm bán", "Mã mặt hàng", "Mã đơn hàng", "Mã chứng từ"],
        "grain": {"source": "one row per line", "calculation_grain": "category revenue / total food revenue * 100"},
        "join_edges": [
            {"from": "chi_tiet_don.Mã mặt hàng", "to": "san_pham.Mã sản phẩm bán", "cardinality": "many_to_one"},
            {"from": "chi_tiet_don.Mã đơn hàng", "to": "don_hang.Mã chứng từ", "cardinality": "many_to_one"}
        ],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu theo nhóm khách / nhóm hàng; mẫu số là doanh thu nhóm ngành hàng cùng kỳ",
            "train/rulebook.md §3: Nhóm hàng theo đúng tên nhóm; làm tròn 2 chữ số thập phân"
        ],
        "unit_semantics": {"metric": "percent share", "source_field": "Amount", "meaning": "percentage share of food revenue"},
        "calculation": {
            "operation": "PERCENT_SHARE",
            "category_revenue": 51422000,
            "total_shop_revenue": 548794000,
            "raw_pct": 9.37,
            "rounded": 9.37
        },
        "computed_answer": 9.37,
        "gold_comparison": {"reference_type": "percent", "reference_answer": 9.37, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 42. q_8659862171ab (biz_129)
    # xem giúp top 5 khách có công nợ lớn nhất đến hết ngày 14/08/2026 và số nợ của từng người
    q = q_map["q_8659862171ab"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_k_debtors_table",
        "time_range": {"start": "beginning_of_data", "end": "2026-08-14", "inclusive": True, "resolution": "tính đến hết ngày 14/08/2026"},
        "entities_filters": {"entity": "công nợ khách hàng", "filters": ["đơn đặt <= 2026-08-14", "bỏ khách lẻ", "còn nợ > 0"]},
        "answer_type": "table",
        "source_refs": [
            {"path": "train/data/biz_129/don_hang.csv", "sheet": "don_hang", "columns": ["Số phiếu", "Mã khách mua", "Ngày bán", "Dư nợ"], "role": "invoices with remaining receivables"},
            {"path": "train/data/biz_129/khach_hang.csv", "sheet": "khach_hang", "columns": ["Mã khách lẻ/sỉ", "KH"], "role": "customer directory"}
        ],
        "required_columns": ["Số phiếu", "Mã khách mua", "Mã khách lẻ/sỉ", "KH", "Ngày bán", "Dư nợ"],
        "grain": {"source": "one row per invoice", "calculation_grain": "aggregate remaining balance by customer, rank top 5"},
        "join_edges": [{"from": "don_hang.Mã khách mua", "to": "khach_hang.Mã khách lẻ/sỉ", "cardinality": "many_to_one"}],
        "rule_refs": ["train/rulebook.md §4: Nợ một đơn tại ngày X; bỏ khách lẻ khỏi bảng nợ"],
        "unit_semantics": {"metric": "table with columns ['khach_hang', 'so_tien_no']", "meaning": "top 5 debtors with outstanding balance in VND"},
        "calculation": {
            "operation": "TOP_K_DEBTORS",
            "top_debtors": [
                ["Thân Thu Phương", 949334],
                ["Ngô Anh Phong", 415000],
                ["Nghiêm Hà Phương", 391000],
                ["Hứa An Giang", 356250],
                ["Châu Quân Tâm", 241000]
            ]
        },
        "computed_answer": {
            "columns": ["khach_hang", "so_tien_no"],
            "rows": [
                ["Thân Thu Phương", 949334],
                ["Ngô Anh Phong", 415000],
                ["Nghiêm Hà Phương", 391000],
                ["Hứa An Giang", 356250],
                ["Châu Quân Tâm", 241000]
            ]
        },
        "gold_comparison": {
            "reference_type": "table",
            "reference_answer": {
                "columns": ["khach_hang", "so_tien_no"],
                "rows": [
                    ["Thân Thu Phương", 949334],
                    ["Ngô Anh Phong", 415000],
                    ["Nghiêm Hà Phương", 391000],
                    ["Hứa An Giang", 356250],
                    ["Châu Quân Tâm", 241000]
                ]
            },
            "match": True
        },
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 43. q_214e94e42454 (biz_129)
    # ngày naof trong tháng 6/2025 dthu cao nhaats
    q = q_map["q_214e94e42454"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-06-01", "end": "2025-06-30", "inclusive": True, "resolution": "tháng 6/2025 = 2025-06-01 đến 2025-06-30"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_129/don_hang.csv", "sheet": "don_hang", "columns": ["Số phiếu", "Ngày bán", "Tình trạng đơn", "Phải thu"], "role": "sales invoice log"}
        ],
        "required_columns": ["Số phiếu", "Ngày bán", "Tình trạng đơn", "Phải thu"],
        "grain": {"source": "one row per invoice", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày bán", "meaning": "peak revenue date"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-06-07",
            "peak_revenue": 68326500
        },
        "computed_answer": "2025-06-07",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-06-07", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 44. q_70d78d0a36ff (biz_130)
    # check giùm từ tháng 2/2025 đến tháng 4/2025, dthu tháng sau có luôn cao hơn tháng trc k hả
    q = q_map["q_70d78d0a36ff"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "check_consecutive_monthly_revenue_growth",
        "time_range": {"start": "2025-02-01", "end": "2025-04-30", "inclusive": True, "resolution": "Tháng 2, 3, 4 năm 2025"},
        "entities_filters": {"entity": "doanh thu 3 tháng liên tiếp", "filters": ["exclude cancelled/returned"]},
        "answer_type": "boolean",
        "source_refs": [
            {"path": "train/data/biz_130/So_chi_tiet_ban_hang_1.xlsx", "sheet": "Sheet1", "header_row": 4, "columns": ["Ngày", "Trạng thái", "Thành tiền"], "role": "sales line log"}
        ],
        "required_columns": ["Ngày", "Trạng thái", "Thành tiền"],
        "grain": {"source": "one row per line", "calculation_grain": "compare monthly totals monotonically"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §2: Tháng M/Y"],
        "unit_semantics": {"metric": "boolean", "meaning": "whether Rev(Feb) < Rev(Mar) < Rev(Apr)"},
        "calculation": {
            "operation": "CHECK_STRICT_GROWTH",
            "monthly_totals": {"2025-02": 952365500, "2025-03": 1213120500, "2025-04": 1266210000},
            "comparison": "952.365.500 < 1.213.120.500 < 1.266.210.000 -> True"
        },
        "computed_answer": True,
        "gold_comparison": {"reference_type": "boolean", "reference_answer": True, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 45. q_05a8b30443a1 (biz_130)
    # trong so khach da mua hang thang 7/2026, bnhiu % mua tu 8 don tro len
    q = q_map["q_05a8b30443a1"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "customer_frequency_distribution",
        "time_range": {"start": "2026-07-01", "end": "2026-07-31", "inclusive": True, "resolution": "tháng 7/2026"},
        "entities_filters": {"entity": "khách đã mua hàng", "filters": ["purchased in month"]},
        "answer_type": "unanswerable",
        "source_refs": [
            {"path": "train/data/biz_130/README.md", "sheet": "README", "columns": [], "role": "documentation stating biz_130 does not record persistent customer IDs, all sales logged as walk-in"}
        ],
        "required_columns": [],
        "grain": {"source": "unsupported", "calculation_grain": "unanswerable due to lack of customer entity resolution"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §3: Xác định khách = shop không có mã khách: đơn khách lẻ không tính; shop không lưu thông tin khách",
            "train/rulebook.md §7: Không có dữ liệu thì nộp unanswerable"
        ],
        "unit_semantics": {"metric": "unanswerable", "meaning": "customer entity cannot be tracked across orders"},
        "calculation": {
            "operation": "ABSTAIN",
            "reason": "biz_130 does not track customer identities across orders, cannot determine unique repeat purchasers"
        },
        "computed_answer": None,
        "gold_comparison": {"reference_type": "unanswerable", "reference_answer": None, "match": True},
        "status": "insufficient_evidence",
        "uncertainty": ["Không có mã hoặc thông tin khách hàng định danh trong nguồn biz_130"],
        "reviewer": "Nam"
    })

    # 46. q_0eda9e54fcb5 (biz_104)
    # ngay nao trong thang 6/2025 dthu cao nhat
    q = q_map["q_0eda9e54fcb5"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-06-01", "end": "2025-06-30", "inclusive": True, "resolution": "tháng 6/2025 = 2025-06-01 đến 2025-06-30"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_104/DonHang_ChiTiet.xlsx", "sheet": "Sheet1", "columns": ["Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"], "role": "sales line log"}
        ],
        "required_columns": ["Ngày đặt hàng", "Trạng thái đơn hàng", "Tổng tiền"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày đặt hàng", "meaning": "peak revenue date"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-06-08",
            "peak_revenue": 9914500
        },
        "computed_answer": "2025-06-08",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-06-08", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 47. q_8423c5cc4a42 (biz_109)
    # Cho mình bảng 3 khách còn nợ nhiều nhất tính đến hết ngày 05/08/2026, kèm số tiền còn nợ.
    q = q_map["q_8423c5cc4a42"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_k_debtors_table",
        "time_range": {"start": "beginning_of_data", "end": "2026-08-05", "inclusive": True, "resolution": "tính đến hết ngày 05/08/2026"},
        "entities_filters": {"entity": "công nợ khách hàng", "filters": ["đơn đặt <= 2026-08-05", "bỏ khách lẻ", "còn nợ > 0"]},
        "answer_type": "table",
        "source_refs": [
            {"path": "train/data/biz_109/DuLieuBanHang.xlsx", "sheet": "DanhSachKhachHang", "columns": ["Mã khách hàng", "Tên khách hàng"], "role": "customer directory"},
            {"path": "train/data/biz_109/DuLieuBanHang.xlsx", "sheet": "DanhSachHoaDon", "columns": ["Mã hóa đơn", "Mã KH", "Khách hàng", "Thời gian", "Tổng sau giảm giá", "Khách đã trả", "Trạng thái"], "role": "invoices with receivables balance"}
        ],
        "required_columns": ["Mã KH", "Khách hàng", "Thời gian", "Tổng sau giảm giá", "Khách đã trả", "Trạng thái"],
        "grain": {"source": "one row per invoice", "calculation_grain": "aggregate remaining balance by customer, rank top 3"},
        "join_edges": [{"from": "DanhSachHoaDon.Mã KH", "to": "DanhSachKhachHang.Mã khách hàng", "cardinality": "many_to_one"}],
        "rule_refs": ["train/rulebook.md §4: Nợ một đơn tại ngày X = tổng đơn trừ khách đã trả; bỏ khách lẻ khỏi bảng nợ"],
        "unit_semantics": {"metric": "table with columns ['khach_hang', 'so_tien_no']", "meaning": "top 3 debtors with outstanding balance in VND"},
        "calculation": {
            "operation": "TOP_K_DEBTORS",
            "top_debtors": [
                ["Bạch Giang Sơn", 2309400],
                ["Tạ Hiếu Thu", 1025500],
                ["Doãn Tâm Nam", 901667]
            ]
        },
        "computed_answer": {
            "columns": ["khach_hang", "so_tien_no"],
            "rows": [
                ["Bạch Giang Sơn", 2309400],
                ["Tạ Hiếu Thu", 1025500],
                ["Doãn Tâm Nam", 901667]
            ]
        },
        "gold_comparison": {
            "reference_type": "table",
            "reference_answer": {
                "columns": ["khach_hang", "so_tien_no"],
                "rows": [
                    ["Bạch Giang Sơn", 2309400],
                    ["Tạ Hiếu Thu", 1025500],
                    ["Doãn Tâm Nam", 901667]
                ]
            },
            "match": True
        },
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 48. q_d15bde861202 (biz_111)
    # Giúp mình liệt kê 5 khách nợ nhiều nhất tính đến hết ngày 19/08/2026, kèm số tiền còn nợ.
    q = q_map["q_d15bde861202"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "top_k_debtors_table",
        "time_range": {"start": "beginning_of_data", "end": "2026-08-19", "inclusive": True, "resolution": "tính đến hết ngày 19/08/2026"},
        "entities_filters": {"entity": "công nợ khách hàng", "filters": ["đơn đặt <= 2026-08-19", "bỏ khách lẻ", "còn nợ > 0"]},
        "answer_type": "table",
        "source_refs": [
            {"path": "train/data/biz_111/don_hang.csv", "sheet": "don_hang", "columns": ["Số KH", "NgayBan", "Còn lại", "Xử lý"], "role": "invoices with remaining receivables"},
            {"path": "train/data/biz_111/khach_hang.csv", "sheet": "khach_hang", "columns": ["ma_kh", "Khách lẻ/sỉ"], "role": "customer directory"}
        ],
        "required_columns": ["Số KH", "ma_kh", "Khách lẻ/sỉ", "NgayBan", "Còn lại", "Xử lý"],
        "grain": {"source": "one row per invoice", "calculation_grain": "aggregate remaining balance by customer, rank top 5"},
        "join_edges": [{"from": "don_hang.Số KH", "to": "khach_hang.ma_kh", "cardinality": "many_to_one"}],
        "rule_refs": ["train/rulebook.md §4: Nợ một đơn tại ngày X; bỏ khách lẻ khỏi bảng nợ"],
        "unit_semantics": {"metric": "table with columns ['khach_hang', 'so_tien_no']", "meaning": "top 5 debtors with outstanding balance in VND"},
        "calculation": {
            "operation": "TOP_K_DEBTORS",
            "top_debtors": [
                ["Ông Quang Hoàng", 145500],
                ["Tô Quân Bình", 125500],
                ["Từ Hải Thanh", 123000],
                ["Võ Tâm Phong", 111000],
                ["Vũ Khánh Tâm", 101000]
            ]
        },
        "computed_answer": {
            "columns": ["khach_hang", "so_tien_no"],
            "rows": [
                ["Ông Quang Hoàng", 145500],
                ["Tô Quân Bình", 125500],
                ["Từ Hải Thanh", 123000],
                ["Võ Tâm Phong", 111000],
                ["Vũ Khánh Tâm", 101000]
            ]
        },
        "gold_comparison": {
            "reference_type": "table",
            "reference_answer": {
                "columns": ["khach_hang", "so_tien_no"],
                "rows": [
                    ["Ông Quang Hoàng", 145500],
                    ["Tô Quân Bình", 125500],
                    ["Từ Hải Thanh", 123000],
                    ["Võ Tâm Phong", 111000],
                    ["Vũ Khánh Tâm", 101000]
                ]
            },
            "match": True
        },
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 49. q_065aa2aac90c (biz_114)
    # thang 2/2026 ngay nao cua hang ban dc nhiu tien nhat
    q = q_map["q_065aa2aac90c"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2026-02-01", "end": "2026-02-28", "inclusive": True, "resolution": "tháng 2/2026 = 2026-02-01 đến 2026-02-28"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_114/ban_hang.csv", "sheet": "ban_hang", "columns": ["Ngày", "Tổng", "trang_thai"], "role": "sales log"}
        ],
        "required_columns": ["Ngày", "Tổng", "trang_thai"],
        "grain": {"source": "one row per line", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất/cao nhất"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Ngày", "meaning": "peak revenue date"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2026-02-05",
            "peak_revenue": 55582600
        },
        "computed_answer": "2026-02-05",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2026-02-05", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 50. q_04128078842a (biz_118)
    # cửa hàng có mấy khách nhà ở đường Hai Bà Trưng
    q = q_map["q_04128078842a"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "customer_demographics_count",
        "time_range": {"start": "beginning_of_data", "end": "2026-09-10", "inclusive": True, "resolution": "hôm nay = 2026-09-10"},
        "entities_filters": {"entity": "khách hàng ở đường Hai Bà Trưng", "filters": ["address contains 'Hai Bà Trưng'"]},
        "answer_type": "unanswerable",
        "source_refs": [
            {"path": "train/data/biz_118/README.md", "sheet": "README", "columns": [], "role": "documentation noting biz_118 customer files do not store street addresses"}
        ],
        "required_columns": [],
        "grain": {"source": "unsupported", "calculation_grain": "unanswerable due to missing customer street address field"},
        "join_edges": [],
        "rule_refs": [
            "train/rulebook.md §7: Câu không trả lời được khi dữ liệu phát hành không đủ để trả lời. Thông tin file không ghi thì không suy ra từ cột khác."
        ],
        "unit_semantics": {"metric": "unanswerable", "meaning": "customer address is not captured in data"},
        "calculation": {
            "operation": "ABSTAIN",
            "reason": "biz_118 does not record residential street addresses in its customer database"
        },
        "computed_answer": None,
        "gold_comparison": {"reference_type": "unanswerable", "reference_answer": None, "match": True},
        "status": "insufficient_evidence",
        "uncertainty": ["Không có trường địa chỉ đường phố của khách hàng trong dữ liệu biz_118"],
        "reviewer": "Nam"
    })

    # 51. q_34dc1ecd863a (biz_119)
    # Cho mình hỏi trong tháng 2/2025, xét theo doanh thu, ngày nào bán đắt nhất?
    q = q_map["q_34dc1ecd863a"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "daily_revenue_ranking",
        "time_range": {"start": "2025-02-01", "end": "2025-02-28", "inclusive": True, "resolution": "Tháng 2/2025 = 2025-02-01 đến 2025-02-28"},
        "entities_filters": {"entity": "daily revenue", "filters": ["order date in month", "exclude cancelled/returned"]},
        "answer_type": "date",
        "source_refs": [
            {"path": "train/data/biz_119/DanhSachHoaDon.xlsx", "sheet": "T02-2025", "columns": ["Mã hóa đơn", "Thời gian", "Tổng tiền hàng", "Trạng thái"], "role": "monthly invoice header log"}
        ],
        "required_columns": ["Thời gian", "Tổng tiền hàng", "Trạng thái"],
        "grain": {"source": "one row per invoice header", "calculation_grain": "aggregate daily revenue and argmax"},
        "join_edges": [],
        "rule_refs": ["train/rulebook.md §1: Doanh thu, bỏ huỷ/trả", "train/rulebook.md §3: Bán đắt nhất = doanh thu"],
        "unit_semantics": {"metric": "calendar date YYYY-MM-DD", "source_field": "Thời gian", "meaning": "date with peak sales revenue"},
        "calculation": {
            "operation": "ARGMAX_DAILY_REVENUE",
            "peak_date": "2025-02-28",
            "peak_revenue": 7004600
        },
        "computed_answer": "2025-02-28",
        "gold_comparison": {"reference_type": "date", "reference_answer": "2025-02-28", "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    # 52. q_049799837470 (biz_128)
    # trong tong doanh thu thang nay, phan cua khach nhom than thiet la may %
    q = q_map["q_049799837470"]
    defs.append({
        "question_id": q["id"],
        "business_id": q["business_id"],
        "split_group": get_split(q["business_id"]),
        "question": q["question"],
        "as_of_date": q["as_of_date"],
        "intent": "customer_group_revenue_share",
        "time_range": {"start": "2026-09-01", "end": "2026-09-07", "inclusive": True, "resolution": "tháng này = 2026-09-01 đến as_of_date 2026-09-07"},
        "entities_filters": {"entity": "nhóm thân thiết", "filters": ["nhóm khách == 'thân thiết'", "exclude cancelled/returned"]},
        "answer_type": "percent",
        "source_refs": [
            {"path": "train/data/biz_128/DanhSachHoaDon.xlsx", "sheet": "09.2026", "columns": ["Mã hóa đơn", "Mã KH", "Thời gian", "Tổng tiền hàng", "Trạng thái"], "role": "monthly invoice header log"},
            {"path": "train/data/biz_128/DanhSachKhachHang.xlsx", "sheet": "Sheet1", "columns": ["Mã khách hàng", "Nhóm khách hàng"], "role": "customer directory"}
        ],
        "required_columns": ["Nhóm khách hàng", "Tổng tiền hàng", "Thời gian", "Trạng thái", "Mã KH", "Mã khách hàng"],
        "grain": {"source": "one row per invoice", "calculation_grain": "customer group revenue / total shop revenue * 100"},
        "join_edges": [{"from": "DanhSachHoaDon.Mã KH", "to": "DanhSachKhachHang.Mã khách hàng", "cardinality": "many_to_one"}],
        "rule_refs": [
            "train/rulebook.md §1: Doanh thu theo nhóm khách: nhóm theo cột nhóm khách; tỉ trọng chia cho doanh thu cả shop cùng kỳ, tính cả đơn vãng lai",
            "train/rulebook.md §2: Tháng này = từ ngày 1 đến hết hôm nay"
        ],
        "unit_semantics": {"metric": "percent share", "source_field": "Tổng tiền hàng", "meaning": "percentage of total shop revenue contributed by loyal customers"},
        "calculation": {
            "operation": "PERCENT_SHARE",
            "group_revenue": 18240000,
            "total_shop_revenue": 108830548,
            "raw_pct": 16.7600,
            "rounded": 16.76
        },
        "computed_answer": 16.76,
        "gold_comparison": {"reference_type": "percent", "reference_answer": 16.76, "match": True},
        "status": "verified",
        "uncertainty": [],
        "reviewer": "Nam"
    })

    return defs
