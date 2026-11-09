"""Gross and net profit use recorded line costs and expense periods."""

import polars as pl

from datamate.application.evidence import InsufficientEvidence, UnsupportedQuestion, numeric_answer
from datamate.application.plans import Period


def gross_profit(lines: pl.DataFrame, period: Period, *, limit: int | None = None) -> dict:
    required = {"day", "amount", "quantity", "cost_per_unit"}
    if not required <= set(lines.columns):
        raise UnsupportedQuestion("profit_line_fields_missing")
    scoped = lines.filter(pl.col("day").is_between(period.start, period.end))
    if scoped["cost_per_unit"].null_count() or scoped["amount"].null_count():
        raise InsufficientEvidence("missing_recorded_cost")
    with_cost = scoped.with_columns((pl.col("quantity") * pl.col("cost_per_unit")).alias("cost"),
                                    (pl.col("amount") - pl.col("quantity") * pl.col("cost_per_unit")).alias("profit"))
    total = with_cost["profit"].sum() or 0
    if "product_id" not in with_cost.columns:
        return numeric_answer(total, money=True)
    by_product = with_cost.group_by("product_id").agg(pl.col("profit").sum().alias("gross_profit"))
    if limit is not None:
        by_product = by_product.sort(["gross_profit", "product_id"], descending=[True, False]).head(limit)
    rows = by_product.sort("product_id").to_dicts()
    return {"type": "table", "columns": ["product_id", "gross_profit"], "rows": rows,
            "total": numeric_answer(total, money=True)["answer"]}


def net_profit(gross: int | float, expenses: pl.DataFrame, period: Period) -> dict:
    if not {"day", "amount"} <= set(expenses.columns):
        raise UnsupportedQuestion("expense_fields_missing")
    rows = expenses.filter(pl.col("day").is_between(period.start, period.end))
    if rows["amount"].null_count():
        raise InsufficientEvidence("incomplete_expense_ledger")
    expense_total = rows["amount"].sum() or 0
    return numeric_answer(gross - expense_total, money=True)
