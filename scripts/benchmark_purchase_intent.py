"""Compare two offline intent routers on a fixed development-only purchase task."""

from __future__ import annotations

import argparse
import calendar
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter_ns

# Polars initializes its thread pool on import.
if __name__ == "__main__":
    os.environ["POLARS_MAX_THREADS"] = "1"

import numpy as np
import polars as pl
from sklearn.metrics.pairwise import cosine_similarity
from threadpoolctl import threadpool_limits

from datamate.application.purchases import answer_purchase_total
from datamate.data.sources import SourceCatalog
from datamate.evaluation.labels import label_match
from datamate.ranking.intents import IntentIndex


ROOT = Path(__file__).resolve().parents[1]
BUSINESSES = ("biz_108", "biz_119", "biz_128")
PURCHASE = "purchase_total"
PROTOTYPES = (
    ("revenue", "tổng doanh thu tiền bán hàng trong tháng"),
    ("order_count", "đếm số đơn hàng hóa đơn bán trong kỳ"),
    ("inventory", "số lượng hàng còn lại tồn kho cuối kỳ"),
    ("ranking", "mặt hàng hoặc nhà cung cấp nào đứng đầu xếp hạng cao nhất"),
    (PURCHASE, "tổng số tiền nhập hàng trong tháng"),
    (PURCHASE, "tổng giá trị các phiếu nhập hàng trong kỳ"),
)
MONTH = re.compile(r"\btháng\s+(\d{1,2})\s*/\s*(\d{4})\b", re.IGNORECASE)
THIS_MONTH = re.compile(r"\btháng\s+này\b", re.IGNORECASE)


def elapsed_ms(start):
    return (perf_counter_ns() - start) / 1_000_000


