#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Samair seferlerini yeniden çek - mevcut DB'yi güncellemek için"""
import sqlite3
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB = "samsun_v25.db"
YBS = "https://ybs.samsun.bel.tr/service"

# YBS API için token al
r = requests.post(YBS, data={'method': 'getGuestToken'}, verify=False, timeout=10)
token = r.json().get('token')
print(f"Token alındı: {token[:20]}...")

conn = sqlite3.connect(DB)

# Temizle
conn.execute("DELETE FROM samair_sefer")
conn.execute("DELETE FROM samair WHERE id > 4")  # Yeni hatlar ekle

# Yeni hatlar: 5 ve 9
conn.execute("INSERT OR REPLACE INTO samair VALUES(5, 'H5 TERME - HAVALİMANI', 'H5')")
conn.execute("INSERT OR REPLACE INTO samair VALUES(9, 'H9 YAKAKENT - HAVALİMANI', 'H9')")

toplam = 0
# 1-10 arası tüm hatları tara
for hatid in range(1, 11):
    params = {
        'method': 'samair_ucaksefersaatleri_public',
        'submethod': 'HatlarList',
        'hatid': hatid,
        'token': token
    }
    r = requests.get(YBS, params=params, verify=False, timeout=15)
    data = r.json()
    seferler = data.get('data') or data.get('root') or []
    
    if seferler:
        print(f"Hat {hatid}: {len(seferler)} sefer")
        for sf in seferler:
            saat = str(sf.get('saat', '')).replace(':00', '') if sf.get('saat') else ''
            varis = str(sf.get('varis_saati', '')).replace(':00', '') if sf.get('varis_saati') else ''
            conn.execute(
                "INSERT INTO samair_sefer(hat,saat,varis,firma,ucak_saat,tarih,gun_format) VALUES(?,?,?,?,?,?,?)",
                (hatid, saat, varis, sf.get('ucak_firmasi', ''), 
                 sf.get('ucak_saatleri', ''), sf.get('tarih', ''), sf.get('formatted_date', ''))
            )
            toplam += 1
    else:
        print(f"Hat {hatid}: 0 sefer")

conn.commit()
conn.close()

print(f"\n✅ Toplam {toplam} sefer güncellendi!")
print("Şimdi http://localhost:8000 sayfasını yenileyin.")
