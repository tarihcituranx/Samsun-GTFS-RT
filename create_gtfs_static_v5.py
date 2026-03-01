#!/usr/bin/env python3
"""
GTFS Static Feed Oluşturucu v5 - ÇOK DİLLİ SÜRÜM (GLOBAL)
==========================================================
Samsun Transit veritabanından GTFS Static feed ZIP dosyası oluşturur.

YENİLİKLER (v5):
- 🌍 ÇOKLU DİL DESTEĞİ: İngilizce, Almanca, Fransızca, Rusça, Arapça
- ✅ trip_coverage warning fix -> Start date (Bugün - 1 gün) yapıldı
- ✅ Tüm önceki düzeltmeler korundu (Title Case, Normalized IDs, Shape Filters)

Kullanım:
    python create_gtfs_static_v5.py
"""

import sqlite3
import csv
import zipfile
import os
import shutil
import math
import unicodedata
import re
from datetime import datetime, date, timedelta

DB = "samsun_v25.db"
OUTPUT_ZIP = "samsun_gtfs_static.zip"

print("=" * 60)
print("  GTFS Static Feed Oluşturucu v5 - ÇOK DİLLİ GLOBAL SÜRÜM")
print("=" * 60)
print()

# === YARDIMCI FONKSİYONLAR ===

def normalize_turkish(text):
    """Türkçe karakterleri ASCII eşdeğerlerine dönüştür"""
    if not text:
        return ""
    
    tr_map = {
        'ş': 's', 'Ş': 'S', 'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C', 'ı': 'i', 'İ': 'I',
        '²': '2', '³': '3', '°': '', '®': '', '™': '', '©': '',
    }
    
    result = str(text)
    for tr_char, ascii_char in tr_map.items():
        result = result.replace(tr_char, ascii_char)
    
    result = unicodedata.normalize('NFKD', result)
    result = ''.join(c for c in result if ord(c) < 128)
    return result.strip()

def format_route_short_name(code):
    """Route short name formatla (max 12 karakter, Title Case)"""
    if not code: return ""
    name = normalize_turkish(str(code).strip())
    if len(name) > 12:
        name = name.replace(" - ", "-").replace(" ", "")
        if len(name) > 12: name = name[:12]
    return name.title()

def format_route_id(code):
    """Route ID formatla (lowercase, ASCII, boşluksuz)"""
    if not code: return ""
    result = normalize_turkish(str(code).strip().lower())
    result = result.replace(" ", "_").replace("-", "_")
    result = re.sub(r'[^a-z0-9_]', '', result)
    return result

def format_route_long_name(name, short_name):
    """Route long name formatla (Title Case, short name içermemeli)"""
    if not name: return ""
    result = normalize_turkish(str(name).strip())
    short_normalized = normalize_turkish(short_name) if short_name else ""
    
    if short_normalized:
        patterns = [
            f"^{re.escape(short_normalized)}\\s*[-–]?\\s*",
            f"\\s*[-–]?\\s*{re.escape(short_normalized)}$",
            f"^{re.escape(short_normalized)}\\s+",
        ]
        for pattern in patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    
    result = result.title()
    corrections = {"Omu": "OMU", "Tttm": "TTTM", "Bel.Evleri": "Bel.Evleri", "Dsi": "DSI"}
    for wrong, correct in corrections.items():
        result = result.replace(wrong, correct)
    return result.strip()

def format_stop_name(name):
    """Stop name formatla (Title Case, ASCII)"""
    if not name: return ""
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
    HIZ_AYARLARI = {
        'otobus': 25, 'ring': 30, 'ekspres': 35, 'havalimani': 50, 'ilce': 60,
        'tramvay': 20, 'teleferik': 15, 'tekne': 40, 'odak': 45, 'samair': 50
    }
    DURAK_BEKLEME = {
        'otobus': 30, 'ring': 20, 'ekspres': 20, 'havalimani': 60, 'ilce': 90,
        'tramvay': 30, 'teleferik': 0, 'tekne': 60, 'odak': 30, 'samair': 60
    }
    ortalama_hiz = HIZ_AYARLARI.get(hat_tipi, 25)
    bekleme_sn = DURAK_BEKLEME.get(hat_tipi, 30)
    
    stop_times = []
    h, m, s = map(int, ilk_kalkis.split(':'))
    current_time = h * 3600 + m * 60 + s
    prev_departure = current_time
    
    for i, durak in enumerate(duraklar):
        if i == 0:
            arrival, departure = current_time, current_time
        else:
            onceki = duraklar[i - 1]
            mesafe_m = haversine(onceki['lat'], onceki['lon'], durak['lat'], durak['lon'])
            yol_mesafe_km = (mesafe_m * 1.3) / 1000.0
            seyahat_sn = int((yol_mesafe_km / ortalama_hiz) * 3600)
            if seyahat_sn < 60: seyahat_sn = 60
            
            arrival = prev_departure + seyahat_sn
            departure = arrival + (bekleme_sn if i < len(duraklar) - 1 else 0)
        
        arr_str = f"{arrival//3600:02d}:{(arrival%3600)//60:02d}:{arrival%60:02d}"
        dep_str = f"{departure//3600:02d}:{(departure%3600)//60:02d}:{departure%60:02d}"
        stop_times.append((arr_str, dep_str))
        prev_departure = departure
    return stop_times

