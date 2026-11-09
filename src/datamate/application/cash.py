"""Cash receipt calculations use the timestamp of each collection."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion, in_period, numeric_answer
from datamate.application.periods import shift_hours
from datamate.application.plans import Period


def cash_collected(payments: pl.DataFrame, period: Period, shift: str,
                   *, coverage: Period | None = None) -> dict:
    required = {"day", "hour", "amount"}
    if not required <= set(payments.columns):
        raise UnsupportedQuestion("payment_fields_missing")
    if payments["amount"].null_count() or payments["hour"].null_count():
        raise UnsupportedQuestion("invalid_payment_amount_or_time")
    start, end = shift_hours(shift)
    scoped = in_period(payments, period, coverage=coverage)
    value = scoped.filter((pl.col("hour") >= start) & (pl.col("hour") < end)).select(pl.col("amount").sum()).item()
    return numeric_answer(value or 0, money=True)
