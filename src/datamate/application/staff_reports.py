"""Staff and high-traffic rankings use valid sales and distinct orders."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion
from datamate.application.plans import Period
from datamate.application.sales import eligible_orders


def rank_staff(orders: pl.DataFrame, period: Period, metric: str, *, limit: int = 10) -> dict:
    if not {"staff_id", "order_id", "day", "status", "amount"} <= set(orders.columns):
        raise UnsupportedQuestion("staff_fields_missing")
    valid = eligible_orders(orders.filter(pl.col("staff_id").is_not_null()), period)
    grouped = valid.group_by("staff_id").agg(pl.col("amount").sum().alias("revenue"),
                                              pl.col("day").n_unique().alias("working_days"))
    field = {"revenue": "revenue", "days": "working_days"}.get(metric)
    if field is None or limit < 1:
        raise UnsupportedQuestion("unsupported_staff_ranking_metric")
    rows = grouped.sort([field, "staff_id"], descending=[True, False]).head(limit).to_dicts()
    return {"type": "table", "columns": list(rows[0]) if rows else ["staff_id", field], "rows": rows}


def busiest_windows(orders: pl.DataFrame, period: Period, *, by: str = "day", limit: int = 10) -> dict:
    if not {"order_id", "day", "status"} <= set(orders.columns) or limit < 1:
        raise UnsupportedQuestion("traffic_fields_missing")
    valid = eligible_orders(orders, period)
    if by == "day":
        group = "day"
    elif by == "hour" and "hour" in valid.columns:
        group = "hour"
    else:
        raise UnsupportedQuestion("unsupported_traffic_window")
    result = valid.group_by(group).agg(pl.col("order_id").n_unique().alias("orders"))
    rows = result.sort(["orders", group], descending=[True, False]).head(limit).to_dicts()
    return {"type": "table", "columns": list(rows[0]) if rows else [group, "orders"], "rows": rows}
