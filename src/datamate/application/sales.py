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
