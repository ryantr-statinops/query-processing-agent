"""Resolve Vietnamese reporting periods using inclusive date bounds."""

from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path
import re

from datamate.application.plans import Period
from datamate.data.calendar import _calendar_rows

_DATE = r"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}(?:/\d{4})?)"
_RANGE = re.compile(r"\btừ\s+(?:ngày\s+)?" + _DATE + r"\s*(?:đến|tới|[-–])\s*(?:ngày\s+)?" + _DATE)
_DAY = re.compile(r"\bngày\s+" + _DATE)
_MONTH = re.compile(r"\btháng\s*(\d{1,2})(?:\s*(?:/|năm)\s*(\d{4}))?(?![\d/])")
_QUARTER = re.compile(r"\bquý\s*([1-4])(?:\s*(?:/|năm)\s*(\d{4}))?\b")


def month_period(year: int, month: int) -> Period:
    return Period(date(year, month, 1), date(year, month, monthrange(year, month)[1]))


def _day(value: str, as_of: date) -> date:
    if "-" in value:
        return date.fromisoformat(value)
    day, month, *year = map(int, value.split("/"))
    return date(year[0] if year else as_of.year, month, day)


def explicit_period(text: str, as_of: date) -> Period | None:
    try:
        if match := _RANGE.search(text):
            return Period(_day(match[1], as_of), _day(match[2], as_of))
        if match := _DAY.search(text):
            day = _day(match[1], as_of)
            return Period(day, day)
        if match := _MONTH.search(text):
            month = int(match[1])
            year = int(match[2]) if match[2] else as_of.year - (month > as_of.month)
            return month_period(year, month)
        if match := _QUARTER.search(text):
            month = 3 * int(match[1]) - 2
            year = int(match[2]) if match[2] else as_of.year - (month > as_of.month)
            return Period(date(year, month, 1), month_period(year, month + 2).end)
    except ValueError:
        return None
    return None


def relative_period(text: str, as_of: date) -> Period | None:
    one_day = timedelta(days=1)
    if match := re.search(r"\b(\d{1,4})\s*ngày\s*(?:gần nhất|qua|vừa qua)\b", text):
        count = int(match[1])
        return Period(as_of - (count - 1) * one_day, as_of) if count else None
    if any(phrase in text for phrase in ("từ đầu năm", "đầu năm tới nay", "đầu năm đến nay")):
        return Period(as_of.replace(month=1, day=1), as_of)
    if "tuần này" in text:
        return Period(as_of - as_of.weekday() * one_day, as_of)
    if any(phrase in text for phrase in ("tuần trước", "tuần rồi", "tuần vừa rồi")):
        monday = as_of - (as_of.weekday() + 7) * one_day
        return Period(monday, monday + 6 * one_day)
    if "tháng này" in text:
        return Period(as_of.replace(day=1), as_of)
    if any(phrase in text for phrase in ("tháng trước", "tháng rồi", "tháng vừa rồi")):
        previous = as_of.replace(day=1) - one_day
        return month_period(previous.year, previous.month)
    if "hôm qua" in text:
        return Period(as_of - one_day, as_of - one_day)
    if "hôm nay" in text:
        return Period(as_of, as_of)
    return None


def resolve_period(text: str, as_of: date) -> Period | None:
    return explicit_period(text, as_of) or relative_period(text, as_of)
