"""
Full trace generator and validator for all 60 representative training questions.
Integrates Part 1 and Part 2 definitions, verifies against representative_questions.json,
and generates the canonical artifacts/data_prep/question_trace.jsonl.
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from trace_definitions_base8 import get_base8_definitions
from trace_definitions_part1 import get_part1_definitions
from trace_definitions_part2 import get_part2_definitions

rep = json.load(open("configs/representative_questions.json", encoding="utf-8"))
questions = rep["questions"]
q_map = {q["id"]: q for q in questions}

splits = json.load(open("configs/splits/seed_2026.json", encoding="utf-8"))
holdout_biz = set(splits["holdout_businesses"])

def get_split(biz_id):
    return "holdout" if biz_id in holdout_biz else "development"

# Combine definitions
traces = {}

# 1. Base 8
base8 = get_base8_definitions(q_map, get_split)
for t in base8:
    traces[t["question_id"]] = t
print(f"Loaded {len(base8)} base traces.")

# 2. Add Part 1
part1 = get_part1_definitions(q_map, get_split)
for t in part1:
    traces[t["question_id"]] = t
print(f"After Part 1: {len(traces)} traces.")

# 3. Add Part 2
part2 = get_part2_definitions(q_map, get_split)
for t in part2:
    traces[t["question_id"]] = t
print(f"After Part 2: {len(traces)} traces.")

# 4. Rigorous Validation against representative_questions.json
assert len(traces) == 60, f"Expected 60 traces, got {len(traces)}"

REQUIRED_KEYS = [
    "question_id", "business_id", "split_group", "question", "as_of_date",
    "intent", "time_range", "entities_filters", "answer_type", "source_refs",
    "required_columns", "grain", "join_edges", "rule_refs", "unit_semantics",
    "calculation", "computed_answer", "gold_comparison", "status", "uncertainty", "reviewer"
]

verified_count = 0
unanswerable_count = 0
holdout_count = 0
dev_count = 0

ordered_records = []
for q in questions:
    qid = q["id"]
    assert qid in traces, f"Missing trace for {qid}"
    rec = traces[qid]

    # Check keys
    for k in REQUIRED_KEYS:
        assert k in rec, f"Key {k} missing in record {qid}"

    # Check metadata match
    assert rec["business_id"] == q["business_id"], f"Business mismatch for {qid}"
    assert rec["as_of_date"] == q["as_of_date"], f"as_of_date mismatch for {qid}"
    assert rec["answer_type"] == q["reference"]["type"], f"answer_type mismatch for {qid}"
    assert rec["gold_comparison"]["reference_type"] == q["reference"]["type"], f"gold comparison type mismatch for {qid}"
    assert rec["gold_comparison"]["reference_answer"] == q["reference"]["answer"], f"gold comparison answer mismatch for {qid}"
    assert rec["gold_comparison"]["match"] is True, f"gold comparison match not True for {qid}"

    if rec["split_group"] == "holdout":
        holdout_count += 1
    else:
        dev_count += 1

    if rec.get("uncertainty") and len(rec["uncertainty"]) > 0:
        rec["decision_owner"] = "Lead / Người 5"

    if rec["answer_type"] == "unanswerable":
        unanswerable_count += 1
        assert rec["status"] == "insufficient_evidence", f"Unanswerable question {qid} must have status 'insufficient_evidence', got {rec['status']}"
        calc = rec.get("calculation", {})
        reason = calc.get("reason", "") or calc.get("result", "")
        assert len(reason) > 15, f"Unanswerable question {qid} lacks explicit blocker reason"
    else:
        verified_count += 1
        assert rec["status"] == "verified", f"Invalid status for {qid}"

    ordered_records.append(rec)

print("\n--- VALIDATION PASSED ---")
print(f"Total verified records: {len(ordered_records)}")
print(f"  Development records: {dev_count} (expected 48)")
print(f"  Holdout records: {holdout_count} (expected 12)")
print(f"  Answerable (verified): {verified_count} (expected 55)")
print(f"  Unanswerable (insufficient_evidence): {unanswerable_count} (expected 5)")

assert dev_count == 48, f"Expected 48 dev records, got {dev_count}"
assert holdout_count == 12, f"Expected 12 holdout records, got {holdout_count}"

# 5. Write canonical artifacts
out_path = Path("artifacts/data_prep/question_trace.jsonl")
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    for rec in ordered_records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"Wrote {len(ordered_records)} records to {out_path}")

print("Phase P1 Task 2 Question Tracing Complete!")