# === ANA MANTIK ===

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

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

class RouteInfo:
    def __init__(self, r):
        self.code, self.name, self.kat = r['code'], r['name'], r['kat']
        self.route_id = format_route_id(r['code'])
        self.short_name = format_route_short_name(r['code'])
        self.long_name = format_route_long_name(r['name'], r['code'])

all_routes_raw = conn.execute("SELECT code, name, kat FROM hat ORDER BY code").fetchall()
all_routes = [RouteInfo(r) for r in all_routes_raw]

usable_routes = []
used_stop_ids = set()
valid_shape_ids = set()

for r in all_routes:
    hat_duraklari = conn.execute("SELECT durak_id, sira, lat, lon FROM hat_durak WHERE hat = ? ORDER BY sira", (r.code,)).fetchall()
    
    if len(hat_duraklari) < 2: continue
    usable_routes.append(r)
    
    for d in hat_duraklari: used_stop_ids.add(str(d['durak_id']))
        
    shape_id = f"shape_{r.route_id}"
    distinct_points = 0
    prev_lat, prev_lon = None, None
    for d in hat_duraklari:
        if d['lat'] != prev_lat or d['lon'] != prev_lon:
            distinct_points += 1
            prev_lat, prev_lon = d['lat'], d['lon']
    if distinct_points >= 2: valid_shape_ids.add(shape_id)

print(f"  📊 Toplam Rota: {len(all_routes)}")
print(f"  📊 Kullanılabilir: {len(usable_routes)}")
print(f"  📊 Aktif Durak: {len(used_stop_ids)}")

# === DOSYA OLUŞTURMA ===

# 1. AGENCY
print("\n📋 agency.txt oluşturuluyor...")
write_csv('agency.txt', 
    ['agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang', 'agency_phone', 'agency_fare_url', 'agency_email'],
    [['samulas', 'Samsun Public Transportation', 'https://samulas.com.tr', 'Europe/Istanbul', 'tr', '+90 362 431 10 12', 'https://samulas.com.tr/ucret-tarifesi', 'info@samulas.com.tr']])

# 2. ROUTES
print("\n🚌 routes.txt oluşturuluyor...")
route_data = []
color_map = {'otobus': '1877F2', 'ekspres': '9B59B6', 'ring': 'F39C12', 'havalimani': 'E74C3C', 'tramvay': 'E67E22', 'teleferik': 'E91E63', 'tekne': '3498DB', 'ilce': '1ABC9C', 'odak': '27AE60', 'samair': 'E74C3C'}
for r in all_routes:
    r_type = 0 if r.kat == 'tramvay' else (6 if r.kat == 'teleferik' else (4 if r.kat in ['tekne', 'feribot'] else 3))
    route_data.append([r.route_id, 'samulas', r.short_name, r.long_name, r_type, '', color_map.get(r.kat, '333333'), 'FFFFFF'])
write_csv('routes.txt', ['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url', 'route_color', 'route_text_color'], route_data)

# 3. STOPS
print("\n🚏 stops.txt oluşturuluyor...")
stops = conn.execute("SELECT DISTINCT id, ad, lat, lon FROM durak WHERE lat > 0").fetchall()
stop_data = []
for s in stops:
    if str(s['id']) in used_stop_ids:
        stop_data.append([str(s['id']), format_stop_name(s['ad']), s['lat'], s['lon'], 0, 1])
write_csv('stops.txt', ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'location_type', 'wheelchair_boarding'], stop_data)

# 4-6-8. TRIPS, STOP_TIMES, SHAPES
print("\n🚎 trips, stop_times ve shapes oluşturuluyor...")
trip_data, stop_times_data, shape_data = [], [], []

def get_last_stop_name(hat_code):
    last = conn.execute("SELECT d.ad FROM hat_durak hd JOIN durak d ON hd.durak_id = d.id WHERE hd.hat = ? ORDER BY hd.sira DESC LIMIT 1", (hat_code,)).fetchone()
    return format_stop_name(last['ad']) if last else ""

