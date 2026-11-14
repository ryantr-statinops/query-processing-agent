import os, csv, re, warnings, collections
warnings.filterwarnings('ignore')
import openpyxl
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pat = re.compile(r'^-?[\d.,]+\s*(đ|d|vnđ|%)?$')

def samples_from_csv(p):
    out=[]
    with open(p, encoding='utf-8-sig') as fh:
        for i,row in enumerate(csv.reader(fh)):
            if i==0: continue
            for v in row:
                s=str(v).strip()
                if s and pat.match(s) and re.search(r'[.,]\d{3}', s): out.append(s)
            if len(out)>400: break
    return out

def samples_from_xlsx(p):
    out=[]
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    for sn in wb.sheetnames[:2]:
        ws=wb[sn]; n=0
        for row in ws.iter_rows(values_only=True):
            n+=1
            if n>400: break
            for v in row:
                s=str(v).strip() if v is not None else ''
                if s and pat.match(s) and re.search(r'[.,]\d{3}', s): out.append(s)
            if len(out)>400: break
    wb.close(); return out

for split in ('train','public_test'):
    root = os.path.join(BASE, split, 'data')
    for b in sorted(os.listdir(root)):
        bd=os.path.join(root,b)
        if not os.path.isdir(bd): continue
        acc=[]
        for f in sorted(os.listdir(bd)):
            p=os.path.join(bd,f); e=os.path.splitext(f)[1].lower()
            if e=='.csv': acc+=samples_from_csv(p)
            elif e=='.xlsx': acc+=samples_from_xlsx(p)
        if not acc: continue
        style=collections.Counter()
        for s in acc:
            if s.endswith('đ') or s.endswith('vnđ'): style['đ_suffix']+=1
            if s.endswith('%'): style['%_suffix']+=1
            if re.match(r'^-?\d{1,3}(,\d{3})+$', s): style['1,234,567']+=1
            elif re.match(r'^-?\d{1,3}(\.\d{3})+$', s): style['1.234.567']+=1
            elif ',' in s: style['comma_other']+=1
            else: style['other']+=1
        ex = [s for s in acc[:6]]
        print(f"{b:8} {dict(style)}  e.g. {ex}")
