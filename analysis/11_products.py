import os, csv, re, warnings, collections
warnings.filterwarnings('ignore')
import openpyxl
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD = re.compile(r'^(tên sản phẩm|tên hàng hóa|tên hàng|tên mặt hàng|tên sp|hàng bán|hàng hóa|hàng|mặt hàng|sản phẩm|nội dung|product|ten_hang|ten hang|tên món|tên gọi|ten san pham)$', re.I)

def scan(p, ext, limit=4000):
    names = []
    if ext == '.csv':
        with open(p, encoding='utf-8-sig') as fh:
            r = csv.reader(fh); rows = list(r)
    else:
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        rows = []
        for sn in wb.sheetnames[:2]:
            for row in wb[sn].iter_rows(values_only=True):
                rows.append(row)
                if len(rows) > limit: break
            if len(rows) > limit: break
        wb.close()
    hi = None
    for i, row in enumerate(rows[:6]):
        vals = [None if v is None else str(v).strip() for v in row]
        if sum(1 for v in vals if v) >= 3:
            hi = i; hdr = vals; break
    if hi is None: return []
    idx = [j for j,h in enumerate(hdr) if h and PROD.match(h)]
    if not idx: return []
    for row in rows[hi+1:hi+4000]:
        for j in idx[:1]:
            if j < len(row) and row[j] is not None:
                names.append(str(row[j]).strip())
    return names

for split in ('train','public_test'):
    root = os.path.join(BASE, split, 'data')
    for b in sorted(os.listdir(root)):
        bd = os.path.join(root,b)
        if not os.path.isdir(bd): continue
        acc = []
        for f in sorted(os.listdir(bd)):
            p = os.path.join(bd,f); e = os.path.splitext(f)[1].lower()
            if e not in ('.csv','.xlsx'): continue
            try: acc += scan(p,e)
            except Exception: pass
        if acc:
            c = collections.Counter(acc)
            print(f"{b:8} ({len(set(acc))} distinct) " + " | ".join(n[:34] for n,_ in c.most_common(6)))
