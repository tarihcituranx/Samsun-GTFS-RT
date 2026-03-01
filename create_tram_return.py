
import sqlite3

db = sqlite3.connect('samsun_v25.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# Mevcut tramvay hattı
hat_code = 'SAMULAŞ - TRAMVAY'
new_hat_code = 'SAMULAŞ - TRAMVAY - DONUS'

# Hat tablosuna ekle (Yoksa)
cur.execute("DELETE FROM hat WHERE code = ?", (new_hat_code,))
cur.execute("INSERT INTO hat (code, name, tip, kat, alias) VALUES (?, ?, 'donus', 'tramvay', '')", (new_hat_code, new_hat_code))

# Durakları çek
duraklar = cur.execute("SELECT * FROM hat_durak WHERE hat = ? ORDER BY sira ASC", (hat_code,)).fetchall()

# Maksimum sıra
max_sira = len(duraklar)

print(f"Toplam {max_sira} durak ters çevrilecek.")

# Ters çevirip ekle
cur.execute("DELETE FROM hat_durak WHERE hat = ?", (new_hat_code,))
count = 0
for d in duraklar:
    new_sira = max_sira - d['sira'] + 1
    cur.execute("""
        INSERT INTO hat_durak (hat, durak_id, ad, sira, lat, lon) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (new_hat_code, d['durak_id'], d['ad'], new_sira, d['lat'], d['lon']))
    count += 1

db.commit()
print(f"{count} durak eklendi. Hat: {new_hat_code}")
