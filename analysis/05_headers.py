import os, json, csv, sqlite3, warnings
warnings.filterwarnings('ignore')
import openpyxl
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

out = {}
for split in ('train','public_test'):
    root = os.path.join(BASE, split, 'data')
    for b in sorted(os.listdir(root)):
        bd = os.path.join(root, b)
        if not os.path.isdir(bd): continue
        info = {}
        for f in sorted(os.listdir(bd)):
            p = os.path.join(bd, f)
            ext = os.path.splitext(f)[1].lower()
            try:
                if ext == '.csv':
                    with open(p, encoding='utf-8-sig') as fh:
                        r = csv.reader(fh)
                        rows = [next(r) for _ in range(2)]
                    info[f] = [[c for c in rows[0]], rows[1]]
                elif ext == '.xlsx':
                    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
                    sh = {}
                    for sn in wb.sheetnames:
                        ws = wb[sn]
                        rows = []
                        for row in ws.iter_rows(max_row=2, values_only=True):
                            rows.append([None if v is None else str(v)[:60] for v in row])
                        while rows and rows[0] and rows[0][-1] is None:
                            rows[0] = rows[0][:-1]
                        sh[sn] = rows
                    wb.close()
                    info[f] = sh
                elif ext == '.sqlite':
                    con = sqlite3.connect(p); cur = con.cursor()
                    tabs = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                    d = {}
                    for t in tabs:
                        cols = [r[1] for r in cur.execute(f'PRAGMA table_info("{t}")')]
                        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                        d[t] = {'cols': cols, 'rows': n}
                    con.close()
                    info[f] = d
            except Exception as e:
                info[f] = {'ERROR': str(e)[:120]}
        out[b] = info

json.dump(out, open(os.path.join(BASE,'analysis','headers.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print("bizs:", len(out))
# quick sanity: count errors
errs = [(b,f) for b,fs in out.items() for f,v in fs.items() if isinstance(v,dict) and 'ERROR' in v]
print("errors:", errs)
# print one example parse
for b in ['biz_101','biz_106','biz_123','dev_012']:
    print("\n##", b)
    for f, v in out[b].items():
        print(" ", f, "->", json.dumps(v, ensure_ascii=False)[:400])
