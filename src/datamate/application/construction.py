"""Construction delivery batches are counted by the actual delivery date."""

import polars as pl

from datamate.application.evidence import UnsupportedQuestion, numeric_answer


def count_deliveries(deliveries: pl.DataFrame, as_of) -> dict:
    if not {"delivery_id", "delivery_day", "status"} <= set(deliveries.columns):
        raise UnsupportedQuestion("delivery_fields_missing")
    arrived = deliveries.filter((pl.col("delivery_day") <= as_of)
                                & pl.col("status").str.to_lowercase().is_in(["delivered", "complete", "completed"]))
    return numeric_answer(arrived["delivery_id"].n_unique())
