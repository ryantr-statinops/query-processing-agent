"""Cafe modifiers are classified without duplicating line quantities or value."""

import re

import polars as pl

from datamate.application.evidence import UnsupportedQuestion

_SIZE = re.compile(r"(?:^|\b)(size\s*)?([ml])(?:\b|$)", re.IGNORECASE)
_TOPPING = re.compile(r"\b(?:topping|thêm|them)\s*[:：-]?\s*([^,;+]+)", re.IGNORECASE)


def classify_cafe_item(name: str) -> tuple[str, str | None, tuple[str, ...]]:
    size_match = _SIZE.search(name)
    size = size_match[2].upper() if size_match else None
    toppings = tuple(match.strip() for match in _TOPPING.findall(name) if match.strip())
    base = _TOPPING.sub("", name)
    if size_match:
        base = base[:size_match.start()] + base[size_match.end():]
    base = re.sub(r"\s+", " ", base).strip(" -,+;")
    return base, size, toppings


def annotate_cafe_lines(lines: pl.DataFrame) -> pl.DataFrame:
    if not {"product_name", "quantity", "amount"} <= set(lines.columns):
        raise UnsupportedQuestion("cafe_line_fields_missing")
    return lines.with_columns(
        pl.col("product_name").map_elements(lambda value: classify_cafe_item(str(value))[0], return_dtype=pl.String).alias("base_item"),
        pl.col("product_name").map_elements(lambda value: classify_cafe_item(str(value))[1], return_dtype=pl.String).alias("size"),
        pl.col("product_name").map_elements(lambda value: list(classify_cafe_item(str(value))[2]), return_dtype=pl.List(pl.String)).alias("toppings"),
    )
