
import sqlite3
import json

db = sqlite3.connect('samsun_v25.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("--- TRAMVAY DURAKLARI ---")
res = cur.execute("SELECT * FROM hat_durak WHERE hat LIKE 'T%' LIMIT 5").fetchall()
for r in res:
    print(dict(r))

print("\n--- SEFERLER (TRAMVAY) ---")
res2 = cur.execute("SELECT * FROM sefer WHERE hat LIKE 'T%' LIMIT 5").fetchall()
for r in res2:
    print(dict(r))
