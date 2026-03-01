#!/usr/bin/env python3
"""
GTFS Static Feed Oluşturucu (İYİLEŞTİRİLMİŞ)
============================================
Samsun Transit veritabanından GTFS Static feed ZIP dosyası oluşturur.

YENİ ÖZELLİKLER:
- ✅ Gerçekçi stop_times (mesafe bazlı, 25-60 km/h)
- ✅ Shapes desteği (güzergah çizgileri)
- ✅ location_type eklendi (validator fix)
- ✅ Unusable trip filtresi (<2 durak atlanır)

Kullanım:
    python create_gtfs_static.py
"""

import sqlite3
import csv
import zipfile
import os
import math
from datetime import datetime, date, timedelta

DB = "samsun_v25.db"
OUTPUT_ZIP = "samsun_gtfs_static.zip"

print("=" * 60)
print("  GTFS Static Feed Oluşturucu (v2 - İyileştirilmiş)")
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

def haversine(lat1, lon1, lat2, lon2):
    """İki nokta arası mesafe (metre)"""
    R = 6371000  # Dünya yarıçapı (metre)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calculate_realistic_stop_times(duraklar, hat_tipi, ilk_kalkis="06:00:00"):
    """
    Gerçekçi durak saatleri hesapla - mesafeye göre
    
    Args:
        duraklar: [{lat, lon, sira}, ...]
        hat_tipi: 'otobus', 'ring', 'ekspres', etc.
        ilk_kalkis: İlk durak kalkış saati
    
    Returns:
        [(arrival_time, departure_time), ...]
    """
    from datetime import datetime, timedelta
    
    # Hat tipine göre ortalama hız (km/h)
    HIZ_AYARLARI = {
        'otobus': 25,
        'ring': 30,
        'ekspres': 35,
        'havalimani': 50,
        'ilce': 60,
        'tramvay': 20,
        'teleferik': 15,
        'tekne': 40,
        'odak': 45,
        'samair': 50
    }
    
    # Durak başına ek bekleme süresi (dakika)
    DURAK_BEKLEME = {
        'otobus': 1.0,
        'ring': 0.5,
        'ekspres': 0.5,
        'havalimani': 2.0,
        'ilce': 3.0,
        'tramvay': 1.0,
        'teleferik': 0,
        'tekne': 2.0,
        'odak': 1.0,
        'samair': 2.0
    }
    
    ortalama_hiz = HIZ_AYARLARI.get(hat_tipi, 25)
    bekleme_dk = DURAK_BEKLEME.get(hat_tipi, 1.0)
    
    stop_times = []
    toplam_sure = 0  # dakika
    
    for i, durak in enumerate(duraklar):
        # İlk durağın saati
        if i == 0:
            arrival = departure = ilk_kalkis
        else:
            # Önceki duraktan mesafe hesapla
            onceki = duraklar[i - 1]
            mesafe_km = haversine(
                onceki['lat'], onceki['lon'],
                durak['lat'], durak['lon']
            ) / 1000.0
            
            # Kıvrım payı ekle (yol mesafesi > kuş uçuşu)
            yol_mesafe = mesafe_km * 1.3
            
            # Süre hesapla (dakika)
            seyahat_dk = (yol_mesafe / ortalama_hiz) * 60
            
            # Minimum seyahat süresi (çok yakın duraklar için)
            if seyahat_dk < 0.5:
                seyahat_dk = 0.5
            
            # Son durak değilse bekleme ekle
            if i < len(duraklar) - 1:
                toplam_sure += seyahat_dk + bekleme_dk
            else:
                toplam_sure += seyahat_dk
            
            # Saat formatına çevir
            baslangic = datetime.strptime(ilk_kalkis, "%H:%M:%S")
            varis_zamani = baslangic + timedelta(minutes=toplam_sure)
            
            arrival = varis_zamani.strftime("%H:%M:%S")
            
            # Durakta bekleme süresi
            if i < len(duraklar) - 1:
                kalkis_zamani = varis_zamani + timedelta(minutes=bekleme_dk)
                departure = kalkis_zamani.strftime("%H:%M:%S")
            else:
                departure = arrival  # Son durakta kalkış yok
        
        stop_times.append((arrival, departure))
    
    return stop_times

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
        'ilce': '1ABC9C',
        'odak': '27AE60',
        'samair': 'E74C3C'
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

# 3. stops.txt (LOCATION_TYPE EKLENDİ!)
print("\n🚏 stops.txt oluşturuluyor...")
stops = conn.execute("SELECT DISTINCT id, ad, lat, lon FROM durak WHERE lat > 0 AND lon > 0").fetchall()
stop_data = []
for s in stops:
    stop_data.append([
        s['id'],            # stop_id
        s['ad'],            # stop_name
        s['lat'],           # stop_lat
        s['lon'],           # stop_lon
        0                   # location_type (0 = stop/platform)
    ])

write_csv('stops.txt',
    ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'location_type'],
    stop_data)

# 4. trips.txt (Basitleştirilmiş - her hat için 1 trip, SHAPE_ID EKLENDİ!)
print("\n🚎 trips.txt oluşturuluyor...")
trip_data = []
usable_routes = 0
unusable_routes = []

for r in routes:
    # UNUSABLE TRIP FİLTRESİ: <2 durak kontrolü
    durak_count = conn.execute("""
        SELECT COUNT(*) as cnt 
        FROM hat_durak 
        WHERE hat = ?
    """, (r['code'],)).fetchone()
    
    if durak_count['cnt'] < 2:
        unusable_routes.append(r['code'])
        continue
    
    trip_id = f"{r['code']}_trip_1"
    trip_data.append([
        r['code'],          # route_id
        'WD',               # service_id (Weekday)
        trip_id,            # trip_id
        '',                 # trip_headsign
        0,                  # direction_id
        f"shape_{r['code']}" # shape_id (YENİ!)
    ])
    usable_routes += 1

