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
