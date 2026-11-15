"""Shared filesystem, text and tabular helpers for exploratory analyses."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import unicodedata
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load non-empty JSONL records without changing source data."""
    with path.open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def fold_vietnamese(value: Any) -> str:
    """Casefold and remove Vietnamese combining marks, preserving punctuation."""
    text = unicodedata.normalize("NFKD", str(value)).casefold().replace("đ", "d")
    return "".join(char for char in text if not unicodedata.combining(char))


def iter_business_dirs(
    root: Path = ROOT, splits: tuple[str, ...] = ("train", "public_test")
) -> Iterator[tuple[str, Path]]:
    """Yield local business directories in stable split and name order."""
    for split in splits:
        data_root = root / split / "data"
        if not data_root.is_dir():
            continue
        for business_dir in sorted(path for path in data_root.iterdir() if path.is_dir()):
            yield split, business_dir


def iter_source_rows(
    path: Path,
    *,
    sheet_limit: int | None = None,
    rows_per_sheet: int | None = None,
) -> Iterator[tuple[str | None, int, tuple[Any, ...] | list[str]]]:
    """Stream CSV or XLSX rows as ``(sheet, one_based_row, values)``.

    XLSX workbooks are opened read-only and closed even when the consumer stops
    early. The row limit applies independently to each sheet.
    """
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for row_number, values in enumerate(csv.reader(stream), start=1):
                if rows_per_sheet is not None and row_number > rows_per_sheet:
                    break
                yield None, row_number, values
        return
    if suffix != ".xlsx":
        raise ValueError(f"Unsupported tabular file type: {path.suffix}")

    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        worksheets = workbook.worksheets
        if sheet_limit is not None:
            worksheets = worksheets[:sheet_limit]
        for worksheet in worksheets:
            for row_number, values in enumerate(
                worksheet.iter_rows(values_only=True), start=1
            ):
                if rows_per_sheet is not None and row_number > rows_per_sheet:
                    break
                yield worksheet.title, row_number, values
    finally:
        workbook.close()


def write_json_artifact(name: str, value: Any, *, root: Path = ROOT) -> Path:
    """Write an analysis result under the ignored local artifact directory."""
    output = root / "artifacts" / "analysis" / name
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output


def configure_utf8_stdout() -> None:
    """Keep Vietnamese CLI output usable on Windows consoles with legacy encodings."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
