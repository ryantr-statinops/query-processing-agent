"""Generic order and sales-line bindings shared by retail sectors."""

import polars as pl

from datamate.data.normalize import date_value, grouped_rows, number_value, status_value
from datamate.data.sources import Binding, SourceCatalog, bind_sources, sheet_year

_ORDER_FIELDS = {
    "order_id": ("mã hóa đơn", "số hóa đơn", "mã đơn hàng", "mã đơn", "số đơn"),
    "day": ("thời gian", "ngày tháng", "ngày bán", "ngày đặt", "ngày giao dịch", "ngày"),
}
_ORDER_OPTIONAL = {
    "status": ("trạng thái", "kết quả", "status"),
    "amount": ("tổng tiền hàng", "tổng sau giảm giá", "tổng thanh toán", "tổng tiền"),
    "customer_id": ("mã kh", "mã khách", "mã khách hàng"),
    "customer_name": ("khách hàng", "tên khách", "tên khách hàng"),
    "customer_group": ("nhóm khách hàng", "nhóm khách"),
    "staff_id": ("người bán", "nhân viên", "mã nhân viên", "thợ"),
    "hour": ("giờ", "giờ tạo", "thời gian tạo"),
    "payment_method": ("hình thức thanh toán", "phương thức thanh toán", "thanh toán"),
    "channel": ("kênh bán", "kênh", "nguồn bán"),
}
_LINE_FIELDS = {"order_id": _ORDER_FIELDS["order_id"], "amount": ("thành tiền", "trị giá", "tiền hàng")}
_LINE_OPTIONAL = {
    "line_id": ("stt", "số thứ tự", "mã dòng"),
    "product_id": ("mã hàng", "mã hàng hóa", "mã sản phẩm"),
    "product_name": ("tên hàng", "tên hàng hóa", "sản phẩm", "mặt hàng"),
    "quantity": ("số lượng", "sl"),
    "quantity_base": ("số lượng quy đổi", "số lượng (đvt cơ bản)", "quy ra đv lẻ"),
    "unit": ("đơn vị tính", "đvt"),
    "unit_price": ("đơn giá", "giá bán"),
    "discount": ("giảm giá", "chiết khấu"),
}


def order_bindings(catalog: SourceCatalog) -> list[Binding]:
    return bind_sources(catalog.sources, _ORDER_FIELDS,
                        ("danhsachhoadon", "sobanhang", "banhanghoadon", "donhang"), _ORDER_OPTIONAL)


def line_bindings(catalog: SourceCatalog) -> list[Binding]:
    return bind_sources(catalog.sources, _LINE_FIELDS,
                        ("danhsachhoadonchitiet", "sobanhang", "banhangchitiethoadon", "chitietdon"), _LINE_OPTIONAL)


def _load(catalog: SourceCatalog, bindings: list[Binding], kind: str) -> pl.DataFrame:
    if not bindings:
        raise FileNotFoundError(f"{kind}_source_missing")
    frames = []
    for binding in bindings:
        def normalize(frame, source):
            expressions = []
            if "day" in frame.columns:
                expressions.append(date_value("day", sheet_year(source)).alias("day"))
            if "status" in frame.columns:
                expressions.append(status_value("status").alias("status"))
            if "amount" in frame.columns:
                expressions.append(number_value("amount").alias("amount"))
            if "quantity" in frame.columns:
                expressions.append(number_value("quantity").alias("quantity"))
            if "quantity_base" in frame.columns:
                expressions.append(number_value("quantity_base").alias("quantity_base"))
            return frame.with_columns(expressions) if expressions else frame
        frames.append(catalog.load(binding, normalize))
    return pl.concat(frames, how="diagonal_relaxed") if len(frames) > 1 else frames[0]


def load_orders(catalog: SourceCatalog) -> pl.DataFrame:
    frame = _load(catalog, order_bindings(catalog), "sales_order")
    return grouped_rows(frame, "order_id", tuple(field for field in
                         ("day", "status", "amount", "customer_id", "customer_name", "customer_group", "staff_id")
                         if field in frame.columns))


def load_sales_lines(catalog: SourceCatalog) -> pl.DataFrame:
    frame = _load(catalog, line_bindings(catalog), "sales_line")
    return grouped_rows(frame, "order_id", tuple(field for field in
                         ("line_id", "product_id", "product_name", "amount", "quantity", "quantity_base", "unit", "unit_price")
                         if field in frame.columns))
