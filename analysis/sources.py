"""Grouped exploratory commands for inspecting local business source files."""

from __future__ import annotations

import argparse
import collections
import csv
import datetime
import json
import re
import sqlite3
import warnings
from pathlib import Path
from typing import Any, Callable, Iterable

from analysis.common import (
    ROOT,
    configure_utf8_stdout,
    iter_business_dirs,
    iter_source_rows,
    load_jsonl,
    write_json_artifact,
)


def inventory(root: Path = ROOT) -> int:
    rows: list[dict[str, Any]] = []
    for split, business_dir in iter_business_dirs(root):
        readme = business_dir / "README.md"
        text = readme.read_text(encoding="utf-8") if readme.exists() else ""
        match = re.search(r"Dữ liệu có đến hết\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})", text)
        files = sorted(path.name for path in business_dir.iterdir() if path.name != "README.md")
        formats = sorted({Path(name).suffix for name in files})
        rows.append(
            {
                "split": split,
                "biz": business_dir.name,
                "cutoff": match.group(1) if match else "",
                "files": files,
                "fmt": "/".join(formats),
            }
        )

    questions = load_jsonl(root / "train/questions.jsonl")
    public_questions = load_jsonl(root / "public_test/questions.jsonl")
    questions_by_business: dict[str, list[str]] = collections.defaultdict(list)
    for question in questions + public_questions:
        questions_by_business[question["business_id"]].append(question["as_of_date"])

    print(f"{'biz':9} {'cutoff':11} {'fmt':10} {'nfiles':6} {'q':4} as_of range")
    for row in rows:
        dates = sorted(questions_by_business.get(row["biz"], []))
        date_range = f"{dates[0]}..{dates[-1]}" if dates else "-"
        row["nq"] = len(dates)
        print(
            f"{row['biz']:9} {row['cutoff']:11} {row['fmt']:10} "
            f"{len(row['files']):<6} {len(dates):<4} {date_range}"
        )

    print("\n\n=== FILE INVENTORY ===")
    for row in rows:
        print(f"\n[{row['biz']}] ({row['split']}, cutoff {row['cutoff']})")
        print("   " + ", ".join(row["files"]))
    write_json_artifact("inventory.json", rows, root=root)
    return 0


