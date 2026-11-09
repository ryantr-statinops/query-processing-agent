"""Grouped development metrics for the deterministic question agent."""

from collections import defaultdict
from time import perf_counter, perf_counter_ns

import numpy as np

from datamate.evaluation.labels import label_match, pa_reward


def evaluate_grouped(agent, questions: list[dict], references: dict[str, dict], group_key: str = "business_id",
                     progress=None):
    rows = []
    started_all = perf_counter()
    for question in questions:
        started = perf_counter_ns()
        answer, trace = agent.answer(question)
        elapsed_ms = (perf_counter_ns() - started) / 1_000_000
        reference = references[question["id"]]
        rows.append({"id": question["id"], group_key: question[group_key], "answer": answer,
                     "correct": label_match(answer, reference), "pa_reward": pa_reward(answer, reference),
                     "elapsed_ms": elapsed_ms, "trace": trace})
        if progress is not None and (len(rows) % 50 == 0 or len(rows) == len(questions)):
            progress(len(rows), len(questions), perf_counter() - started_all)
    groups = defaultdict(list)
    for row in rows:
        groups[row[group_key]].append(row)
    return {"overall": _metrics(rows), "groups": {key: _metrics(values) for key, values in sorted(groups.items())},
            "rows": rows}


def _metrics(rows: list[dict]) -> dict:
    latencies = [row["elapsed_ms"] for row in rows]
    attempted = sum(row["answer"].get("type") != "abstain" for row in rows)
    return {"questions": len(rows), "correct": sum(row["correct"] for row in rows),
            "wrong": sum(not row["correct"] and row["answer"].get("type") != "abstain" for row in rows),
            "abstain": len(rows) - attempted, "coverage": attempted / len(rows) if rows else 0.0,
            "pa_total": sum(row["pa_reward"] for row in rows),
            "pa_average": sum(row["pa_reward"] for row in rows) / len(rows) if rows else 0.0,
            "latency_ms": {"p50": float(np.percentile(latencies, 50)) if latencies else None,
                           "p95": float(np.percentile(latencies, 95)) if latencies else None}}
