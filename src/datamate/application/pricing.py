"""Selling-price reporting separates list prices from discounted revenue."""

import polars as pl

from datamate.application.evidence import InsufficientEvidence, UnsupportedQuestion, numeric_answer
from datamate.application.plans import Period


def average_list_price(lines: pl.DataFrame, period: Period) -> dict:
    if not {"day", "unit_price", "quantity_base"} <= set(lines.columns):
        raise UnsupportedQuestion("selling_price_fields_missing")
    scoped = lines.filter(pl.col("day").is_between(period.start, period.end))
    quantity = scoped["quantity_base"].sum()
    if not quantity:
        raise InsufficientEvidence("no_selling_price_evidence")
    return numeric_answer((scoped["unit_price"] * scoped["quantity_base"]).sum() / quantity, money=True)


def price_increase_effect(previous: pl.DataFrame, current: pl.DataFrame) -> dict:
    required = {"unit_price", "quantity_base"}
    if not required <= set(previous.columns) or not required <= set(current.columns):
        raise UnsupportedQuestion("price_change_fields_missing")
    old_qty, new_qty = previous["quantity_base"].sum(), current["quantity_base"].sum()
    if not old_qty or not new_qty:
        raise InsufficientEvidence("no_comparable_price_window")
    old_price = (previous["unit_price"] * previous["quantity_base"]).sum() / old_qty
    new_price = (current["unit_price"] * current["quantity_base"]).sum() / new_qty
    return numeric_answer((new_price - old_price) * new_qty, money=True)