for r in usable_routes:
    trip_id = f"{r.route_id}_trip_1"
    shape_id = f"shape_{r.route_id}"
    final_shape_id = shape_id if shape_id in valid_shape_ids else ""
    bikes = 1 if r.kat not in ['tramvay', 'teleferik', 'tekne'] else 2
    
    trip_data.append([r.route_id, 'wd', trip_id, get_last_stop_name(r.code), 0, final_shape_id, 1, bikes])
    
    duraklar = conn.execute("SELECT durak_id, sira, lat, lon FROM hat_durak WHERE hat = ? ORDER BY sira", (r.code,)).fetchall()
    times = calculate_stop_times_fixed([dict(d) for d in duraklar], r.kat)
    
    for idx, (d, (arr, dep)) in enumerate(zip(duraklar, times)):
        stop_times_data.append([trip_id, arr, dep, str(d['durak_id']), idx+1, '', 0, 0])
    
    if final_shape_id:
        total_dist, prev_lat, prev_lon, seq = 0.0, None, None, 0
        for d in duraklar:
            lat, lon = d['lat'], d['lon']
            if prev_lat == lat and prev_lon == lon: continue
            if prev_lat: total_dist += haversine(prev_lat, prev_lon, lat, lon)
            seq += 1
            shape_data.append([final_shape_id, lat, lon, seq, round(total_dist, 2)])
            prev_lat, prev_lon = lat, lon

