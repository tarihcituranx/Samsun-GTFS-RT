#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

print('=== API TEST ===')
print()

# Hat listesi
r = requests.get('http://localhost:8000/api/hat', timeout=10)
hats = r.json()
print(f'Hatlar: {len(hats)}')
for h in hats[:5]:
    print(f'  {h["code"]} | {h["name"]} | {h["kat"]}')
print()

# Samair
r = requests.get('http://localhost:8000/api/samair', timeout=10)
samair = r.json()
print(f'Samair: {len(samair)}')
for s in samair:
    print(f'  ID:{s["id"]} | {s["ad"]}')
print()

# Odak
r = requests.get('http://localhost:8000/api/odak', timeout=10)
odak = r.json()
print(f'Odak: {len(odak)}')
for o in odak[:3]:
    print(f'  {o["id"]} | {o["ad"]}')
