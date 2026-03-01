#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ASIS vs YBS ID karşılaştırması"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

# ASIS'teki H hatlarını çek
print("=== ASIS API - Lines (H hatları) ===")
r = requests.get('https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/Lines', timeout=30)
data = r.json().get('data', [])
h_hatlar = [d for d in data if 'H' in d.get('lineCode', '').upper() and 'HAVAL' in d.get('lineName', '').upper()]
for h in h_hatlar:
    print(f"  {h['lineCode']} | {h['lineName']} | No:{h['lineNo']}")

print()
print("=== YBS API - Samair Seferler (hatid ile) ===")
# YBS token al
import urllib3
urllib3.disable_warnings()
r = requests.post('https://ybs.samsun.bel.tr/service/', data={'method': 'getGuestToken'}, verify=False, timeout=10)
resp = r.json()
print(f"Token response: {resp}")
token = resp.get('token')

if token:
    for hatid in range(1, 11):
        params = {
            'method': 'samair_ucaksefersaatleri_public',
            'submethod': 'HatlarList',
            'hatid': hatid,
            'token': token
        }
        r = requests.get('https://ybs.samsun.bel.tr/service/', params=params, verify=False, timeout=10)
        data = r.json()
        seferler = data.get('data') or data.get('root') or []
        if seferler:
            # İlk seferin firma bilgisine bak
            ornek = seferler[0]
            print(f"  hatid={hatid}: {len(seferler)} sefer | Örnek: {ornek.get('ucak_firmasi')} | Tarih: {ornek.get('formatted_date')}")
else:
    print("Token alınamadı!")
