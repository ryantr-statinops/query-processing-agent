#!/usr/bin/env python3
"""Offline DataMate inference runner with SQL candidates and optional reranking/policy."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from typing import Any

from datamate.answers import answer_from_result
from datamate.context import calendar_context
from datamate.features import candidate_features
from datamate.generator import LocalSQLGenerator
from datamate.policy import CandidateBandit
from datamate.rerank import FeatureReranker
from datamate.sql import execute_select
from datamate.data.catalog import BusinessCatalog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=pathlib.Path, default=pathlib.Path("/data"))
    parser.add_argument("--result-root", type=pathlib.Path, default=pathlib.Path("/result"))
    parser.add_argument("--model-path", type=pathlib.Path, default=None)
    parser.add_argument("--candidate-count", type=int, default=3, choices=(1, 2, 3))
    parser.add_argument("--reranker-path", type=pathlib.Path, default=None)
    parser.add_argument("--policy-path", type=pathlib.Path, default=None)
    return parser.parse_args()


def load_text(path: pathlib.Path, limit: int = 12000) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")[:limit]


def load_pickle(path: pathlib.Path | None) -> Any:
    if path is None or not path.is_file():
        return None
    import joblib

    return joblib.load(path)


def gpu_memory_used_mb() -> int | None:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return None
    try:
        output = subprocess.run(
            [executable, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        ).stdout.splitlines()
        values = [int(line.strip()) for line in output if line.strip().isdigit()]
        return max(values) if values else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


class DataMateAgent:
    def __init__(self, data_root: pathlib.Path, model_path: pathlib.Path | None, count: int,
                 reranker: FeatureReranker | None, policy: CandidateBandit | None):
        self.data_root = data_root
        self.count = max(1, min(3, count))
        self.reranker = reranker
        self.policy = policy
        self.catalogs: dict[str, BusinessCatalog] = {}
        self.generator = None
        if model_path and model_path.is_file():
            self.generator = LocalSQLGenerator(
                model_path,
                context_size=int(os.environ.get("DATAMATE_CONTEXT_SIZE", "3072")),
                seed=int(os.environ.get("DATAMATE_SEED", "2026")),
            )

    def _catalog(self, business_id: str) -> BusinessCatalog:
        if business_id not in self.catalogs:
            self.catalogs[business_id] = BusinessCatalog(self.data_root / "data" / business_id)
        return self.catalogs[business_id]

    def _candidates(self, question: dict[str, Any], catalog: BusinessCatalog) -> list[dict[str, Any]]:
        if self.generator is None:
            return []
        business_id = question.get("business_id", "")
        business_dir = self.data_root / "data" / str(business_id)
        rules = load_text(self.data_root / "rulebook.md")
        business_readme = load_text(business_dir / "README.md", limit=4000)
        if business_readme:
            rules = f"{rules}\n\nBUSINESS README:\n{business_readme}"
        cal = calendar_context(self.data_root / "calendar.csv", question)
        schema = catalog.schema_text(str(question.get("question", "")))

        # The policy can stop early or spend inference on another candidate, but never exceed 3.
        candidates: list[dict[str, Any]] = []
        attempts = 0
        while len(candidates) < self.count and attempts < self.count:
            raw = self.generator.generate_one(question, schema, attempts, rules, cal)
            attempts += 1
            sql = raw.get("sql", "").strip()
            if not sql and raw.get("type") != "unanswerable":
                continue
            if any(sql and sql.casefold() == str(item.get("sql", "")).casefold() for item in candidates):
                continue
            if raw.get("type") == "unanswerable":
                answer = {"type": "unanswerable"}
                result = {"ok": True, "columns": [], "rows": [], "error": None, "elapsed_ms": 0}
            else:
                execution = execute_select(catalog, sql)
                result = {
                    "ok": execution.ok,
                    "columns": execution.columns,
                    "rows": execution.rows,
                    "error": execution.error,
                    "elapsed_ms": execution.elapsed_ms,
                }
                answer = answer_from_result(raw.get("type", ""), execution.columns, execution.rows) if execution.ok else None
            candidate = {**raw, "answer": answer, "result": result, "heuristic_score": float(bool(result["ok"]))}
            candidates.append(candidate)
            answers = [candidate.get("answer") for candidate in candidates]
            for item in candidates:
                item["all_answers"] = answers
                item["features"] = candidate_features(question, item, schema, rules)
            if self.policy:
                ordered = self.reranker.rerank(candidates) if self.reranker else candidates
                action = self.policy.choose(ordered, can_generate_more=len(candidates) < self.count)
                if action != "generate_more":
                    break

        if self.reranker and candidates:
            candidates = self.reranker.rerank(candidates)
        return candidates

    def answer(self, question: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        business_id = str(question.get("business_id", ""))
        trace: dict[str, Any] = {"code": [], "output": []}
        try:
            catalog = self._catalog(business_id)
            candidates = self._candidates(question, catalog)
            for item in candidates:
                trace["code"].append(item.get("sql", ""))
                result = dict(item.get("result", {}))
                rows = result.get("rows", []) or []
                result["row_count"] = len(rows)
                result["truncated_for_log"] = len(rows) > 20
                result["rows"] = rows[:20]
                trace["output"].append(result)
            selected = next((c for c in candidates if c.get("answer") is not None), None)
            if selected is None:
                answer = {"id": question["id"], "type": "abstain"}
            else:
                answer = {"id": question["id"], **selected["answer"]}
            trace["candidate_count"] = len(candidates)
            trace["selected_candidate"] = selected.get("index") if selected else None
            return answer, trace
        except Exception as error:
            trace["error"] = f"{type(error).__name__}: {error}"[:500]
            return {"id": question["id"], "type": "abstain"}, trace

    def close(self) -> None:
        for catalog in self.catalogs.values():
            catalog.close()


def write_jsonl_record(stream: Any, record: dict[str, Any]) -> None:
    try:
        import orjson

        stream.write(orjson.dumps(record, option=orjson.OPT_NON_STR_KEYS).decode("utf-8"))
    except ImportError:
        stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
    stream.write("\n")
    stream.flush()


def run(args: argparse.Namespace) -> int:
    questions_path = args.data_root / "questions.jsonl"
    if not questions_path.is_file():
        raise FileNotFoundError(f"Question file not found: {questions_path}")
    model_path = args.model_path or pathlib.Path(os.environ.get(
        "DATAMATE_MODEL_PATH",
        "/models/qwen2.5-coder-1.5b-q4/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
    ))
    reranker = load_pickle(args.reranker_path or pathlib.Path(os.environ.get("DATAMATE_RERANKER_PATH", "")))
    policy = load_pickle(args.policy_path or pathlib.Path(os.environ.get("DATAMATE_POLICY_PATH", "")))
    agent = DataMateAgent(args.data_root, model_path, args.candidate_count,
                          reranker if isinstance(reranker, FeatureReranker) else None,
                          policy if isinstance(policy, CandidateBandit) else None)

    args.result_root.mkdir(parents=True, exist_ok=True)
    logs_root = args.result_root / "logs"
    logs_root.mkdir(parents=True, exist_ok=True)
    submission_path = args.result_root / "submission.jsonl"
    log_path = logs_root / "questions.jsonl"
    count = 0
    peak_vram_mb = None
    current_vram_mb = gpu_memory_used_mb()
    started_run = time.monotonic()
    try:
        with questions_path.open("r", encoding="utf-8-sig") as questions_stream, submission_path.open(
            "w", encoding="utf-8", newline="\n"
        ) as submission_stream, log_path.open("w", encoding="utf-8", newline="\n") as log_stream:
            for line_number, raw_line in enumerate(questions_stream, start=1):
                if not raw_line.strip():
                    continue
                started_ns = time.monotonic_ns()
                try:
                    question = json.loads(raw_line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON in {questions_path}:{line_number}: {error}") from error
                if not isinstance(question, dict) or not isinstance(question.get("id"), str):
                    raise ValueError(f"Question at line {line_number} must have a string id")
                answer, trace = agent.answer(question)
                elapsed_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
                if count % 25 == 0:
                    current_vram_mb = gpu_memory_used_mb()
                    if current_vram_mb is not None:
                        peak_vram_mb = max(peak_vram_mb or 0, current_vram_mb)
                write_jsonl_record(submission_stream, answer)
                log: dict[str, Any] = {
                    "id": question["id"],
                    "answer": {key: value for key, value in answer.items() if key != "id"},
                    "elapsed_ms": elapsed_ms,
                    "thinking": None,
                    "gpu_memory_used_mb": current_vram_mb,
                }
                log.update(trace)
                write_jsonl_record(log_stream, log)
                count += 1
    finally:
        agent.close()
    (args.result_root / "runtime.json").write_text(json.dumps({
        "questions": count,
        "wall_time_seconds": round(time.monotonic() - started_run, 3),
        "peak_sampled_gpu_memory_mb": peak_vram_mb,
        "gpu_memory_measurement": "nvidia-smi device-wide memory.used, sampled every 25 questions; null when unavailable",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {count} answers to {submission_path}", file=sys.stderr)
    return 0


def main() -> int:
    args = parse_args()
    try:
        return run(args)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"DataMate runner failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
