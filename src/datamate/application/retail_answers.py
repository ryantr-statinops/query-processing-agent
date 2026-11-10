"""Deterministic answers for basic order count and line-revenue questions."""

import polars as pl

from datamate.application.evidence import InsufficientEvidence, UnsupportedQuestion, numeric_answer
from datamate.application.plans import Period
from datamate.application.sales import count_orders, eligible_orders, revenue_total
from datamate.data.retail import load_orders, load_sales_lines
from datamate.data.sources import SourceCatalog


def answer_order_count(catalog: SourceCatalog, period: Period) -> dict:
    try:
        return count_orders(load_orders(catalog), period)
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
