
import sqlite3

db = sqlite3.connect('samsun_v25.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("--- T_RK_ ---")
res = cur.execute("SELECT * FROM hat_durak WHERE ad LIKE '%T_RK_%'").fetchall()
for r in res:
    print(dict(r))
