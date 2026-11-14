import json, os, re, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]

qs = load(os.path.join(BASE,'train','questions.jsonl'))
ans = {a['id']: a for a in load(os.path.join(BASE,'train','answers.jsonl'))}
pqs = load(os.path.join(BASE,'public_test','questions.jsonl'))

def strip(s):
    s = s.lower()
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[đ]', 'd', s)
    return s

RULES = [
 ('unanswerable_like', ['le phep','quy men','thoi tiet','cam xuc','thich','dep trai']),
 ('hang_het_han', ['het han','han dung','han su dung']),
 ('thuoc_ke_don', ['ke don','hoat chat']),
 ('lo_hang', ['lo hang','theo lo','ma lo']),
 ('lai_rong', ['lai rong','chi phi','loi nhuan rong']),
 ('lai_gop', ['lai gop','hang loi','loi nhat','lai nhat']),
 ('gia_ban', ['gia ban','gia le','gia niem yet','gia moi','tang gia','doi gia','gia cua']),
 ('ton_kho', ['ton kho','con ton','ton cuoi','trong kho','con bao nhieu','con may','ton thuc','het hang']),
 ('nhap_hang', ['nhap hang','phieu nhap','nha cung cap','tien nhap','gia nhap']),
 ('cong_no', ['cong no','con no','no nhieu','tra no','thu no','no them','tuoi no','dang no','so no']),
 ('giao_hang', ['giao hang','dot giao','luot giao','so dot','giao']),
 ('ban_chay', ['ban chay','ban nhieu nhat','hot nhat','ban duoc nhieu nhat','chay nhat','ban duoc bao nhieu']),
 ('top_khach', ['khach mua nhieu','khach chi tieu','top','khach hang co tong','khach nao']),
 ('nhan_vien', ['nhan vien','nguoi ban','ban gioi']),
 ('ti_le_huy', ['ti le huy','ti le don huy','don bi huy','don da huy','huy don','ty le huy']),
 ('pct_change', ['tang hay giam','thay doi','tang bao nhieu','giam bao nhieu','tang truong','so voi','phan tram','%']),
 ('avg_order', ['trung binh','binh quan']),
 ('ngay_cao_nhat', ['ngay nao','thang nao','ngay ban dat','ban dat nhat','cao nhat','nhieu tien nhat','dat nhat']),
 ('so_don', ['so don','may don','bao nhieu don','dem so don','so luong don']),
 ('doanh_thu', ['doanh thu','dthu','ban duoc bao nhieu tien','ban dc bao nhieu tien','tong cong bao nhieu tien','doanh so','ban duoc tong cong','tien hang','tien ban']),
]

def classify(q):
    s = strip(q)
    for name, keys in RULES:
        for k in keys:
            if k in s:
                return name
    return 'other'

for label, data in (('TRAIN', qs), ('PUBLIC_TEST', pqs)):
    print(f"\n===== {label} intent classification =====")
    c = collections.Counter(classify(q['question']) for q in data)
    for k, v in c.most_common():
        print(f"  {k:20} {v:5}  {v/len(data)*100:5.1f}%")
    print("  --- 'other' samples ---")
    n=0
    for q in data:
        if classify(q['question'])=='other':
            print("   *", q['question'][:150]); n+=1
            if n>=20: break

# type x intent for train
print("\n===== TRAIN: intent x answer-type =====")
m = collections.defaultdict(collections.Counter)
for q in qs:
    m[classify(q['question'])][ans[q['id']]['type']] += 1
for k in sorted(m):
    tot = sum(m[k].values())
    print(f"  {k:20} {tot:5}  {dict(m[k])}")

# question length / language style
print("\n===== style =====")
telex = sum(1 for q in qs if re.search(r'\b(khong|bao nhieu|bnhiu|dc|ko|khong|nhiu|thang|ngay|don|khach)\b', strip(q['question'])))
print("questions w/o diacritics (telex/typo):", telex, "/", len(qs))
print("avg q len:", sum(len(q['question']) for q in qs)/len(qs))
