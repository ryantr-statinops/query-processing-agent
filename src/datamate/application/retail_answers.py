"""Deterministic answers for basic order count and line-revenue questions."""

from datamate.application.evidence import InsufficientEvidence
from datamate.application.plans import Period
from datamate.application.sales import count_orders, revenue_total
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
