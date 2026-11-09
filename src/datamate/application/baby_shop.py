"""Baby-shop invoice totals include supported voucher, points and shipping fields."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion
from datamate.application.plans import Period


def invoice_totals(orders: pl.DataFrame) -> pl.DataFrame:
    required = {"order_id", "status", "gross", "order_discount", "voucher", "points", "shipping"}
    if not required <= set(orders.columns):
        raise UnsupportedQuestion("baby_invoice_fields_missing")
    valid = orders.filter(~pl.col("status").str.to_lowercase().is_in(["cancelled", "returned"]))
    return valid.with_columns((pl.col("gross") - pl.col("order_discount") - pl.col("voucher")
                               - pl.col("points") + pl.col("shipping")).alias("customer_payable"))


def product_sizes(products: pl.DataFrame) -> pl.DataFrame:
    size_fields = [field for field in ("size_number", "size_label") if field in products.columns]
    if "product_id" not in products.columns or not size_fields:
        raise UnsupportedQuestion("baby_product_size_fields_missing")
    exprs = [pl.col(field).cast(pl.String).str.strip_chars().replace("", None) for field in size_fields]
    return products.with_columns(pl.coalesce(exprs).alias("size"))


def member_summary(members: pl.DataFrame, orders: pl.DataFrame, period: Period) -> dict:
    if not {"customer_id", "registered_day"} <= set(members.columns) or not {"customer_id", "status"} <= set(orders.columns):
        raise UnsupportedQuestion("baby_member_fields_missing")
    bought = orders.filter(~pl.col("status").str.to_lowercase().is_in(["cancelled", "returned"]))
    buyers = set(bought["customer_id"].drop_nulls().to_list())
    registered = members.filter(pl.col("registered_day").is_between(period.start, period.end))
    new_buyer_count = registered.filter(pl.col("customer_id").is_in(buyers)).height
    never_bought = members.filter(~pl.col("customer_id").is_in(buyers)).height
    return {"type": "table", "columns": ["registered_members", "new_members_with_sales", "never_bought"],
            "rows": [{"registered_members": registered.height, "new_members_with_sales": new_buyer_count,
                      "never_bought": never_bought}]}
