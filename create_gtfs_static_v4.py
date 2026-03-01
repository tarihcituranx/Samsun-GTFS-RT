#!/usr/bin/env python3
"""
GTFS Static Feed Oluşturucu v4 - KUSURSUZ SÜRÜM
=================================================
Samsun Transit veritabanından GTFS Static feed ZIP dosyası oluşturur.

DÜZELTİLEN SORUNLAR (v4):
- ✅ foreign_key_violation (shape_teleferik missing) -> Shape filtreleme mantığı düzeltildi
- ✅ translation_foreign_key_violation -> Normalized route_id kullanımı eklendi
- ✅ mixed_case (routes) -> Title Case dönüştürüldü
- ✅ unused_stops -> Filtrasyon sıkılaştırıldı (sadece usable routes durakları)
- ✅ trip_coverage -> Calendar otomatik güncellemeli

Kullanım:
    python create_gtfs_static_v4.py
"""

import sqlite3
import csv
import zipfile
import os
import math
import unicodedata
import re
from datetime import datetime, date, timedelta

DB = "samsun_v25.db"
OUTPUT_ZIP = "samsun_gtfs_static.zip"

print("=" * 60)
print("  GTFS Static Feed Oluşturucu v4 - KUSURSUZ SÜRÜM")
print("=" * 60)
print()

# === YARDIMCI FONKSİYONLAR ===

def normalize_turkish(text):
    """Türkçe karakterleri ASCII eşdeğerlerine dönüştür"""
    if not text:
        return ""
    
    # Türkçe karakter eşleştirmesi
    tr_map = {
        'ş': 's', 'Ş': 'S',
        'ğ': 'g', 'Ğ': 'G', 
        'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O',
        'ç': 'c', 'Ç': 'C',
        'ı': 'i', 'İ': 'I',
        # Diğer özel karakterler
        '²': '2', '³': '3',
        '°': '', '®': '',
        '™': '', '©': '',
    }
    
    result = str(text)
    for tr_char, ascii_char in tr_map.items():
        result = result.replace(tr_char, ascii_char)
    
    # Kalan non-ASCII karakterleri temizle
    result = unicodedata.normalize('NFKD', result)
    result = ''.join(c for c in result if ord(c) < 128)
    
    return result.strip()

def format_route_short_name(code):
    """Route short name formatla (max 12 karakter, Title Case)"""
    if not code:
        return ""
    
    name = normalize_turkish(str(code).strip())
    
    # Maksimum 12 karakter
    if len(name) > 12:
        name = name.replace(" - ", "-")
        name = name.replace(" ", "")
        if len(name) > 12:
            name = name[:12]
    
    return name.title()

def format_route_id(code):
    """Route ID formatla (lowercase, ASCII, boşluksuz)"""
    if not code:
        return ""
    result = normalize_turkish(str(code).strip().lower())
    result = result.replace(" ", "_").replace("-", "_")
    result = re.sub(r'[^a-z0-9_]', '', result)
    return result

def format_route_long_name(name, short_name):
    """Route long name formatla (Title Case, short name içermemeli)"""
    if not name:
        return ""
    
    result = normalize_turkish(str(name).strip())
    short_normalized = normalize_turkish(short_name) if short_name else ""
    
    if short_normalized:
        # Short name'i çıkar
        patterns = [
            f"^{re.escape(short_normalized)}\\s*[-–]?\\s*",  # Başta
            f"\\s*[-–]?\\s*{re.escape(short_normalized)}$",  # Sonda
            f"^{re.escape(short_normalized)}\\s+",           # Başta boşlukla
        ]
        for pattern in patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    
    # Title Case uygula
    result = result.title()
    
    corrections = {
        "Omu": "OMU", "Tttm": "TTTM", "Bel.Evleri": "Bel.Evleri",
        "B.Kolpinar": "B.Kolpinar", "Dsi": "DSI",
    }
    for wrong, correct in corrections.items():
        result = result.replace(wrong, correct)
    
    return result.strip()

def format_stop_name(name):
    """Stop name formatla (Title Case, ASCII)"""
    if not name:
        return ""
    result = normalize_turkish(str(name).strip())
    match = re.match(r'^(\d+)\s*(.*)$', result)
    if match:
        kod, isim = match.groups()
        return f"{kod} {isim.title()}".strip()
    return result.title()

