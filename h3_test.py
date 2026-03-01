#!/usr/bin/env python3
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

# H3 için sefer API testi
print("=== H3 BAFRA Seferleri API Testi ===")
r = requests.get('http://localhost:8000/api/samair/3/sefer', timeout=10)
data = r.json()
seferler = data.get('data', [])
print(f"Toplam sefer: {len(seferler)}")
print(f"Son güncelleme: {data.get('last_update')}")
print()
print("İlk 5 sefer:")
for s in seferler[:5]:
    print(f"  {s['saat']} -> {s['varis']} | {s['firma']} | {s['gun_format']}")

print()
print("=== H4 ÇARŞAMBA Seferleri ===")
r = requests.get('http://localhost:8000/api/samair/4/sefer', timeout=10)
data = r.json()
seferler = data.get('data', [])
print(f"Toplam sefer: {len(seferler)}")
for s in seferler[:3]:
    print(f"  {s['saat']} -> {s['varis']} | {s['firma']}")
