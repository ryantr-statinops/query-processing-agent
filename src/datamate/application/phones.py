"""Phone-shop reporting separates sales, payable and trade-in value."""

import re

import polars as pl

from datamate.application.evidence import UnsupportedQuestion
from datamate.application.plans import Period


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


def installment_balances(schedule: pl.DataFrame, payments: pl.DataFrame, as_of) -> dict:
    if not {"installment_id", "due_day", "amount"} <= set(schedule.columns):
        raise UnsupportedQuestion("installment_schedule_fields_missing")
    if not {"installment_id", "paid_day", "amount"} <= set(payments.columns):
        raise UnsupportedQuestion("installment_payment_fields_missing")
    paid = payments.filter(pl.col("paid_day") <= as_of).group_by("installment_id").agg(
        pl.col("amount").sum().alias("paid"))
    balances = schedule.join(paid, on="installment_id", how="left").with_columns(
        (pl.col("amount") - pl.col("paid").fill_null(0)).clip(lower_bound=0).alias("balance"))
    overdue = balances.filter((pl.col("due_day") < as_of) & (pl.col("balance") > 0))
    outstanding = balances.filter(pl.col("balance") > 0)
    return {"type": "table", "columns": ["outstanding", "overdue", "overdue_installments"],
            "rows": [{"outstanding": int(outstanding["balance"].sum() or 0),
                      "overdue": int(overdue["balance"].sum() or 0), "overdue_installments": overdue.height}]}


def phone_model(name: str) -> tuple[str, str | None]:
    capacity = re.search(r"(?<!\d)(\d{2,4})\s*(?:gb|g)\b", name, re.IGNORECASE)
    clean = name
    if capacity:
        clean = clean[:capacity.start()] + clean[capacity.end():]
    clean = re.sub(r"\b(?:4g|5g|lte)\b", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip(" -_/")
    return clean.casefold(), f"{capacity[1]}GB" if capacity else None


def warranty_rate_by_quarter(sales: pl.DataFrame, claims: pl.DataFrame, period: Period) -> dict:
    if not {"imei", "sale_day"} <= set(sales.columns) or not {"imei", "claim_day"} <= set(claims.columns):
        raise UnsupportedQuestion("phone_warranty_fields_missing")
    sold = sales.filter(pl.col("sale_day").is_between(period.start, period.end))["imei"].n_unique()
    if not sold:
        raise UnsupportedQuestion("no_quarter_phone_sales")
    claimed = claims.filter(pl.col("claim_day").is_between(period.start, period.end))["imei"].n_unique()
    return {"type": "percent", "answer": round(claimed / sold * 100, 2)}
