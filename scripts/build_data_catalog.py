"""Read-only train discovery; stdlib fallback while the project scaffold is absent.

No labels are used for profiling. XLSX streams OOXML shared strings/styles.
Raw blanks/duplicates are measured, never filled/deduplicated in source files.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import closing
import csv
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import posixpath
import re
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
TAG = "{" + NS["s"] + "}"


def fold(value):
    return "".join(c for c in unicodedata.normalize("NFD", str(value).lower().replace("đ", "d"))
                   if unicodedata.category(c) != "Mn")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*")) if p.is_file()}


def readme_sections(text):
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            refs = re.findall(r"`([^`]+)`", line)
            current = tuple(refs) if line.startswith("## Cột") and refs else None
            if current:
                sections[current] = {}
        match = re.match(r"- \*\*(.+?)\*\*:\s*(.*)", line)
        if current and match:
            sections[current][match[1]] = match[2]
    return sections


def display_filename(name):
    """Compare README Unicode names with legacy ZIP filename decoding; never rename."""
    for encoding in ("cp437", "cp850"):
        try:
            decoded = name.encode(encoding).decode("utf-8")
            if decoded != name:
                return decoded
        except (UnicodeError, LookupError):
            pass
    return name


def prior_headers(document):
    headers = {}
    business = file = sheet = None
    for line in document.split("## public_test", 1)[0].splitlines():
        if line.startswith("### biz_"):
            business = line.split()[1]
        match = re.match(r"- \*\*(.+?)\*\*", line)
        if match:
            file = match[1]
            sheet_match = re.search(r"\*\* / `([^`]+)`", line)
            sheet = sheet_match[1] if sheet_match else None
        if line.startswith("  - Columns:") and business and file:
            headers[(business, file, sheet)] = re.findall(r"`([^`]+)`", line)
        match = re.match(r"  - `([^`]+)`.*candidate header: (.*)", line)
        if match:
            headers[(business, file, match[1])] = re.findall(r"`([^`]+)`", match[2])
    return headers


def partition_checks(tables, counters):
    checks = []
    for i, left in enumerate(tables):
        for j in range(i + 1, len(tables)):
            right = tables[j]
            if [c["name"] for c in left["columns"]] != [c["name"] for c in right["columns"]]:
                continue
            dates = []
            for a, b in zip(left["columns"], right["columns"]):
                da, db = a.get("date_profile"), b.get("date_profile")
                if da and db and da["min"] and db["min"]:
                    dates.append({"column": a["name"], "left_min": da["min"], "left_max": da["max"],
                                  "right_min": db["min"], "right_max": db["max"],
                                  "range_overlap": max(da["min"], db["min"]) <= min(da["max"], db["max"])})
            common = counters[i].keys() & counters[j].keys()
            role = next((k for k in ("order_line", "order", "receipt", "product") if k in common), None)
            checks.append({"left": left["source_ref"], "right": right["source_ref"], "same_columns_and_order": True,
                           "date_ranges": dates, "key_role": role,
                           "shared_distinct_keys": len(counters[i][role].keys() & counters[j][role].keys()) if role else None,
                           "interpretation": "Potential partitions only; overlapping keys/ranges require review"})
    return checks


def xlsx_tables(path):
    with zipfile.ZipFile(path) as book:
        shared = []
        if "xl/sharedStrings.xml" in book.namelist():
            with book.open("xl/sharedStrings.xml") as stream:
                for _, element in ET.iterparse(stream, events=("end",)):
                    if element.tag == TAG + "si":
                        shared.append("".join(t.text or "" for t in element.iter(TAG + "t")))
                        element.clear()
        styles = set()
        if "xl/styles.xml" in book.namelist():
            tree = ET.fromstring(book.read("xl/styles.xml"))
            custom = {int(n.attrib["numFmtId"]): n.attrib.get("formatCode", "")
                      for n in tree.findall("s:numFmts/s:numFmt", NS)}
            for i, xf in enumerate(tree.findall("s:cellXfs/s:xf", NS)):
                fmt = int(xf.attrib.get("numFmtId", 0))
                code = re.sub(r'"[^\"]*"|\[[^\]]*\]|\\.', "", custom.get(fmt, ""))
                if fmt in set(range(14, 23)) | set(range(45, 48)) or re.search("[yd]", code, re.I):
                    styles.add(i)
        wb = ET.fromstring(book.read("xl/workbook.xml"))
        date1904 = wb.find("s:workbookPr", NS)
        epoch = datetime(1904, 1, 1) if date1904 is not None and date1904.get("date1904") in ("1", "true") else datetime(1899, 12, 30)
        rels = {n.attrib["Id"]: n.attrib["Target"] for n in ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))}
        for sheet in wb.findall("s:sheets/s:sheet", NS):
            target = rels[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
            member = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)

            def rows(member=member):
                with book.open(member) as stream:
                    for _, element in ET.iterparse(stream, events=("end",)):
                        if element.tag != TAG + "row":
                            continue
                        cells = {}
                        for cell in element.findall("s:c", NS):
                            letters = re.match(r"[A-Z]+", cell.get("r", "A1"))[0]
                            index = 0
                            for letter in letters:
                                index = index * 26 + ord(letter) - 64
                            kind = cell.get("t", "n")
                            raw = cell.findtext("s:v", default="", namespaces=NS)
                            if kind == "inlineStr":
                                value = "".join(t.text or "" for t in cell.iter(TAG + "t"))
                            elif kind == "s":
                                value = shared[int(raw)] if raw else ""
                            elif kind == "b":
                                value = raw == "1"
                            elif raw and kind == "n":
                                value = float(raw)
                                if int(cell.get("s", 0)) in styles:
                                    value = (epoch + timedelta(days=value)).isoformat(sep=" ")
                                elif value.is_integer():
                                    value = int(value)
                            else:
                                value = raw
                            cells[index - 1] = value
                        width = max(cells, default=-1) + 1
                        yield int(element.get("r", 0)), [cells.get(i, "") for i in range(width)]
                        element.clear()
            yield sheet.attrib["name"], rows()


def source_tables(path):
    if path.suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            yield None, enumerate(csv.reader(stream), 1), None
    elif path.suffix == ".xlsx":
        for sheet, rows in xlsx_tables(path):
            yield sheet, rows, None
    elif path.suffix == ".sqlite":
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            connection.execute("PRAGMA query_only=ON")
            check = connection.execute("PRAGMA quick_check").fetchone()[0]
            if check != "ok":
                raise ValueError(f"SQLite quick_check: {check}")
            for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
                quoted = '"' + table.replace('"', '""') + '"'
                cursor = connection.execute("SELECT * FROM " + quoted)
                columns = [d[0] for d in cursor.description]
                yield table, enumerate(cursor, 1), columns


@lru_cache(maxsize=200000)
def parse_day(value, year=None):
    value = value.strip()
    if not value:
        return None
    vietnamese = re.fullmatch(r"(\d{1,2}) thg (\d{1,2}) (\d{4})", value)
    if vietnamese:
        try:
            return date(int(vietnamese[3]), int(vietnamese[2]), int(vietnamese[1])).isoformat()
        except ValueError:
            return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    if year and re.fullmatch(r"\d{1,2}/\d{1,2}", value):
        try:
            return datetime.strptime(value + "/" + str(year), "%d/%m/%Y").date().isoformat()
        except ValueError:
            pass
    return None


@lru_cache(maxsize=256)
def workbook_epoch(path):
    with zipfile.ZipFile(path) as book:
        properties = ET.fromstring(book.read("xl/workbook.xml")).find("s:workbookPr", NS)
    return datetime(1904, 1, 1) if properties is not None and properties.get("date1904") in ("1", "true") else datetime(1899, 12, 30)


def semantic_roles(columns, descriptions):
    roles = {}
    for i, column in enumerate(columns):
        desc = fold(descriptions.get(column, ""))
        name = fold(column)
        for role, phrase in (("order", "ma don"), ("product", "ma hang"), ("customer", "ma khach"),
                             ("receipt", "ma phieu nhap"), ("line", "so thu tu dong"), ("payment", "ma phieu thu")):
            if desc.startswith(phrase):
                roles[role] = i
        if name in ("ten san pham", "ten hang hoa") and desc.startswith("ten hang"):
            roles["product_name"] = i
        if name in ("don vi tinh", "don vi quy doi") and desc.startswith("don vi"):
            roles["unit"] = i
        if name == "idcuahang":
            roles["store"] = i
        for role, exact in (("order", "mahoadon"), ("product", "mahanghoa"), ("customer", "makhachhang"),
                            ("receipt", "maphieunhap"), ("line", "sothutu"), ("payment", "maphieuthu"), ("lot", "malo")):
            if name == exact:
                roles[role] = i
    return roles


def profile(path, sheet, rows, sql_columns, descriptions, header_hint=None):
    prefix = list(itertools.islice(rows, 100)) if sql_columns is None else []
    if sql_columns is None:
        if not prefix:
            raise ValueError("Empty table")
        expected = set(descriptions) or set(header_hint or [])
        def score(item):
            values = [str(v).strip() for v in item[1]]
            matches = len(expected.intersection(values))
            text = sum(isinstance(v, str) and bool(v.strip()) and not re.fullmatch(r"[\d.,/ :\-]+", v) for v in item[1])
            return (matches, text, -item[0])
        header_no, raw_columns = max(prefix, key=score)
        columns = [str(v) for v in raw_columns]
        header_status = "verified" if columns and all(c.strip() for c in columns) and len(set(columns)) == len(columns) and expected and expected.issubset(columns) else "needs_review"
        data = itertools.chain((r for r in prefix if r[0] > header_no), rows)
    else:
        columns, header_no, header_status, data = sql_columns, None, "verified", rows
    n = len(columns)
    nulls, types, dates, values = [0] * n, [Counter() for _ in columns], {}, {}
    year_match = re.search(r"20\d{2}", sheet or "")
    year = int(year_match[0]) if year_match else None
    for i, column in enumerate(columns):
        name, desc = fold(column), fold(descriptions.get(column, ""))
        if re.search(r"ngay|date|time|thoigian|han su dung|hansudung|han dung", name) or desc.startswith(("ngay", "thoi diem")):
            if "so ngay" not in name and "han gop" not in name and not desc.startswith("so ngay") and not ("han no" in name and "(ngay)" in name):
                dates[i] = {"min": None, "max": None, "parsed": 0, "invalid": 0, "serial_corroborated": 0, "serial_workbook_epoch": 0}
        if "trang thai" in name or name in ("status", "tinhtrang", "ket qua", "xu ly", "dvt", "donvitinh", "donvi") or desc.startswith(("trang thai", "don vi")):
            values[i] = Counter()
    roles = semantic_roles(columns, descriptions)
    key_indices = {role: ([roles["store"]] if "store" in roles and role != "store" else []) + [index]
                   for role, index in roles.items()}
    if "order" in roles and "line" in roles:
        key_indices["order_line"] = ([roles["store"]] if "store" in roles else []) + [roles["order"], roles["line"]]
    if "product" in roles and "lot" in roles:
        key_indices["product_lot"] = ([roles["store"]] if "store" in roles else []) + [roles["product"], roles["lot"]]
    if "product_name" in roles and "unit" in roles:
        key_indices["product_unit"] = [roles["product_name"], roles["unit"]]
    keys = {role: Counter() for role in key_indices}
    key_nulls = Counter()
    hashes = Counter()
    count = blank = repeated = overflow = 0
    max_physical = header_no or 0
    for physical, raw in data:
        max_physical = max(max_physical, physical)
        if not any(v is not None and str(v).strip() for v in raw):
            blank += 1
            continue
        if list(raw) == columns:
            repeated += 1
            continue
        if len(raw) > n and any(str(v).strip() for v in raw[n:]):
            overflow += 1
        row = list(raw[:n]) + [None] * max(0, n - len(raw))
        count += 1
        hashes[hashlib.sha256(json.dumps(row, ensure_ascii=False, default=str).encode()).digest()] += 1
        for i, value in enumerate(row):
            empty = value is None or not str(value).strip()
            if empty:
                nulls[i] += 1
                continue
            types[i][type(value).__name__] += 1
            if i in dates:
                day = parse_day(str(value), year)
                d = dates[i]
                if not day and path.suffix == ".xlsx" and isinstance(value, (int, float)) and not isinstance(value, bool) and 1 <= value <= 100000:
                    candidate = (workbook_epoch(path) + timedelta(days=value)).date()
                    if year is None or candidate.year == year:
                        day = candidate.isoformat()
                        d["serial_workbook_epoch"] += 1
                # Accept a text serial only when an independent timestamp on
                # the same SQLite row corroborates the 1900-epoch conversion.
                if not day and sql_columns and "ThoiGianLap" in columns and re.fullmatch(r"\d{5}(?:\.0+)?", str(value)):
                    candidate = (datetime(1899, 12, 30) + timedelta(days=float(value))).date().isoformat()
                    reference = parse_day(str(row[columns.index("ThoiGianLap")]))
                    if candidate == reference:
                        day = candidate
                        d["serial_corroborated"] += 1
                if day:
                    d["parsed"] += 1
                    d["min"] = min(d["min"] or day, day)
                    d["max"] = max(d["max"] or day, day)
                else:
                    d["invalid"] += 1
            if i in values:
                values[i][str(value)] += 1
        for role, indices in key_indices.items():
            key = tuple(str(row[i]).strip() if row[i] is not None else "" for i in indices)
            if all(key):
                keys[role][key] += 1
            else:
                key_nulls[role] += 1
    columns_info = []
    for i, column in enumerate(columns):
        entry = {"name": column, "readme_description": descriptions.get(column), "blank_or_null": nulls[i], "observed_storage_types": dict(types[i])}
        if i in dates:
            entry["date_profile"] = dates[i] | {"parse_rule": "ISO/day-first/d thg m yyyy; year from sheet only; numeric XLSX date field uses workbook epoch and sheet-year check; text serial only if same-row ThoiGianLap corroborates; no fill", "status": "verified" if not dates[i]["invalid"] else "needs_review"}
        if i in values:
            entry["observed_values"] = dict(values[i]) if len(values[i]) <= 100 else {"distinct": len(values[i]), "status": "needs_review"}
        columns_info.append(entry)
    ref = f"{path.parent.name}/{path.name}" + (f"#{sheet}" if sheet else "")
    table = {"source_ref": ref, "file": path.name, "sheet_or_table": sheet, "format": path.suffix[1:],
             "header_row_1based": header_no, "header_status": header_status, "columns": columns_info,
             "header_evidence": "SQLite cursor schema" if sql_columns is not None else ("README column names matched" if descriptions else "prior catalog header matched actual row; semantic review separate"),
             "data_rows": count, "max_physical_row": max_physical, "blank_rows_after_header": blank,
             "repeated_header_rows": repeated, "overflow_rows": overflow,
             "exact_duplicate_excess_rows": sum(v - 1 for v in hashes.values()),
             "grain": "needs_review: determine from README and key evidence; duplicates are not automatically removed",
             "grain_status": "needs_review", "status": "needs_review",
             "keys": {role: {"columns": [columns[i] for i in key_indices[role]], "non_null_rows": sum(counter.values()),
                              "null_rows": key_nulls[role], "distinct": len(counter), "duplicate_excess_rows": sum(counter.values()) - len(counter)}
                      for role, counter in keys.items()}}
    return table, keys


def set_grain(table, readme):
    name = fold(table["sheet_or_table"] if table["file"] in ("DuLieuBanHang.xlsx", "DuLieuXuat.xlsx", "Bao_cao_ban_hang.xlsx", "pos.sqlite") else table["file"])
    keys = table["keys"]
    description = None
    if "product_unit" in keys and ("quydoi" in name or "quy_doi" in name):
        description, evidence = "one unit conversion per product name + selling unit", "README conversion columns + composite-key counts"
        verified = keys["product_unit"]["null_rows"] == 0 and keys["product_unit"]["duplicate_excess_rows"] == 0
    elif "order_line" in keys and "lo" not in name:
        description = "sales line identified by order + line (plus store where present)"
        key = keys["order_line"]
        evidence = "README line descriptions / SQLite README + composite key counts"
        verified = key["null_rows"] == 0 and key["duplicate_excess_rows"] == 0
    elif table["source_ref"].startswith(("biz_101/", "biz_114/", "biz_125/")):
        description, evidence, verified = "one sales line in an order", "README introduction explicitly defines grain; raw duplicates/blanks reported", True
    elif table["source_ref"].startswith(("biz_107/", "biz_113/", "biz_126/")):
        description, evidence, verified = "one recorded item purchase; no order/customer ID", "README introduction; rulebook section 8: identical records still count", True
    elif "donhang_chitiet" in name or "so_chi_tiet_ban_hang" in name:
        description, evidence, verified = "one sales line; order attributes can repeat", "README introduction explicitly defines line grain", "mỗi dòng một" in readme
    elif "order" in keys and (name.startswith("don_hang") or "danhsachhoadon" in name and "chitiet" not in name or "hoadon" in name and "chitiet" not in name or "danh_sach_hoa_don" in name):
        key = keys["order"]
        description, evidence = "one order", "README source role + order-key uniqueness/null counts"
        verified = key["null_rows"] == 0 and key["duplicate_excess_rows"] == 0
    elif name in ("thanh_toan", "thanh_toan.csv") or "phieuthu" in name or "soquy" in name:
        description, evidence, verified = "one payment event (not one order)", "README debt/payment convention; verify payment identity separately", "mỗi lần khách trả tiền" in readme
    elif "tonkho" in name or "ton_kho" in name:
        description, evidence, verified = "inventory snapshot; snapshot date requires README", "source role inferred from name; not transaction history", False
    elif "the_kho" in name:
        description, evidence, verified = "one inventory movement with post-movement balance", "SQLite README inventory convention", "mỗi dòng `the_kho.TonCuoi`" in readme
    elif "chi_tiet_don_lo" in name:
        description, evidence, verified = "allocation of one sales line to a lot; a line can use multiple lots", "SQLite README lot convention; order-line duplicates expected", "Một dòng bán có thể lấy từ nhiều lô" in readme
    elif name == "lo_hang":
        description, evidence, verified = "one received lot", "SQLite README lot convention", "mỗi dòng nhập là một lô" in readme
    elif name == "lich_su_gia":
        description, evidence, verified = "product price effective from date until next change", "SQLite README price convention; temporal join required", "áp dụng từ" in readme
    if description:
        table.update(grain=description, grain_evidence=evidence, grain_status="verified" if verified else "needs_review")
    table["status"] = "verified" if table["header_status"] == "verified" and table["grain_status"] == "verified" and not table["overflow_rows"] else "needs_review"


def join_profile(left, right, role, left_keys, right_keys):
    a, b = left_keys[role], right_keys[role]
    common = a.keys() & b.keys()
    joined = sum(a[k] * b[k] for k in common)
    matched_a, matched_b = sum(a[k] for k in common), sum(b[k] for k in common)
    a_many, b_many = any(v > 1 for v in a.values()), any(v > 1 for v in b.values())
    return {"left": left["source_ref"], "right": right["source_ref"], "role": role,
            "left_columns": left["keys"][role]["columns"], "right_columns": right["keys"][role]["columns"],
            "left_rows": left["data_rows"], "right_rows": right["data_rows"],
            "left_matched_rows": matched_a, "right_matched_rows": matched_b,
            "left_unmatched_non_null_rows": sum(a.values()) - matched_a,
            "right_unmatched_non_null_rows": sum(b.values()) - matched_b,
            "left_null_key_rows": left["keys"][role]["null_rows"], "right_null_key_rows": right["keys"][role]["null_rows"],
            "inner_join_rows": joined, "left_join_rows": joined + left["data_rows"] - matched_a,
            "cardinality": ("many" if a_many else "one") + "-to-" + ("many" if b_many else "one"),
            "fanout_on_matched_left": joined / matched_a if matched_a else None,
            "warning": "Do not sum order-level totals after joining to lines/payments; raw blanks not group-filled.",
            "status": "measured_candidate", "semantic_review": "needs_review"}


def findings_for(result):
    findings = []
    def add(ref, category, severity, detail):
        findings.append({"id": f"CAT-{len(findings)+1:04}", "source_ref": ref, "category": category,
                         "severity": severity, "detail": detail, "reproduce": "scripts/build_data_catalog.py; inspect source_ref in data_catalog.json", "status": "needs_review"})
    for error in result["errors"]:
        add(error["business"] + "/" + error["file"], "read_error", "high", error["error"])
    for business in result["businesses"]:
        bid = business["business_id"]
        for label in ("missing_declared_files", "undeclared_files"):
            if business[label]:
                add(bid, "readme_filename_conflict", "medium", {label: business[label], "unicode_matches": business["unicode_filename_matches"]})
        for table in business["tables"]:
            ref = table["source_ref"]
            if table["header_status"] != "verified":
                add(ref, "header", "high", "Header candidate did not fully match README/prior schema or is non-unique/blank; counts provisional")
            if table["exact_duplicate_excess_rows"]:
                add(ref, "exact_duplicate_rows", "medium", {"excess_rows": table["exact_duplicate_excess_rows"], "interpretation": "Rulebook section 8: deduplicate only identical rows within same order; no automatic removal"})
            if table["repeated_header_rows"] or table["overflow_rows"]:
                add(ref, "row_structure", "high", {k: table[k] for k in ("repeated_header_rows", "overflow_rows")})
            for column in table["columns"]:
                dp = column.get("date_profile")
                if dp and dp["invalid"]:
                    add(ref, "unparsed_date", "high", {"column": column["name"], "invalid": dp["invalid"], "nonblank": table["data_rows"] - column["blank_or_null"]})
                desc = fold(column.get("readme_description") or "")
                if desc.startswith("trang thai don") or (table["sheet_or_table"] == "don_hang" and column["name"] == "TinhTrang"):
                    aliases = {k: v for k, v in column.get("observed_values", {}).items()
                               if fold(k).strip() not in ("hoan thanh", "huy", "tra hang", "dang giao")}
                    if aliases:
                        add(ref, "status_alias_review", "medium", {"column": column["name"], "observed_noncanonical_labels": aliases,
                                                                    "rule_ref": "train/rulebook.md section 8", "note": "Observed aliases, not proven invalid; mapping needs semantic review"})
            # Compare only the sales/order date, not birthdays, expiry or price history.
            cutoff_match = re.search(r"Dữ liệu có đến hết (\d{2}/\d{2}/\d{4})", business["readme_rules"])
            if cutoff_match:
                cutoff = parse_day(cutoff_match[1])
                for column in table["columns"]:
                    desc = fold(column.get("readme_description") or "")
                    if desc.startswith("ngay ban") and column.get("date_profile", {}).get("max") and column["date_profile"]["max"] > cutoff:
                        add(ref, "readme_date_coverage", "high", {"column": column["name"], "readme_cutoff": cutoff, "observed_max": column["date_profile"]["max"]})
        for edge in business["joins"]:
            if edge["fanout_on_matched_left"] and edge["fanout_on_matched_left"] > 1:
                add(edge["left"], "join_fanout", "high", {"right": edge["right"], "role": edge["role"], "inner_join_rows": edge["inner_join_rows"], "matched_left_rows": edge["left_matched_rows"], "factor": edge["fanout_on_matched_left"]})
    return findings


def write_document(result, document):
    previous = document.read_text(encoding="utf-8")
    public = previous.split("## public_test", 1)[1] if "## public_test" in previous else ""
    tables = [t for b in result["businesses"] for t in b["tables"]]
    lines = ["# Data schema catalog", "", "## Train — kiểm tra trên dữ liệu local", "",
             "Nguồn: `train/`; script: `scripts/build_data_catalog.py`. Không tải dữ liệu, không sửa nguồn.",
             f"Đã đọc {len(result['businesses'])}/30 business, {result['file_count']} file trong toàn train, {len(tables)} sheet/table/CSV.",
             "Checksum gói chính thức **chưa xác minh**. SHA-256 từng file chỉ dùng so trước/sau; nguồn không đổi trong lượt quét.",
             "Môi trường khóa bị chặn vì thiếu `src/datamate/__init__.py`; công cụ dùng thư viện chuẩn qua uv, không đổi dependencies.", "",
             "`header_status=verified` xác nhận schema SQLite hoặc dòng header thực khớp README/catalog cũ; không tự xác nhận ý nghĩa dữ liệu.",
             "`status=verified` chỉ xác nhận header và grain nêu trong entry; quality/join có trạng thái độc lập. Các join thống kê là candidate, chưa thay thế review ngữ nghĩa.",
             "Số dòng là dòng không trống sau header, loại header lặp khớp nguyên dòng; chưa fill nhóm, chưa deduplicate, chưa lọc trạng thái.",
             "Kiểu là kiểu lưu trữ: CSV giữ string; Excel đọc cached values và date styles. Công thức chưa có cached value và header nhiều dòng cần review.",
             "Ngày parse ISO hoặc dd/mm/yyyy (có giờ), dd-mm-yyyy/dd.mm.yyyy, d thg m yyyy; dd/mm chỉ dùng năm của sheet. Không đoán năm từ tên file.",
             "Lượt quét cơ sở chỉ parse serial text khi khớp ThoiGianLap độc lập cùng dòng SQLite; policy CSV đã audit được ghi riêng trong review bổ sung. unparsed_date không đồng nghĩa nguồn hỏng.",
             "Ô số trong cột ngày XLSX được giải theo epoch workbook, đối chiếu năm sheet nếu có; duration như Hạn nợ (ngày) không được coi là ngày lịch.",
             "Null/blank và duplicates là quan sát raw, không tự coi là lỗi; áp dụng rulebook §8 trước khi tính đáp án.",
             "Chi tiết cột, date coverage, keys, join coverage/fan-out, fingerprints và findings ở `artifacts/data_prep/` (local, không commit).", "",
             "Tái lập trong PowerShell (sau khi có Python):", "", "```powershell",
             "$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'",
             "uv run --no-project --python .venv/Scripts/python.exe python scripts/build_data_catalog.py --write-docs", "```", "",
             "D01: kiểm kê toàn bộ. D02: header/grain có trạng thái từng nguồn. D03: profiling raw đã đo, date/units/status chưa đầy đủ kiểm tra ngữ nghĩa.",
             "D04: các phép đo bằng counter, không thực thi SQL do model sinh; trạng thái map/validation xem review bổ sung. D05: chờ Người 2/lead review.",
             "48 câu development / 12 câu holdout đã tiếp xúc nhãn: dùng ID/text để bàn giao nguồn, không dùng gold để profiling hoặc chọn cấu hình.", ""]
    if result.get("review_provenance"):
        grain_counts = Counter(t["grain_status"] for t in tables)
        edges = [e for b in result["businesses"] for e in b.get("validated_join_unions", [])]
        lines += ["### Review bổ sung có bằng chứng", "",
                  f"Grain: {dict(grain_counts)}; {len(edges)} quan hệ được đo theo loại nguồn và kiểm tra khóa, không phê duyệt mọi candidate chung khóa.",
                  f"Trạng thái cạnh: {dict(Counter(e['status'] for e in edges))}.",
                  "CSV serial có policy audit riêng trong `date_reviews`; chỉ áp khi epoch duy nhất khớp ngày bao quanh, README cutoff và nguồn thu tiền độc lập. Không bật parser số tổng quát.",
                  "Source contracts của 60 câu: `artifacts/data_prep/question_source_map.json`; chưa phải trace/đáp án đã xác minh. Chi tiết handoff: [data-catalog-handoff.md](data-catalog-handoff.md).", "",
                  "Sau bước build (chỉ khi cần), tiếp tục review và validation:", "", "```powershell",
                  "uv run --no-project --python .venv/Scripts/python.exe python scripts/review_data_catalog.py --write-docs",
                  "uv run --no-project --python .venv/Scripts/python.exe python scripts/validate_data_catalog.py --write-report", "```", ""]
    for business in sorted(result["businesses"], key=lambda b: b["business_id"]):
        lines += ["### " + business["business_id"], "", f"README: `{business['readme']}`; {len(business['actual_files'])} data files; {len(business['tables'])} tables; {len(business['joins'])} measured join candidates."]
        if business["missing_declared_files"] or business["undeclared_files"]:
            lines += ["README/path conflicts (không đổi tên nguồn): " + json.dumps({"missing": business["missing_declared_files"], "extra": business["undeclared_files"], "unicode_matches": business["unicode_filename_matches"]}, ensure_ascii=False)]
        lines += [""]
        for table in business["tables"]:
            lines += [f"- **{table['file']}**" + (f" / `{table['sheet_or_table']}`" if table['sheet_or_table'] else "") +
                      f" — {table['data_rows']} data rows; header: {table['header_row_1based'] or 'SQLite schema'} ({table['header_status']}); status: `{table['status']}`.",
                      "  - Columns: " + " · ".join("`" + c["name"] + "`" for c in table["columns"]),
                      f"  - Grain ({table['grain_status']}): {table['grain']}."]
            coverage = [f"`{c['name']}`: {c['date_profile']['min']} → {c['date_profile']['max']}; invalid={c['date_profile']['invalid']}" for c in table["columns"] if "date_profile" in c]
            if coverage:
                lines += ["  - Dates: " + "; ".join(coverage)]
            if table["exact_duplicate_excess_rows"]:
                lines += [f"  - Raw duplicate excess rows: {table['exact_duplicate_excess_rows']} (không tự loại)."]
        lines += [""]
    if result["errors"]:
        lines += ["### Read blockers", "", "```json", json.dumps(result["errors"], ensure_ascii=False, indent=2), "```", ""]
    lines += ["## public_test" + public] if public else []
    document.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-root", type=Path, default=ROOT / "train")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/data_prep")
    parser.add_argument("--write-docs", action="store_true", help="Update train catalog section, preserve public-test snapshot")
    args = parser.parse_args()
    train, output = args.train_root.resolve(), args.output.resolve()
    if output == train or train in output.parents:
        raise SystemExit("Output must not be inside source train/")
    before = snapshot(train)
    old_headers = prior_headers((ROOT / "docs/data-schema-catalog.md").read_text(encoding="utf-8"))
    expected = {f"biz_{i}" for i in range(101, 131)}
    actual = {p.name for p in (train / "data").iterdir() if p.is_dir()}
    if actual != expected:
        raise SystemExit(f"Business mismatch: missing={expected-actual}, extra={actual-expected}")
    for name in ("rulebook.md", "calendar.csv", "questions.jsonl", "answers.jsonl"):
        if not (train / name).is_file():
            raise SystemExit(f"Missing {name}")
    manifest = json.loads((ROOT / "configs/splits/seed_2026.json").read_text(encoding="utf-8"))
    samples = json.loads((ROOT / "configs/representative_questions.json").read_text(encoding="utf-8"))["questions"]
    inventory_text = (ROOT / "docs/data-inventory.md").read_text(encoding="utf-8").split("## public_test", 1)[0]
    inventory_files = {b: int(n) for b, n in re.findall(r"\| `(biz_\d+)` \| \d+ \| (\d+) \|", inventory_text)}
    result = {"version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(), "archive_checksum": "not_verified: no archive or independent reference",
              "script_sha256": digest(Path(__file__)),
              "method": "stdlib CSV / OOXML streaming / SQLite mode=ro, query_only; no labels used",
              "source_root": str(train), "file_count": len(before), "extension_counts": dict(Counter(Path(p).suffix for p in before)),
              "environment_blocker": "uv sync --locked fails: missing src/datamate/__init__.py; stdlib fallback, no dependency changes",
              "root_files_present": [n for n in ("rulebook.md", "calendar.csv", "questions.jsonl", "answers.jsonl") if (train / n).is_file()],
              "jsonl_nonblank_record_counts": {name: sum(bool(line.strip()) for line in (train / name).open(encoding="utf-8-sig")) for name in ("questions.jsonl", "answers.jsonl")},
              "businesses": [], "errors": [], "review_status": "Person 2 / lead review pending"}
    for business in sorted(actual, key=lambda b: (b not in ("biz_101", "biz_102", "biz_123"), b)):
        directory = train / "data" / business
        readme_path = directory / "README.md"
        text = readme_path.read_text(encoding="utf-8-sig")
        sections = readme_sections(text)
        files = sorted(p for p in directory.rglob("*") if p.is_file() and p.name != "README.md")
        declared = re.findall(r"^- `([^`]+\.(?:csv|xlsx|sqlite))`", text, re.M)
        item = {"business_id": business, "split_group": "holdout_exposed" if business in manifest["holdout_businesses"] else "development",
                "readme": readme_path.relative_to(train).as_posix(), "readme_sha256": digest(readme_path),
                "declared_files": declared, "actual_files": [p.name for p in files],
                "missing_declared_files": sorted(set(declared) - {p.name for p in files}),
                "undeclared_files": sorted({p.name for p in files} - set(declared)),
                "unicode_filename_matches": {p.name: display_filename(p.name) for p in files if display_filename(p.name) in declared and p.name not in declared},
                "representative_question_ids": [q["id"] for q in samples if q["business_id"] == business],
                "tables": [], "joins": [], "readme_rules": text.split("## Quy ước", 1)[-1].strip()}
        item["inventory_data_file_count"] = inventory_files.get(business)
        item["inventory_file_count_matches"] = inventory_files.get(business) == len(files)
        counters = []
        for path in files:
            try:
                for sheet, rows, sql_columns in source_tables(path):
                    descriptions = next((desc for refs, desc in sections.items() if refs[0] == display_filename(path.name) and (len(refs) == 1 or refs[1] == sheet)), {})
                    hint = old_headers.get((business, path.name, sheet))
                    table, keys = profile(path, sheet, iter(rows), sql_columns, descriptions, hint)
                    set_grain(table, text)
                    item["tables"].append(table)
                    counters.append(keys)
                    print(json.dumps({"source_ref": table['source_ref'], "rows": table['data_rows']}), flush=True)
            except (OSError, ValueError, sqlite3.Error, zipfile.BadZipFile, ET.ParseError) as exc:
                result["errors"].append({"business": business, "file": path.name, "error": str(exc)})
        for i, left in enumerate(item["tables"]):
            for j in range(i + 1, len(item["tables"])):
                right = item["tables"][j]
                # Sheets of the same source are partitions, not join candidates.
                if left["file"] == right["file"] and left["format"] != "sqlite":
                    continue
                common = counters[i].keys() & counters[j].keys() - {"store", "line", "payment", "unit"}
                if "product_unit" in common:
                    common -= {"product_name"}
                if "order_line" in common:
                    common -= {"order", "product", "lot", "product_lot"}
                elif "product_lot" in common:
                    common -= {"product", "lot"}
                for role in sorted(common):
                    item["joins"].append(join_profile(left, right, role, counters[i], counters[j]))
        item["schema_groups"] = []
        groups = defaultdict(list)
        for table in item["tables"]:
            groups[tuple(c["name"] for c in table["columns"])].append(table["source_ref"])
        item["schema_groups"] = [{"columns": list(cols), "source_refs": refs} for cols, refs in groups.items()]
        item["partition_checks"] = partition_checks(item["tables"], counters)
        result["businesses"].append(item)
    # Shared calendar is profiled without reading answer contents.
    path = train / "calendar.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        calendar, _ = profile(path, None, enumerate(csv.reader(stream), 1), None, {})
    result["calendar"] = calendar
    after = snapshot(train)
    if before != after:
        raise SystemExit("Source changed during scan; refusing to publish catalog")
    result["source_unchanged"] = True
    result["source_fingerprints"] = before
    result["findings"] = findings_for(result)
    output.mkdir(parents=True, exist_ok=True)
    (output / "data_catalog.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "findings.jsonl").write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in result["findings"]), encoding="utf-8")
    with (output / "source_quality.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["business_id", "source_ref", "column", "metric", "value", "denominator", "status"])
        for business in result["businesses"]:
            for table in business["tables"]:
                for metric in ("data_rows", "exact_duplicate_excess_rows", "blank_rows_after_header", "repeated_header_rows", "overflow_rows"):
                    writer.writerow([business["business_id"], table["source_ref"], "", metric, table[metric], table["data_rows"], "measured"])
                for column in table["columns"]:
                    writer.writerow([business["business_id"], table["source_ref"], column["name"], "blank_or_null", column["blank_or_null"], table["data_rows"], "measured"])
                    for metric, value in column.get("date_profile", {}).items():
                        if metric in ("min", "max", "parsed", "invalid", "serial_corroborated", "serial_workbook_epoch"):
                            writer.writerow([business["business_id"], table["source_ref"], column["name"], "date_" + metric, value, table["data_rows"] - column["blank_or_null"], column["date_profile"]["status"]])
                for role, key in table["keys"].items():
                    for metric in ("null_rows", "distinct", "duplicate_excess_rows"):
                        writer.writerow([business["business_id"], table["source_ref"], " + ".join(key["columns"]), role + "_" + metric, key[metric], table["data_rows"], "measured_candidate"])
    if args.write_docs:
        write_document(result, ROOT / "docs/data-schema-catalog.md")
    print(json.dumps({"businesses": len(result["businesses"]), "tables": sum(len(b["tables"]) for b in result["businesses"]), "errors": result["errors"], "source_unchanged": True}))


if __name__ == "__main__":
    main()
