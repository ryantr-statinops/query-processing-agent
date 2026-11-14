import os, json, csv, warnings
warnings.filterwarnings('ignore')
import openpyxl
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def best_header(rows):
    best, bi = -1, 0
    for i, r in enumerate(rows):
        n = sum(1 for v in r if v not in (None, ''))
        if n > best and n >= 3:
            best, bi = n, i
    return bi

flags = []
inv = {}
for split in ('train','public_test'):
    root = os.path.join(BASE, split, 'data')
    for b in sorted(os.listdir(root)):
        bd = os.path.join(root, b)
        if not os.path.isdir(bd): continue
        for f in sorted(os.listdir(bd)):
            p = os.path.join(bd, f); ext = os.path.splitext(f)[1].lower()
            if ext == '.csv':
                with open(p, encoding='utf-8-sig') as fh:
                    rows = [[c for c in r] for _, r in zip(range(6), csv.reader(fh))]
                bi = best_header(rows)
                inv.setdefault(b, {})[f] = {'header_row': bi, 'header': rows[bi] if rows else []}
                if bi != 0: flags.append((b, f, bi, rows[bi]))
            elif ext == '.xlsx':
                wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
                for sn in wb.sheetnames:
                    ws = wb[sn]
                    rows = []
                    for row in ws.iter_rows(max_row=6, values_only=True):
                        rows.append([None if v is None else str(v)[:50] for v in row])
                    bi = best_header(rows)
                    inv.setdefault(b, {})[f + ' :: ' + sn] = {'header_row': bi, 'header': rows[bi] if rows else []}
                    if bi != 0: flags.append((b, f + ' :: ' + sn, bi, rows[bi]))
                wb.close()

print("=== files/sheets where header is NOT first row ===")
for b,f,bi,h in flags:
    print(f"  {b:8} {f[:60]:60} row#{bi}  {h}")

json.dump(inv, open(os.path.join(BASE,'analysis','headers_detected.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print("\ntotal flagged:", len(flags))
