"""Grouped exploratory commands for question wording and answer patterns."""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path
from typing import Callable

from analysis.common import ROOT, configure_utf8_stdout, fold_vietnamese, load_jsonl


def overview(root: Path = ROOT) -> int:
    questions = load_jsonl(root / "train/questions.jsonl")
    answers = load_jsonl(root / "train/answers.jsonl")
    public_questions = load_jsonl(root / "public_test/questions.jsonl")

    print("counts:", len(questions), len(answers), len(public_questions))
    print("\n=== QUESTION KEYS ===")
    question_keys = collections.Counter()
    for question in questions:
        question_keys.update(question.keys())
    print(question_keys)
    print("\n=== ANSWER KEYS ===")
    answer_keys = collections.Counter()
    for answer in answers:
        answer_keys.update(answer.keys())
    print(answer_keys)
    print("\n=== SAMPLE QUESTIONS ===")
    for question in questions[:5]:
        print(json.dumps(question, ensure_ascii=False))
    print("\n=== SAMPLE ANSWERS ===")
    for answer in answers[:8]:
        print(json.dumps(answer, ensure_ascii=False))
    print("\n=== PUBLIC TEST SAMPLE ===")
    for question in public_questions[:3]:
        print(json.dumps(question, ensure_ascii=False))

    print("\n=== ANSWER TYPE DIST ===")
    for answer_type, count in collections.Counter(a.get("type") for a in answers).most_common():
        print(f"{answer_type:15} {count}")

    print("\n=== Q: fields other than id/question/as_of_date ===")
    extra = collections.Counter()
    for question in questions:
        for key in question:
            if key not in ("id", "question", "as_of_date", "biz_id", "shop_id"):
                extra[key] += 1
    print(extra)

    print("\n=== as_of_date range ===")
    dates = sorted(q["as_of_date"] for q in questions if "as_of_date" in q)
    print(dates[0], "->", dates[-1], "unique:", len(set(dates)))
    print("\n=== biz/shop dist (train) ===")
    for key in ("biz_id", "shop_id"):
        if key in questions[0]:
            print(key, collections.Counter(q[key] for q in questions).most_common())

    print("\n=== answer sample per type ===")
    seen = {}
    for answer in answers:
        answer_type = answer.get("type")
        if answer_type not in seen:
            seen[answer_type] = answer
    for answer_type, answer in seen.items():
        sample = {key: value for key, value in answer.items() if key != "id"}
        print(answer_type, "=>", json.dumps(sample, ensure_ascii=False)[:300])
    return 0


