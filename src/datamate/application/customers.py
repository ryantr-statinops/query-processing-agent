"""Resolve customer identity from the fields actually present on sales orders."""

import unicodedata

import polars as pl

from datamate.application.evidence import UnsupportedQuestion


def with_customer_key(orders: pl.DataFrame) -> pl.DataFrame:
    if "customer_id" in orders.columns:
        # A shop with customer codes uses those codes; missing code means walk-in.
        return orders.with_columns(pl.col("customer_id").cast(pl.String).str.strip_chars()
                                   .replace("", None).alias("customer_key"))
    if "customer_name" not in orders.columns:
        raise UnsupportedQuestion("customer_identity_fields_missing")
    return orders.with_columns(pl.col("customer_name").cast(pl.String)
                               .map_elements(normalize_customer_name, return_dtype=pl.String).alias("customer_key"))


def normalize_customer_name(name: str) -> str | None:
    value = " ".join(unicodedata.normalize("NFC", name).casefold().split())
    if value in {"khách lẻ", "khach le", "walk-in", "walk in"} or not value:
        return None
    return value
