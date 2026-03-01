#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normal otobüs hatlarının fiyat eşleşmesi kontrolü"""
import sqlite3, sys, re
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('samsun_v25.db')
conn.row_factory = sqlite3.Row

print("="*70)
print("NORMAL OTOBÜS HATLARI - FİYAT EŞLEŞMESİ")
print("="*70)

# 12, 13, 14 gibi numaralı hatlar
hatlar = conn.execute("""
    SELECT code, name FROM hat 
    WHERE code NOT LIKE '%EKSPRES%' 
    AND code NOT LIKE 'H%'
    AND code NOT LIKE 'R%'
    LIMIT 20
""").fetchall()

eslesen = 0
eslesmeyen = []

for h in hatlar:
    code = h['code']
    name = h['name']
    
    # Fiyat tablosunda ara
    fiyat = conn.execute("SELECT hat_adi, tam_fiyat FROM fiyat WHERE hat_adi=?", (name,)).fetchone()
    if not fiyat:
        # Hat numarasıyla ara (örn: "13 KAMALI TOKİ" -> "13")
        m = re.match(r'^(\d+)', name)
        if m:
            fiyat = conn.execute("SELECT hat_adi, tam_fiyat FROM fiyat WHERE hat_adi LIKE ?", (f"{m.group(1)} %",)).fetchone()
    
    if fiyat:
        eslesen += 1
        print(f"✅ {code[:30]:30} -> {fiyat['tam_fiyat']} TL")
    else:
        eslesmeyen.append((code, name))
        print(f"❌ {code[:30]:30} -> FİYAT YOK")

print()
print(f"Eşleşen: {eslesen}, Eşleşmeyen: {len(eslesmeyen)}")
