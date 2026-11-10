"""Deterministic answers for basic order count and line-revenue questions."""

import polars as pl

from datamate.application.evidence import InsufficientEvidence, UnsupportedQuestion, numeric_answer
from datamate.application.plans import Period
from datamate.application.formatting import table_answer
from datamate.application.sales import (count_orders, count_orders_by_shift, eligible_orders,
                                        revenue_by_group, revenue_total)
from datamate.application.cash import cash_collected
from datamate.application.metrics import period_change
from datamate.data.payments import load_payments
from datamate.data.retail import load_orders, load_sales_lines
from datamate.data.sources import SourceCatalog


def answer_order_count(catalog: SourceCatalog, period: Period) -> dict:
    try:
        return count_orders(load_orders(catalog), period)
    except FileNotFoundError as error:
        raise InsufficientEvidence(str(error)) from error


def answer_order_count_by_shift(catalog: SourceCatalog, period: Period, start_hour: int, end_hour: int) -> dict:
    try:
        return count_orders_by_shift(load_orders(catalog), period, start_hour, end_hour)
    except FileNotFoundError as error:
        raise InsufficientEvidence(str(error)) from error


def answer_revenue(catalog: SourceCatalog, period: Period) -> dict:
    try:
        return revenue_total(load_orders(catalog), load_sales_lines(catalog), period)
    except FileNotFoundError as error:
        raise InsufficientEvidence(str(error)) from error


def answer_product_revenue(catalog: SourceCatalog, question: str, period: Period) -> dict:
    """Sum eligible sales lines for the single product named in the question."""
    from datamate.data.sources import schema_key

    try:
        orders = load_orders(catalog)
        lines = load_sales_lines(catalog)
    except FileNotFoundError as error:
        raise InsufficientEvidence(str(error)) from error
    if "product_name" not in lines.columns:
        raise UnsupportedQuestion("sales_product_name_missing")

    question_key = schema_key(question)
    names = [name for name in lines.get_column("product_name").drop_nulls().unique().to_list()
             if isinstance(name, str) and name.strip()]
    matched = {name for name in names if schema_key(name) in question_key}
    if not matched:
        raise UnsupportedQuestion("product_name_not_found")
    longest = max(len(schema_key(name)) for name in matched)
    best = {name for name in matched if len(schema_key(name)) == longest}
    keys = {schema_key(name) for name in best}
    if len(keys) != 1:
        raise UnsupportedQuestion("ambiguous_product_name")
    product_key = next(iter(keys))
    display_name = next(name for name in best if schema_key(name) == product_key)

    product_lines = lines.filter(pl.col("product_name").cast(pl.String).str.to_lowercase()
                                 == display_name.casefold())
    if product_lines["order_id"].null_count() or product_lines["amount"].null_count():
        raise UnsupportedQuestion("invalid_product_sales_lines")
    allowed = eligible_orders(orders, period).select("order_id")
    selected = product_lines.join(allowed, on="order_id", how="inner")
    total = selected.select(pl.col("amount").sum()).item()
    return numeric_answer(total or 0, money=True)


def answer_revenue_by_group(catalog: SourceCatalog, period: Period, group: str) -> dict:
    try:
        result = revenue_by_group(load_orders(catalog), load_sales_lines(catalog), period, group)
    except FileNotFoundError as error:
        raise InsufficientEvidence(str(error)) from error
    return table_answer(result["columns"], result["rows"])


def answer_cash_by_shift(catalog: SourceCatalog, period: Period, shift: str) -> dict:
    try:
        return cash_collected(load_payments(catalog), period, shift)
    except FileNotFoundError as error:
        raise InsufficientEvidence(str(error)) from error


def answer_revenue_change(catalog: SourceCatalog, current: Period, previous: Period, metric: str) -> dict:
    current_total = answer_revenue(catalog, current)["answer"]
    previous_total = answer_revenue(catalog, previous)["answer"]
    change = period_change(current_total, previous_total)["rows"][0]
    if metric == "percent":
        growth = change["growth_percent"]
        if growth is None:
            raise InsufficientEvidence("zero_comparison_denominator")
        return numeric_answer(growth, percent=True)
    if metric == "difference":
        return numeric_answer(change["difference"], money=True)
    raise InsufficientEvidence("unsupported_revenue_change_metric")
