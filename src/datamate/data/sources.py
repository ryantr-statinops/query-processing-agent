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
