import json, collections, re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]

qs = load(os.path.join(BASE,'train','questions.jsonl'))
ans = {a['id']: a for a in load(os.path.join(BASE,'train','answers.jsonl'))}
pqs = load(os.path.join(BASE,'public_test','questions.jsonl'))

print("=== biz distribution train ===")
tr = collections.Counter(q['business_id'] for q in qs)
for k,v in sorted(tr.items()): print(f"  {k}: {v}")
print("\n=== biz distribution public_test ===")
te = collections.Counter(q['business_id'] for q in pqs)
for k,v in sorted(te.items()): print(f"  {k}: {v}")

print("\n=== type x biz (train) ===")
t = collections.defaultdict(collections.Counter)
for q in qs: t[q['business_id']][ans[q['id']]['type']] += 1
for k in sorted(t): print(f"  {k}: {dict(t[k])}")

def norm(s):
    s = s.lower().strip()
    s = re.sub(r'\d+', '#', s)
    s = re.sub(r'[^\w\s%#/]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

print("\n=== top 40 normalized question templates ===")
c = collections.Counter(norm(q['question']) for q in qs)
for tpl, n in c.most_common(40):
    print(f"  {n:3}  {tpl}")

print("\n=== sample questions per answer type ===")
bytype = collections.defaultdict(list)
for q in qs:
    a = ans[q['id']]
    bytype[a['type']].append((q, a))
for ty in ['number','percent','date','string','boolean','list','table','unanswerable']:
    print(f"\n--- {ty} ({len(bytype[ty])}) ---")
    step = max(1, len(bytype[ty])//8)
    for q, a in bytype[ty][::step][:8]:
        print(f"  [{q['business_id']}] {q['question']}")
        print(f"      => {json.dumps(a['answer'], ensure_ascii=False)[:260]}  as_of={q['as_of_date']}")

print("\n=== alias non-empty ===")
n_alias = sum(1 for a in ans.values() if a.get('alias'))
print(n_alias, "/", len(ans))
for a in list(ans.values()):
    if a.get('alias'):
        print(" ", json.dumps(a, ensure_ascii=False)[:300])
        if a['type'] != 'table': break
