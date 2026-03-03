
import sqlite3

# Mobil uygulama veritabanına bağlan
db = sqlite3.connect('samsun_mobil/samsun_mobil_app/assets/samsun_mobil.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# 'E1' hat kodunu sorgula ve sonucu yazdır
res = cur.execute("SELECT code FROM hat WHERE code = 'E1'").fetchone()
if res:
    print(res['code'])

db.close()
