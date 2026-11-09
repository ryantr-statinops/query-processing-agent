"""Pharmacy sales classifications follow catalog flags and exact ingredients."""

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
