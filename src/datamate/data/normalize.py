"""Normalize source values in memory while preserving original identifiers."""

import polars as pl


def clean(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.String).str.strip_chars().replace("", None)


def date_value(column: str, year: int | None = None) -> pl.Expr:
    text = clean(column).str.extract(r"^(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)", 1)
    if year:
        text = pl.when(text.str.contains(r"^\d{1,2}[/-]\d{1,2}$")).then(text + f"/{year}").otherwise(text)
    return pl.coalesce(text.str.to_date(fmt, strict=False) for fmt in
                       ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"))


def number_value(column: str) -> pl.Expr:
    text = clean(column).str.replace_all(r"\s|₫|đ|VND", "").str.replace(r"_\d+$", "")
    multiplier = (pl.when(text.str.contains(r"(?i)(?:tr|triệu)$")).then(pl.lit(1_000_000))
                  .when(text.str.contains(r"(?i)(?:k|nghìn)$")).then(pl.lit(1_000))
                  .otherwise(pl.lit(1)))
    text = text.str.replace(r"(?i)(?:triệu|nghìn|tr|k)$", "")
    vietnamese = text.str.contains(r"^-?\d{1,3}(?:\.\d{3})+(?:,\d+)?$")
    decimal_comma = text.str.contains(r"^-?\d+,\d{1,2}$") | ((multiplier > 1) & text.str.contains(r"^-?\d+,\d+$"))
    normalized = (
        pl.when(vietnamese).then(text.str.replace_all(r"\.", "").str.replace(",", "."))
        .when(decimal_comma).then(text.str.replace(",", "."))
        .otherwise(text.str.replace_all(",", ""))
    )
    return (normalized.cast(pl.Decimal(28, 6), strict=False) * multiplier.cast(pl.Decimal(28, 6)))


def hour_value(column: str) -> pl.Expr:
    text = clean(column)
    from_time = text.str.extract(r"(?:^|[ T])(\d{1,2})(?::\d{2}){1,2}", 1).cast(pl.Int64, strict=False)
    numeric = text.cast(pl.Int64, strict=False)
    value = pl.coalesce(from_time, numeric)
    return pl.when(value.is_between(0, 23, closed="both")).then(value).otherwise(None)


def status_value(column: str, *, note: bool = False) -> pl.Expr:
    value = clean(column).str.to_lowercase()
    return (
        pl.when(value.str.contains(r"(?:^|\W)hu[ỷy](?:$|\W)|hủy|cancel|không giao được|giao thất bại")).then(pl.lit("cancelled"))
        .when(value.str.contains(r"trả hàng|trả lại|hoàn hàng|hoàn trả|hàng trả về|đã trả|đổi trả|returned")).then(pl.lit("returned"))
        .when(value.str.contains(r"đang giao|đang gửi|đang giao dịch|đang vận chuyển|chờ giao|đang xử lý|shipping")).then(pl.lit("shipping"))
        .when(value.str.contains(r"hoàn thành|hoàn tất|thành công|đã lấy|xong|đã nhập|đã giao|complete|delivered|^ok$|^ok\b")).then(pl.lit("completed"))
        .otherwise(pl.lit("completed") if note else None)
    )


def grouped_rows(frame: pl.DataFrame, key: str, fields: tuple[str, ...]) -> pl.DataFrame:
    """Restore export fields for contiguous lines of each identified order."""
    selected = [field for field in fields if field in frame.columns and field != key]
    frame = frame.with_columns(clean(key).forward_fill().alias(key))
    if selected:
        expressions = []
        for field in selected:
            value = pl.col(field)
            if frame.schema[field] == pl.String:
                value = value.str.strip_chars().replace("", None)
            expressions.append(value.forward_fill().over(key).backward_fill().over(key).alias(field))
        frame = frame.with_columns(expressions)
    return frame.unique(maintain_order=True)
