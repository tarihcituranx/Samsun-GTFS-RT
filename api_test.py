#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API Explorer - Tüm endpoint'leri test et ve yapıyı anla"""
import requests
import json

BASE = 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis'

def test_endpoint(name, url, params=None):
    print("="*60)
    print(f"ENDPOINT: {name}")
    print(f"URL: {url}")
    print("="*60)
    try:
        r = requests.get(url, params=params, timeout=30)
        d = r.json()
        print(f"Status Code: {d.get('statusCode', 'N/A')}")
        print(f"Message: {d.get('message', 'N/A')}")
        
        data = d.get('data', [])
        print(f"Data Count: {len(data) if isinstance(data, list) else 'not a list'}")
        
        if data and isinstance(data, list) and len(data) > 0:
            print(f"Keys: {list(data[0].keys())}")
            print("\nSample Items:")
            for i, item in enumerate(data[:3]):
                print(f"  [{i}] {json.dumps(item, ensure_ascii=False)}")
        print()
        return d
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# Test all endpoints
print("\n" + "="*60)
print("SAMSUN ASIS API EXPLORER")
print("="*60 + "\n")

# 1. Lines
lines_data = test_endpoint("Lines", f"{BASE}/Lines")

# 2. OrjLines 
test_endpoint("OrjLines", f"{BASE}/OrjLines")

# 3. StopsStations (tüm duraklar)
test_endpoint("StopsStations (all)", f"{BASE}/StopsStations")

# 4. Bir hat için duraklar
if lines_data and lines_data.get('data'):
    sample_line = lines_data['data'][0].get('lineCode', '')
    if sample_line:
        test_endpoint(f"StopsStations (lineCode={sample_line})", f"{BASE}/StopsStations", {'lineCode': sample_line})

# 5. SmartStations
test_endpoint("SmartStations", f"{BASE}/SmartStations")

# 6. LineDirections
if lines_data and lines_data.get('data'):
    sample_line = lines_data['data'][0].get('lineCode', '')
    test_endpoint(f"LineDirections (lineCode={sample_line})", f"{BASE}/LineDirections", {'lineCode': sample_line})

# 7. RealTimeData
if lines_data and lines_data.get('data'):
    sample_line = lines_data['data'][0].get('lineCode', '')
    test_endpoint(f"RealTimeData (lineCode={sample_line})", f"{BASE}/RealTimeData", {'lineCode': sample_line})

# 8. Schedules
if lines_data and lines_data.get('data'):
    sample_line = lines_data['data'][0].get('lineCode', '')
    test_endpoint(f"Schedules (lineCode={sample_line})", f"{BASE}/Schedules", {'lineCode': sample_line, 'scheduleDate': '2026-02-10'})

print("\n" + "="*60)
print("ÖZET")
print("="*60)
if lines_data and lines_data.get('data'):
    print(f"Toplam Hat Sayısı: {len(lines_data['data'])}")
    # Hat kategorilerini say
    categories = {}
    for line in lines_data['data']:
        code = line.get('lineCode', '')
        if code:
            first_char = code[0].upper()
            categories[first_char] = categories.get(first_char, 0) + 1
    print(f"Hat Kategorileri: {categories}")