write_csv('trips.txt', ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id', 'shape_id', 'wheelchair_accessible', 'bikes_allowed'], trip_data)
write_csv('stop_times.txt', ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'stop_headsign', 'pickup_type', 'drop_off_type'], stop_times_data)
write_csv('shapes.txt', ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence', 'shape_dist_traveled'], shape_data)

# 7. CALENDAR (FIX: Start date = Yesterday)
today = date.today()
yesterday = today - timedelta(days=1)
start_s = yesterday.strftime('%Y%m%d')
end_s = (today + timedelta(days=365)).strftime('%Y%m%d')
write_csv('calendar.txt', ['service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date'], [['wd', 1, 1, 1, 1, 1, 1, 1, start_s, end_s]])

# 9. FEED_INFO
write_csv('feed_info.txt', ['feed_publisher_name', 'feed_publisher_url', 'feed_lang', 'feed_start_date', 'feed_end_date', 'feed_version', 'feed_contact_email', 'feed_contact_url'], [['Samsun Metropolitan Municipality', 'https://www.samsun.bel.tr', 'tr', start_s, end_s, '5.0', 'info@samulas.com.tr', 'https://samulas.com.tr']])

# 10. ATTRIBUTIONS
write_csv('attributions.txt', ['attribution_id', 'agency_id', 'route_id', 'trip_id', 'organization_name', 'is_producer', 'is_operator', 'is_authority', 'attribution_url', 'attribution_email', 'attribution_phone'], [
    ['samulas_data', 'samulas', '', '', 'Samsun Public Transportation', 0, 1, 0, 'https://samulas.com.tr', 'info@samulas.com.tr', '+90 362 431 10 12'],
    ['samsun_bel', '', '', '', 'Samsun Metropolitan Municipality', 1, 0, 1, 'https://www.samsun.bel.tr', 'cm@samsun.bel.tr', '+90 362 431 00 00']
])

# 11. TRANSLATIONS (ÇOK DİLLİ)
print("\n🌍 translations.txt oluşturuluyor (EN, DE, FR, RU, AR)...")
translations_data = []

# Statik çeviriler
base_translations = [
    # Agency
    ('agency', 'agency_name', 'Samsun Public Transportation', 'samulas', 'en'),
    ('agency', 'agency_name', 'Samsun Öffentliche Verkehrsmittel', 'samulas', 'de'),
    ('agency', 'agency_name', 'Transports Publics de Samsun', 'samulas', 'fr'),
    ('agency', 'agency_name', 'Общественный транспорт Самсуна', 'samulas', 'ru'),
    ('agency', 'agency_name', 'وسائل النقل العام في سامسون', 'samulas', 'ar'),
    # Feed Publisher
    ('feed_info', 'feed_publisher_name', 'Samsun Metropolitan Municipality', '', 'en'),
    ('feed_info', 'feed_publisher_name', 'Stadtverwaltung Samsun', '', 'de'),
    ('feed_info', 'feed_publisher_name', 'Municipalité Métropolitaine de Samsun', '', 'fr'),
    ('feed_info', 'feed_publisher_name', 'Мэрия Самсуна', '', 'ru'),
    ('feed_info', 'feed_publisher_name', 'بلدية سامسون الكبرى', '', 'ar'),
]
for t in base_translations:
    translations_data.append([t[0], t[1], t[4], t[2], t[3], ''])

# Kelime sözlüğü (Rota isimleri için)
vocab = {
    'Merkez': {'en': 'Center', 'de': 'Zentrum', 'fr': 'Centre', 'ru': 'Центр', 'ar': 'مركز'},
    'Terminal': {'en': 'Terminal', 'de': 'Terminal', 'fr': 'Terminal', 'ru': 'Терминал', 'ar': 'محطة'},
    'Hastane': {'en': 'Hospital', 'de': 'Krankenhaus', 'fr': 'Hôpital', 'ru': 'Больница', 'ar': 'مستشفى'},
    'Universite': {'en': 'University', 'de': 'Universität', 'fr': 'Université', 'ru': 'Университет', 'ar': 'جامعة'},
    'Havaalani': {'en': 'Airport', 'de': 'Flughafen', 'fr': 'Aéroport', 'ru': 'Аэропорт', 'ar': 'مطار'},
    'Otogar': {'en': 'Bus Station', 'de': 'Busbahnhof', 'fr': 'Gare Routière', 'ru': 'Автовокзал', 'ar': 'محطة الحافلات'},
    'Liman': {'en': 'Port', 'de': 'Hafen', 'fr': 'Port', 'ru': 'Порт', 'ar': 'ميناء'},
    'Sahil': {'en': 'Coast', 'de': 'Küste', 'fr': 'Côte', 'ru': 'Побережье', 'ar': 'ساحل'},
    'Istasyon': {'en': 'Station', 'de': 'Bahnhof', 'fr': 'Gare', 'ru': 'Станция', 'ar': 'محطة'},
    'Sanayi': {'en': 'Industrial', 'de': 'Industrie', 'fr': 'Industriel', 'ru': 'Промышленность', 'ar': 'صناعي'},
    'Organize': {'en': 'Organized', 'de': 'Organisiert', 'fr': 'Organisé', 'ru': 'Организованный', 'ar': 'منظم'},
    'Cadde': {'en': 'Avenue', 'de': 'Allee', 'fr': 'Avenue', 'ru': 'Проспект', 'ar': 'شارع'},
    'Meydan': {'en': 'Square', 'de': 'Platz', 'fr': 'Place', 'ru': 'Площадь', 'ar': 'ميدان'},
    'Pazar': {'en': 'Market', 'de': 'Markt', 'fr': 'Marché', 'ru': 'Рынок', 'ar': 'سوق'},
    'Cami': {'en': 'Mosque', 'de': 'Moschee', 'fr': 'Mosquée', 'ru': 'Мечеть', 'ar': 'مسجد'},
    'Park': {'en': 'Park', 'de': 'Park', 'fr': 'Parc', 'ru': 'Парк', 'ar': 'حديقة'},
    'Koy': {'en': 'Village', 'de': 'Dorf', 'fr': 'Village', 'ru': 'Деревня', 'ar': 'قرية'},
    'Mahalle': {'en': 'Neighborhood', 'de': 'Nachbarschaft', 'fr': 'Quartier', 'ru': 'Район', 'ar': 'حي'},
    'Kampus': {'en': 'Campus', 'de': 'Campus', 'fr': 'Campus', 'ru': 'Кампус', 'ar': 'حرم جامعي'},
}

# Rota isimlerini çevir
languages = ['en', 'de', 'fr', 'ru', 'ar']

for r in all_routes:
    for lang in languages:
        translated_name = r.long_name
        changed = False
        
        # Kelime kelime çevir
        for tr_word, translations in vocab.items():
            if tr_word in translated_name:
                translated_name = translated_name.replace(tr_word, translations[lang])
                changed = True
        
        if changed:
            translations_data.append([
                'routes', 'route_long_name', lang, translated_name, r.route_id, ''
            ])

write_csv('translations.txt',
    ['table_name', 'field_name', 'language', 'translation', 'record_id', 'record_sub_id'],
    translations_data)

conn.close()

# ZIP
print(f"\n📦 {OUTPUT_ZIP} oluşturuluyor...")
with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for filename in os.listdir('gtfs_temp'):
        zipf.write(os.path.join('gtfs_temp', filename), filename)
shutil.rmtree('gtfs_temp')
print(f"  ✅ ZIP: {OUTPUT_ZIP} ({os.path.getsize(OUTPUT_ZIP)/1024:.1f} KB)")
print("\n✨ GTFS Static Feed v5 HAZIR! (Multi-Language)")
