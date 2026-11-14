import sqlite3, os
for b, split in (('biz_123','train'), ('dev_006','public_test')):
    p = os.path.join(split,'data',b,'pos.sqlite')
    con = sqlite3.connect(p); cur = con.cursor()
    tabs = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print('===', b, '===')
    for t in tabs:
        cols = cur.execute(f'PRAGMA table_info("{t}")').fetchall()
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f'  {t} ({n} rows): ' + ', '.join(c[1]+':'+c[2] for c in cols))
    con.close()
