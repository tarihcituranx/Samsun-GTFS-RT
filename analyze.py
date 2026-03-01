#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fiyat ve Samair ID analizi"""
import sqlite3, requests, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('samsun_v25.db')
conn.row_factory = sqlite3.Row

print("="*60)
print("1. FIYAT TABLOSU ANALİZİ")
print("="*60)
rows = conn.execute("SELECT kaynak, hat_adi, tam_fiyat, indirimli_fiyat FROM fiyat LIMIT 10").fetchall()
for r in rows:
    print(f"  [{r['kaynak']}] {r['hat_adi']} | Tam: {r['tam_fiyat']} TL")

print()
print("="*60)
print("2. HAT TABLOSU - İLK 10")
print("="*60)
rows = conn.execute("SELECT code, name FROM hat LIMIT 10").fetchall()
for r in rows:
    print(f"  {r['code']} | {r['name']}")

print()
print("="*60)
print("3. SAMAIR DURAK FİYATLARI")
print("="*60)
rows = conn.execute("SELECT hat, ad, fiyat FROM samair_durak WHERE fiyat != '' LIMIT 10").fetchall()
for r in rows:
    print(f"  Hat {r['hat']}: {r['ad']} | Fiyat: {r['fiyat']}")

# YBS'den Samair durak fiyatlarını çek
print()
print("="*60)
print("4. YBS API - SAMAIR DURAKLAR (fiyatlar)")
print("="*60)
import urllib3
urllib3.disable_warnings()
r = requests.post('https://ybs.samsun.bel.tr/service/', data={'method': 'getGuestToken'}, verify=False, timeout=10)
token = r.json().get('token')
if token:
    params = {
        'method': 'samair_duraklar_public',
        'submethod': 'DuraklarList',
        'token': token
    }
    r = requests.post('https://ybs.samsun.bel.tr/service/', data=params, verify=False, timeout=10)
    data = r.json().get('data') or r.json().get('root') or []
    print(f"Toplam durak: {len(data)}")
    for d in data[:10]:
        print(f"  {d.get('hat_id')} | {d.get('durak_adi') or d.get('durak_kodu')} | Fiyat: {d.get('durak_fiyat', 'N/A')}")

print()
print("="*60) 
print("5. YBS API - TÜM HAT ID'LERİ İÇİN SEFER KONTROLÜ")
print("="*60)
for hatid in range(1, 15):
    params = {
        'method': 'samair_ucaksefersaatleri_public',
        'submethod': 'HatlarList',
        'hatid': hatid,
        'token': token
    }
    r = requests.get('https://ybs.samsun.bel.tr/service/', params=params, verify=False, timeout=10)
    data = r.json()
    seferler = data.get('data') or data.get('root') or []
    if len(seferler) > 0:
        print(f"  hatid={hatid}: {len(seferler)} sefer")
