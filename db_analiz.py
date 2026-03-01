"""DB analiz scripti"""
import sqlite3

conn = sqlite3.connect('samsun_v25.db')
cur = conn.cursor()

print("=== HAT TABLOSU ANALIZI ===")
cur.execute('SELECT kat, COUNT(*) FROM hat GROUP BY kat')
for r in cur.fetchall():
    print(f"  {r[0] or 'diger'}: {r[1]}")

print("\n=== ALIAS KONTROLU ===")
cur.execute('SELECT code, name, alias FROM hat WHERE alias != "" LIMIT 10')
for r in cur.fetchall():
    print(f"  {r[0]} -> alias: {r[2]}")

print("\n=== FIYAT ESLESTIRME ===")
cur.execute('SELECT COUNT(*) FROM fiyat WHERE hat_code != ""')
match = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM fiyat')
total = cur.fetchone()[0]
print(f"  {match}/{total} eslesti ({match*100//total if total else 0}%)")

print("\n=== ODAK HATLARI ===")
cur.execute('SELECT id, kod, ad FROM odak')
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} - {r[2][:40]}")

print("\n=== SAMAIR HATLARI ===")
cur.execute('SELECT id, kod, ad FROM samair')
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} - {r[2]}")

print("\n=== SAMAIR DURAK FIYATLARI ===")
cur.execute('SELECT hat, ad, fiyat FROM samair_durak WHERE fiyat != "" LIMIT 5')
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  Hat {r[0]}: {r[1]} - {r[2]} TL")
else:
    print("  Fiyat bilgisi yok (bos)")

conn.close()
