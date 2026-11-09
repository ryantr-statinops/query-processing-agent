"""Normalize source values in memory while preserving original identifiers."""

import polars as pl


def clean(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.String).str.strip_chars().replace("", None)


def date_value(column: str, year: int | None = None) -> pl.Expr:
    text = clean(column).str.extract(r"^(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)", 1)
    if year:
        text = pl.when(text.str.contains(r"^\d{1,2}[/-]\d{1,2}$")).then(text + f"/{year}").otherwise(text)
    return pl.coalesce(text.str.to_date(fmt, strict=False) for fmt in
                       ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"))


def number_value(column: str) -> pl.Expr:
    text = clean(column).str.replace_all(r"\s|₫|đ|VND", "")
    vietnamese = text.str.contains(r"^-?\d{1,3}(?:\.\d{3})+(?:,\d+)?$")
    decimal_comma = text.str.contains(r"^-?\d+,\d{1,2}$")
    normalized = (
        pl.when(vietnamese).then(text.str.replace_all(r"\.", "").str.replace(",", "."))
        .when(decimal_comma).then(text.str.replace(",", "."))
        .otherwise(text.str.replace_all(",", ""))
    )
    return normalized.cast(pl.Decimal(28, 6), strict=False)


def status_value(column: str, *, note: bool = False) -> pl.Expr:
    value = clean(column).str.to_lowercase()
    return (
        pl.when(value.str.contains(r"hu[ỷy]|hủy|cancel")).then(pl.lit("cancelled"))
        .when(value.str.contains(r"trả hàng|đã trả|returned")).then(pl.lit("returned"))
        .when(value.str.contains(r"đang giao|shipping")).then(pl.lit("shipping"))
        .when(value.str.contains(r"hoàn thành|đã nhập|đã giao|complete|delivered")).then(pl.lit("completed"))
        .otherwise(pl.lit("completed") if note else None)
    )
