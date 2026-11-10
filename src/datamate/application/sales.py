"""Shared sale eligibility and aggregation rules."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion, in_period, numeric_answer
from datamate.application.plans import Period

_EXCLUDED = ("cancelled", "returned")


def eligible_orders(orders: pl.DataFrame, period: Period, *, coverage: Period | None = None) -> pl.DataFrame:
    """Filter order-level rows; shipping remains eligible, any return does not."""
    required = {"order_id", "day", "status"}
    if not required <= set(orders.columns):
        raise UnsupportedQuestion("sales_order_fields_missing")
    if orders["order_id"].null_count() or orders["status"].null_count():
        raise UnsupportedQuestion("invalid_sales_order_identity_or_status")
    scoped = in_period(orders, period, coverage=coverage)
    return scoped.filter(~pl.col("status").str.to_lowercase().is_in(_EXCLUDED)).unique("order_id", keep="first")


def count_orders(orders: pl.DataFrame, period: Period, *, coverage: Period | None = None) -> dict:
    return numeric_answer(eligible_orders(orders, period, coverage=coverage).height)


def count_orders_by_shift(orders: pl.DataFrame, period: Period, start_hour: int, end_hour: int,
                          *, coverage: Period | None = None) -> dict:
    if "hour" not in orders.columns or orders["hour"].null_count():
        raise UnsupportedQuestion("sales_order_hour_missing")
    scoped = eligible_orders(orders, period, coverage=coverage)
    shifted = scoped.filter(pl.col("hour").is_between(start_hour, end_hour, closed="left"))
    return numeric_answer(shifted.height)


def revenue_total(orders: pl.DataFrame, lines: pl.DataFrame, period: Period,
                 *, coverage: Period | None = None) -> dict:
    """Sum already-discounted line totals for eligible orders only."""
    if not {"order_id", "amount"} <= set(lines.columns):
        raise UnsupportedQuestion("sales_line_fields_missing")
    if lines["order_id"].null_count() or lines["amount"].null_count():
        raise UnsupportedQuestion("invalid_sales_line_identity_or_amount")
    allowed = eligible_orders(orders, period, coverage=coverage).select("order_id")
    revenue_lines = lines.join(allowed, on="order_id", how="inner")
    amount = revenue_lines.select(pl.col("amount").sum()).item()
    return numeric_answer(amount or 0, money=True)


def revenue_by_group(orders: pl.DataFrame, lines: pl.DataFrame, period: Period, group: str,
                     *, coverage: Period | None = None) -> dict:
    """Group eligible line revenue; group share uses whole-shop revenue as denominator."""
    if group not in orders.columns:
        raise UnsupportedQuestion("sales_group_field_missing")
    allowed = eligible_orders(orders, period, coverage=coverage)
    joined = lines.join(allowed.select("order_id", group), on="order_id", how="inner")
    if joined["amount"].null_count():
        raise UnsupportedQuestion("invalid_sales_line_amount")
    denominator = joined.select(pl.col("amount").sum()).item() or 0
    grouped = joined.filter(pl.col(group).is_not_null()).group_by(group).agg(pl.col("amount").sum().alias("revenue"))
    rows = []
    for label, amount in grouped.sort(group).iter_rows():
        share = (amount / denominator * 100) if denominator else 0
        rows.append({"group": label, "revenue": int(amount), "share_percent": round(float(share), 2)})
    return {"type": "table", "columns": ["group", "revenue", "share_percent"], "rows": rows}