def _sqlite_file_info(path: Path) -> dict[str, dict[str, Any]]:
    connection = sqlite3.connect(path)
    try:
        cursor = connection.cursor()
        tables = [
            row[0]
            for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        result = {}
        for table in tables:
            columns = [row[1] for row in cursor.execute(f'PRAGMA table_info("{table}")')]
            count = cursor.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            result[table] = {"cols": columns, "rows": count}
        return result
    finally:
        connection.close()


def headers(root: Path = ROOT) -> int:
    output: dict[str, dict[str, Any]] = {}
    for _, business_dir in iter_business_dirs(root):
        business_info: dict[str, Any] = {}
        for path in sorted(business_dir.iterdir()):
            if not path.is_file():
                continue
            extension = path.suffix.lower()
            try:
                if extension == ".csv":
                    with path.open(encoding="utf-8-sig", newline="") as stream:
                        reader = csv.reader(stream)
                        first = next(reader)
                        second = next(reader)
                    business_info[path.name] = [[cell for cell in first], second]
                elif extension == ".xlsx":
                    sheets: dict[str, list[list[str | None]]] = {}
                    sheet_rows: dict[str, list[list[str | None]]] = collections.defaultdict(list)
                    for sheet, _, values in iter_source_rows(path, rows_per_sheet=2):
                        if sheet is None:
                            raise RuntimeError("XLSX row has no worksheet name")
                        sheet_rows[sheet].append(
                            [None if value is None else str(value)[:60] for value in values]
                        )
                    for sheet, rows in sheet_rows.items():
                        while rows and rows[0] and rows[0][-1] is None:
                            rows[0] = rows[0][:-1]
                        sheets[sheet] = rows
                    business_info[path.name] = sheets
                elif extension == ".sqlite":
                    business_info[path.name] = _sqlite_file_info(path)
            except Exception as error:
                business_info[path.name] = {"ERROR": str(error)[:120]}
        output[business_dir.name] = business_info

    write_json_artifact("headers.json", output, root=root)
    print("bizs:", len(output))
    errors = [
        (business, filename)
        for business, files in output.items()
        for filename, value in files.items()
        if isinstance(value, dict) and "ERROR" in value
    ]
    print("errors:", errors)
    for business in ("biz_101", "biz_106", "biz_123", "dev_012"):
        print("\n##", business)
        for filename, value in output.get(business, {}).items():
            print(" ", filename, "->", json.dumps(value, ensure_ascii=False)[:400])
    return 0


def best_header(rows: Iterable[Iterable[Any]]) -> int:
    best_count, best_index = -1, 0
    for index, row in enumerate(rows):
        count = sum(1 for value in row if value not in (None, ""))
        if count > best_count and count >= 3:
            best_count, best_index = count, index
    return best_index


def header_rows(root: Path = ROOT) -> int:
    flags: list[tuple[str, str, int, list[Any]]] = []
    inventory_by_business: dict[str, dict[str, Any]] = {}
    for _, business_dir in iter_business_dirs(root):
        for path in sorted(business_dir.iterdir()):
            if path.suffix.lower() == ".csv":
                rows = [list(values) for _, _, values in iter_source_rows(path, rows_per_sheet=6)]
                index = best_header(rows)
                inventory_by_business.setdefault(business_dir.name, {})[path.name] = {
                    "header_row": index,
                    "header": rows[index] if rows else [],
                }
                if index != 0:
                    flags.append((business_dir.name, path.name, index, rows[index]))
            elif path.suffix.lower() == ".xlsx":
                sheet_rows: dict[str | None, list[list[Any]]] = collections.defaultdict(list)
                for sheet, _, values in iter_source_rows(path, rows_per_sheet=6):
                    row = [None if value is None else str(value)[:50] for value in values]
                    sheet_rows[sheet].append(row)
                for sheet, rows in sheet_rows.items():
                    index = best_header(rows)
                    name = f"{path.name} :: {sheet}"
                    inventory_by_business.setdefault(business_dir.name, {})[name] = {
                        "header_row": index,
                        "header": rows[index] if rows else [],
                    }
                    if index != 0:
                        flags.append((business_dir.name, name, index, rows[index]))

    print("=== files/sheets where header is NOT first row ===")
    for business, filename, index, header in flags:
        print(f"  {business:8} {filename[:60]:60} row#{index}  {header}")
    write_json_artifact("headers_detected.json", inventory_by_business, root=root)
    print("\ntotal flagged:", len(flags))
    return 0


def sqlite_schema(root: Path = ROOT) -> int:
    for business, split in (("biz_123", "train"), ("dev_006", "public_test")):
        path = root / split / "data" / business / "pos.sqlite"
        connection = sqlite3.connect(path)
        try:
            cursor = connection.cursor()
            tables = [
                row[0]
                for row in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
            ]
            print("===", business, "===")
            for table in tables:
                columns = cursor.execute(f'PRAGMA table_info("{table}")').fetchall()
                count = cursor.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                print(
                    f"  {table} ({count} rows): "
                    + ", ".join(column[1] + ":" + column[2] for column in columns)
                )
        finally:
            connection.close()
    return 0


NUM_TEXT = re.compile(r"^-?[\d.,]+\s*(đ|d|%|vnđ)?$")
DATE_TEXT = re.compile(r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}([ T].*)?$")


def classify_cell(value: Any) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return "empty"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, (datetime.datetime, datetime.date)):
        return "date_obj"
    text = str(value).strip()
    if NUM_TEXT.match(text):
        return "num_text"
    if DATE_TEXT.match(text):
        return "date_text"
    return "text"


