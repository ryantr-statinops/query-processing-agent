"""Locate tabular sources by their schema."""

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata


def schema_key(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text.casefold().replace("đ", "d"))
    return re.sub(r"[^a-z0-9]", "", plain)


@dataclass(frozen=True)
class Source:
    path: Path
    table: str | None
    columns: tuple[str, ...]

    @property
    def family(self) -> str:
        if self.path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            return schema_key(self.table or "")
        stem = re.sub(r"[_ -](?:\d{1,2}|20\d{2})$", "", self.path.stem)
        return schema_key(stem)


@dataclass(frozen=True)
class Binding:
    source: Source
    fields: dict[str, str]


class AmbiguousSource(ValueError):
    """More than one incompatible source supplies the requested fields."""


def bind_sources(sources: list[Source], required: dict[str, tuple[str, ...]],
                 preferred: tuple[str, ...], optional: dict[str, tuple[str, ...]] | None = None) -> list[Binding]:
    groups: dict[tuple[Path, str, tuple[str, ...]], list[Binding]] = {}
    for source in sources:
        by_key: dict[str, list[str]] = {}
        for column in source.columns:
            by_key.setdefault(schema_key(column), []).append(column)
        fields = {}
        for field, aliases in {**required, **(optional or {})}.items():
            for alias in aliases:
                matches = by_key.get(schema_key(alias), [])
                if len(matches) == 1:
                    fields[field] = matches[0]
                    break
        if required.keys() <= fields.keys() and len(set(fields.values())) == len(fields):
            key = (source.path.parent, source.family, tuple(fields))
            groups.setdefault(key, []).append(Binding(source, fields))
    if not groups:
        return []
    ranks = {schema_key(name): index for index, name in reversed(list(enumerate(preferred)))}
    ordered = sorted(groups.items(), key=lambda item: ranks.get(item[0][1], len(ranks)))
    if len(ordered) > 1 and ranks.get(ordered[0][0][1]) == ranks.get(ordered[1][0][1]):
        raise AmbiguousSource("multiple_tables_match")
    return ordered[0][1]


def csv_source(path: Path) -> Source:
    import csv

    with path.open(encoding="utf-8-sig", errors="replace", newline="") as stream:
        headers = next(csv.reader(stream), [])
    return Source(path, None, tuple(headers))


def load_csv(binding: Binding):
    import polars as pl

    return pl.read_csv(binding.source.path, columns=list(binding.fields.values()), infer_schema=False)


def excel_sources(path: Path):
    import fastexcel

    workbook = fastexcel.read_excel(path)
    for name in workbook.sheet_names:
        sheet = workbook.load_sheet(name, n_rows=0, dtypes="string")
        yield Source(path, name, tuple(column.name for column in sheet.available_columns()))


def load_excel(binding: Binding):
    import polars as pl

    return pl.read_excel(binding.source.path, sheet_name=binding.source.table, engine="calamine",
                         columns=list(binding.fields.values()), raise_if_empty=False)


def sheet_year(source: Source) -> int | None:
    if match := re.search(r"\b(20\d{2})\b", source.table or ""):
        return int(match[1])
    return None


def _identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _sqlite(path: Path):
    from contextlib import closing
    import sqlite3

    return closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True))


def sqlite_sources(path: Path):
    with _sqlite(path) as database:
        names = database.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
        for name, in names:
            if not name.startswith("sqlite_"):
                columns = database.execute(f"PRAGMA table_info({_identifier(name)})")
                yield Source(path, name, tuple(row[1] for row in columns))


def load_sqlite(binding: Binding):
    import polars as pl

    columns = list(binding.fields.values())
    projection = ", ".join(_identifier(column) for column in columns)
    table = _identifier(binding.source.table or "")
    with _sqlite(binding.source.path) as database:
        rows = database.execute(f"SELECT {projection} FROM {table}").fetchall()
    return pl.DataFrame(rows, schema=columns, orient="row", infer_schema_length=None)


class SourceCatalog:
    def __init__(self, business_dir: Path, capacity: int = 48):
        from collections import OrderedDict

        if capacity < 1:
            raise ValueError("Cache capacity must be positive")
        self.capacity = capacity
        self.tables = OrderedDict()
        self.sources: list[Source] = []
        for path in sorted(business_dir.iterdir()):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix == ".csv":
                self.sources.append(csv_source(path))
            elif suffix in {".xlsx", ".xls", ".xlsb"}:
                self.sources.extend(excel_sources(path))
            elif suffix in {".sqlite", ".sqlite3", ".db"}:
                self.sources.extend(sqlite_sources(path))
        readme = business_dir / "README.md"
        self.description = readme.read_text(encoding="utf-8-sig", errors="replace") if readme.is_file() else ""

    def load(self, binding: Binding, normalize=None):
        key = (binding.source, tuple(binding.fields.items()), normalize)
        if key not in self.tables:
            suffix = binding.source.path.suffix.lower()
            reader = load_csv if suffix == ".csv" else load_excel if suffix in {".xlsx", ".xls", ".xlsb"} else load_sqlite
            frame = reader(binding).rename({column: field for field, column in binding.fields.items()})
            self.tables[key] = normalize(frame, binding.source) if normalize is not None else frame
            if len(self.tables) > self.capacity:
                self.tables.popitem(last=False)
        self.tables.move_to_end(key)
        return self.tables[key]
