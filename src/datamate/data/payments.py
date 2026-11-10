"""Schema-based loading for recorded payment and collection events."""

import polars as pl

from datamate.data.normalize import date_value, hour_value, number_value
from datamate.data.sources import Binding, SourceCatalog, bind_sources, sheet_year

_PAYMENT_FIELDS = {
    "timestamp": ("thời gian thu", "thời điểm thu", "thời điểm", "ngày thu tiền", "ngày thu",
                  "ngày thanh toán", "ngày giao dịch"),
    "amount": ("số tiền thu", "tiền thu", "giá trị", "số tiền", "tiền", "amount"),
}
_PAYMENT_OPTIONAL = {
    "hour": ("giờ thu", "giờ nhận", "giờ"),
    "order_id": ("mã đơn hàng", "số hóa đơn", "mã hóa đơn", "số hđ", "mã giao dịch", "mã đơn"),
    "collection_id": ("mã phiếu thu", "mã gd", "mã giao dịch thu"),
}


def payment_bindings(catalog: SourceCatalog) -> list[Binding]:
    return bind_sources(catalog.sources, _PAYMENT_FIELDS,
                        ("thanhtoan", "banhangphieuthu", "phieuthu", "lichsuthanhtoan"), _PAYMENT_OPTIONAL)


def load_payments(catalog: SourceCatalog) -> pl.DataFrame:
    bindings = payment_bindings(catalog)
    if not bindings:
        raise FileNotFoundError("payment_source_missing")
    frames = []
    for binding in bindings:
        def normalize(frame: pl.DataFrame, source) -> pl.DataFrame:
            hour_source = "hour" if "hour" in frame.columns else "timestamp"
            return frame.with_columns(
                date_value("timestamp", sheet_year(source)).alias("day"),
                hour_value(hour_source).alias("hour"),
                number_value("amount").alias("amount"),
            )

        frames.append(catalog.load(binding, normalize))
    return pl.concat(frames, how="diagonal_relaxed") if len(frames) > 1 else frames[0]
