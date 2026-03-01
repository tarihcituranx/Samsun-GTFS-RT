#!/usr/bin/env python3
"""
GTFS Static Feed Oluşturucu
============================
Samsun Transit veritabanından GTFS Static feed ZIP dosyası oluşturur.

Kullanım:
    python create_gtfs_static.py
"""

import sqlite3
import csv
import zipfile
import os
from datetime import datetime, date, timedelta

DB = "samsun_v25.db"
OUTPUT_ZIP = "samsun_gtfs_static.zip"

print("=" * 60)
print("  GTFS Static Feed Oluşturucu")
print("=" * 60)
print()

# Veritabanı bağlantısı
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Temp klasör
if not os.path.exists('gtfs_temp'):
    os.makedirs('gtfs_temp')

def write_csv(filename, headers, rows):
    """CSV dosyası yaz"""
    filepath = os.path.join('gtfs_temp', filename)
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"✅ {filename}: {len(rows)} kayıt")

# 1. agency.txt
print("\n📋 agency.txt oluşturuluyor...")
agency_data = [
    ['SAMULAS', 'Samulaş', 'https://samulas.com.tr', 'Europe/Istanbul', 'tr', '+90 362 431 10 12']
]
write_csv('agency.txt', 
    ['agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang', 'agency_phone'],
    agency_data)

# 2. routes.txt
print("\n🚌 routes.txt oluşturuluyor...")
routes = conn.execute("SELECT code, name, kat FROM hat ORDER BY code").fetchall()
route_data = []
for r in routes:
    # route_type: 0=Tram, 1=Metro, 3=Bus, 6=Cable Car, 4=Ferry
    if r['kat'] == 'tramvay':
        route_type = 0
    elif r['kat'] == 'teleferik':
        route_type = 6
    elif r['kat'] in ['tekne', 'feribot']:
        route_type = 4
    else:
        route_type = 3  # Bus
    
    # Renk (kategori bazlı)
    color_map = {
        'otobus': '1877F2',
        'ekspres': '9B59B6',
        'ring': 'F39C12',
        'havalimani': 'E74C3C',
        'tramvay': 'E67E22',
        'teleferik': 'E91E63',
        'tekne': '3498DB',
        'ilce': '1ABC9C'
    }
    color = color_map.get(r['kat'], '333333')
    
    route_data.append([
        r['code'],           # route_id
        'SAMULAS',          # agency_id
        r['code'],          # route_short_name
        r['name'],          # route_long_name
        route_type,         # route_type
        '',                 # route_url
        color,              # route_color
        'FFFFFF'            # route_text_color
    ])

write_csv('routes.txt',
    ['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url', 'route_color', 'route_text_color'],
    route_data)

# 3. stops.txt
print("\n📍 stops.txt oluşturuluyor...")
stops = conn.execute("SELECT DISTINCT id, ad, lat, lon FROM durak WHERE lat > 0 AND lon > 0").fetchall()
stop_data = []
for s in stops:
    stop_data.append([
        s['id'],            # stop_id
        s['ad'],            # stop_name
        s['lat'],           # stop_lat
        s['lon'],           # stop_lon
    ])

write_csv('stops.txt',
    ['stop_id', 'stop_name', 'stop_lat', 'stop_lon'],
    stop_data)

# 4. trips.txt (Basitleştirilmiş - her hat için 1 trip)
print("\n🚏 trips.txt oluşturuluyor...")
trip_data = []
for r in routes:
    trip_id = f"{r['code']}_trip_1"
    trip_data.append([
        r['code'],          # route_id
        'WD',               # service_id (Weekday)
        trip_id,            # trip_id
        '',                 # trip_headsign
        0                   # direction_id
    ])

write_csv('trips.txt',
    ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id'],
    trip_data)

# 5. stop_times.txt (Her trip için duraklar)
print("\n⏱️ stop_times.txt oluşturuluyor...")
stop_times_data = []
seq = 0

for r in routes:
    trip_id = f"{r['code']}_trip_1"
    
    # Bu hattın durakları
    hat_duraklari = conn.execute("""
        SELECT durak_id, sira 
        FROM hat_durak 
        WHERE hat = ? 
        ORDER BY sira
    """, (r['code'],)).fetchall()
    
    if not hat_duraklari:
        continue
    
    # İlk sefer 06:00'dan başlasın
    start_time = "06:00:00"
    
    for idx, durak in enumerate(hat_duraklari):
        # Her durak arası 2 dakika
        minutes = idx * 2
        hours = 6 + (minutes // 60)
        mins = minutes % 60
        arrival = f"{hours:02d}:{mins:02d}:00"
        
        stop_times_data.append([
            trip_id,                # trip_id
            arrival,                # arrival_time
            arrival,                # departure_time
            durak['durak_id'],      # stop_id
            idx + 1,                # stop_sequence
            '',                     # stop_headsign
            0,                      # pickup_type
            0                       # drop_off_type
        ])
        seq += 1

write_csv('stop_times.txt',
    ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'stop_headsign', 'pickup_type', 'drop_off_type'],
    stop_times_data)

# 6. calendar.txt (Servis günleri)
print("\n📅 calendar.txt oluşturuluyor...")
today = date.today()
start_date = today.strftime('%Y%m%d')
end_date = (today + timedelta(days=365)).strftime('%Y%m%d')

calendar_data = [
    ['WD', 1, 1, 1, 1, 1, 1, 1, start_date, end_date]  # Her gün
]

write_csv('calendar.txt',
    ['service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date'],
    calendar_data)

# 7. feed_info.txt (Opsiyonel ama önerilen)
print("\n📰 feed_info.txt oluşturuluyor...")
feed_info_data = [
    ['Samulaş', 'https://samulas.com.tr', 'tr', start_date, end_date, '1.0']
]
write_csv('feed_info.txt',
    ['feed_publisher_name', 'feed_publisher_url', 'feed_lang', 'feed_start_date', 'feed_end_date', 'feed_version'],
    feed_info_data)

conn.close()

# ZIP oluştur
print(f"\n📦 {OUTPUT_ZIP} oluşturuluyor...")
with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for filename in os.listdir('gtfs_temp'):
        filepath = os.path.join('gtfs_temp', filename)
        zipf.write(filepath, filename)

print(f"✅ ZIP oluşturuldu: {OUTPUT_ZIP}")

# Temp klasörü temizle
import shutil
shutil.rmtree('gtfs_temp')
print("🗑️  Geçici dosyalar temizlendi")

print()
print("=" * 60)
print("  ✨ GTFS Static Feed Hazır!")
print("=" * 60)
print()
print(f"📁 Dosya: {OUTPUT_ZIP}")
print(f"📊 Boyut: {os.path.getsize(OUTPUT_ZIP) / 1024:.1f} KB")
print()
print("🔍 Validator'da Test:")
print("   1. https://gtfs-validator.mobilitydata.org/ aç")
print(f"   2. {OUTPUT_ZIP} dosyasını yükle")
print("   3. Validate'e tıkla")
print()
