"""Incremental evidence review of an unchanged catalog; never changes train/.

Reuses the initial row counts/profiles. Reads rows only to audit date evidence,
review remaining grains and measure approved relation types for source handoff.
No answers are calculated and no labels are consulted.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import csv
from pathlib import Path
import re

SPEC = importlib.util.spec_from_file_location("catalog_base", Path(__file__).with_name("build_data_catalog.py"))
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
ROOT = base.ROOT


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_pairs,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError(f"Nonfinite {v}")))


def dump_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def csv_serial_evidence(values, order_ids, payment_days, cutoff):
    """Confirm an epoch using explicit date brackets AND an independent source.

    No scalar numeric parser is enabled. Every accepted row must be bracketed
    by already parseable dates and lie inside README coverage. A winning epoch
    also requires exact same-day anchors and matching independently dated payments.
    """
    explicit = [base.parse_day(str(v)) for v in values]
    previous, following = [], [None] * len(values)
    anchor = None
    for day in explicit:
        previous.append(anchor)
        anchor = day or anchor
    anchor = None
    for i in reversed(range(len(values))):
        following[i] = anchor
        anchor = explicit[i] or anchor
    formats = Counter("excel_serial_candidate" if re.fullmatch(r"\d{5}", str(v)) else
                      "d_thg_m_yyyy" if " thg " in str(v) else
                      "day_first" if "/" in str(v) and d else
                      "iso" if d else "unresolved" for v, d in zip(values, explicit))
    candidates, reviewed = {}, {}
    for label, epoch in (("excel_1900", datetime(1899, 12, 30)), ("excel_1904", datetime(1904, 1, 1))):
        counts = Counter()
        resolved = {}
        for i, value in enumerate(values):
            if not re.fullmatch(r"\d{5}", str(value)):
                continue
            day = (epoch + timedelta(days=int(value))).date().isoformat()
            counts["serial_rows"] += 1
            bracketed = previous[i] is not None and following[i] is not None and previous[i] <= day <= following[i]
            in_coverage = day <= cutoff and min(d for d in (previous[i], following[i]) if d) <= day if (previous[i] or following[i]) else False
            if bracketed and in_coverage:
                counts["bracket_range_matches"] += 1
                resolved[i] = day
            else:
                counts["bracket_or_coverage_conflicts"] += 1
            if previous[i] == following[i] == day:
                counts["exact_same_day_brackets"] += 1
            payments = payment_days.get(order_ids[i], set())
            if day in payments:
                counts["independent_payment_same_day"] += 1
            elif payments:
                counts["payments_other_days"] += 1
            else:
                counts["no_parsed_payment"] += 1
        candidates[label] = dict(counts)
        reviewed[label] = resolved
    winners = [label for label, c in candidates.items() if c.get("serial_rows", 0) and
               c.get("bracket_range_matches") == c["serial_rows"] and c.get("exact_same_day_brackets", 0) > 0 and
               c.get("independent_payment_same_day", 0) > 0 and not c.get("bracket_or_coverage_conflicts")]
    winner = winners[0] if len(winners) == 1 else None
    return {"formats": dict(formats), "epoch_comparison": candidates, "confirmed_epoch": winner,
            "resolved": len(reviewed[winner]) if winner else 0,
            "unresolved": formats["excel_serial_candidate"] - (len(reviewed[winner]) if winner else 0),
            "evidence_limits": "Payment on another date is not an error: payments can occur after purchase. Chronological brackets corroborate this export, not a universal row-order guarantee."}, reviewed[winner] if winner else {}


def kind_for(table):
    raw = table["sheet_or_table"] if table["file"] in ("pos.sqlite", "DuLieuBanHang.xlsx", "DuLieuXuat.xlsx", "Bao_cao_ban_hang.xlsx") else base.display_filename(table["file"])
    name = re.sub(r"\.xlsx$|\.csv$|_\d+$|_20\d\d$", "", base.fold(raw))
    compact = name.replace("_", "").replace(" ", "")
    if "chitietdonlo" in compact or "hoadonchitietlo" in compact or "donhanglo" in compact or "bantheolo" in compact:
        return "lot_allocations"
    if name == "lo_hang" or "danhsachlohang" in compact or compact == "banhanglohang":
        return "lots"
    if "chitietnhap" in compact or "donnhaphangchitiet" in compact or "sonhaphang" in compact or "sotaynhaphang" in compact:
        return "purchase_lines"
    if "danhsachnhaphang" in compact or compact in ("phieunhap", "donnhaphang"):
        return "purchase_orders"
    if "danhsachhoadonchitiet" in compact or "donhangchitiet" in compact or "sochitietbanhang" in compact or "chitiethoadon" in compact or compact == "chitietdon":
        return "sales_lines"
    if "sobanhang" in compact or compact == "banhang":
        return "sales_lines"
    if compact in ("donhang", "danhsachhoadon", "banhanghoadon"):
        return "orders"
    if "tonkho" in compact:
        return "stock_snapshot"
    if "quydoi" in compact or "danhsachdonvitinh" in compact or compact in ("danhmuc", "donvisp"):
        return "conversions"
    if "lichsugia" in compact or compact == "banggia":
        return "price_history"
    if compact in ("danhsachsanpham", "sanpham", "danhsachhanghoa", "banhanghanghoa"):
        return "products"
    if compact in ("danhsachkhachhang", "khachhang", "banhangkhachhang"):
        return "customers"
    if compact in ("thongtinthuoc", "danhsachthuoc", "banhangthuoc"):
        return "drug_attributes"
    if compact in ("soquy", "thanhtoan", "banhangphieuthu"):
        return "payments"
    if compact in ("sogiaohang", "bangkephieugiaohang"):
        return "delivery_lines"
    if compact in ("sohanno", "chitietcongnotheohan"):
        return "debt_snapshot"
    return {"thekho": "stock_movements", "sotaychiphi": "expenses", "chinhanh": "branches",
            "nhanvien": "staff", "nhacungcap": "suppliers", "trahang": "returns"}.get(compact, "unclassified")


ALIASES = {
    "order": ("mahoadon", "ma hoa don", "ma don hang", "ma don", "ma chung tu", "so ct", "order id", "ma giao dich", "ma bill", "so hoa don", "so hd", "so phieu", "ma phieu"),
    "product": ("mahanghoa", "ma hang", "ma hang hoa", "ma mat hang", "ma san pham", "ma san pham ban", "ma sp", "ma_sp", "id sp", "ma hh", "ma mon", "sku"),
    "customer": ("makhachhang", "ma khach hang", "ma kh", "ma kh mua", "ma khach mua", "customer id", "so kh", "ma_kh"),
    "receipt": ("maphieunhap", "ma nhap hang", "ma phieu nhap", "so phieu"),
    "line": ("sothutu", "stt", "no.", "so thu tu", "thu tu", "tt dong"),
    "lot": ("malo", "ma lo", "lo"),
    "unit": ("donvitinh", "don vi tinh", "don vi quy doi", "don vi", "dvt", "donvi", "unit", "dv lon", "dv nhap", "dvt nhap", "dvt nhap hang", "don vi (tinh)", "d.vi"),
    "product_name": ("ten hang", "ten san pham", "ten hang hoa", "ten sp", "product", "hang", "hang hoa", "ten_hang", "tenhang", "ten mat hang", "ten mon", "san pham", "chi tiet hang", "mon"),
    "event": ("luot giao", "dot giao", "lan giao"),
    "effective_date": ("ngayapdung", "ngay ap dung"),
    "payment": ("maphieuthu", "ma phieu thu", "phieu thu", "ma phieu", "ma gd"),
    "movement": ("magiaodichkho",), "branch": ("machinhanh",), "staff": ("manhanvien",), "supplier": ("manhacungcap",), "return": ("maphieutra",),
}


def review_keys(table):
    cols = [c["name"] for c in table["columns"]]
    folded = [base.fold(c) for c in cols]
    kind = kind_for(table)
    roles = base.semantic_roles(cols, {c["name"]: c.get("readme_description") or "" for c in table["columns"]})
    allowed = {
        "order": {"orders", "sales_lines", "payments", "lot_allocations", "delivery_lines", "debt_snapshot", "returns"},
        "receipt": {"purchase_orders", "purchase_lines", "lots"},
        "line": {"sales_lines", "purchase_lines", "lot_allocations"},
        "event": {"delivery_lines"}, "payment": {"payments"}, "effective_date": {"price_history"},
        "movement": {"stock_movements"}, "branch": {"branches"}, "staff": {"staff"}, "supplier": {"suppliers"}, "return": {"returns"},
    }
    for role, names in ALIASES.items():
        if role in roles or role in allowed and kind not in allowed[role]:
            continue
        matches = [i for i, name in enumerate(folded) if name in names]
        if role == "order" and kind == "payments":
            matches = [i for i in matches if folded[i] != "ma phieu"]
        if len(matches) == 1:
            roles[role] = matches[0]
    # README descriptions take priority over ambiguous aliases such as Số phiếu.
    for i, c in enumerate(table["columns"]):
        desc = base.fold(c.get("readme_description") or "")
        if desc.startswith("ten hang") or desc == "ten" and kind == "products":
            roles.setdefault("product_name", i)
        if desc.startswith(("don vi lon", "don vi nhap", "don vi tinh")):
            roles.setdefault("unit", i)
        if desc.startswith("dot giao"):
            roles.setdefault("event", i)
    store = [roles["store"]] if "store" in roles else []
    keys = {role: store + [i] for role, i in roles.items() if role != "store"}
    for composite, parts in (("order_line", ("order", "line")), ("receipt_line", ("receipt", "line")),
                             ("order_lot", ("order", "lot")),
                             ("product_lot", ("product", "lot")), ("order_line_lot", ("order", "line", "lot")),
                             ("delivery_line", ("order", "event", "product_name")), ("delivery_event", ("order", "event")),
                             ("product_unit", ("product", "unit")), ("name_unit", ("product_name", "unit")),
                             ("price_point", ("product", "effective_date")), ("name_price_point", ("product_name", "effective_date"))):
        if all(p in roles for p in parts):
            keys[composite] = store + [roles[p] for p in parts]
    return kind, keys


def raw_rows(path, tables):
    by_sheet = {t["sheet_or_table"]: t for t in tables}
    for sheet, rows, _ in base.source_tables(path):
        if sheet not in by_sheet:
            continue
        table = by_sheet[sheet]
        columns = [c["name"] for c in table["columns"]]
        for physical, raw in rows:
            if table["header_row_1based"] and physical <= table["header_row_1based"]:
                continue
            if not any(v is not None and str(v).strip() for v in raw) or list(raw) == columns:
                continue
            yield table, physical, list(raw[:len(columns)]) + [None] * max(0, len(columns) - len(raw))


def collect_keys(train, business):
    records = {}
    files = defaultdict(list)
    for table in business["tables"]:
        kind, keys = review_keys(table)
        table["logical_role"] = kind
        files[table["file"]].append(table)
        records[table["source_ref"]] = {"indices": keys, "raw": {k: Counter() for k in keys},
                                         "dedup": {k: Counter() for k in keys}, "nulls": Counter(), "rows": 0, "seen": set(),
                                         "summary_labels": 0, "summary_without_order": 0}
    import hashlib
    for filename, tables in files.items():
        for table, physical, row in raw_rows(train / "data" / business["business_id"] / filename, tables):
            rec = records[table["source_ref"]]
            rec["rows"] += 1
            if table["logical_role"] in ("sales_lines", "orders"):
                product = rec["indices"].get("product_name")
                candidates = [row[product[-1]]] if product else row
                labels = [v for v in candidates if isinstance(v, str) and v.lstrip()[:1].lower() in ("t", "c") and summary_label(v)]
                order = rec["indices"].get("order")
                if table["logical_role"] == "orders" and order and str(row[order[-1]] or "").strip():
                    labels = []
                if labels:
                    rec["summary_labels"] += 1
                    if not order or not str(row[order[-1]] or "").strip():
                        rec["summary_without_order"] += 1
            h = hashlib.sha256(json.dumps(row, ensure_ascii=False, default=str).encode()).digest()
            new = h not in rec["seen"]
            rec["seen"].add(h)
            for role, indices in rec["indices"].items():
                key = tuple("" if row[i] is None else str(row[i]).strip() for i in indices)
                if role in ("price_point", "name_price_point", "effective_date"):
                    normalized = list(key)
                    for offset, index in enumerate(indices):
                        if base.fold(table["columns"][index]["name"]) in ALIASES["effective_date"]:
                            day = base.parse_day(str(row[index]))
                            if not day and path_suffix(filename) == ".xlsx" and isinstance(row[index], (int, float)):
                                day = (base.workbook_epoch(train / "data" / business["business_id"] / filename) + timedelta(days=row[index])).date().isoformat()
                            normalized[offset] = day or ""
                    key = tuple(normalized)
                if all(key):
                    rec["raw"][role][key] += 1
                    if new:
                        rec["dedup"][role][key] += 1
                else:
                    rec["nulls"][role] += 1
    for table in business["tables"]:
        rec = records[table["source_ref"]]
        if rec["rows"] != table["data_rows"]:
            raise ValueError(f"Cached row count mismatch: {table['source_ref']}")
        rec.pop("seen")
        table["reviewed_keys"] = {role: {"columns": [table["columns"][i]["name"] for i in indices],
                                           "null_rows": rec["nulls"][role], "distinct": len(rec["raw"][role]),
                                           "raw_duplicate_excess": sum(rec["raw"][role].values()) - len(rec["raw"][role]),
                                           "duplicate_excess_after_exact_row_projection": sum(rec["dedup"][role].values()) - len(rec["dedup"][role]),
                                           "note": "Exact-row projection is diagnostic only; rulebook permits dedup only within an order. No source rows removed."}
                                    for role, indices in rec["indices"].items()}
        if rec["summary_labels"]:
            table["row_kind_review"] = {"summary_label_rows": rec["summary_labels"], "summary_rows_without_order_id": rec["summary_without_order"],
                                         "detector": "TỔNG NGÀY / TỔNG THÁNG / TỔNG CỘNG / CỘNG NGÀY in item field (or row without item column)",
                                         "status": "needs_review", "policy": "Raw count includes these rows. Do not fill order IDs into totals or sum these with item rows; confirm row filter before execution."}
    return records


def path_suffix(name):
    return Path(name).suffix.lower()


def name_key(value):
    """Rulebook spelling lookup; preserve all letters/numbers/punctuation positions."""
    return re.sub(r"\s+", " ", base.fold(value)).strip()


def summary_label(value):
    return bool(re.match(r"^(?:tong ngay|tong thang|tong cong|cong ngay)(?:\s|$)", name_key(value)))


def review_grain(table, readme_ref, text):
    role, keys = table["logical_role"], table["reviewed_keys"]
    def unique(key):
        return key in keys and keys[key]["null_rows"] == 0 and keys[key]["raw_duplicate_excess"] == 0
    def unique_after_order_dedup(key):
        return key in keys and keys[key]["null_rows"] == 0 and keys[key]["duplicate_excess_after_exact_row_projection"] == 0
    proof = {"readme_ref": readme_ref, "role": role, "key_counts": keys,
             "structure": [c["name"] for c in table["columns"]], "rule_ref": "train/rulebook.md §8"}
    description, verified, selected = table["grain"], table["grain_status"] == "verified", None
    if role in ("products", "customers", "drug_attributes", "branches", "staff", "suppliers"):
        selected = {"products": "product", "customers": "customer", "drug_attributes": "product", "branches": "branch", "staff": "staff", "suppliers": "supplier"}[role]
        description = {"products": "một bản ghi danh mục sản phẩm", "customers": "một bản ghi danh mục khách theo mã", "drug_attributes": "thuộc tính thuốc của một mã hàng", "branches": "một chi nhánh", "staff": "một nhân viên", "suppliers": "một nhà cung cấp"}[role]
        verified = unique(selected)
    elif role == "orders":
        selected, description = "order", "một đơn hàng; ngày và tổng tiền ở cấp đơn"
        verified = unique("order") or "mỗi dòng một đơn hàng" in text
    elif role == "sales_lines":
        selected, description = "order_line", "một dòng hàng của đơn; dòng trùng xuất file và ô trống nhóm phải xử lý theo rulebook §8"
        physical_item = "product" in keys or "product_name" in keys
        verified = ("mỗi dòng một" in text and physical_item) or unique_after_order_dedup("order_line") or (physical_item and "order" in keys and any(base.fold(c.get("readme_description") or "").startswith("so luong") for c in table["columns"]))
        if not verified and table["grain_status"] == "verified":
            verified, description = True, table["grain"]
    elif role == "purchase_orders":
        selected, description, verified = "receipt", "một phiếu nhập; tổng giá trị là cấp phiếu", unique("receipt")
    elif role == "purchase_lines":
        selected, description = "receipt_line", "một dòng hàng nhập; không cộng lặp tổng tiền phiếu"
        verified = unique("receipt_line") or unique("lot") and "mỗi dòng nhập là một lô" in text
        if not verified:
            verified = "receipt" in keys and "product_name" in keys and any("tien nhap cua ca dong" in base.fold(c.get("readme_description") or "") for c in table["columns"])
    elif role == "conversions":
        selected = "product_unit" if "product_unit" in keys else "name_unit"
        description, verified = "một hệ số quy đổi theo sản phẩm và đơn vị bán/đơn vị lớn", unique(selected)
    elif role == "stock_snapshot":
        selected = "product" if "product" in keys else "product_name"
        description = "snapshot tồn một sản phẩm vào cuối ngày dữ liệu trong README; không phải lịch sử tồn"
        verified = unique(selected) and ("tồn cuối ngày cuối" in text or "tồn cuối ngày cuối có dữ liệu" in text)
    elif role == "price_history":
        selected = "price_point" if "price_point" in keys else "name_price_point"
        description = "một mốc giá của sản phẩm; hiệu lực đến trước lần đổi sau, cần temporal join"
        verified = unique(selected) and "đến trước lần đổi" in text
    elif role == "lots":
        selected, description = "lot", "một lô nhập; mã lô không trùng trong business"
        verified = unique("lot") and "số lô không trùng" in text
    elif role == "lot_allocations":
        if "order_line_lot" in keys:
            selected, description = "order_line_lot", "phân bổ một dòng bán cho một lô; một dòng bán có thể lấy nhiều lô"
            verified = unique(selected) and "Một dòng bán có thể lấy từ nhiều lô" in text
        else:
            selected, description = "order_lot", "phân bổ đơn–lô (không có khóa dòng hàng); nối chi tiết bán chỉ bằng mã đơn sẽ fan-out"
            verified = unique(selected) and any("so luong ban lay tu lo" in base.fold(c.get("readme_description") or "") for c in table["columns"])
    elif role == "delivery_lines":
        selected, description = "delivery_line", "một mặt hàng trong một đợt giao của đơn; đếm đợt bằng DISTINCT (đơn, đợt), không đếm dòng hàng"
        verified = unique("delivery_line") and "delivery_event" in keys and ("đợt giao" in text or "1–3 đợt" in text)
    elif role == "debt_snapshot":
        selected, description, verified = "order", "một bản ghi hạn/công nợ của đơn; không phải lịch sử thanh toán", unique("order")
    elif role == "payments":
        selected, description = "payment", "một lần thu tiền cho đơn; nhiều lần thu không phải nhiều đơn"
        verified = unique("payment") and "mỗi lần khách trả tiền" in text
    elif role == "stock_movements":
        selected, description, verified = "movement", "một biến động kho có số dư sau biến động", unique("movement") and "tồn sau lần" in text
    elif role == "expenses":
        description, verified = "một khoản ghi sổ chi phí; không loại dòng giống nhau khi không có mã đơn", "Sổ chi phí" in text
    elif role == "returns":
        selected, description, verified = "return", "một phiếu trả hàng tham chiếu đơn", unique("return")
    proof["selected_key"] = selected
    proof["conclusion"] = "verified" if verified else "needs_review"
    if not verified:
        proof["blocker"] = "Thiếu khóa phù hợp hoặc khóa không duy nhất/null, hoặc README chưa xác nhận ý nghĩa; không tự nâng trạng thái."
    table.update(grain=description, grain_status="verified" if verified else "needs_review", grain_review=proof,
                 grain_evidence=f"{readme_ref}; cấu trúc cột và reviewed_keys; rulebook §8")
    table["status"] = "verified" if verified and table["header_status"] == "verified" and not table["overflow_rows"] else "needs_review"


# Only these semantic source-role pairs can be promoted; shared keys alone do not suffice.
RELATIONS = {
    ("sales_lines", "orders"): ("order",),
    ("sales_lines", "products"): ("product", "product_name"),
    ("sales_lines", "conversions"): ("product_unit", "name_unit"),
    ("orders", "customers"): ("customer",),
    ("payments", "orders"): ("order",),
    ("purchase_lines", "purchase_orders"): ("receipt",),
    ("purchase_lines", "products"): ("product", "product_name"),
    ("purchase_lines", "conversions"): ("product_unit", "name_unit"),
    ("lot_allocations", "sales_lines"): ("order_line",),
    ("lot_allocations", "lots"): ("lot",),
    ("lots", "products"): ("product",),
    ("stock_movements", "products"): ("product",),
    ("stock_snapshot", "products"): ("product", "product_name"),
    ("products", "drug_attributes"): ("product",),
    ("price_history", "products"): ("product", "product_name"),
}


def edge_measure(left, right, role, records, readme_ref):
    a, b = records[left["source_ref"]], records[right["source_ref"]]
    ca, cb = a["raw"][role], b["raw"][role]
    common = ca.keys() & cb.keys()
    matched_a, matched_b = sum(ca[k] for k in common), sum(cb[k] for k in common)
    inner = sum(ca[k] * cb[k] for k in common)
    dedup_b = b["dedup"][role]
    right_unique = max(cb.values(), default=0) <= 1
    right_unique_projected = max(dedup_b.values(), default=0) <= 1
    conversion = right["logical_role"] == "conversions"
    missing = sum(ca.values()) - matched_a
    if not common:
        status = "needs_review"
    elif right_unique and not b["nulls"][role]:
        status = "verified" if not missing or conversion else "verified_with_unmatched"
    elif right_unique_projected and right["logical_role"] == "sales_lines":
        status = "verified_requires_order_line_dedup"
    else:
        status = "needs_review"
    return {"id": left["source_ref"] + " -> " + right["source_ref"] + " [" + role + "]",
            "left": left["source_ref"], "right": right["source_ref"], "key_role": role,
            "left_columns": left["reviewed_keys"][role]["columns"], "right_columns": right["reviewed_keys"][role]["columns"],
            "readme_ref": readme_ref, "semantic_relation": left["logical_role"] + " -> " + right["logical_role"],
            "status": status, "left_rows": left["data_rows"], "right_rows": right["data_rows"],
            "left_null_rows": a["nulls"][role], "right_null_rows": b["nulls"][role],
            "left_matched_rows": matched_a, "right_matched_rows": matched_b,
            "left_unmatched_non_null_rows": missing, "right_unmatched_non_null_rows": sum(cb.values()) - matched_b,
            "inner_join_rows": inner, "left_join_rows": inner + left["data_rows"] - matched_a,
            "cardinality": ("many" if max(ca.values(), default=0) > 1 else "one") + "-to-" + ("many" if not right_unique else "one"),
            "fanout_on_matched_left": inner / matched_a if matched_a else None,
            "right_unique_after_exact_order_line_projection": right_unique_projected,
            "unmatched_interpretation": "Bảng quy đổi chỉ liệt kê đơn vị lớn; không match chưa phải lỗi, cần kiểm chứng đơn vị cơ bản (rulebook §10)." if conversion else "Giữ null keys/unmatched riêng; không loại mất giao dịch bằng inner join mặc định.",
            "double_counting_policy": "Không SUM tổng đơn sau nối dòng hàng/thu tiền; aggregate payment theo đơn trước; dedup dòng xuất trùng trong cùng đơn theo §8. Lookup tên phải unique; bảng giá cần điều kiện hiệu lực."}


def relation_review(business, records):
    edges = []
    for left in business["tables"]:
        for right in business["tables"]:
            roles = RELATIONS.get((left["logical_role"], right["logical_role"]), ())
            role = next((r for r in roles if r in records[left["source_ref"]]["raw"] and r in records[right["source_ref"]]["raw"]), None)
            if role:
                edges.append(edge_measure(left, right, role, records, business["readme"]))
    business["validated_join_edges"] = edges
    business["validated_join_unions"] = union_edges(edges, business["tables"], records, business["business_id"])
    partition_groups = defaultdict(list)
    for table in business["tables"]:
        primary = table.get("grain_review", {}).get("selected_key")
        if not primary:
            primary = {"orders": "order", "sales_lines": "order_line"}.get(table["logical_role"])
        if primary and primary in records[table["source_ref"]]["raw"]:
            partition_groups[(table["logical_role"], primary)].append(table["source_ref"])
    business["cross_partition_key_review"] = []
    for (kind, role), refs in partition_groups.items():
        if len(refs) < 2:
            continue
        total = Counter()
        for ref in refs:
            total.update(records[ref]["raw"][role])
        business["cross_partition_key_review"].append({"logical_role": kind, "key_role": role, "source_refs": refs,
            "sum_member_distinct": sum(len(records[r]["raw"][role]) for r in refs), "union_distinct": len(total),
            "cross_partition_key_overlap": sum(len(records[r]["raw"][role]) for r in refs) - len(total),
            "note": "Overlap counts keys, not duplicate full rows; never automatically discard source partitions."})
    for edge in business["joins"]:
        matches = [e for e in edges if {e["left"], e["right"]} == {edge["left"], edge["right"]} and e["key_role"] == edge["role"]]
        edge["semantic_review"] = matches[0]["status"] if matches else "not_approved_shared_key_only"
        edge["review_note"] = "Xem validated_join_edges; không dùng chung khóa để suy ra quan hệ nghiệp vụ."
    return edges


def union_edges(edges, tables, records, business_id):
    """Measure logical partitions together; a month is not a missing order."""
    by_ref = {t["source_ref"]: t for t in tables}
    groups = defaultdict(list)
    for edge in edges:
        groups[(by_ref[edge["left"]]["logical_role"], by_ref[edge["right"]]["logical_role"], edge["key_role"])].append(edge)
    result = []
    for (left_role, right_role, role), members in groups.items():
        left_refs, right_refs = sorted({e["left"] for e in members}), sorted({e["right"] for e in members})
        left, right, right_projected = Counter(), Counter(), Counter()
        for ref in left_refs:
            left.update(records[ref]["raw"][role])
        for ref in right_refs:
            right.update(records[ref]["raw"][role])
            right_projected.update(records[ref]["dedup"][role])
        common = left.keys() & right.keys()
        matched_a, matched_b = sum(left[k] for k in common), sum(right[k] for k in common)
        inner = sum(left[k] * right[k] for k in common)
        a_rows = sum(by_ref[r]["data_rows"] for r in left_refs)
        b_rows = sum(by_ref[r]["data_rows"] for r in right_refs)
        a_null = sum(records[r]["nulls"][role] for r in left_refs)
        b_null = sum(records[r]["nulls"][role] for r in right_refs)
        unique = max(right.values(), default=0) <= 1
        projected_unique = max(right_projected.values(), default=0) <= 1
        unmatched = sum(left.values()) - matched_a
        if not common:
            status = "needs_review"
        elif unique and not b_null:
            status = "verified" if not unmatched or right_role == "conversions" else "verified_with_unmatched"
        elif projected_unique and right_role == "sales_lines":
            status = "verified_requires_order_line_dedup"
        else:
            status = "needs_review"
        entry = {"id": f"{business_id}:{left_role}->{right_role}[{role}]", "key_role": role,
                       "semantic_relation": left_role + " -> " + right_role,
                       "left_sources": left_refs, "right_sources": right_refs,
                       "left_columns": {r: by_ref[r]["reviewed_keys"][role]["columns"] for r in left_refs},
                       "right_columns": {r: by_ref[r]["reviewed_keys"][role]["columns"] for r in right_refs},
                       "left_rows": a_rows, "right_rows": b_rows, "left_null_rows": a_null, "right_null_rows": b_null,
                       "left_matched_rows": matched_a, "right_matched_rows": matched_b,
                       "left_unmatched_non_null_rows": unmatched, "right_unmatched_non_null_rows": sum(right.values()) - matched_b,
                       "inner_join_rows": inner, "left_join_rows": inner + a_rows - matched_a,
                       "cardinality": ("many" if max(left.values(), default=0) > 1 else "one") + "-to-" + ("one" if unique else "many"),
                       "fanout_on_matched_left": inner / matched_a if matched_a else None,
                       "status": status, "right_unique_after_exact_order_line_projection": projected_unique,
                       "readme_ref": members[0]["readme_ref"], "double_counting_policy": members[0]["double_counting_policy"],
                       "unmatched_interpretation": members[0]["unmatched_interpretation"],
                       "partition_policy": "Union same-role partitions first; check key uniqueness across all members, not just per sheet."}
        if role == "product_name":
            normalized_right = Counter()
            for key, n in right.items():
                normalized_right[key[:-1] + (name_key(key[-1]),)] += n
            collisions = sum(v > 1 for v in normalized_right.values())
            resolved = sum(n for k, n in left.items() if k not in right and normalized_right.get(k[:-1] + (name_key(k[-1]),)) == 1) if not collisions else 0
            entry["name_normalization_review"] = {"policy": "NFD remove diacritics + lower + collapse whitespace; preserve digits/punctuation; in-memory lookup only, rulebook §8",
                                                  "right_normalized_key_collisions": collisions,
                                                  "raw_unmatched_rows": unmatched, "additional_matches": resolved,
                                                  "remaining_unmatched_rows": unmatched - resolved,
                                                  "status": "verified_unique_lookup" if not collisions else "needs_review"}
        result.append(entry)
    return result


def resolve_csv_dates(catalog, train):
    reports = []
    for business in catalog["businesses"]:
        orders = [t for t in business["tables"] if t["format"] == "csv" and kind_for(t) == "orders"]
        payment_tables = [t for t in business["tables"] if kind_for(t) == "payments"]
        for table in orders:
            for col in table["columns"]:
                if not col.get("date_profile", {}).get("invalid"):
                    continue
                cols = [c["name"] for c in table["columns"]]
                _, order_keys = review_keys(table)
                if "order" not in order_keys:
                    continue
                id_index = order_keys["order"][-1]
                date_index = cols.index(col["name"])
                rows = [row for _, _, row in raw_rows(train / "data" / business["business_id"] / table["file"], [table])]
                payment_days = defaultdict(set)
                for payments in payment_tables:
                    _, pkeys = review_keys(payments)
                    date_indices = [i for i, c in enumerate(payments["columns"]) if "date_profile" in c]
                    if "order" not in pkeys or not date_indices:
                        continue
                    for _, _, row in raw_rows(train / "data" / business["business_id"] / payments["file"], [payments]):
                        day = base.parse_day(str(row[date_indices[0]]))
                        if day:
                            payment_days[str(row[pkeys["order"][-1]])].add(day)
                match = re.search(r"Dữ liệu có đến hết (\d{2}/\d{2}/\d{4})", business["readme_rules"])
                if not match:
                    continue
                report, resolved = csv_serial_evidence([row[date_index] for row in rows], [str(row[id_index]) for row in rows], payment_days, base.parse_day(match[1]))
                report.update(source_ref=table["source_ref"], column=col["name"], readme_ref=business["readme"],
                              independent_sources=[t["source_ref"] for t in payment_tables], source_sha256=catalog["source_fingerprints"][f"data/{business['business_id']}/{table['file']}"],
                              accepted_policy="Numeric strings remain rejected by scalar parse_day; this file/column is resolved only after context + independent-source audit.")
                dp = col["date_profile"]
                dp["invalid"] -= len(resolved)
                dp["parsed"] += len(resolved)
                dp["serial_context_verified"] = len(resolved)
                if resolved:
                    days = list(resolved.values()) + [d for d in (dp["min"], dp["max"]) if d]
                    dp["min"], dp["max"] = min(days), max(days)
                dp["status"] = "verified" if not dp["invalid"] else "needs_review"
                dp["parse_rule"] += "; CSV numeric serial only after unique-epoch contextual audit, recorded in date_reviews"
                reports.append(report)
    return reports


def question_sources(question, business):
    """Source contract only; no question answers, gold checks, or trace execution."""
    text = base.fold(question["question"])
    tables = business["tables"]
    roles = {t["logical_role"] for t in tables}
    required = {"sales_lines"}
    missing = []
    operation = "sales / revenue / quantity; rulebook §1, §3, §8"
    if "con no" in text or "cong no" in text or "no nhieu" in text or "khach no" in text:
        required = {"orders", "payments", "customers"}
        operation = "Receivables as-of: aggregate payments per order before joining customers; rulebook §4"
    elif "nhap" in text and ("gia" in text or "phieu" in text):
        required = {"purchase_lines", "purchase_orders", "products", "conversions"} if "binh quan" in text else {"purchase_orders"}
        operation = "Purchase header totals once per receipt / weighted unit price; rulebook §5"
    elif "dot" in text and "giao" in text:
        required = {"delivery_lines"}
        operation = "COUNT DISTINCT order + delivery event; never count item rows; rulebook §6"
    elif "lo " in text and "han" in text:
        required = {"lots", "lot_allocations", "sales_lines", "orders", "products"}
        operation = "Lot balance/expiry as-of; allocations must join by order + line, not order alone; rulebook §6"
    elif "trong kho" in text or "con bao nhieu hop" in text:
        required = {"stock_snapshot", "products", "conversions"}
        operation = "Snapshot date must cover as_of_date; no historical inventory inferred; rulebook §5, §7"
    elif "khen" in text:
        required = set()
        missing.append("Không có nguồn nhận xét/khen nhân viên trong catalog; cần Người 2 xác nhận evidence requirement.")
    elif "dia chi" in text or "nha o duong" in text:
        required = {"customers"}
        operation = "Customer address evidence required; do not infer address from transaction names"
    else:
        if "sales_lines" in roles and "orders" in roles:
            required.add("orders")
        if "nhom hang" in text or ("nhom " in text and "khach" not in text and "than thiet" not in text) or "hoat chat" in text or "hang nao" in text or "mat hang" in text or "hang ban chay" in text:
            required.add("products")
        if "hoat chat" in text:
            required.add("drug_attributes")
        if "nhom" in text and ("khach" in text or "than thiet" in text):
            required |= {"customers", "orders"}
        if "so don" in text and "orders" in roles:
            required = {"orders"}
    # A flat single-table order export supports revenue even without sales details.
    if required == {"sales_lines"} and "sales_lines" not in roles and "orders" in roles:
        required = {"orders"}
    selected = [t for t in tables if t["logical_role"] in required]
    for role in sorted(required - roles):
        missing.append("Missing source role: " + role)
    refs = {t["source_ref"] for t in selected}
    edges = [e for e in business["validated_join_unions"] if set(e["left_sources"] + e["right_sources"]).issubset(refs)]
    if "products" in required and "sales_lines" in required:
        product_joins = [e for e in edges if {"sales_lines", "products"}.issubset({e["semantic_relation"].split(" -> ")[0], e["semantic_relation"].split(" -> ")[1]})]
        if not product_joins:
            missing.append("Missing approved join: sales_lines -> products")
    unresolved = [t["source_ref"] for t in selected if t["grain_status"] != "verified"]
    bad_edges = [e["id"] for e in edges if e["status"] == "needs_review" or e.get("name_normalization_review", {}).get("status") == "needs_review"]
    caveats = [{"source_ref": t["source_ref"], "exact_duplicate_excess_rows": t["exact_duplicate_excess_rows"]} for t in selected if t["exact_duplicate_excess_rows"]]
    caveats += [{"source_ref": t["source_ref"], "row_kind_review": t["row_kind_review"]} for t in selected if t.get("row_kind_review")]
    caveats += [{"edge_id": e["id"], "status": e["status"], "left_unmatched_rows": e["left_unmatched_non_null_rows"], "left_null_rows": e["left_null_rows"]}
                for e in edges if e["status"] != "verified" or e["left_null_rows"]]
    return {"question_id": question["id"], "business_id": business["business_id"], "split_group": business["split_group"],
            "as_of_date": question["as_of_date"],
            "source_refs": [t["source_ref"] for t in selected],
            "source_columns": {t["source_ref"]: [c["name"] for c in t["columns"]] for t in selected},
            "join_edges": [e["id"] for e in edges], "operation_boundary": operation,
            "status": "needs_review" if missing or unresolved or bad_edges else "source_contract_ready_with_caveats" if caveats else "source_contract_ready",
            "data_caveats": caveats,
            "missing_evidence": missing, "unresolved_grain_refs": unresolved, "unresolved_join_edges": bad_edges,
            "reviewer": "Người 2 / lead pending", "scope": "Data Catalog source handoff only; not a calculation trace or answer verification"}


def export_quality(catalog, output):
    metrics = []
    for business in catalog["businesses"]:
        for table in business["tables"]:
            def add(column, metric, value, denominator, status):
                metrics.append([business["business_id"], table["source_ref"], column, metric, value, denominator, status])
            for name in ("data_rows", "exact_duplicate_excess_rows", "blank_rows_after_header", "repeated_header_rows", "overflow_rows"):
                add("", name, table[name], table["data_rows"], "measured")
            for name in ("summary_label_rows", "summary_rows_without_order_id"):
                if table.get("row_kind_review"):
                    add("", name, table["row_kind_review"][name], table["data_rows"], "needs_review")
            for column in table["columns"]:
                add(column["name"], "blank_or_null", column["blank_or_null"], table["data_rows"], "measured")
                for name, value in column.get("date_profile", {}).items():
                    if name in ("min", "max", "parsed", "invalid", "serial_corroborated", "serial_workbook_epoch", "serial_context_verified"):
                        add(column["name"], "date_" + name, value, table["data_rows"] - column["blank_or_null"], column["date_profile"]["status"])
            for role, key in table["reviewed_keys"].items():
                for name in ("null_rows", "distinct", "raw_duplicate_excess", "duplicate_excess_after_exact_row_projection"):
                    add(" + ".join(key["columns"]), "review_" + role + "_" + name, key[name], table["data_rows"], "measured")
    with (output / "source_quality.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["business_id", "source_ref", "column", "metric", "value", "denominator", "status"])
        writer.writerows(metrics)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/data_prep")
    parser.add_argument("--write-docs", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    initial = output / "data_catalog.initial.json"
    if not initial.exists():
        initial.write_bytes((output / "data_catalog.json").read_bytes())
    catalog = load_json(initial)
    train = Path(catalog["source_root"])
    before = base.snapshot(train)
    if before != catalog["source_fingerprints"]:
        raise SystemExit("Source differs from initial fingerprints; rebuild/review baseline explicitly")
    targets = {t["source_ref"] for b in catalog["businesses"] for t in b["tables"] if t["grain_status"] == "needs_review"}
    catalog["date_reviews"] = resolve_csv_dates(catalog, train)
    for business in catalog["businesses"]:
        records = collect_keys(train, business)
        text = (train / business["readme"]).read_text(encoding="utf-8-sig")
        for table in business["tables"]:
            if table["source_ref"] in targets:
                review_grain(table, business["readme"], text)
            if table.get("row_kind_review"):
                table.setdefault("grain_review", {"readme_ref": business["readme"], "structure": [c["name"] for c in table["columns"]]})
                table["grain_review"]["blocker"] = "Bảng trộn dòng giao dịch với dòng nhãn tổng; chưa duyệt filter để loại cộng đôi, raw row count chưa phải số giao dịch."
                table["grain_review"]["conclusion"] = "needs_review"
                table["grain"] += f"; OBSERVED MIXED ROWS: {table['row_kind_review']['summary_label_rows']} dòng mang nhãn tổng, cần xác minh bộ lọc"
                table["grain_status"] = table["status"] = "needs_review"
        relation_review(business, records)
        print(json.dumps({"reviewed_business": business["business_id"], "remaining_grains": sum(t["grain_status"] != "verified" for t in business["tables"])}), flush=True)
    samples = load_json(ROOT / "configs/representative_questions.json")["questions"]
    lookup = {b["business_id"]: b for b in catalog["businesses"]}
    source_map = [question_sources({k: q[k] for k in ("id", "business_id", "question", "as_of_date")}, lookup[q["business_id"]]) for q in samples]
    catalog["question_source_map"] = source_map
    catalog["review_provenance"] = {"script": "scripts/review_data_catalog.py", "script_sha256": base.digest(Path(__file__)),
                                     "base_artifact_sha256": base.digest(initial), "generated_utc": datetime.now(timezone.utc).isoformat(),
                                     "initial_grains_needs_review": len(targets), "labels_used": False,
                                     "review_status": "Catalog technical review completed; Person 2 / lead acceptance pending"}
    if before != base.snapshot(train):
        raise SystemExit("Source changed during review; refusing to publish")
    catalog["findings"] = [f for f in base.findings_for(catalog) if f["category"] != "join_fanout"]
    for business in catalog["businesses"]:
        for edge in business["validated_join_unions"]:
            if edge["fanout_on_matched_left"] and edge["fanout_on_matched_left"] > 1:
                catalog["findings"].append({"source_refs": edge["left_sources"], "category": "validated_relation_fanout", "severity": "high",
                                            "status": "requires_aggregation_policy", "edge_id": edge["id"], "factor": edge["fanout_on_matched_left"],
                                            "reproduce": "scripts/review_data_catalog.py; validated_join_edges", "detail": edge["double_counting_policy"]})
        for check in business["cross_partition_key_review"]:
            if check["cross_partition_key_overlap"]:
                catalog["findings"].append({"source_refs": check["source_refs"], "category": "cross_partition_key_overlap", "severity": "high", "status": "needs_review",
                                            "detail": check, "reproduce": "scripts/review_data_catalog.py; cross_partition_key_review"})
        for table in business["tables"]:
            if table["grain_status"] == "needs_review":
                catalog["findings"].append({"source_ref": table["source_ref"], "category": "grain_unresolved", "severity": "high", "status": "needs_review",
                                            "reproduce": "scripts/review_data_catalog.py; grain_review", "detail": table["grain_review"]["blocker"]})
    for i, finding in enumerate(catalog["findings"], 1):
        finding["id"] = f"CAT-{i:04}"
    catalog["source_unchanged"] = True
    dump_json(output / "data_catalog.json", catalog)
    dump_json(output / "question_source_map.json", source_map)
    dump_json(output / "date_review.json", catalog["date_reviews"])
    dump_json(output / "unmatched_name_review.json", [{"edge_id": e["id"], **e["name_normalization_review"]} for b in catalog["businesses"] for e in b["validated_join_unions"] if e.get("name_normalization_review")])
    (output / "findings.jsonl").write_text("".join(json.dumps(f, ensure_ascii=False, allow_nan=False) + "\n" for f in catalog["findings"]), encoding="utf-8")
    export_quality(catalog, output)
    if args.write_docs:
        base.write_document(catalog, ROOT / "docs/data-schema-catalog.md")
    print(json.dumps({"date_reviews": catalog["date_reviews"], "grain_counts": dict(Counter(t["grain_status"] for b in catalog["businesses"] for t in b["tables"])),
                      "question_source_contracts": dict(Counter(q["status"] for q in source_map))}))


if __name__ == "__main__":
    main()
