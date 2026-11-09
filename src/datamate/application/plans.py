"""Structured requests shared by the router and the rule handlers."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

AnswerType = Literal["number", "percent", "string", "date", "boolean", "list", "table"]


@dataclass(frozen=True)
class Period:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("Period ends before it starts")


@dataclass(frozen=True)
class QuestionPlan:
    intent: str
    answer_type: AnswerType
    period: Period | None = None
    comparison: Period | None = None
    entity: str | None = None
    filters: tuple[tuple[str, str], ...] = ()
    limit: int | None = None


@dataclass(frozen=True)
class Unresolved:
    reason: str
