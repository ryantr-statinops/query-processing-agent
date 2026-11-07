"""Rust-backed data loading and per-business DataFusion catalog."""

from __future__ import annotations

import pathlib
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable

import polars as pl
from datafusion import SessionConfig, SessionContext


def safe_identifier(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", ascii_value).strip("_").lower()
    return cleaned or "table"


def normalize_headers(values: Iterable[Any]) -> list[str]:
    headers: list[str] = []
    seen: dict[str, int] = {}
    for i, value in enumerate(values):
        base = safe_identifier(str(value).strip()) if value is not None else f"column_{i + 1}"
        seen[base] = seen.get(base, 0) + 1
        headers.append(base if seen[base] == 1 else f"{base}_{seen[base]}")
    return headers


@dataclass
class TableInfo:
    name: str
    source: str
    columns: list[str]
    row_count: int
    samples: list[dict[str, Any]]


class BusinessCatalog:
    """Load one business package into Polars and register Arrow tables in DataFusion."""

    def __init__(self, business_dir: pathlib.Path, sample_rows: int = 3):
        if not business_dir.is_dir():
            raise FileNotFoundError(f"Business package not found: {business_dir}")
        self.business_dir = business_dir
        self.context = SessionContext(SessionConfig(config_options={
            "datafusion.execution.target_partitions": "1",
        }))
        self.tables: list[TableInfo] = []
        self._used_names: set[str] = set()
        self._sample_rows = sample_rows
        for path in sorted(business_dir.iterdir()):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix == ".csv":
                self._load_csv(path)
            elif suffix in {".xlsx", ".xls", ".xlsb"}:
                self._load_excel(path)
            elif suffix in {".sqlite", ".db"}:
                self._load_sqlite(path)

    def _unique_name(self, value: str) -> str:
        base = safe_identifier(value)
        name = base
        suffix = 2
        while name in self._used_names:
            name = f"{base}_{suffix}"
            suffix += 1
        self._used_names.add(name)
        return name

    def _register(self, name: str, source: str, frame: pl.DataFrame) -> None:
        if frame.is_empty() and frame.width == 0:
            return
        columns = normalize_headers(frame.columns)
        if frame.columns != columns:
            frame = frame.rename(dict(zip(frame.columns, columns)))
        table_name = self._unique_name(name)
        # DataFusion consumes Polars through the Arrow C data interface.
        self.context.register_view(table_name, self.context.from_polars(frame))
        samples = frame.head(self._sample_rows).to_dicts()
        self.tables.append(TableInfo(table_name, source, columns, frame.height, samples))

    def _load_csv(self, path: pathlib.Path) -> None:
        frame = pl.read_csv(
            path,
            encoding="utf8-lossy",
            infer_schema_length=1000,
            try_parse_dates=False,
            truncate_ragged_lines=True,
            ignore_errors=True,
        )
        self._register(path.stem, path.name, frame)

    def _load_excel(self, path: pathlib.Path) -> None:
        sheets = pl.read_excel(path, sheet_id=0, engine="calamine", infer_schema_length=1000)
        if isinstance(sheets, pl.DataFrame):
            self._register(path.stem, path.name, sheets)
            return
        for sheet_name, frame in sheets.items():
            self._register(f"{path.stem}_{sheet_name}", f"{path.name}:{sheet_name}", frame)

    def _load_sqlite(self, path: pathlib.Path) -> None:
        uri = path.resolve().as_uri() + "?mode=ro"
        source_db = sqlite3.connect(uri, uri=True)
        try:
            names = source_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            for (source_name,) in names:
                # pandas is deliberately avoided; the SQLite file is only an ingestion format.
                cursor = source_db.execute(f'SELECT * FROM "{source_name.replace(chr(34), chr(34)*2)}"')
                columns = normalize_headers(desc[0] for desc in cursor.description or [])
                rows = cursor.fetchall()
                frame = pl.DataFrame(rows, schema=columns, orient="row", infer_schema_length=None)
                self._register(f"{path.stem}_{source_name}", f"{path.name}:{source_name}", frame)
        finally:
            source_db.close()

    def schema_text(self, question: str = "", max_tables: int = 80, max_chars: int = 7000) -> str:
        parts = []
        question_tokens = set(re.findall(r"[\w]+", question.casefold()))
        scored_tables = []
        for order, table in enumerate(self.tables):
            searchable = f"{table.name} {' '.join(table.columns)} {table.samples}".casefold()
            table_tokens = set(re.findall(r"[\w]+", searchable))
            relevance = len(question_tokens & table_tokens)
            scored_tables.append((relevance, -order, table))
        selected = [entry[2] for entry in sorted(scored_tables, reverse=True)[:max_tables]]
        for table in selected:
            columns = ", ".join(table.columns)
            parts.append(
                f"TABLE {table.name} ({columns}); rows={table.row_count}; "
                f"source={table.source}; sample={table.samples[:2]}"
            )
        if len(self.tables) > max_tables:
            parts.append(f"... {len(self.tables) - max_tables} more tables")
        return "\n".join(parts)[:max_chars]

    def close(self) -> None:
        # Drop the Rust-backed session and its in-memory table providers.
        self.context = None
