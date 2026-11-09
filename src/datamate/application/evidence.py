"""Separate unsupported reasoning from confirmed missing evidence."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import polars as pl

from datamate.application.plans import Period


class UnsupportedQuestion(ValueError):
    """The pipeline could not establish a reliable plan or binding."""


class InsufficientEvidence(ValueError):
    """The identified source cannot support an otherwise resolved plan."""


def in_period(frame: pl.DataFrame, period: Period, *, coverage: Period | None = None,
              column: str = "day") -> pl.DataFrame:
    if frame[column].null_count():
        raise UnsupportedQuestion("invalid_source_dates")
    if coverage is None:
        start, end = frame.select(pl.col(column).min().alias("start"), pl.col(column).max().alias("end")).row(0)
        if not isinstance(start, date) or not isinstance(end, date):
            raise InsufficientEvidence("missing_date_coverage")
        coverage = Period(start, end)
    if period.end < coverage.start or period.start > coverage.end:
        raise InsufficientEvidence("period_outside_data_coverage")
    return frame.filter(pl.col(column).is_between(period.start, period.end))


def numeric_answer(value: Decimal | int | float, *, percent: bool = False, money: bool = False) -> dict[str, Any]:
    amount = Decimal(str(value))
    if not amount.is_finite():
        raise InsufficientEvidence("undefined_number")
    if percent or money:
        amount = amount.quantize(Decimal("0.01") if percent else Decimal(1), rounding=ROUND_HALF_UP)
    return {"type": "percent" if percent else "number",
            "answer": int(amount) if amount == amount.to_integral_value() else float(amount)}
