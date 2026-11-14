import json, os, re, collections
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p):
    with open(p, encoding='utf-8') as f: return [json.loads(l) for l in f if l.strip()]
qs = load(os.path.join(BASE,'train','questions.jsonl'))
ans = {a['id']: a for a in load(os.path.join(BASE,'train','answers.jsonl'))}
pqs = load(os.path.join(BASE,'public_test','questions.jsonl'))

def s(t):
    t=t.lower()
    for a,b in [('à','a'),('á','a'),('ạ','a'),('ả','a'),('ã','a'),('â','a'),('ă','a'),
                ('è','e'),('é','e'),('ẹ','e'),('ẻ','e'),('ẽ','e'),('ê','e'),
                ('ì','i'),('í','i'),('ị','i'),('ỉ','i'),('ĩ','i'),
                ('ò','o'),('ó','o'),('ọ','o'),('ỏ','o'),('õ','o'),('ô','o'),('ơ','o'),
                ('ù','u'),('ú','u'),('ụ','u'),('ủ','u'),('ũ','u'),('ư','u'),
                ('ỳ','y'),('ý','y'),('ỵ','y'),('ỷ','y'),('ỹ','y'),('đ','d')]:
        t=t.replace(a,b)
    return t

TIME = [
 ('hôm nay/hnay', r'\b(hom nay|hnay|hôm nay|ngay hom nay|trong ngay hom nay)\b'),
 ('hôm qua', r'\b(hom qua|hqua|hôm qua)\b'),
 ('tuần này', r'\btuan nay\b'),
 ('tuần trước/rồi', r'\b(tuan truoc|tuan roi)\b'),
 ('tháng này', r'\bthang nay\b'),
 ('tháng M/Y', r'\b(thang|tháng)\s*\d{1,2}\s*[/\-]\s*\d{4}\b'),
 ('tháng M (không năm)', r'\b(thang|tháng)\s*\d{1,2}\b(?!\s*[/\-]\s*\d{4})'),
 ('quý', r'\bquy\b'),
 ('từ đầu năm', r'\btu dau nam\b|\bdau nam\b'),
 ('N ngày gần nhất', r'\b\d+\s*ngay (gan nhat|gan day|truoc)\b|\bgan nhat\b'),
 ('N ngày kể từ', r'\bke tu ngay\b|\bke tu\b'),
 ('ngày cụ thể', r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{4}\b'),
 ('khoảng X–Y', r'\btu\b.{0,40}\bden\b'),
 ('Tết', r'\btet\b'),
 ('đến hết ngày X', r'\bden het ngay\b|\btinh den\b|\bcuoi ngay\b'),
]

for label, data in (('TRAIN', qs), ('PUBLIC_TEST', pqs)):
    print(f"\n=== {label}: mốc thời gian xuất hiện (đếm câu, không loại trừ) ===")
    c = collections.Counter()
    for q in data:
        t = s(q['question'])
        for name, pat in TIME:
            if re.search(pat, t): c[name]+=1
    for k,v in c.most_common():
        print(f"  {k:24} {v:5} {v/len(data)*100:5.1f}%")

print("\n=== unanswerable: 70 câu, mẫu + as_of ===")
n=0
for q in qs:
    a=ans[q['id']]
    if a['type']=='unanswerable':
        print(f"  [{q['business_id']} as_of={q['as_of_date']}] {q['question'][:120]}")
        n+=1
        if n>=25: break

print("\n=== câu hỏi dạng bảng: 19 mẫu cột ===")
cols = collections.Counter()
for a in ans.values():
    if a['type']=='table':
        cols[tuple(a['answer']['columns'])]+=1
print(cols)

print("\n=== list: số phần tử ===")
print(collections.Counter(len(a['answer']) for a in ans.values() if a['type']=='list').most_common())
