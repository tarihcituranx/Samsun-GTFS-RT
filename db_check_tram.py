
import sqlite3
import json

db = sqlite3.connect('samsun_v25.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("--- TRAMVAY DURAKLARI (SAMULA - TRAMVAY) ---")
res = cur.execute("SELECT * FROM hat_durak WHERE hat LIKE 'SAMULA%' LIMIT 5").fetchall()
for r in res:
    print(dict(r))

print("\n--- SEFERLER (SAMULA - TRAMVAY) ---")
res2 = cur.execute("SELECT * FROM sefer WHERE hat LIKE 'SAMULA%' LIMIT 5").fetchall()
for r in res2:
    print(dict(r))