def read_jsonl(path):
    with path.open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def month_bounds(text, as_of):
    explicit = MONTH.findall(text)
    relative = THIS_MONTH.findall(text)
    if len(explicit) + len(relative) != 1:
        return None
    if relative:
        return as_of.replace(day=1), as_of
    month, year = map(int, explicit[0])
    if not (1 <= month <= 12 and 1 <= year <= 9999):
        return None
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def select_questions(train, manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not set(BUSINESSES) <= set(manifest["development_businesses"]):
        raise ValueError("Benchmark businesses must belong to the development split")
    questions = read_jsonl(train / "questions.jsonl")
    sample = []
    for business, expected in zip(BUSINESSES, (3, 4, 5)):
        rows = sorted((q for q in questions if q["business_id"] == business), key=lambda q: q["id"])
        # This predicate builds the fixed gold sample only. The routers never see it.
        positive = [q for q in rows if any(term in q["question"].casefold() for term in ("nhập hàng", "phiếu nhập"))
                    and month_bounds(q["question"], date.fromisoformat(q["as_of_date"]))]
        if len(positive) != expected:
            raise ValueError(f"Unexpected positive sample size for {business}: {len(positive)}")
        negative = [q for q in rows if q not in positive][:6]
        if len(negative) != 6:
            raise ValueError(f"Not enough out-of-scope questions for {business}")
        sample.extend({**q, "in_scope": q in positive} for q in positive + negative)
    return sample


def normalize_receipts(frame):
    return frame.select(
        pl.col("Thời gian").cast(pl.String).str.strip_chars().str.strptime(pl.Date, "%d/%m/%Y").alias("day"),
        pl.col("Cần trả NCC").cast(pl.String).str.strip_chars().str.replace_all(",", "").cast(pl.Int64).alias("amount"),
        pl.col("Trạng thái").cast(pl.String).str.to_lowercase().str.contains("huỷ|hủy").fill_null(False).alias("cancelled"),
    )


def sum_receipts(frame, bounds):
    start, end = bounds
    return frame.filter(pl.col("day").is_between(start, end) & ~pl.col("cancelled"))["amount"].sum()


class ReceiptCache:
    def __init__(self, root):
        self.root = root
        self.catalogs = {}

    def catalog(self, business):
        if business not in self.catalogs:
            self.catalogs[business] = SourceCatalog(self.root / business)
        return self.catalogs[business]


def nearest_intent(vector, index):
    # Stable ties favor the earlier, out-of-scope descriptions.
    best = int(cosine_similarity(vector, index)[0].argmax())
    return PROTOTYPES[best][0]


def tfidf_router():
    index = IntentIndex(PROTOTYPES)
    return lambda question: index.rank(question)[0].intent


def phobert_router(model_dir, segmenter_dir):
    if not shutil.which("java") and not (Path(os.getenv("JAVA_HOME", "")) / "bin" / "java.exe").is_file():
        raise RuntimeError("Java is unavailable. Set JAVA_HOME and add its bin directory to PATH.")
    if not (model_dir / "config.json").is_file():
        raise FileNotFoundError(f"Missing local PhoBERT snapshot at {model_dir}")
    if not (segmenter_dir / "VnCoreNLP-1.2.jar").is_file():
        raise FileNotFoundError(f"Missing local RDRSegmenter assets at {segmenter_dir}")

    import py_vncorenlp
    import torch
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    java_options = os.environ.get("JAVA_TOOL_OPTIONS", "")
    os.environ["JAVA_TOOL_OPTIONS"] = f"{java_options} -XX:ActiveProcessorCount=1".strip()
    cwd = Path.cwd()
    try:
        segmenter = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir=str(segmenter_dir))
    finally:
        os.chdir(cwd)
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    model = AutoModel.from_pretrained(model_dir, local_files_only=True, add_pooling_layer=False).eval().cpu()

    def encode(texts):
        segmented = [" ".join(segmenter.word_segment(text)) for text in texts]
        batch = tokenizer(segmented, padding=True, truncation=True, max_length=256,
                          return_special_tokens_mask=True, return_tensors="pt")
        mask = (batch["attention_mask"].bool() & ~batch.pop("special_tokens_mask").bool()).unsqueeze(-1)
        with torch.inference_mode():
            hidden = model(**batch).last_hidden_state
            return ((hidden * mask).sum(1) / mask.sum(1).clamp_min(1)).numpy()

    index = encode([text for _, text in PROTOTYPES])
    return lambda question: nearest_intent(encode([question]), index)


def answer_one(question, route, cache):
    start = perf_counter_ns()
    intent = route(question["question"])
    routing_ms = elapsed_ms(start)
    data_start = perf_counter_ns()
    bounds = month_bounds(question["question"], date.fromisoformat(question["as_of_date"])) if intent == PURCHASE else None
    answer = {"type": "abstain"}
    if bounds is not None:
        answer = answer_purchase_total(cache.catalog(question["business_id"]), question["question"],
                                       date.fromisoformat(question["as_of_date"]))
    return {"id": question["id"], "business_id": question["business_id"], "in_scope": question["in_scope"],
            "intent": intent, "answer": answer, "routing_ms": routing_ms,
            "data_ms": elapsed_ms(data_start) if bounds is not None else None, "total_ms": elapsed_ms(start)}


def verify_backend(sample, references, data_root):
    cache = ReceiptCache(data_root)
    cancelled = normalize_receipts(pl.DataFrame({"Thời gian": ["01/09/2026", "07/09/2026", "07/09/2026", "08/09/2026"],
                                                "Cần trả NCC": ["1,000", "500", "500", "900"],
                                                "Trạng thái": ["Đã nhập hàng", "Đã nhập hàng", "Đã hủy", "Đã nhập hàng"]}))
    bounds = month_bounds("tổng tiền nhập tháng này", date(2026, 9, 7))
    if sum_receipts(cancelled, bounds) != 1500 or month_bounds("tuần này", date(2026, 9, 7)) is not None:
        raise ValueError("Purchase backend failed the cutoff, cancellation or unsupported-period check")
    if answer_one(sample[0], lambda _: "revenue", cache)["answer"]["type"] != "abstain":
        raise ValueError("Out-of-scope intent must abstain")
    for q in (q for q in sample if q["in_scope"]):
        actual = answer_one(q, lambda _: PURCHASE, cache)["answer"]
        if not label_match(actual, references[q["id"]]):
            raise ValueError(f"Shared backend mismatch for {q['id']}: {actual}")
        if q["id"] == "q_001883280e83" and actual["answer"] != 89526400:
            raise ValueError("Unexpected value for the verified purchase example")


