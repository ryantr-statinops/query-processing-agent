"""
Base 8 trace definitions, fully grounded and matching canonical 21-key schema.
"""
import json
from pathlib import Path

def get_base8_definitions(q_map, get_split):
    p = Path(__file__).parent / "base_8_records.json"
    recs = json.load(open(p, encoding="utf-8"))
    for r in recs:
        r["split_group"] = get_split(r["business_id"])
    return recs
