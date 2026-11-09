"""Pharmacy sales classifications follow catalog flags and exact ingredients."""

from datetime import timedelta

import polars as pl

from datamate.application.evidence import UnsupportedQuestion


def sales_by_prescription(lines: pl.DataFrame, products: pl.DataFrame) -> dict:
    if not {"product_id", "amount"} <= set(lines.columns) or not {"product_id", "prescription"} <= set(products.columns):
        raise UnsupportedQuestion("pharmacy_prescription_fields_missing")
    joined = lines.join(products.select("product_id", "prescription"), on="product_id", how="left")
    if joined["prescription"].null_count():
        raise UnsupportedQuestion("unknown_prescription_classification")
    rows = joined.group_by("prescription").agg(pl.col("amount").sum().alias("revenue")).sort("prescription").to_dicts()
    return {"type": "table", "columns": ["prescription", "revenue"], "rows": rows}


def sales_by_ingredient(lines: pl.DataFrame, products: pl.DataFrame) -> dict:
    if not {"product_id", "amount"} <= set(lines.columns) or not {"product_id", "ingredient"} <= set(products.columns):
        raise UnsupportedQuestion("pharmacy_ingredient_fields_missing")
    joined = lines.join(products.select("product_id", "ingredient"), on="product_id", how="left")
    if joined["ingredient"].null_count():
        raise UnsupportedQuestion("unknown_ingredient_classification")
    # Combination strings are keys in their own right; never split and double-count them.
    rows = joined.group_by("ingredient").agg(pl.col("amount").sum().alias("revenue")).sort("ingredient").to_dicts()
    return {"type": "table", "columns": ["ingredient", "revenue"], "rows": rows}


def expiring_lots(lots: pl.DataFrame, as_of, days: int) -> dict:
    required = {"product_id", "lot_id", "expiry", "remaining_quantity", "unit_cost"}
    if not required <= set(lots.columns) or days < 0:
        raise UnsupportedQuestion("pharmacy_lot_fields_missing")
    active = lots.filter((pl.col("expiry") >= as_of) & (pl.col("expiry") <= as_of + timedelta(days=days))
                         & (pl.col("remaining_quantity") > 0))
    valued = active.with_columns((pl.col("remaining_quantity") * pl.col("unit_cost")).alias("remaining_cost"))
    rows = valued.sort(["expiry", "product_id", "lot_id"]).to_dicts()
    return {"type": "table", "columns": list(valued.columns), "rows": rows}
