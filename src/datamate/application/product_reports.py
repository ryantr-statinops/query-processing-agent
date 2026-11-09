"""Product ranking based on base-unit sales and distinct qualifying orders."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion
from datamate.application.plans import Period
from datamate.application.sales import eligible_orders


def rank_products(orders: pl.DataFrame, lines: pl.DataFrame, period: Period, *, metric: str = "quantity",
                  limit: int = 10, coverage: Period | None = None) -> dict:
    required = {"order_id", "product_id", "quantity_base"}
    if not required <= set(lines.columns) or limit < 1:
        raise UnsupportedQuestion("product_ranking_fields_missing")
    if lines["quantity_base"].null_count():
        raise UnsupportedQuestion("invalid_product_quantity")
    allowed = eligible_orders(orders, period, coverage=coverage).select("order_id")
    sale_lines = lines.join(allowed, on="order_id", how="inner")
    if "product_name" in sale_lines.columns:
        service = pl.col("product_name").cast(pl.String).str.to_lowercase().str.contains("phí phục vụ")
        sale_lines = sale_lines.filter(~service.fill_null(False))
    if metric == "quantity":
        ranked = sale_lines.group_by("product_id").agg(pl.col("quantity_base").sum().alias("value"))
    elif metric == "orders":
        ranked = sale_lines.group_by("product_id").agg(pl.col("order_id").n_unique().alias("value"))
    else:
        raise UnsupportedQuestion("unsupported_product_ranking_metric")
    if "product_name" in sale_lines.columns:
        names = sale_lines.group_by("product_id").agg(pl.col("product_name").first())
        ranked = ranked.join(names, on="product_id", how="left")
    rows = ranked.sort(["value", "product_id"], descending=[True, False]).head(limit).to_dicts()
    return {"type": "table", "columns": list(rows[0]) if rows else ["product_id", "value"], "rows": rows}
