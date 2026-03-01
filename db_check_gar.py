
import sqlite3
import json

db = sqlite3.connect('samsun_v25.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("--- GAR İSTASYONU ---")
res = cur.execute("SELECT * FROM hat_durak WHERE ad LIKE '%Gar%'").fetchall()
for r in res:
    print(dict(r))