def haversine(lat1, lon1, lat2, lon2):
    """İki nokta arası mesafe (metre)"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calculate_stop_times_fixed(duraklar, hat_tipi, ilk_kalkis="06:00:00"):
    """Gerçekçi durak saatleri hesapla"""
    HIZ_(hat_tipi) # Dummy call, defined below locally
    
    HIZ_AYARLARI = {
        'otobus': 25, 'ring': 30, 'ekspres': 35,
        'havalimani': 50, 'ilce': 60, 'tramvay': 20,
        'teleferik': 15, 'tekne': 40, 'odak': 45, 'samair': 50
    }
    DURAK_BEKLEME = {
        'otobus': 30, 'ring': 20, 'ekspres': 20,
        'havalimani': 60, 'ilce': 90, 'tramvay': 30,
        'teleferik': 0, 'tekne': 60, 'odak': 30, 'samair': 60
    }
    
    ortalama_hiz = HIZ_AYARLARI.get(hat_tipi, 25)
    bekleme_sn = DURAK_BEKLEME.get(hat_tipi, 30)
    
    stop_times = []
    h, m, s = map(int, ilk_kalkis.split(':'))
    current_time = h * 3600 + m * 60 + s
    prev_departure = current_time
    
    for i, durak in enumerate(duraklar):
        if i == 0:
            arrival = current_time
            departure = current_time
        else:
            onceki = duraklar[i - 1]
            mesafe_m = haversine(onceki['lat'], onceki['lon'], durak['lat'], durak['lon'])
            yol_mesafe_km = (mesafe_m * 1.3) / 1000.0
            seyahat_sn = int((yol_mesafe_km / ortalama_hiz) * 3600)
            if seyahat_sn < 60: seyahat_sn = 60
            
            arrival = prev_departure + seyahat_sn
            if i < len(duraklar) - 1:
                departure = arrival + bekleme_sn
            else:
                departure = arrival
        
        arr_str = f"{arrival//3600:02d}:{(arrival%3600)//60:02d}:{arrival%60:02d}"
        dep_str = f"{departure//3600:02d}:{(departure%3600)//60:02d}:{departure%60:02d}"
        stop_times.append((arr_str, dep_str))
        prev_departure = departure
    return stop_times

# Dummy definition to avoid syntax error above
def HIZ_(x): pass

# === ANA MANTIK ===

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Temp klasör
if os.path.exists('gtfs_temp'):
    import shutil
    shutil.rmtree('gtfs_temp')
os.makedirs('gtfs_temp')

def write_csv(filename, headers, rows):
    filepath = os.path.join('gtfs_temp', filename)
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  ✅ {filename}: {len(rows)} kayıt")

print("\n⚙️  Veri analizi ve ön işleme yapılıyor...")

# Rota sınıfı
class RouteInfo:
    def __init__(self, r):
        self.code = r['code']
        self.name = r['name']
        self.kat = r['kat']
        self.route_id = format_route_id(r['code'])
        self.short_name = format_route_short_name(r['code'])
        self.long_name = format_route_long_name(r['name'], r['code'])

all_routes_raw = conn.execute("SELECT code, name, kat FROM hat ORDER BY code").fetchall()
all_routes = [RouteInfo(r) for r in all_routes_raw]

usable_routes = []
used_stop_ids = set()
valid_shape_ids = set()

for r in all_routes:
    hat_duraklari = conn.execute("""
        SELECT durak_id, sira, lat, lon
        FROM hat_durak WHERE hat = ? ORDER BY sira
    """, (r.code,)).fetchall()
    
    # 1. En az 2 durak olmalı
    if len(hat_duraklari) < 2:
        continue
        
    usable_routes.append(r)
    
    # 2. Kullanılan durakları kaydet
    for d in hat_duraklari:
        used_stop_ids.add(str(d['durak_id']))
        
    # 3. Shape geçerlilik kontrolü
    shape_id = f"shape_{r.route_id}"
    distinct_points = 0
    prev_lat, prev_lon = None, None
    for d in hat_duraklari:
        if d['lat'] != prev_lat or d['lon'] != prev_lon:
            distinct_points += 1
            prev_lat, prev_lon = d['lat'], d['lon']
            
    if distinct_points >= 2:
        valid_shape_ids.add(shape_id)

print(f"  📊 Toplam Rota: {len(all_routes)}")
print(f"  📊 Kullanılabilir Rota: {len(usable_routes)}")
print(f"  📊 Aktif Duraklar: {len(used_stop_ids)}")
print(f"  📊 Geçerli Shape: {len(valid_shape_ids)}")

# === 1. AGENCY.TXT ===
print("\n📋 agency.txt oluşturuluyor...")
agency_data = [[
    'samulas', 'Samsun Public Transportation', 'https://samulas.com.tr',
    'Europe/Istanbul', 'tr', '+90 362 431 10 12',
    'https://samulas.com.tr/ucret-tarifesi', 'info@samulas.com.tr'
]]
write_csv('agency.txt', 
    ['agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang', 'agency_phone', 'agency_fare_url', 'agency_email'],
    agency_data)

# === 2. ROUTES.TXT ===
print("\n🚌 routes.txt oluşturuluyor...")
route_data = []
for r in all_routes:  # Tüm rotaları listele (GTFS gereği trips'de olmasa da olabilir)
    # route_type belirleme
    if r.kat == 'tramvay': r_type = 0
    elif r.kat == 'teleferik': r_type = 6
    elif r.kat in ['tekne', 'feribot']: r_type = 4
    else: r_type = 3
    
    color_map = {
        'otobus': '1877F2', 'ekspres': '9B59B6', 'ring': 'F39C12',
        'havalimani': 'E74C3C', 'tramvay': 'E67E22', 'teleferik': 'E91E63',
        'tekne': '3498DB', 'ilce': '1ABC9C', 'odak': '27AE60', 'samair': 'E74C3C'
    }
    
    route_data.append([
        r.route_id, 'samulas', r.short_name, r.long_name, r_type, '',
        color_map.get(r.kat, '333333'), 'FFFFFF'
    ])
write_csv('routes.txt',
    ['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url', 'route_color', 'route_text_color'],
    route_data)

# === 3. STOPS.TXT ===
print("\n🚏 stops.txt oluşturuluyor...")
stops = conn.execute("SELECT DISTINCT id, ad, lat, lon FROM durak WHERE lat > 0").fetchall()
stop_data = []
for s in stops:
    s_id = str(s['id'])
    if s_id in used_stop_ids:
        stop_data.append([
            s_id, format_stop_name(s['ad']), s['lat'], s['lon'], 0, 1
        ])
write_csv('stops.txt',
    ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'location_type', 'wheelchair_boarding'],
    stop_data)

# === 4. SHARED FUNCTIONS FOR TRIPS ===
def get_last_stop_name(hat_code):
    last = conn.execute("SELECT d.ad FROM hat_durak hd JOIN durak d ON hd.durak_id = d.id WHERE hd.hat = ? ORDER BY hd.sira DESC LIMIT 1", (hat_code,)).fetchone()
    return format_stop_name(last['ad']) if last else ""

# === 5. TRIPS.TXT & 6. STOP_TIMES.TXT & 8. SHAPES.TXT ===
print("\n🚎 trips, stop_times ve shapes oluşturuluyor...")
trip_data, stop_times_data, shape_data = [], [], []

for r in usable_routes:
    trip_id = f"{r.route_id}_trip_1"
    shape_id = f"shape_{r.route_id}"
    
    # Shape ID kullanımı (geçersizse boş bırak)
    final_shape_id = shape_id if shape_id in valid_shape_ids else ""
    
    # Trip Ekle
    bikes = 1 if r.kat not in ['tramvay', 'teleferik', 'tekne'] else 2
    trip_data.append([
        r.route_id, 'wd', trip_id, get_last_stop_name(r.code), 0,
        final_shape_id, 1, bikes
    ])
    
    # Durak verileri
    duraklar = conn.execute("""
        SELECT durak_id, sira, lat, lon FROM hat_durak WHERE hat = ? ORDER BY sira
    """, (r.code,)).fetchall()
    
    # Stop Times Hesapla
    times = calculate_stop_times_fixed([dict(d) for d in duraklar], r.kat)
    for idx, (d, (arr, dep)) in enumerate(zip(duraklar, times)):
        stop_times_data.append([
            trip_id, arr, dep, str(d['durak_id']), idx+1, '', 0, 0
        ])
    
    # Shape Data (Sadece valid ise)
    if final_shape_id:
        total_dist = 0.0
        prev_lat, prev_lon = None, None
        seq = 0
        for i, d in enumerate(duraklar):
            lat, lon = d['lat'], d['lon']
            if prev_lat == lat and prev_lon == lon: continue
            
            if prev_lat:
                total_dist += haversine(prev_lat, prev_lon, lat, lon)
            
            seq += 1
            shape_data.append([
                final_shape_id, lat, lon, seq, round(total_dist, 2)
            ])
            prev_lat, prev_lon = lat, lon

write_csv('trips.txt',
    ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id', 'shape_id', 'wheelchair_accessible', 'bikes_allowed'],
    trip_data)
write_csv('stop_times.txt',
    ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'stop_headsign', 'pickup_type', 'drop_off_type'],
    stop_times_data)
write_csv('shapes.txt',
    ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence', 'shape_dist_traveled'],
    shape_data)

# === 7. CALENDAR.TXT ===
today = date.today()
start_s = today.strftime('%Y%m%d')
end_s = (today + timedelta(days=365)).strftime('%Y%m%d')
write_csv('calendar.txt',
    ['service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date'],
    [['wd', 1, 1, 1, 1, 1, 1, 1, start_s, end_s]])

# === 9. FEED_INFO.TXT ===
write_csv('feed_info.txt',
    ['feed_publisher_name', 'feed_publisher_url', 'feed_lang', 'feed_start_date', 'feed_end_date', 'feed_version', 'feed_contact_email', 'feed_contact_url'],
    [[
        'Samsun Metropolitan Municipality', 'https://www.samsun.bel.tr', 'tr',
        start_s, end_s, '4.0', 'info@samulas.com.tr', 'https://samulas.com.tr'
    ]])

# === 10. ATTRIBUTIONS.TXT ===
write_csv('attributions.txt',
    ['attribution_id', 'agency_id', 'route_id', 'trip_id', 'organization_name', 'is_producer', 'is_operator', 'is_authority', 'attribution_url', 'attribution_email', 'attribution_phone'],
    [
        ['samulas_data', 'samulas', '', '', 'Samsun Public Transportation', 0, 1, 0, 'https://samulas.com.tr', 'info@samulas.com.tr', '+90 362 431 10 12'],
        ['samsun_bel', '', '', '', 'Samsun Metropolitan Municipality', 1, 0, 1, 'https://www.samsun.bel.tr', 'cm@samsun.bel.tr', '+90 362 431 00 00']
    ])

# === 11. TRANSLATIONS.TXT ===
print("\n🌍 translations.txt oluşturuluyor...")
translations_data = [
    ['agency', 'agency_name', 'en', 'Samsun Public Transportation', 'samulas', ''],
    ['feed_info', 'feed_publisher_name', 'en', 'Samsun Metropolitan Municipality', '', ''],
]
tr_to_en = {
    'Merkez': 'Center', 'Terminal': 'Terminal', 'Hastane': 'Hospital',
    'Universite': 'University', 'Havaalani': 'Airport', 'Otogar': 'Bus Station',
    'Liman': 'Port', 'Sahil': 'Coast', 'Istasyon': 'Station',
    'Sanayi': 'Industrial', 'Organize': 'Organized', 'Cadde': 'Avenue',
    'Meydan': 'Square', 'Pazar': 'Market', 'Cami': 'Mosque',
    'Park': 'Park', 'Koy': 'Village', 'Mahalle': 'Neighborhood'
}
for r in all_routes:
    en_name = r.long_name
    for tr, en in tr_to_en.items():
        en_name = en_name.replace(tr, en)
    if en_name != r.long_name:
        translations_data.append(['routes', 'route_long_name', 'en', en_name, r.route_id, '' ])

write_csv('translations.txt',
    ['table_name', 'field_name', 'language', 'translation', 'record_id', 'record_sub_id'],
    translations_data)

conn.close()

# === ZIP OLUŞTUR ===
print(f"\n📦 {OUTPUT_ZIP} oluşturuluyor...")
with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for filename in os.listdir('gtfs_temp'):
        filepath = os.path.join('gtfs_temp', filename)
        zipf.write(filepath, filename)

import shutil
shutil.rmtree('gtfs_temp')
print(f"  ✅ ZIP: {OUTPUT_ZIP} ({os.path.getsize(OUTPUT_ZIP)/1024:.1f} KB)")
print("\n✨ GTFS Static Feed v4 HAZIR! (Kusursuz)")
