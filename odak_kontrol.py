"""Odak durak durumu kontrolu"""
import sqlite3

conn = sqlite3.connect('samsun_v25.db')
cur = conn.cursor()

print("=== ODAK DURAK DURUMU ===\n")

cur.execute('SELECT COUNT(*) FROM odak_durak')
toplam = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM odak_durak WHERE kod != ''")
kodlu = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM odak_durak WHERE lat != 0')
koordinatli = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM odak_durak WHERE fiyat > 0')
fiyatli = cur.fetchone()[0]

print(f"Toplam durak: {toplam}")
print(f"Durak ID (kod) dolu: {kodlu}/{toplam} ({kodlu*100//toplam}%)")
print(f"Koordinatli: {koordinatli}/{toplam} ({koordinatli*100//toplam}%)")
print(f"Fiyatli: {fiyatli}/{toplam} ({fiyatli*100//toplam}%)")

print("\n=== HAT BAZLI DETAY ===")
cur.execute('''SELECT hat, COUNT(*), 
    SUM(CASE WHEN kod != '' THEN 1 ELSE 0 END),
    SUM(CASE WHEN lat != 0 THEN 1 ELSE 0 END),
    SUM(CASE WHEN fiyat > 0 THEN 1 ELSE 0 END)
FROM odak_durak GROUP BY hat ORDER BY hat''')

for r in cur.fetchall():
    print(f"  Hat {r[0]:2}: {r[1]:2} durak | ID: {r[2]}/{r[1]} | Koord: {r[3]}/{r[1]} | Fiyat: {r[4]}/{r[1]}")

print("\n=== ORNEK DURAKLAR ===")
cur.execute("SELECT hat, ad, kod, lat, lon, fiyat FROM odak_durak ORDER BY hat LIMIT 12")
for r in cur.fetchall():
    print(f"  Hat {r[0]}: {r[1][:25]:25} | ID:{r[2]:6} | [{r[3]:.4f}, {r[4]:.4f}] | {r[5]} TL")

conn.close()
