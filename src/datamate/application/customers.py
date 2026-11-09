"""Resolve customer identity from the fields actually present on sales orders."""

import unicodedata

import polars as pl

from datamate.application.evidence import UnsupportedQuestion
from datamate.application.plans import Period
from datamate.application.sales import eligible_orders


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


def rank_customers(orders: pl.DataFrame, period: Period, metric: str, *, limit: int = 10,
                  minimum_orders: int = 3) -> dict:
    required = {"customer_key", "order_id", "day", "status", "amount"}
    if not required <= set(orders.columns) or limit < 1:
        raise UnsupportedQuestion("customer_ranking_fields_missing")
    identified = orders.filter(pl.col("customer_key").is_not_null())
    valid = eligible_orders(identified, period).group_by("customer_key").agg(
        pl.col("order_id").n_unique().alias("orders"), pl.col("day").n_unique().alias("buying_days"),
        pl.col("amount").sum().alias("revenue"), pl.col("amount").mean().alias("average_order_value"))
    valid = valid.filter(pl.col("orders") >= minimum_orders)
    if metric == "revenue":
        ranked, value = valid, "revenue"
    elif metric == "buying_days":
        ranked, value = valid, "buying_days"
    elif metric == "average_order":
        ranked, value = valid, "average_order_value"
    elif metric == "cancelled_orders":
        cancelled = identified.filter(pl.col("day").is_between(period.start, period.end)
                                      & (pl.col("status").str.to_lowercase() == "cancelled"))
        cancellations = cancelled.group_by("customer_key").agg(pl.col("order_id").n_unique().alias("cancelled_orders"))
        ranked, value = valid.join(cancellations, on="customer_key", how="left").with_columns(
            pl.col("cancelled_orders").fill_null(0)), "cancelled_orders"
    else:
        raise UnsupportedQuestion("unsupported_customer_ranking_metric")
    rows = ranked.sort([value, "customer_key"], descending=[True, False]).head(limit).to_dicts()
    return {"type": "table", "columns": list(rows[0]) if rows else ["customer_key", value], "rows": rows}
