"""Receivable balances and collection flows, separated from sales revenue."""

from datetime import date
from decimal import Decimal

import polars as pl

from datamate.application.evidence import UnsupportedQuestion, numeric_answer
from datamate.application.plans import Period


def outstanding_as_of(invoices: pl.DataFrame, payments: pl.DataFrame, as_of: date) -> dict:
    if not {"order_id", "day", "amount"} <= set(invoices.columns) or not {"order_id", "day", "amount"} <= set(payments.columns):
        raise UnsupportedQuestion("receivable_fields_missing")
    bills = invoices.filter(pl.col("day") <= as_of).group_by("order_id").agg(
        pl.col("day").min().alias("day"), pl.col("amount").sum().alias("due"))
    received = payments.filter(pl.col("day") <= as_of)
    if "excluded" in received.columns:
        received = received.filter(~pl.col("excluded").fill_null(False))
    received = received.group_by("order_id").agg(pl.col("amount").sum().alias("paid"))
    balance = bills.join(received, on="order_id", how="left").with_columns(
        (pl.col("due") - pl.col("paid").fill_null(0)).alias("balance"))
    owing = balance.filter(pl.col("balance") > 0)
    total = owing.select(pl.col("balance").sum()).item() or Decimal(0)
    age = (as_of - min(row[0] for row in owing.select("day").iter_rows())).days if owing.height else 0
    return {"type": "table", "columns": ["outstanding", "orders_with_debt", "oldest_debt_days"],
            "rows": [{"outstanding": int(total), "orders_with_debt": owing.height, "oldest_debt_days": age}]}
