"""Phone-shop reporting separates sales, payable and trade-in value."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion


def phone_sale_totals(orders: pl.DataFrame) -> dict:
    required = {"order_id", "status", "revenue", "customer_payable", "trade_in_value"}
    if not required <= set(orders.columns):
        raise UnsupportedQuestion("phone_sale_fields_missing")
    valid = orders.filter(~pl.col("status").str.to_lowercase().is_in(["cancelled", "returned"]))
    totals = valid.select(pl.col("revenue").sum().alias("revenue"),
                          pl.col("customer_payable").sum().alias("customer_payable"),
                          pl.col("trade_in_value").sum().alias("trade_in_value")).row(0, named=True)
    row = {key: int(value or 0) for key, value in totals.items()}
    return {"type": "table", "columns": list(row), "rows": [row]}
