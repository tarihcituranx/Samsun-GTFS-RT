#!/usr/bin/env python3
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('samsun_v25.db')

print('=== EKSPRES HATLARİ - FIYAT ===')
rows = conn.execute("SELECT hat_adi, tam_fiyat FROM fiyat WHERE hat_adi LIKE '%E1%' OR hat_adi LIKE '%EKSPRES%' OR hat_adi LIKE '%OMÜ%'").fetchall()
for r in rows:
    print(f'{r[0]} | {r[1]} TL')

print()
print('=== HAT TABLOSUNDA EKSPRES ===')
rows = conn.execute("SELECT code, name FROM hat WHERE code LIKE '%E%' OR name LIKE '%EKSPRES%'").fetchall()
for r in rows:
    print(f'{r[0]} | {r[1]}')

print()
print('=== FİYAT EŞLEŞME KONTROLÜ ===')
# Samulaş'tan gelen hat adları ASIS'ten gelen ile aynı mı kontrol et
fiyatlar = conn.execute("SELECT hat_adi FROM fiyat").fetchall()
hatlar = conn.execute("SELECT code, name FROM hat").fetchall()

eslesen = 0
for f in fiyatlar:
    f_adi = f[0].upper()
    for h in hatlar:
        h_code = h[0].upper()
        h_name = h[1].upper()
        # Benzerlik kontrol
        if f_adi in h_name or h_code in f_adi:
            eslesen += 1
            break

print(f"Toplam fiyat: {len(fiyatlar)}, Eşleşen: {eslesen}")
