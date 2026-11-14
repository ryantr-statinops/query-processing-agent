import os, csv, re, json, warnings
warnings.filterwarnings('ignore')
import openpyxl, datetime
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

num_text = re.compile(r'^-?[\d.,]+\s*(đ|d|%|vnđ)?$')
date_text = re.compile(r'^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}([ T].*)?$')

def classify_cell(v):
    if v is None or (isinstance(v, str) and not v.strip()): return 'empty'
    if isinstance(v, (int,)): return 'int'
    if isinstance(v, float): return 'float'
    if isinstance(v, (datetime.datetime, datetime.date)): return 'date_obj'
    s = str(v).strip()
    if num_text.match(s): return 'num_text'
    if date_text.match(s): return 'date_text'
    return 'text'

report = {}
for split in ('train','public_test'):
    root = os.path.join(BASE, split, 'data')
    for b in sorted(os.listdir(root)):
        bd = os.path.join(root, b)
        if not os.path.isdir(bd): continue
        for f in sorted(os.listdir(bd)):
            p = os.path.join(bd, f); ext = os.path.splitext(f)[1].lower()
            counts = {}
            def bump(k): counts[k] = counts.get(k,0)+1
            try:
                if ext == '.csv':
                    with open(p, encoding='utf-8-sig') as fh:
                        r = csv.reader(fh); rows = list(r)[:250]
                    for row in rows[1:]:
                        for v in row: bump(classify_cell(v))
                elif ext == '.xlsx':
                    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
                    for sn in wb.sheetnames[:3]:
                        ws = wb[sn]; n=0
                        for row in ws.iter_rows(values_only=True):
                            n+=1
                            if n>250: break
                            if n<=2: continue
                            for v in row: bump(classify_cell(v))
                    wb.close()
                else:
                    continue
            except Exception as e:
                counts = {'ERROR': str(e)[:80]}
            tot = sum(counts.values()) or 1
            flags = {k: round(v*100/tot,1) for k,v in counts.items() if k in ('num_text','date_text','text','date_obj')}
            if flags:
                report.setdefault(b, {})[f] = flags

print("files with >=20% numeric-as-text or date-as-text:")
for b, fs in report.items():
    for f, c in fs.items():
        if c.get('num_text',0) >= 20 or c.get('date_text',0) >= 20:
            print(f"  {b:8} {f[:46]:46} {c}")
