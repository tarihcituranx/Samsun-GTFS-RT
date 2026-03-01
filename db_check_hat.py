
import sqlite3
import json

db = sqlite3.connect('samsun_v25.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("--- HATLAR (KAT=TRAMVAY) ---")
res = cur.execute("SELECT * FROM hat WHERE kat='tramvay'").fetchall()
for r in res:
    print(dict(r))

print("\n--- HATLAR (LIKE T%) ---")
res2 = cur.execute("SELECT * FROM hat WHERE code LIKE 'T%'").fetchall()
for r in res2:
    print(dict(r))
