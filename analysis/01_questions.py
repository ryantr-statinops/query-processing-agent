import json, collections, re, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(p):
    out = []
    with open(p, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

qs = load(os.path.join(BASE, 'train', 'questions.jsonl'))
ans = load(os.path.join(BASE, 'train', 'answers.jsonl'))
pqs = load(os.path.join(BASE, 'public_test', 'questions.jsonl'))

print("counts:", len(qs), len(ans), len(pqs))
print("\n=== QUESTION KEYS ===")
kc = collections.Counter()
for q in qs: kc.update(q.keys())
print(kc)
print("\n=== ANSWER KEYS ===")
ka = collections.Counter()
for a in ans: ka.update(a.keys())
print(ka)
print("\n=== SAMPLE QUESTIONS ===")
for q in qs[:5]:
    print(json.dumps(q, ensure_ascii=False))
print("\n=== SAMPLE ANSWERS ===")
for a in ans[:8]:
    print(json.dumps(a, ensure_ascii=False))
print("\n=== PUBLIC TEST SAMPLE ===")
for q in pqs[:3]:
    print(json.dumps(q, ensure_ascii=False))

print("\n=== ANSWER TYPE DIST ===")
for t, c in collections.Counter(a.get('type') for a in ans).most_common():
    print(f"{t:15} {c}")

print("\n=== Q: fields other than id/question/as_of_date ===")
extra = collections.Counter()
for q in qs:
    for k in q:
        if k not in ('id','question','as_of_date','biz_id','shop_id'):
            extra[k] += 1
print(extra)

print("\n=== as_of_date range ===")
ds = sorted(q['as_of_date'] for q in qs if 'as_of_date' in q)
print(ds[0], '->', ds[-1], 'unique:', len(set(ds)))
print("\n=== biz/shop dist (train) ===")
for k in ('biz_id','shop_id'):
    if k in qs[0]:
        print(k, collections.Counter(q[k] for q in qs).most_common())

print("\n=== answer sample per type ===")
seen = {}
for a in ans:
    t = a.get('type')
    if t not in seen:
        seen[t] = a
for t, a in seen.items():
    print(t, '=>', json.dumps({k:v for k,v in a.items() if k!='id'}, ensure_ascii=False)[:300])
