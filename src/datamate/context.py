"""Small question-specific excerpts from shared DataMate context files."""

from __future__ import annotations

import csv
import datetime as dt
import functools
import pathlib
import re
from typing import Any


@functools.lru_cache(maxsize=16)
def _calendar_rows(path: str) -> tuple[dict[str, str], ...]:
    try:
        with pathlib.Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
            return tuple(csv.DictReader(stream))
    except OSError:
        return ()


def calendar_context(calendar_path: pathlib.Path, question: dict[str, Any], limit: int = 2500) -> str:
    if not calendar_path.is_file():
        return ""
    try:
        as_of = dt.date.fromisoformat(str(question.get("as_of_date", ""))[:10])
    except ValueError:
        return ""
    rows = _calendar_rows(str(calendar_path.resolve()))

    question_text = str(question.get("question", "")).casefold()
    target_months: set[tuple[int, int]] = {(as_of.year, as_of.month)}
    for month, year in re.findall(r"tháng\s*(\d{1,2})(?:\s*năm\s*(\d{4}))?", question_text):
        month_number = int(month)
        year_number = int(year) if year else as_of.year
        if 1 <= month_number <= 12:
            target_months.add((year_number, month_number))
    if any(token in question_text for token in ("tháng trước", "tháng vừa rồi", "tháng liền trước")):
        previous = as_of.replace(day=1) - dt.timedelta(days=1)
        target_months.add((previous.year, previous.month))
    if any(token in question_text for token in ("tháng sau", "tháng tới", "tháng tiếp theo")):
        next_month = (as_of.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        target_months.add((next_month.year, next_month.month))

    selected: list[dict[str, str]] = []
    for row in rows:
        raw_date = row.get("date", "")
        try:
            day = dt.date.fromisoformat(raw_date[:10])
        except ValueError:
            continue
        if (day.year, day.month) in target_months or abs((day - as_of).days) <= 3:
            selected.append(row)
    compact = "\n".join(
        ",".join(f"{key}={value}" for key, value in row.items()) for row in selected[:70]
    )
    return compact[:limit]
