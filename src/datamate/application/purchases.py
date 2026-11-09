"""Purchase reporting handlers for the deterministic pipeline."""

from datetime import date
from decimal import Decimal

import polars as pl

from datamate.application.evidence import InsufficientEvidence, UnsupportedQuestion, in_period, numeric_answer
from datamate.application.periods import resolve_period
from datamate.application.plans import Period
from datamate.data.normalize import clean, date_value, number_value, status_value
from datamate.data.sources import Binding, SourceCatalog, bind_sources

_FIELDS = {
    "day": ("thời gian", "ngày nhập", "ngày nhập hàng", "ngày nhập kho", "ngày", "thời điểm"),
    "amount": ("cần trả ncc", "tổng tiền", "tổng tiền nhập", "tổng giá trị nhập", "tong gia tri nhap", "thành tiền", "trị giá", "giá trị"),
}
_OPTIONAL = {
    "status": ("trạng thái", "tình trạng", "tinh trang"),
    "note": ("ghi chú", "ghi chu", "diễn giải"),
    "code": ("mã nhập hàng", "số phiếu", "mã phiếu nhập", "mã nhập"),
}


def purchase_bindings(catalog: SourceCatalog) -> list[Binding]:
    matches = bind_sources(catalog.sources, _FIELDS, ("danhsachnhaphang", "sophieunhap", "phieunhap"), _OPTIONAL)
    if not matches:
        raise InsufficientEvidence("purchase_table_or_columns_missing")
    return matches


def normalize_purchases(frame: pl.DataFrame, source) -> pl.DataFrame:
    year = None
    from datamate.data.sources import sheet_year

    year = sheet_year(source)
    expressions = [date_value("day", year).alias("day"), number_value("amount").alias("amount")]
    if "status" in frame.columns:
        expressions.append(status_value("status").alias("status"))
    elif "note" in frame.columns:
        expressions.append(status_value("note", note=True).alias("status"))
    else:
        expressions.append(pl.lit("completed").alias("status"))
    selected = frame.with_columns(expressions)
    return selected


def purchase_total(frame: pl.DataFrame, period: Period, *, coverage: Period | None = None) -> dict:
    """Sum valid receipt totals for an inclusive period."""
    if frame.height == 0:
        raise InsufficientEvidence("empty_purchase_source")
    if frame["day"].null_count():
        raise UnsupportedQuestion("invalid_source_dates")
    if frame["amount"].null_count():
        raise UnsupportedQuestion("invalid_purchase_amounts")
    available = in_period(frame, period, coverage=coverage)
    valid = available.filter(~pl.col("status").is_in(["cancelled", "returned"]))
    total = valid.select(pl.col("amount").sum()).item()
    return numeric_answer(total or Decimal(0), money=True)


def answer_purchase_total(catalog: SourceCatalog, question: str, as_of: date) -> dict:
    period = resolve_period(question, as_of)
    if period is None:
        raise UnsupportedQuestion("unsupported_purchase_period")
    bindings = purchase_bindings(catalog)
    frames = [catalog.load(binding, normalize_purchases) for binding in bindings]
    frame = pl.concat(frames, how="diagonal_relaxed") if len(frames) > 1 else frames[0]
    coverage = None
    if catalog.description:
        import re

        found = re.search(r"(?:đến hết|tới hết|đến ngày|cập nhật đến)\s+(\d{1,2}/\d{1,2}/\d{4})", catalog.description, re.I)
        if found:
            day, month, year = map(int, found[1].split("/"))
            first_day = frame["day"].min()
            if first_day is not None:
                coverage = Period(first_day, date(year, month, day))
    return purchase_total(frame, period, coverage=coverage)
