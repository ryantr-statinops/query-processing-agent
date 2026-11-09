"""Inventory snapshots use all movements through the inclusive as-of date."""

import polars as pl

from datamate.application.evidence import InsufficientEvidence, UnsupportedQuestion
from datamate.application.plans import Period


def stock_as_of(movements: pl.DataFrame, as_of, *, coverage: Period | None = None) -> dict:
    required = {"product_id", "day", "quantity_delta", "value_delta"}
    if not required <= set(movements.columns):
        raise UnsupportedQuestion("stock_movement_fields_missing")
    if movements["day"].null_count() or movements["quantity_delta"].null_count():
        raise UnsupportedQuestion("invalid_stock_movement")
    if coverage and as_of > coverage.end:
        raise InsufficientEvidence("stock_snapshot_after_coverage")
    through_day = movements.filter(pl.col("day") <= as_of)
    totals = through_day.group_by("product_id").agg(pl.col("quantity_delta").sum().alias("quantity"),
                                                      pl.col("value_delta").sum().alias("stock_value"))
    rows = totals.sort("product_id").to_dicts()
    return {"type": "table", "columns": ["product_id", "quantity", "stock_value"], "rows": rows}