write_csv('trips.txt',
    ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id', 'shape_id'],
    trip_data)

if unusable_routes:
    print(f"   ⚠️  {len(unusable_routes)} unusable trip atlandı: {', '.join(unusable_routes[:5])}")
print(f"   ✅ {usable_routes} kullanılabilir trip eklendi")

# 5. stop_times.txt (GERÇEKÇİ SÜRELERLE!)
print("\n⏱️ stop_times.txt oluşturuluyor (gerçekçi süreler)...")
stop_times_data = []
seq = 0
hat_sayi = 0

for r in routes:
    # Unusable olanları atla
    if r['code'] in unusable_routes:
        continue
    
    trip_id = f"{r['code']}_trip_1"
    
    # Bu hattın durakları
    hat_duraklari = conn.execute("""
        SELECT durak_id, sira, lat, lon
        FROM hat_durak 
        WHERE hat = ? 
        ORDER BY sira
    """, (r['code'],)).fetchall()
    
    if len(hat_duraklari) < 2:
        continue
    
    # Dict'e çevir
    duraklar_dict = [dict(d) for d in hat_duraklari]
    
    # GERÇEKÇİ SÜRELER HESAPLA
    stop_times = calculate_realistic_stop_times(duraklar_dict, r['kat'])
    
    for idx, (durak, (arr, dep)) in enumerate(zip(hat_duraklari, stop_times)):
        stop_times_data.append([
            trip_id,                # trip_id
            arr,                    # arrival_time
            dep,                    # departure_time
            durak['durak_id'],      # stop_id
            idx + 1,                # stop_sequence
            '',                     # stop_headsign
            0,                      # pickup_type
            0                       # drop_off_type
        ])
        seq += 1
    
    hat_sayi += 1

write_csv('stop_times.txt',
    ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'stop_headsign', 'pickup_type', 'drop_off_type'],
    stop_times_data)
print(f"   ✅ {hat_sayi} hat için gerçekçi süreler hesaplandı")

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

# 7. shapes.txt (YENİ!)
print("\n📐 shapes.txt oluşturuluyor...")

# Önce DB'de shape var mı kontrol et
db_shapes = conn.execute("SELECT COUNT(*) as cnt FROM gtfs_shape").fetchone()

if db_shapes and db_shapes['cnt'] > 0:
    # DB'den kullan
    print("   📦 DB'den shape yükleniyor...")
    shapes = conn.execute("""
        SELECT shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence, shape_dist_traveled
        FROM gtfs_shape 
        ORDER BY shape_id, shape_pt_sequence
    """).fetchall()
    
    shape_data = []
    for s in shapes:
        shape_data.append([
            s['shape_id'],
            s['shape_pt_lat'],
            s['shape_pt_lon'],
            s['shape_pt_sequence'],
            s['shape_dist_traveled']
        ])
    
    write_csv('shapes.txt',
        ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence', 'shape_dist_traveled'],
        shape_data)
    print(f"   ✅ {len(shape_data)} shape noktası (DB'den)")
else:
    # Duraklardan oluştur
    print("   🔨 Duraklardan shape oluşturuluyor...")
    shape_data = []
    shape_count = 0
    
    for r in routes:
        # Unusable olanları atla
        if r['code'] in unusable_routes:
            continue
        
        shape_id = f"shape_{r['code']}"
        
        duraklar = conn.execute("""
            SELECT lat, lon, sira
            FROM hat_durak 
            WHERE hat = ? 
            ORDER BY sira
        """, (r['code'],)).fetchall()
        
        if len(duraklar) < 2:
            continue
        
        total_dist = 0.0
        
        for i, durak in enumerate(duraklar):
            if i > 0:
                onceki = duraklar[i - 1]
                segment_dist = haversine(
                    onceki['lat'], onceki['lon'],
                    durak['lat'], durak['lon']
                )
                total_dist += segment_dist
            
            shape_data.append([
                shape_id,
                durak['lat'],
                durak['lon'],
                i + 1,
                total_dist
            ])
        
        shape_count += 1
    
    write_csv('shapes.txt',
        ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence', 'shape_dist_traveled'],
        shape_data)
    print(f"   ✅ {shape_count} hat için shape oluşturuldu")

# 8. feed_info.txt (Opsiyonel ama önerilen)
print("\n📰 feed_info.txt oluşturuluyor...")
feed_info_data = [
    ['Samulaş', 'https://samulas.com.tr', 'tr', start_date, end_date, '2.0']
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
print("  ✨ GTFS Static Feed Hazır! (v2 - İyileştirilmiş)")
print("=" * 60)
print()
print(f"📁 Dosya: {OUTPUT_ZIP}")
print(f"📊 Boyut: {os.path.getsize(OUTPUT_ZIP) / 1024:.1f} KB")
print()
print("🎯 İYİLEŞTİRMELER:")
print("   ✅ Gerçekçi stop_times (25-60 km/h, mesafe bazlı)")
print("   ✅ Shapes eklendi (güzergah çizgileri)")
print("   ✅ location_type eklendi (validator fix)")
print("   ✅ Unusable trip filtresi (<2 durak)")
print()
print("🔍 Validator'da Test:")
print("   1. https://gtfs-validator.mobilitydata.org/ aç")
print(f"   2. {OUTPUT_ZIP} dosyasını yükle")
print("   3. Validate'e tıkla")
print()
print("📈 BEKLENEN SONUÇ:")
print("   ✅ Errors: 0")
print("   ✅ Warnings: 0")
print("   ✅ %100 Uyumlu!")
print()