def patterns(root: Path = ROOT) -> int:
    questions = load_jsonl(root / "train/questions.jsonl")
    answers = {a["id"]: a for a in load_jsonl(root / "train/answers.jsonl")}
    public_questions = load_jsonl(root / "public_test/questions.jsonl")

    print("=== biz distribution train ===")
    train_businesses = collections.Counter(q["business_id"] for q in questions)
    for business, count in sorted(train_businesses.items()):
        print(f"  {business}: {count}")
    print("\n=== biz distribution public_test ===")
    test_businesses = collections.Counter(q["business_id"] for q in public_questions)
    for business, count in sorted(test_businesses.items()):
        print(f"  {business}: {count}")

    print("\n=== type x biz (train) ===")
    type_by_business = collections.defaultdict(collections.Counter)
    for question in questions:
        type_by_business[question["business_id"]][answers[question["id"]]["type"]] += 1
    for business in sorted(type_by_business):
        print(f"  {business}: {dict(type_by_business[business])}")

    def normalize_template(value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"\d+", "#", value)
        value = re.sub(r"[^\w\s%#/ ]", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    print("\n=== top 40 normalized question templates ===")
    template_counts = collections.Counter(normalize_template(q["question"]) for q in questions)
    for template, count in template_counts.most_common(40):
        print(f"  {count:3}  {template}")

    print("\n=== sample questions per answer type ===")
    by_type = collections.defaultdict(list)
    for question in questions:
        answer = answers[question["id"]]
        by_type[answer["type"]].append((question, answer))
    for answer_type in ("number", "percent", "date", "string", "boolean", "list", "table", "unanswerable"):
        print(f"\n--- {answer_type} ({len(by_type[answer_type])}) ---")
        step = max(1, len(by_type[answer_type]) // 8)
        for question, answer in by_type[answer_type][::step][:8]:
            print(f"  [{question['business_id']}] {question['question']}")
            print(f"      => {json.dumps(answer['answer'], ensure_ascii=False)[:260]}  as_of={question['as_of_date']}")

    print("\n=== alias non-empty ===")
    nonempty_aliases = sum(1 for answer in answers.values() if answer.get("alias"))
    print(nonempty_aliases, "/", len(answers))
    for answer in list(answers.values()):
        if answer.get("alias"):
            print(" ", json.dumps(answer, ensure_ascii=False)[:300])
            if answer["type"] != "table":
                break
    return 0


RULES = [
    ("unanswerable_like", ["le phep", "quy men", "thoi tiet", "cam xuc", "thich", "dep trai"]),
    ("hang_het_han", ["het han", "han dung", "han su dung"]),
    ("thuoc_ke_don", ["ke don", "hoat chat"]),
    ("lo_hang", ["lo hang", "theo lo", "ma lo"]),
    ("lai_rong", ["lai rong", "chi phi", "loi nhuan rong"]),
    ("lai_gop", ["lai gop", "hang loi", "loi nhat", "lai nhat"]),
    ("gia_ban", ["gia ban", "gia le", "gia niem yet", "gia moi", "tang gia", "doi gia", "gia cua"]),
    ("ton_kho", ["ton kho", "con ton", "ton cuoi", "trong kho", "con bao nhieu", "con may", "ton thuc", "het hang"]),
    ("nhap_hang", ["nhap hang", "phieu nhap", "nha cung cap", "tien nhap", "gia nhap"]),
    ("cong_no", ["cong no", "con no", "no nhieu", "tra no", "thu no", "no them", "tuoi no", "dang no", "so no"]),
    ("giao_hang", ["giao hang", "dot giao", "luot giao", "so dot", "giao"]),
    ("ban_chay", ["ban chay", "ban nhieu nhat", "hot nhat", "ban duoc nhieu nhat", "chay nhat", "ban duoc bao nhieu"]),
    ("top_khach", ["khach mua nhieu", "khach chi tieu", "top", "khach hang co tong", "khach nao"]),
    ("nhan_vien", ["nhan vien", "nguoi ban", "ban gioi"]),
    ("ti_le_huy", ["ti le huy", "ti le don huy", "don bi huy", "don da huy", "huy don", "ty le huy"]),
    ("pct_change", ["tang hay giam", "thay doi", "tang bao nhieu", "giam bao nhieu", "tang truong", "so voi", "phan tram", "%"]),
    ("avg_order", ["trung binh", "binh quan"]),
    ("ngay_cao_nhat", ["ngay nao", "thang nao", "ngay ban dat", "ban dat nhat", "cao nhat", "nhieu tien nhat", "dat nhat"]),
    ("so_don", ["so don", "may don", "bao nhieu don", "dem so don", "so luong don"]),
    ("doanh_thu", ["doanh thu", "dthu", "ban duoc bao nhieu tien", "ban dc bao nhieu tien", "tong cong bao nhieu tien", "doanh so", "ban duoc tong cong", "tien hang", "tien ban"]),
]


def classify_intent(question: str) -> str:
    normalized = fold_vietnamese(question)
    for name, keywords in RULES:
        if any(keyword in normalized for keyword in keywords):
            return name
    return "other"


def intents(root: Path = ROOT) -> int:
    questions = load_jsonl(root / "train/questions.jsonl")
    answers = {a["id"]: a for a in load_jsonl(root / "train/answers.jsonl")}
    public_questions = load_jsonl(root / "public_test/questions.jsonl")

    for label, data in (("TRAIN", questions), ("PUBLIC_TEST", public_questions)):
        print(f"\n===== {label} intent classification =====")
        counts = collections.Counter(classify_intent(q["question"]) for q in data)
        for name, count in counts.most_common():
            print(f"  {name:20} {count:5}  {count / len(data) * 100:5.1f}%")
        print("  --- 'other' samples ---")
        shown = 0
        for question in data:
            if classify_intent(question["question"]) == "other":
                print("   *", question["question"][:150])
                shown += 1
                if shown >= 20:
                    break

    print("\n===== TRAIN: intent x answer-type =====")
    matrix = collections.defaultdict(collections.Counter)
    for question in questions:
        matrix[classify_intent(question["question"])][answers[question["id"]]["type"]] += 1
    for intent_name in sorted(matrix):
        total = sum(matrix[intent_name].values())
        print(f"  {intent_name:20} {total:5}  {dict(matrix[intent_name])}")

    print("\n===== style =====")
    telex = sum(
        1
        for question in questions
        if re.search(
            r"\b(khong|bao nhieu|bnhiu|dc|ko|khong|nhiu|thang|ngay|don|khach)\b",
            fold_vietnamese(question["question"]),
        )
    )
    print("questions w/o diacritics (telex/typo):", telex, "/", len(questions))
    print("avg q len:", sum(len(q["question"]) for q in questions) / len(questions))
    return 0


TIME_PATTERNS = [
    ("hôm nay/hnay", r"\b(hom nay|hnay|hôm nay|ngay hom nay|trong ngay hom nay)\b"),
    ("hôm qua", r"\b(hom qua|hqua|hôm qua)\b"),
    ("tuần này", r"\btuan nay\b"),
    ("tuần trước/rồi", r"\b(tuan truoc|tuan roi)\b"),
    ("tháng này", r"\bthang nay\b"),
    ("tháng M/Y", r"\b(thang|tháng)\s*\d{1,2}\s*[/\-]\s*\d{4}\b"),
    ("tháng M (không năm)", r"\b(thang|tháng)\s*\d{1,2}\b(?!\s*[/\-]\s*\d{4})"),
    ("quý", r"\bquy\b"),
    ("từ đầu năm", r"\btu dau nam\b|\bdau nam\b"),
    ("N ngày gần nhất", r"\b\d+\s*ngay (gan nhat|gan day|truoc)\b|\bgan nhat\b"),
    ("N ngày kể từ", r"\bke tu ngay\b|\bke tu\b"),
    ("ngày cụ thể", r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{4}\b"),
    ("khoảng X–Y", r"\btu\b.{0,40}\bden\b"),
    ("Tết", r"\btet\b"),
    ("đến hết ngày X", r"\bden het ngay\b|\btinh den\b|\bcuoi ngay\b"),
]


_LEGACY_TIME_TRANSLATION = str.maketrans(
    {
        **dict.fromkeys("àáạảãâă", "a"),
        **dict.fromkeys("èéẹẻẽê", "e"),
        **dict.fromkeys("ìíịỉĩ", "i"),
        **dict.fromkeys("òóọỏõôơ", "o"),
        **dict.fromkeys("ùúụủũư", "u"),
        **dict.fromkeys("ỳýỵỷỹ", "y"),
        "đ": "d",
    }
)


def normalize_time_marker_text(value: str) -> str:
    """Preserve the original time audit's accent mapping and counts."""
    return value.lower().translate(_LEGACY_TIME_TRANSLATION)


def time_markers(root: Path = ROOT) -> int:
    questions = load_jsonl(root / "train/questions.jsonl")
    answers = {a["id"]: a for a in load_jsonl(root / "train/answers.jsonl")}
    public_questions = load_jsonl(root / "public_test/questions.jsonl")

    for label, data in (("TRAIN", questions), ("PUBLIC_TEST", public_questions)):
        print(f"\n=== {label}: mốc thời gian xuất hiện (đếm câu, không loại trừ) ===")
        counts = collections.Counter()
        for question in data:
            normalized = normalize_time_marker_text(question["question"])
            for name, pattern in TIME_PATTERNS:
                if re.search(pattern, normalized):
                    counts[name] += 1
        for name, count in counts.most_common():
            print(f"  {name:24} {count:5} {count / len(data) * 100:5.1f}%")

    print("\n=== unanswerable: 70 câu, mẫu + as_of ===")
    shown = 0
    for question in questions:
        answer = answers[question["id"]]
        if answer["type"] == "unanswerable":
            print(f"  [{question['business_id']} as_of={question['as_of_date']}] {question['question'][:120]}")
            shown += 1
            if shown >= 25:
                break

    print("\n=== câu hỏi dạng bảng: 19 mẫu cột ===")
    columns = collections.Counter(
        tuple(answer["answer"]["columns"])
        for answer in answers.values()
        if answer["type"] == "table"
    )
    print(columns)

    print("\n=== list: số phần tử ===")
    lengths = collections.Counter(
        len(answer["answer"]) for answer in answers.values() if answer["type"] == "list"
    )
    print(lengths.most_common())
    return 0


COMMANDS: dict[str, Callable[[Path], int]] = {
    "overview": overview,
    "patterns": patterns,
    "intents": intents,
    "time": time_markers,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, command in COMMANDS.items():
        child = subparsers.add_parser(name)
        child.set_defaults(handler=command)
    args = parser.parse_args(argv)
    configure_utf8_stdout()
    return args.handler(ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
