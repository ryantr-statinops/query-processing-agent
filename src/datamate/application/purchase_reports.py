"""Supplier and purchase-line summaries."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion, in_period
from datamate.application.plans import Period


def rank_suppliers(receipts: pl.DataFrame, period: Period, metric: str, *, limit: int = 10) -> dict:
    required = {"receipt_id", "supplier_id", "day", "status", "amount"}
    if not required <= set(receipts.columns) or limit < 1:
        raise UnsupportedQuestion("supplier_fields_missing")
    valid = in_period(receipts, period).filter(
        pl.col("supplier_id").is_not_null() & ~pl.col("status").str.to_lowercase().is_in(["cancelled", "returned"]))
    grouped = valid.group_by("supplier_id").agg(pl.col("amount").sum().alias("spend"),
                                                 pl.col("receipt_id").n_unique().alias("receipts"))
    field = {"spend": "spend", "receipts": "receipts"}.get(metric)
    if field is None:
        raise UnsupportedQuestion("unsupported_supplier_ranking_metric")
    rows = grouped.sort([field, "supplier_id"], descending=[True, False]).head(limit).to_dicts()
    return {"type": "table", "columns": list(rows[0]) if rows else ["supplier_id", field], "rows": rows}