def percentiles(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    return {"p50": float(np.percentile(values, 50)), "p95": float(np.percentile(values, 95))} if values else None


def benchmark(route, sample, references, data_root):
    cache = ReceiptCache(data_root)
    first = answer_one(next(q for q in sample if q["id"] == "q_001883280e83"), route, cache)
    for business in BUSINESSES:
        cache.catalog(business)
    for q in sample[:5]:
        answer_one(q, route, cache)
    rows = []
    for repetition in range(1, 4):
        for q in sample:
            row = answer_one(q, route, cache)
            correct = label_match(row["answer"], references[row["id"]])
            outcome = "abstain" if row["answer"]["type"] == "abstain" else "correct" if correct else "wrong"
            rows.append({**row, "repetition": repetition, "outcome": outcome})
    once = [row for row in rows if row["repetition"] == 1]
    positive = [row for row in rows if row["in_scope"]]
    summary = {
        "first_request": first,
        "unique_questions": len(once),
        "measured_requests": len(rows),
        "outcomes": {key: sum(row["outcome"] == key for row in once) for key in ("correct", "wrong", "abstain")},
        "in_scope_correct": sum(row["in_scope"] and row["outcome"] == "correct" for row in once),
        "entered_calculation": sum(row["data_ms"] is not None for row in once),
        "false_purchase_routes": sum(not row["in_scope"] and row["intent"] == PURCHASE for row in once),
        "all_questions_ms": {field: percentiles(rows, field) for field in ("routing_ms", "data_ms", "total_ms")},
        "in_scope_ms": {field: percentiles(positive, field) for field in ("routing_ms", "data_ms", "total_ms")},
    }
    return summary, rows


def package_versions():
    packages = {}
    for package in ("numpy", "polars", "fastexcel", "scikit-learn", "torch", "transformers", "py-vncorenlp"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = None
    return packages


def write_report(output, report):
    (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Purchase intent CPU benchmark", "", "One supported purchase intent, 12 in-scope and 18 out-of-scope development questions.",
             "Three serial repetitions per question. Warm timings use a preloaded table cache.", "",
             "| Router | Startup ms | First request ms | Route p50 / p95 ms | Data p50 / p95 ms | Total p50 / p95 ms | In-scope total p50 / p95 ms | Correct / wrong / abstain | Correct in scope | Calculated | False purchase routes |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]

    def pair(values):
        return f"{values['p50']:.3f} / {values['p95']:.3f}" if values else "—"

    for name, result in report["routers"].items():
        if result["status"] != "completed":
            lines.append(f"| {name} | Blocked | — | — | — | — | — | — | — | — | — |")
            continue
        all_ms = result["all_questions_ms"]
        outcomes = " / ".join(str(result["outcomes"][key]) for key in ("correct", "wrong", "abstain"))
        lines.append(f"| {name} | {result['startup_ms']:.2f} | {result['first_request']['total_ms']:.2f} | "
                     f"{pair(all_ms['routing_ms'])} | {pair(all_ms['data_ms'])} | {pair(all_ms['total_ms'])} | "
                     f"{pair(result['in_scope_ms']['total_ms'])} | {outcomes} | "
                     f"{result['in_scope_correct']}/12 | {result['entered_calculation']} | {result['false_purchase_routes']} |")
    lines += ["", "Data timings cover calculated requests only. In-scope totals include abstentions."]
    for name, result in report["routers"].items():
        if result["status"] != "completed":
            lines.append(f"\n{name} setup or execution error: {result['error']}")
    if all(result["status"] == "completed" for result in report["routers"].values()):
        ordered = sorted(report["routers"], key=lambda key: report["routers"][key]["all_questions_ms"]["total_ms"]["p50"])
        lines.append(f"\n{ordered[0]} had the lower observed median end-to-end latency. Compare coverage and errors before drawing a quality conclusion.")
    else:
        lines.append("\nA head-to-head latency conclusion requires both routers to finish.")
    lines += ["", f"CPU: {report['cpu']} (one compute thread per router)", "",
              "First-request timing starts after index initialization with a fresh in-memory table cache.", "",
              "Reproduce from the repository root after preparing the optional packages and local model assets.",
              "Set `JAVA_HOME` and put its `bin` on `PATH` for PhoBERT.", "", "```powershell", report["command"],
              "```", "", "Resolved package versions are in `summary.json`."]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / f"intent_benchmark_{datetime.now():%Y%m%d_%H%M%S}")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models" / "phobert-base-v2")
    parser.add_argument("--segmenter-dir", type=Path, default=ROOT / "models" / "vncorenlp")
    args = parser.parse_args()
    train = ROOT / "train"
    sample = select_questions(train, ROOT / "configs" / "splits" / "seed_2026.json")
    ids = {q["id"] for q in sample}
    references = {row["id"]: row for row in read_jsonl(train / "answers.jsonl") if row["id"] in ids}
    if len(ids) != 30 or set(references) != ids:
        raise ValueError("Expected 30 unique questions with train references")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "sample.json").write_text(json.dumps([{key: q[key] for key in ("id", "business_id", "in_scope")} for q in sample],
                                                    indent=2) + "\n", encoding="utf-8")
    run_args = ["python", "scripts/benchmark_purchase_intent.py", "--model-dir", str(args.model_dir),
                "--segmenter-dir", str(args.segmenter_dir)]
    revision_file = args.model_dir / "benchmark-revision.txt"
    command = ["$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'"]
    if java_home := os.getenv("JAVA_HOME"):
        command.append("$env:JAVA_HOME = '" + java_home.replace("'", "''") + "'")
        command.append("$env:PATH = (Join-Path $env:JAVA_HOME 'bin') + ';' + $env:PATH")
    command.append("uv run --offline --locked --no-sync --with 'torch==2.9.1+cpu' --with 'transformers<5' "
                   "--with py-vncorenlp --index https://download.pytorch.org/whl/cpu " + subprocess.list2cmdline(run_args))
    report = {"cpu": os.getenv("PROCESSOR_IDENTIFIER") or platform.processor() or platform.machine(),
              "logical_cpus": os.cpu_count(), "python": platform.python_version(), "packages": package_versions(),
              "polars_threads": pl.thread_pool_size(),
              "phobert_revision": revision_file.read_text(encoding="utf-8").strip() if revision_file.is_file() else None,
              "command": "\n".join(command), "routers": {}}
    data_root = train / "data"
    with threadpool_limits(limits=1):
        verify_backend(sample, references, data_root)
        for name, make_router in (("tfidf", tfidf_router), ("phobert", lambda: phobert_router(args.model_dir.resolve(), args.segmenter_dir.resolve()))):
            try:
                start = perf_counter_ns()
                route = make_router()
                startup_ms = elapsed_ms(start)
                result, rows = benchmark(route, sample, references, data_root)
                report["routers"][name] = {"status": "completed", "startup_ms": startup_ms, **result}
                with (output / f"{name}_requests.jsonl").open("w", encoding="utf-8") as stream:
                    for row in rows:
                        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception as error:
                if name == "tfidf":
                    raise
                report["routers"][name] = {"status": "blocked", "error": f"{type(error).__name__}: {error}"}
            write_report(output, report)
    print(output)


if __name__ == "__main__":
    main()