def cell_formats(root: Path = ROOT) -> int:
    report: dict[str, dict[str, dict[str, float]]] = {}
    for _, business_dir in iter_business_dirs(root):
        for path in sorted(business_dir.iterdir()):
            extension = path.suffix.lower()
            if extension not in (".csv", ".xlsx"):
                continue
            counts: collections.Counter[str] = collections.Counter()
            try:
                if extension == ".csv":
                    rows = list(iter_source_rows(path, rows_per_sheet=250))
                    for _, _, row in rows[1:]:
                        counts.update(classify_cell(value) for value in row)
                else:
                    for sheet, row_number, row in iter_source_rows(
                        path, sheet_limit=3, rows_per_sheet=250
                    ):
                        if row_number <= 2:
                            continue
                        counts.update(classify_cell(value) for value in row)
            except Exception as error:
                counts = collections.Counter({"ERROR": str(error)[:80]})
            total = sum(counts.values()) or 1
            flags = {
                kind: round(count * 100 / total, 1)
                for kind, count in counts.items()
                if kind in ("num_text", "date_text", "text", "date_obj")
            }
            if flags:
                report.setdefault(business_dir.name, {})[path.name] = flags

    print("files with >=20% numeric-as-text or date-as-text:")
    for business, files in report.items():
        for filename, counts in files.items():
            if counts.get("num_text", 0) >= 20 or counts.get("date_text", 0) >= 20:
                print(f"  {business:8} {filename[:46]:46} {counts}")
    return 0


NUMBER_STYLE_PATTERN = re.compile(r"^-?[\d.,]+\s*(đ|d|vnđ|%)?$")


def _number_samples(path: Path) -> list[str]:
    samples: list[str] = []
    if path.suffix.lower() == ".csv":
        for _, row_number, row in iter_source_rows(path):
            if row_number == 1:
                continue
            for value in row:
                text = str(value).strip()
                if text and NUMBER_STYLE_PATTERN.match(text) and re.search(r"[.,]\d{3}", text):
                    samples.append(text)
            if len(samples) > 400:
                break
        return samples
    current_sheet = None
    skip_current_sheet = False
    for sheet, _, row in iter_source_rows(path, sheet_limit=2, rows_per_sheet=400):
        if sheet != current_sheet:
            current_sheet = sheet
            skip_current_sheet = False
        if skip_current_sheet:
            continue
        for value in row:
            text = str(value).strip() if value is not None else ""
            if text and NUMBER_STYLE_PATTERN.match(text) and re.search(r"[.,]\d{3}", text):
                samples.append(text)
        if len(samples) > 400:
            skip_current_sheet = True
    return samples


def _number_style(samples: list[str]) -> collections.Counter[str]:
    style: collections.Counter[str] = collections.Counter()
    for value in samples:
        if value.endswith("đ") or value.endswith("vnđ"):
            style["đ_suffix"] += 1
        if value.endswith("%"):
            style["%_suffix"] += 1
        if re.match(r"^-?\d{1,3}(,\d{3})+$", value):
            style["1,234,567"] += 1
        elif re.match(r"^-?\d{1,3}(\.\d{3})+$", value):
            style["1.234.567"] += 1
        elif "," in value:
            style["comma_other"] += 1
        else:
            style["other"] += 1
    return style


def number_style(root: Path = ROOT) -> int:
    for _, business_dir in iter_business_dirs(root):
        samples = []
        for path in sorted(business_dir.iterdir()):
            if path.suffix.lower() in (".csv", ".xlsx"):
                samples.extend(_number_samples(path))
        if samples:
            print(f"{business_dir.name:8} {dict(_number_style(samples))}  e.g. {samples[:6]}")
    return 0


STATUS_PATTERN = re.compile(
    r"(trạng thái|status|tình trạng|kết quả|tình trạng|xử lý|tiến độ|tt đơn|ghi chú tt|xử lý)",
    re.I,
)
STATUS_SKIP = re.compile(r"(hđđt|phiếu)", re.I)


