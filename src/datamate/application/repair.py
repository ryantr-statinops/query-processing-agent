"""Repair-shop visits and service labels remain separate from item sales."""

import re
import unicodedata

import polars as pl

from datamate.application.evidence import UnsupportedQuestion, numeric_answer


def normalize_service(text: str) -> str:
    value = unicodedata.normalize("NFC", text).casefold().strip()
    value = re.sub(r"\s+", " ", value)
    aliases = {"nhot may": "nhớt máy", "nhot may": "nhớt máy", "nhot lap": "nhớt láp",
               "nhớt láp": "nhớt láp", "nhot láp": "nhớt láp"}
    return aliases.get(value, value)


def count_repair_visits(visits: pl.DataFrame) -> dict:
    if "visit_id" not in visits.columns:
        raise UnsupportedQuestion("repair_visit_identity_missing")
    return numeric_answer(visits["visit_id"].n_unique())


def service_visit_counts(visits: pl.DataFrame) -> dict:
    if not {"work", "amount"} <= set(visits.columns):
        raise UnsupportedQuestion("repair_service_fields_missing")
    if visits["amount"].null_count():
        raise UnsupportedQuestion("invalid_repair_amount")
    charged = visits.filter(pl.col("amount") > 0)
    charged = charged.with_columns(pl.col("work").cast(pl.String).map_elements(normalize_service,
                                                                               return_dtype=pl.String).alias("work"))
    rows = []
    for work, count in charged.group_by("work").len().sort("work").iter_rows():
        rows.append({"work": work, "visits": count})
    return {"type": "table", "columns": ["work", "visits"], "rows": rows}


def warranty_rate(visits: pl.DataFrame) -> dict:
    if not {"visit_id", "amount", "is_warranty"} <= set(visits.columns):
        raise UnsupportedQuestion("repair_warranty_fields_missing")
    paid = visits.filter((pl.col("amount") > 0) & ~pl.col("is_warranty"))
    warranties = visits.filter(pl.col("is_warranty")).height
    if paid.height == 0:
        raise UnsupportedQuestion("no_paid_repair_denominator")
    return {"type": "percent", "answer": round(warranties / paid["visit_id"].n_unique() * 100, 2)}


def repeat_vehicles(visits: pl.DataFrame, *, minimum_visits: int = 2) -> dict:
    if not {"plate", "visit_id"} <= set(visits.columns):
        raise UnsupportedQuestion("repair_vehicle_identity_missing")
    repeated = visits.filter(pl.col("plate").is_not_null() & (pl.col("plate").str.strip_chars() != ""))
    counts = repeated.group_by("plate").agg(pl.col("visit_id").n_unique().alias("visits"))
    rows = counts.filter(pl.col("visits") >= minimum_visits).sort("plate").to_dicts()
    return {"type": "table", "columns": ["plate", "visits"], "rows": rows}
