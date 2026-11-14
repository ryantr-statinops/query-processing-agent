import os, re, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()

rows = []
for split in ('train','public_test'):
    root = os.path.join(BASE, split, 'data')
    for b in sorted(os.listdir(root)):
        bd = os.path.join(root, b)
        if not os.path.isdir(bd): continue
        rm = os.path.join(bd, 'README.md')
        txt = read(rm) if os.path.exists(rm) else ''
        m = re.search(r'Dữ liệu có đến hết\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})', txt)
        cutoff = m.group(1) if m else ''
        files = [f for f in sorted(os.listdir(bd)) if f != 'README.md']
        fmt = sorted(set(os.path.splitext(f)[1] for f in files))
        rows.append(dict(split=split, biz=b, cutoff=cutoff, files=files, fmt='/'.join(fmt)))

# questions per biz, date range
def load(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]
qs = load(os.path.join(BASE,'train','questions.jsonl'))
pqs = load(os.path.join(BASE,'public_test','questions.jsonl'))
import collections
qr = collections.defaultdict(list)
for q in qs+pqs: qr[q['business_id']].append(q['as_of_date'])

print(f"{'biz':9} {'cutoff':11} {'fmt':10} {'nfiles':6} {'q':4} as_of range")
for r in rows:
    ds = sorted(qr.get(r['biz'], []))
    rng = f"{ds[0]}..{ds[-1]}" if ds else '-'
    r['nq'] = len(ds)
    print(f"{r['biz']:9} {r['cutoff']:11} {r['fmt']:10} {len(r['files']):<6} {len(ds):<4} {rng}")

print("\n\n=== FILE INVENTORY ===")
for r in rows:
    print(f"\n[{r['biz']}] ({r['split']}, cutoff {r['cutoff']})")
    print("   " + ", ".join(r['files']))

json.dump(rows, open(os.path.join(BASE,'analysis','inventory.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
