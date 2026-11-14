import os, csv, re, warnings, collections, json
warnings.filterwarnings('ignore')
import openpyxl
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STAT = re.compile(r'(trạng thái|status|tình trạng|kết quả|tình trạng|xử lý|tiến độ|tt đơn|ghi chú tt|xử lý)', re.I)
SKIP = re.compile(r'(hđđt|phiếu)', re.I)

def rows_of(p, ext, limit=20000):
    if ext == '.csv':
        with open(p, encoding='utf-8-sig') as fh:
            yield from csv.reader(fh)
    else:
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        for sn in wb.sheetnames:
            ws = wb[sn]
            yield from ws.iter_rows(values_only=True)
        wb.close()

res = collections.defaultdict(collections.Counter)
for split in ('train','public_test'):
    root = os.path.join(BASE, split, 'data')
    for b in sorted(os.listdir(root)):
        bd = os.path.join(root,b)
        if not os.path.isdir(bd): continue
        for f in sorted(os.listdir(bd)):
            p=os.path.join(bd,f); e=os.path.splitext(f)[1].lower()
            if e not in ('.csv','.xlsx'): continue
            try:
                it = rows_of(p,e)
                hdr = None; idx = []
                for i,row in enumerate(it):
                    vals = [None if v is None else str(v).strip() for v in row]
                    if hdr is None:
                        if sum(1 for v in vals if v) >= 3:
                            hdr = vals
                            idx = [j for j,h in enumerate(hdr) if h and STAT.search(h) and not SKIP.search(h)]
                    else:
                        for j in idx:
                            if j < len(vals) and vals[j]:
                                res[(b, f)][vals[j][:40]] += 1
                    if i > 20000: break
            except Exception as ex:
                print("ERR", b, f, type(ex).__name__, str(ex)[:100])

print("=== distinct status-like values per file ===")
for (b,f), c in res.items():
    top = c.most_common(12)
    if not top: continue
    print(f"  {b:8} {f[:38]:38} {dict(top)}")
