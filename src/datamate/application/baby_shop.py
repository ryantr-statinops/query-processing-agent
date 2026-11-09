"""Baby-shop invoice totals include supported voucher, points and shipping fields."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion


def invoice_totals(orders: pl.DataFrame) -> pl.DataFrame:
    required = {"order_id", "status", "gross", "order_discount", "voucher", "points", "shipping"}
    if not required <= set(orders.columns):
        raise UnsupportedQuestion("baby_invoice_fields_missing")
    valid = orders.filter(~pl.col("status").str.to_lowercase().is_in(["cancelled", "returned"]))
    return valid.with_columns((pl.col("gross") - pl.col("order_discount") - pl.col("voucher")
                               - pl.col("points") + pl.col("shipping")).alias("customer_payable"))
