"""Run grouped OOF comparisons and the one-time business holdout evaluation."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datamate.evaluation.labels import pa_reward  # noqa: E402
from datamate.metrics import score_predictions  # noqa: E402
from datamate.policy import CandidateBandit  # noqa: E402
from datamate.ranking.reranker import FeatureReranker  # noqa: E402


def load_jsonl(path: pathlib.Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def fit_reranker(rows: list[dict]) -> FeatureReranker:
    examples = [candidate for row in rows for candidate in row["candidates"]]
    return FeatureReranker().fit(examples)


def ranked_candidates(reranker: FeatureReranker, candidates: list[dict]) -> list[dict]:
    # Keep candidates in generation order for policy replay but attach inference-only scores.
    for candidate in candidates:
        candidate["rerank_score"] = reranker.score(candidate)
    return candidates


def policy_for(reranker: FeatureReranker, rows: list[dict]) -> CandidateBandit | None:
    traces = []
    business_ids = sorted({row["business_id"] for row in rows})
    for business_id in business_ids:
        # Produce training states with scores from a reranker that never saw this business.
        scorer_rows = [row for row in rows if row["business_id"] != business_id]
        scorer = fit_reranker(scorer_rows) if scorer_rows else reranker
        business_rows = [row for row in rows if row["business_id"] == business_id]
        for row in business_rows:
            candidates = ranked_candidates(scorer, [dict(candidate) for candidate in row["candidates"]])
            rewards = [int(candidate.get("reward", 0)) for candidate in candidates]
            if candidates:
                traces.append({"candidates": candidates, "rewards": rewards})
    if not traces:
        return None
    try:
        return CandidateBandit().fit(traces)
    except ValueError:
        return None


def run_policy(policy: CandidateBandit | None, reranker: FeatureReranker,
               candidates: list[dict]) -> dict | None:
    if policy is None:
        ranked = reranker.rerank([dict(candidate) for candidate in candidates])
        return next((item["answer"] for item in ranked if item.get("answer") is not None), None)
    visible: list[dict] = []
    for candidate in candidates[:3]:
        visible.append(dict(candidate))
        ranked_candidates(reranker, visible)
        action = policy.choose(visible, can_generate_more=len(visible) < min(3, len(candidates)))
        if action == "submit":
            ranked = reranker.rerank(visible)
            return next((item["answer"] for item in ranked if item.get("answer") is not None), None)
        if action == "abstain":
            return None
    if not visible:
        return None
    ranked = reranker.rerank(visible)
    return next((item["answer"] for item in ranked if item.get("answer") is not None), None)


def evaluate(rows: list[dict], reranker: FeatureReranker, policy: CandidateBandit | None = None) -> dict:
    references: dict[str, dict] = {}
    greedy_n1: dict[str, dict] = {}
    top1_n3: dict[str, dict] = {}
    reranked: dict[str, dict] = {}
    policy_answers: dict[str, dict] = {}
    oracle = 0
    latencies = [int(row.get("generation_elapsed_ms", 0)) for row in rows if row.get("generation_elapsed_ms") is not None]
    sql_candidates = [candidate for row in rows for candidate in row.get("candidates", []) if candidate.get("sql")]
    sql_errors = sum(not bool(candidate.get("result", {}).get("ok")) for candidate in sql_candidates)
    ordered_latencies = sorted(latencies)
    def percentile(fraction: float) -> int:
        if not ordered_latencies:
            return 0
        return ordered_latencies[round((len(ordered_latencies) - 1) * fraction)]
    for row in rows:
        qid = row["id"]
        reference = row.get("reference")
        if not reference:
            continue
        references[qid] = reference
        candidates = [dict(candidate) for candidate in row.get("candidates", [])]
        if not candidates:
            greedy_n1[qid] = {"type": "abstain"}
            top1_n3[qid] = {"type": "abstain"}
            reranked[qid] = {"type": "abstain"}
            policy_answers[qid] = {"type": "abstain"}
            continue
        oracle += int(any(candidate.get("answer") and pa_reward(candidate["answer"], reference) > 0 for candidate in candidates))
        first_answer = candidates[0].get("answer")
        greedy_n1[qid] = first_answer if first_answer is not None else {"type": "abstain"}
        heuristic_order = sorted(
            candidates,
            key=lambda candidate: (
                bool(candidate.get("result", {}).get("ok")),
                float(candidate.get("features", {}).get("result_type_shape", 0.0)),
            ),
            reverse=True,
        )
        heuristic_answer = next((candidate.get("answer") for candidate in heuristic_order if candidate.get("answer") is not None), None)
        top1_n3[qid] = heuristic_answer or {"type": "abstain"}
        ranked = reranker.rerank(candidates)
        reranked[qid] = next((candidate["answer"] for candidate in ranked if candidate.get("answer") is not None), {"type": "abstain"})
        selected = run_policy(policy, reranker, candidates)
        policy_answers[qid] = selected or {"type": "abstain"}
    total = len(references)
    return {
        "questions": total,
        "oracle_at_3": oracle / total if total else 0.0,
        "latency_ms_p50": percentile(0.50),
        "latency_ms_p95": percentile(0.95),
        "sql_candidate_count": len(sql_candidates),
        "sql_execution_errors": sql_errors,
        "sql_execution_error_rate": sql_errors / len(sql_candidates) if sql_candidates else 0.0,
        "_latencies": latencies,
        "greedy_n1": score_predictions(greedy_n1, references),
        "top1_n3": score_predictions(top1_n3, references),
        "reranker": score_predictions(reranked, references),
        "policy": score_predictions(policy_answers, references),
    }


def aggregate_fold_metrics(folds: list[dict]) -> dict:
    total_questions = sum(item["questions"] for item in folds)
    merged = {"questions": total_questions, "oracle_at_3": 0.0}
    merged["oracle_at_3"] = sum(item["oracle_at_3"] * item["questions"] for item in folds) / total_questions if total_questions else 0.0
    all_latencies = sorted(value for item in folds for value in item.get("_latencies", []))
    merged["latency_ms_p50"] = all_latencies[round((len(all_latencies) - 1) * 0.5)] if all_latencies else 0
    merged["latency_ms_p95"] = all_latencies[round((len(all_latencies) - 1) * 0.95)] if all_latencies else 0
    candidate_count = sum(item["sql_candidate_count"] for item in folds)
    error_count = sum(item["sql_execution_errors"] for item in folds)
    merged["sql_candidate_count"] = candidate_count
    merged["sql_execution_errors"] = error_count
    merged["sql_execution_error_rate"] = error_count / candidate_count if candidate_count else 0.0
    for strategy in ("greedy_n1", "top1_n3", "reranker", "policy"):
        counts = {key: sum(item[strategy][key] for item in folds) for key in ("total", "correct", "wrong", "abstain", "missing")}
        answered = counts["correct"] + counts["wrong"]
        total = counts["total"]
        merged[strategy] = {
            **counts,
            "coverage": (total - counts["abstain"] - counts["missing"]) / total if total else 0.0,
            "accuracy_answered": counts["correct"] / answered if answered else 0.0,
            "pa": (counts["correct"] - counts["wrong"]) / total if total else 0.0,
        }
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=pathlib.Path, default=ROOT / "artifacts" / "train_candidates.jsonl")
    parser.add_argument("--manifest", type=pathlib.Path, default=ROOT / "configs" / "splits" / "seed_2026.json")
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "artifacts" / "experiment_metrics.json")
    args = parser.parse_args()
    rows = load_jsonl(args.candidates)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    by_business: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_business[row["business_id"]].append(row)

    fold_eval_metrics = []
    fold_metrics = {}
    for fold_index, fold_businesses in enumerate(manifest["folds"]):
        train_businesses = set(manifest["development_businesses"]) - set(fold_businesses)
        train_rows = [row for business in train_businesses for row in by_business.get(business, [])]
        eval_rows = [row for business in fold_businesses for row in by_business.get(business, [])]
        reranker = fit_reranker(train_rows)
        policy = policy_for(reranker, train_rows)
        metrics = evaluate(eval_rows, reranker, policy)
        fold_metrics[str(fold_index)] = {key: value for key, value in metrics.items() if key != "_latencies"}
        fold_eval_metrics.append(metrics)

    all_dev_rows = [row for business in manifest["development_businesses"] for row in by_business.get(business, [])]
    final_reranker = fit_reranker(all_dev_rows)
    final_policy = policy_for(final_reranker, all_dev_rows)
    holdout_rows = [row for business in manifest["holdout_businesses"] for row in by_business.get(business, [])]
    holdout_metrics = evaluate(holdout_rows, final_reranker, final_policy)
    holdout_metrics.pop("_latencies", None)
    metrics = {
        "seed": manifest["seed"],
        "split_manifest_sha256": manifest["manifest_sha256"],
        "oof": aggregate_fold_metrics(fold_eval_metrics),
        "folds": fold_metrics,
        "holdout_once": holdout_metrics,
        "note": "Fold predictions use a model fit without the evaluated businesses. Holdout is evaluated once after development selection.",
    }
    reranker_keep = (
        metrics["oof"]["reranker"]["pa"] > metrics["oof"]["top1_n3"]["pa"]
        and holdout_metrics["reranker"]["pa"] >= holdout_metrics["top1_n3"]["pa"]
    )
    policy_keep = (
        reranker_keep
        and metrics["oof"]["policy"]["pa"] > metrics["oof"]["reranker"]["pa"]
        and holdout_metrics["policy"]["pa"] >= holdout_metrics["reranker"]["pa"]
    )
    metrics["deployment_selection"] = {
        "reranker_enabled": reranker_keep,
        "policy_enabled": policy_keep,
        "rule": "Compare greedy N=1, heuristic top-1 within N=3, and the feature reranker. Keep reranker only if OOF PA improves over N=3 top-1 and holdout PA does not drop; keep policy only if it further improves OOF PA and does not drop holdout PA.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    import joblib
    joblib.dump(final_reranker if reranker_keep else None, ROOT / "artifacts" / "reranker.joblib")
    joblib.dump(final_policy if policy_keep else None, ROOT / "artifacts" / "policy.joblib")
    print(f"Wrote metrics to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
