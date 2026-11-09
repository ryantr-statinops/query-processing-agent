"""Common ratio and period-change metrics with defined zero-denominator behavior."""

from decimal import Decimal, ROUND_HALF_UP

from datamate.application.evidence import InsufficientEvidence, numeric_answer


def rate(numerator: int | float | Decimal, denominator: int | float | Decimal) -> dict:
    bottom = Decimal(str(denominator))
    if bottom == 0:
        raise InsufficientEvidence("zero_denominator")
    return numeric_answer(Decimal(str(numerator)) / bottom * 100, percent=True)


def period_change(current: int | float | Decimal, previous: int | float | Decimal) -> dict:
    now, before = Decimal(str(current)), Decimal(str(previous))
    change = now - before
    if before == 0:
        growth = None
    else:
        growth = ((change / abs(before)) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"type": "table", "columns": ["difference", "growth_percent"],
            "rows": [{"difference": int(change) if change == change.to_integral_value() else float(change),
                      "growth_percent": float(growth) if growth is not None else None}]}


def average(total: int | float | Decimal, count: int) -> dict:
    if count <= 0:
        raise InsufficientEvidence("empty_average_denominator")
    return numeric_answer(Decimal(str(total)) / count, money=True)
