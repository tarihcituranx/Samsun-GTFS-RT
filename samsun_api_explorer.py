# -*- coding: utf-8 -*-
"""
Samsun Belediyesi Otobüs Hareket Saatleri API Explorer
Bu script, Samsun Belediyesi'nin otobüs API'sini çağırır ve çıktıları gösterir.
Özel karakterler (Türkçe, -, /, vb.) doğru şekilde işlenir.
"""

import requests
import json
from datetime import datetime

# API Base URL
BASE_URL = "https://api.samsun.bel.tr/OHSSoapToJson"

# Encoding ayarları
import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def pretty_print(title, data, max_items=10):
    """Veriyi güzel formatlı olarak yazdır"""
    print("\n" + "=" * 60)
    print(f"📌 {title}")
    print("=" * 60)
    
    if isinstance(data, list):
        print(f"Toplam {len(data)} kayıt bulundu.")
        print("-" * 60)
        for i, item in enumerate(data[:max_items]):
            if isinstance(item, dict):
                for key, value in item.items():
                    print(f"  {key}: {value}")
                print("-" * 40)
            else:
                print(f"  {item}")
        if len(data) > max_items:
            print(f"\n  ... ve {len(data) - max_items} kayıt daha")
    elif isinstance(data, dict):
        for key, value in data.items():
            print(f"  {key}: {value}")
    else:
        print(data)

def get_lines():
    """Tüm hatları getir"""
    try:
        response = requests.get(f"{BASE_URL}/api/Asis/Lines", timeout=30)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hata: {response.status_code}")
            return None
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def get_orj_lines():
    """Orijinal hatları getir"""
    try:
        response = requests.get(f"{BASE_URL}/api/Asis/OrjLines", timeout=30)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hata: {response.status_code}")
            return None
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def get_stops_stations(line_code=None, stop_id=None):
    """Durakları getir"""
    try:
        params = {}
        if line_code:
            params['lineCode'] = line_code
        if stop_id:
            params['stopId'] = stop_id
        
        response = requests.get(f"{BASE_URL}/api/Asis/StopsStations", params=params, timeout=30)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hata: {response.status_code}")
            return None
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def get_smart_stations(station_id=None):
    """Akıllı durakları getir"""
    try:
        params = {}
        if station_id:
            params['stationId'] = station_id
        
        response = requests.get(f"{BASE_URL}/api/Asis/SmartStations", params=params, timeout=30)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hata: {response.status_code}")
            return None
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def get_line_directions(line_code):
    """Hat yönlerini getir"""
    try:
        params = {'lineCode': line_code}
        response = requests.get(f"{BASE_URL}/api/Asis/LineDirections", params=params, timeout=30)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hata: {response.status_code}")
            return None
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def get_real_time_data(line_code):
    """Gerçek zamanlı veri getir"""
    try:
        params = {'lineCode': line_code}
        response = requests.get(f"{BASE_URL}/api/Asis/RealTimeData", params=params, timeout=30)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hata: {response.status_code}")
            return None
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def get_schedules(line_code, schedule_date=None):
    """Sefer programını getir"""
    try:
        params = {'lineCode': line_code}
        if schedule_date:
            params['scheduleDate'] = schedule_date
        else:
            # Bugünün tarihini kullan
            params['scheduleDate'] = datetime.now().strftime('%Y-%m-%dT00:00:00')
        
        response = requests.get(f"{BASE_URL}/api/Asis/Schedules", params=params, timeout=30)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hata: {response.status_code}")
            return None
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def main():
    print("\n" + "🚌" * 30)
    print("SAMSUN BELEDİYESİ OTOBÜS API EXPLORER")
    print("🚌" * 30)
    
    line_code = None  # Başta tanımla
    
    # 1. Tüm hatları getir
    print("\n\n📍 1. TÜM HATLAR (Lines)")
    lines = get_lines()
    if lines:
        pretty_print("Hat Listesi", lines, max_items=15)
        
        # İlk hattın kodunu al (örnek için)
        if isinstance(lines, list) and len(lines) > 0:
            # Hat kodunu bul (farklı API formatlarına göre)
            first_line = lines[0]
            if isinstance(first_line, dict):
                line_code = first_line.get('HatKodu') or first_line.get('lineCode') or first_line.get('code') or first_line.get('hatKodu')
                if not line_code:
                    # İlk key'i dene
                    line_code = list(first_line.values())[0] if first_line else None
            else:
                line_code = str(first_line)
            
            print(f"\n💡 Örnek hat kodu: {line_code}")
    
    # 2. Orijinal hatları getir
    print("\n\n📍 2. ORİJİNAL HATLAR (OrjLines)")
    orj_lines = get_orj_lines()
    if orj_lines:
        pretty_print("Orijinal Hat Listesi", orj_lines, max_items=15)
    
    # 3. Durakları getir (örnek hat ile)
    print("\n\n📍 3. DURAKLAR (StopsStations)")
    if line_code:
        stops = get_stops_stations(line_code=line_code)
        if stops:
            pretty_print(f"Hat {line_code} Durakları", stops, max_items=10)
    else:
        # Parametresiz dene
        stops = get_stops_stations()
        if stops:
            pretty_print("Tüm Duraklar", stops, max_items=10)
    
    # 4. Akıllı durakları getir
    print("\n\n📍 4. AKILLI DURAKLAR (SmartStations)")
    smart_stations = get_smart_stations()
    if smart_stations:
        pretty_print("Akıllı Durak Listesi", smart_stations, max_items=10)
    
    # 5. Hat yönlerini getir
    if line_code:
        print(f"\n\n📍 5. HAT YÖNLERİ (LineDirections) - Hat: {line_code}")
        directions = get_line_directions(line_code)
        if directions:
            pretty_print(f"Hat {line_code} Yönleri", directions)
    
    # 6. Gerçek zamanlı veri
    if line_code:
        print(f"\n\n📍 6. GERÇEK ZAMANLI VERİ (RealTimeData) - Hat: {line_code}")
        realtime = get_real_time_data(line_code)
        if realtime:
            pretty_print(f"Hat {line_code} Gerçek Zamanlı Veri", realtime, max_items=10)
    
    # 7. Sefer programı
    if line_code:
        print(f"\n\n📍 7. SEFER PROGRAMI (Schedules) - Hat: {line_code}")
        schedules = get_schedules(line_code)
        if schedules:
            pretty_print(f"Hat {line_code} Sefer Programı", schedules, max_items=10)
    
    print("\n\n" + "=" * 60)
    print("✅ API Explorer tamamlandı!")
    print("=" * 60)

if __name__ == "__main__":
    main()