def _status_values(path: Path, *, limit: int = 20000) -> collections.Counter[str]:
    result: collections.Counter[str] = collections.Counter()
    header = None
    indexes: list[int] = []
    for row_index, (_, _, row) in enumerate(iter_source_rows(path)):
        values = [None if value is None else str(value).strip() for value in row]
        if header is None:
            if sum(1 for value in values if value) >= 3:
                header = values
                indexes = [
                    index
                    for index, name in enumerate(header)
                    if name and STATUS_PATTERN.search(name) and not STATUS_SKIP.search(name)
                ]
        else:
            for index in indexes:
                if index < len(values) and values[index]:
                    result[values[index][:40]] += 1
        if row_index > limit:
            break
    return result


def statuses(root: Path = ROOT) -> int:
    results: dict[tuple[str, str], collections.Counter[str]] = {}
    for _, business_dir in iter_business_dirs(root):
        for path in sorted(business_dir.iterdir()):
            if path.suffix.lower() not in (".csv", ".xlsx"):
                continue
            try:
                results[(business_dir.name, path.name)] = _status_values(path)
            except Exception as error:
                print("ERR", business_dir.name, path.name, type(error).__name__, str(error)[:100])

    print("=== distinct status-like values per file ===")
    for (business, filename), counts in results.items():
        top = counts.most_common(12)
        if top:
            print(f"  {business:8} {filename[:38]:38} {dict(top)}")
    return 0


PRODUCT_PATTERN = re.compile(
    r"^(tên sản phẩm|tên hàng hóa|tên hàng|tên mặt hàng|tên sp|hàng bán|hàng hóa|hàng|mặt hàng|sản phẩm|nội dung|product|ten_hang|ten hang|tên món|tên gọi|ten san pham)$",
    re.I,
)


def product_names(path: Path, *, limit: int = 4000) -> list[str]:
    rows: list[Iterable[Any]] = []
    extension = path.suffix.lower()
    if extension == ".csv":
        rows = [row for _, _, row in iter_source_rows(path, rows_per_sheet=4005)]
    elif extension == ".xlsx":
        for _, _, row in iter_source_rows(path, sheet_limit=2):
            rows.append(row)
            if len(rows) > limit:
                break
    else:
        return []

    header_index = None
    header: list[str | None] = []
    for index, row in enumerate(rows[:6]):
        values = [None if value is None else str(value).strip() for value in row]
        if sum(1 for value in values if value) >= 3:
            header_index, header = index, values
            break
    if header_index is None:
        return []
    indexes = [index for index, name in enumerate(header) if name and PRODUCT_PATTERN.match(name)][:1]
    if not indexes:
        return []
    names = []
    for row in rows[header_index + 1 : header_index + 4000]:
        for index in indexes:
            if index < len(row) and row[index] is not None:
                names.append(str(row[index]).strip())
    return names


def products(root: Path = ROOT) -> int:
    for _, business_dir in iter_business_dirs(root):
        accumulated = []
        for path in sorted(business_dir.iterdir()):
            if path.suffix.lower() not in (".csv", ".xlsx"):
                continue
            try:
                accumulated.extend(product_names(path))
            except Exception:
                continue
        if accumulated:
            counts = collections.Counter(accumulated)
            print(
                f"{business_dir.name:8} ({len(set(accumulated))} distinct) "
                + " | ".join(name[:34] for name, _ in counts.most_common(6))
            )
    return 0


COMMANDS: dict[str, Callable[[Path], int]] = {
    "inventory": inventory,
    "headers": headers,
    "header-rows": header_rows,
    "sqlite": sqlite_schema,
    "cell-formats": cell_formats,
    "number-style": number_style,
    "statuses": statuses,
    "products": products,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, command in COMMANDS.items():
        child = subparsers.add_parser(name)
        child.set_defaults(handler=command)
    args = parser.parse_args(argv)
    warnings.filterwarnings("ignore")
    configure_utf8_stdout()
    return args.handler(ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
