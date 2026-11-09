"""Supplier and purchase-line summaries."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion, in_period
from datamate.application.plans import Period
from datamate.application.evidence import InsufficientEvidence, numeric_answer


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


def weighted_purchase_price(lines: pl.DataFrame, period: Period, *, coverage: Period | None = None) -> dict:
    if not {"day", "amount", "quantity_base"} <= set(lines.columns):
        raise UnsupportedQuestion("purchase_line_fields_missing")
    scoped = in_period(lines, period, coverage=coverage)
    quantity = scoped["quantity_base"].sum()
    if not quantity:
        raise InsufficientEvidence("purchase_quantity_is_zero")
    amount = scoped["amount"].sum()
    return numeric_answer(amount / quantity, money=True)


def net_purchased_quantity(purchases: pl.DataFrame, sales: pl.DataFrame,
                           purchase_period: Period, sales_period: Period) -> dict:
    required = {"product_id", "quantity_base", "unit_base"}
    if not required | {"day"} <= set(purchases.columns) or not required | {"day"} <= set(sales.columns):
        raise UnsupportedQuestion("base_quantity_fields_missing")
    purchase_units = {row[0]: row[1] for row in purchases.select("product_id", "unit_base").unique().iter_rows()}
    sales_units = {row[0]: row[1] for row in sales.select("product_id", "unit_base").unique().iter_rows()}
    if any(sales_units.get(product) != unit for product, unit in purchase_units.items() if product in sales_units):
        raise UnsupportedQuestion("incompatible_base_units")
    bought = purchases.filter(pl.col("day").is_between(purchase_period.start, purchase_period.end))
    sold = sales.filter(pl.col("day").is_between(sales_period.start, sales_period.end))
    inbound = bought.group_by("product_id").agg(pl.col("quantity_base").sum().alias("purchased"))
    outbound = sold.group_by("product_id").agg(pl.col("quantity_base").sum().alias("sold"))
    net = inbound.join(outbound, on="product_id", how="full", coalesce=True).with_columns(
        pl.col("purchased").fill_null(0), pl.col("sold").fill_null(0)).with_columns(
        (pl.col("purchased") - pl.col("sold")).alias("net_quantity"))
    return {"type": "table", "columns": ["product_id", "purchased", "sold", "net_quantity"],
            "rows": net.sort("product_id").to_dicts()}
