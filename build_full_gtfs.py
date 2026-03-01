import sqlite3
import zipfile
import io
import re
import requests
from bs4 import BeautifulSoup

DB = 'samsun_v25.db'

# ── Türkçe karakter haritası ──────────────────────────────────────
_ASCII_MAP = str.maketrans({
    'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's',
    'Ç': 'C', 'ç': 'c', 'Ğ': 'G', 'ğ': 'g',
    'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o',
})

def sanitize_id(text):
    """ID alanları için: Türkçe karakterleri ASCII'ye çevir, boşluk/özel karakter temizle."""
    if not text:
        return text
    t = str(text).translate(_ASCII_MAP)
    t = re.sub(r'[^A-Za-z0-9_\-./]', '_', t)
    t = re.sub(r'_+', '_', t).strip('_')
    return t

def _tr_lower(text):
    """Türkçe kurallarına uygun küçük harf dönüşümü.
    I → ı (dotless), İ → i (dotted), diğerleri standart."""
    result = []
    for ch in text:
        if ch == 'I':
            result.append('ı')
        elif ch == 'İ':
            result.append('i')
        else:
            result.append(ch.lower())
    return ''.join(result)

def _tr_upper_first(ch):
    """Tek bir karakteri Türkçe kuralına göre büyük harf yap.
    i → İ (dotted), ı → I (dotless), diğerleri standart."""
    if ch == 'i':
        return 'İ'
    elif ch == 'ı':
        return 'I'
    else:
        return ch.upper()

def title_case_tr(text):
    """Türkçe uyumlu Title Case dönüştürücü (ör. 'SOĞUKSU' → 'Soğuksu')."""
    if not text:
        return text
    words = str(text).split()
    result = []
    small_words = {'ve', 'ile', 'ya', 'da', 'de', 'den', 'dan', 'ne', 'bir'}
    for i, word in enumerate(words):
        if word == '-' or word == '–':
            result.append(word)
            continue
        # Tamamen sayısal ise olduğu gibi bırak (ör. "50122")
        if word.isdigit():
            result.append(word)
            continue
        # Parantez içi dahil
        parts = []
        for part in re.split(r'(\(|\))', word):
            if part in ('(', ')'):
                parts.append(part)
                continue
            if not part:
                continue
            low = _tr_lower(part)
            if i > 0 and low in small_words:
                parts.append(low)
            else:
                first = _tr_upper_first(low[0])
                parts.append(first + low[1:])
        result.append(''.join(parts))
    return ' '.join(result)

def extract_short_name(code, short_name):
    """route_short_name max 12 karakter. Hat numarasini cikarir.
    Oncelik: code'dan hat numarasi > uygun short_name > fallback.
    Samulas V1 bazen short_line_name olarak dahili ID (402, 416) doner;
    bunlar kullanilmamali."""
    code_str = str(code).strip() if code else ''
    short_str = str(short_name).strip() if short_name else ''

    # 1) code'dan hat numarasini cikarmak
    m_code = re.match(r'^([A-Za-z\u00c7\u00e7\u011e\u011f\u00d6\u00f6\u00dc\u00fc\u015e\u015f\u0130\u0131]\d+[A-Za-z]?)', code_str)
    if m_code and len(m_code.group(1)) <= 12:
        return m_code.group(1).upper().translate(_ASCII_MAP)

    m_num = re.match(r'^(\d+(?:/\d+)?[A-Za-z]?)', code_str)
    if m_num and len(m_num.group(1)) <= 12:
        extracted = m_num.group(1)
        if int(re.match(r'^(\d+)', extracted).group(1)) < 100:
            return extracted

    # 2) short_name akillica kullan
    if short_str:
        m_short_alpha = re.match(r'^([A-Za-z]\d+[A-Za-z]?)', short_str)
        if m_short_alpha and len(m_short_alpha.group(1)) <= 12:
            return m_short_alpha.group(1).upper().translate(_ASCII_MAP)
        m_short_num = re.match(r'^(\d+)', short_str)
        if m_short_num and int(m_short_num.group(1)) < 100:
            return short_str[:12]

    # 3) Ozel hat isimleri
    code_ascii = code_str.upper().translate(_ASCII_MAP)
    combined = f"{code_ascii} {short_str.upper().translate(_ASCII_MAP)}"

    if 'TELEFERIK' in combined: return 'TLFRK'
    m_sn = re.search(r'SAMSUNUM\s*(\d+)', combined)
    if m_sn: return f'SN{m_sn.group(1)}'
    if 'ALTINKAYA' in combined: return 'AK55'
    if 'TRAMVAY' in combined: return 'TRAM'

    ilce = [
        (r'SAMSUN\s*-\s*TERME', 'SAM-TRM'), (r'TERME\s*-\s*SAMSUN', 'TRM-SAM'),
        (r'SAMSUN\s*-\s*CARSAMBA', 'SAM-CRS'), (r'CARSAMBA\s*-\s*SAMSUN', 'CRS-SAM'),
        (r'SAMSUN\s*-\s*BAFRA', 'SAM-BFR'), (r'BAFRA\s*-\s*SAMSUN', 'BFR-SAM'),
        (r'SAMSUN\s*-\s*HAVZA', 'SAM-HVZ'), (r'HAVZA\s*-\s*SAMSUN', 'HVZ-SAM'),
    ]
    for pattern, short in ilce:
        if re.search(pattern, combined): return short

    m_eks = re.search(r'EKSPRES\s*(\d+)', combined)
    if m_eks: return f'E{m_eks.group(1)}'
    if 'EKSPRES' in combined:
        m_eks2 = re.search(r'EKSPRES\s*([A-Z])', combined)
        return f'E{m_eks2.group(1)}' if m_eks2 else 'EXP'

    fallback = code_str.split(' ')[0] if ' ' in code_str else code_str
    return fallback[:12].rstrip(' -')


def clean_long_name(gtfs_short_name, long_name, db_short_name=''):
    """route_long_name başından short_name prefix'ini kaldır.
    gtfs_short_name: GTFS'e yazılacak kısa isim (ör. '15', 'R1')
    long_name: orijinal uzun isim
    db_short_name: veritabanındaki short_name"""
    if not long_name:
        return ''
    ln = str(long_name).strip()
    
    # Hat numarası prefix'i kaldır (ör. "R1 BÜYÜK CAMİ…" → "Büyük Cami…")
    # Hem gtfs_short_name hem de olası hat kodu ile dene
    for prefix in [gtfs_short_name, db_short_name]:
        if not prefix:
            continue
        pf = str(prefix).strip()
        if ln == pf:
            # long_name == short_name ise, olduğu gibi bırak
            continue
        if ln.startswith(pf + ' '):
            cleaned = ln[len(pf):].strip().lstrip('- ').strip()
            if cleaned:
                return cleaned
    
    # Regex ile hat numarasını kaldır (ör. "15/B SOĞUKSU…" → "Soğuksu…")
    m = re.match(r'^(\d+[/]?[A-Za-z]?|[A-Za-z]\d+[A-Za-z]?)\s+(.+)', ln)
    if m:
        code = m.group(1)
        if code == gtfs_short_name or code == db_short_name:
            return m.group(2).strip()
    
    return ln


def fetch_agency_info():
    print("Fetcing Agency Info from samulas.com.tr...")
    try:
        r = requests.get("https://samulas.com.tr/iletisim/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        email = "bilgi@samulas.com.tr"
        phone = "444 1 619"
        
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('mailto:'):
                email = a['href'].replace('mailto:', '').strip()
            elif a['href'].startswith('tel:'):
                phone = a['href'].replace('tel:', '').strip()
                
        return phone, email
        
    except Exception as e:
        print("Scrape error:", e)
        return "444 1 619", "bilgi@samulas.com.tr"

def build_full_gtfs():
    phone, email = fetch_agency_info()
    
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("Generating FULL GTFS ZIP...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        
        # 1. agency.txt
        agency_txt = "agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone,agency_email\n"
        agency_txt += f"samulas,Samulaş A.Ş.,https://samulas.com.tr,Europe/Istanbul,tr,{phone},{email}\n"
        zf.writestr("agency.txt", agency_txt)
        
        # 2. feed_info.txt (YENİ — missing_recommended_file düzeltmesi)
        feed_info_txt = "feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version,feed_contact_email,feed_contact_url\n"
        feed_info_txt += f"Samulaş A.Ş.,https://samulas.com.tr,tr,20240101,20261231,2.5,{email},https://samulas.com.tr/iletisim\n"
        zf.writestr("feed_info.txt", feed_info_txt)
        
        # 3. routes.txt (düzeltmeli)
        routes_txt = "route_id,agency_id,route_short_name,route_long_name,route_type,route_color,route_text_color\n"
        hatlar = c.execute("SELECT code, name, tip, short_name FROM hat").fetchall()
        
        # route_id → sanitize mapping (trip'lerde de kullanılacak)
        route_id_map = {}  # original_code → sanitized_route_id
        
        for h in hatlar:
            route_type = {
                'otobus': '3', 'tramvay': '0', 'ring': '3', 'ekspres': '3',
                'havalimani': '3', 'ilce': '3', 'teleferik': '6', 'tekne': '4'
            }.get(h['tip'], '3')
            color = {
                'otobus': '1877F2', 'tramvay': 'E67E22', 'ring': 'F39C12', 'ekspres': '9B59B6',
                'havalimani': 'E74C3C', 'ilce': '1ABC9C', 'teleferik': 'E91E63', 'tekne': '3498DB'
            }.get(h['tip'], '1877F2')
            
            # Sanitize route_id (non_ascii fix)
            route_id = sanitize_id(h['code'])
            route_id_map[h['code']] = route_id
            
            # Extract short name (max 12 chars)
            r_short = extract_short_name(h['code'], h['short_name'])
            
            # Clean long name: remove short_name prefix + title case
            raw_long = str(h['name']).strip() if h['name'] else h['code']
            db_short = str(h['short_name']).strip() if h['short_name'] else ''
            long_name = clean_long_name(r_short, raw_long, db_short)
            long_name = title_case_tr(long_name)
            # Virgülleri temizle (CSV güvenliği)
            long_name = long_name.replace(',', ' -')
            
            routes_txt += f"{route_id},samulas,{r_short},{long_name},{route_type},{color},FFFFFF\n"
        zf.writestr("routes.txt", routes_txt)
        
        # 4. calendar.txt — dinamik tarih
        from datetime import date as dt_date
        bugun = dt_date.today()
        cal_start = bugun.strftime('%Y%m%d')
        cal_end = bugun.replace(year=bugun.year + 2).strftime('%Y%m%d')
        calendar_txt = "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        calendar_txt += f"1,1,1,1,1,1,0,0,{cal_start},{cal_end}\n"
        calendar_txt += f"2,0,0,0,0,0,1,0,{cal_start},{cal_end}\n"
        calendar_txt += f"3,0,0,0,0,0,0,1,{cal_start},{cal_end}\n"
        calendar_txt += f"4,1,1,1,1,1,1,1,{cal_start},{cal_end}\n"
        zf.writestr("calendar.txt", calendar_txt)
        
        # 5. trips.txt + stop_times.txt
        trips_lines = ["route_id,service_id,trip_id,trip_headsign,direction_id"]
        stop_times_lines = ["trip_id,arrival_time,departure_time,stop_id,stop_sequence"]
        
        import math
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        seferler = c.execute("SELECT id, hat, saat, yon, gun FROM sefer").fetchall()
        
        # Cache durak coordinates
        durak_dict = {}
        for row in c.execute("SELECT id, lat, lon FROM durak").fetchall():
            durak_dict[row['id']] = (row['lat'], row['lon'])
        
        # N+1 sorgu cache — tüm hat_durak'ları tek sorguda al
        from collections import defaultdict
        hat_durak_cache = defaultdict(list)
        for row in c.execute("SELECT hat, durak_id, sira FROM hat_durak ORDER BY hat, sira ASC").fetchall():
            hat_durak_cache[row['hat']].append(row)
        
        # Kullanılan stop_id'leri takip et (stop_without_stop_time düzeltmesi)
        used_stop_ids = set()
        
        # Skipped trip/sefer counters
        skipped_trips = 0
            
        for s in seferler:
            route_id_orig = s['hat']
            route_id = route_id_map.get(route_id_orig, sanitize_id(route_id_orig))
            trip_id = sanitize_id(f"T_{s['id']}")
            headsign = title_case_tr(str(s['yon']).replace(',', ' '))
            
            # Match service_id
            gun_str = str(s['gun']).lower()
            service_id = "4"
            if "hafta" in gun_str: service_id = "1"
            elif "cumartesi" in gun_str: service_id = "2"
            elif "pazar" in gun_str: service_id = "3"
            
            yon_ascii = str(s['yon']).upper().translate(_ASCII_MAP)
            direction_id = "0" if "GIDIS" in yon_ascii or s['yon'] == 'G' else "1"
            
            # Route'a ait durakları cache'den al
            route_duraklar = hat_durak_cache.get(route_id_orig, [])
            
            # unusable_trip düzeltmesi: tek duraklı trip'leri atla
            if len(route_duraklar) <= 1:
                skipped_trips += 1
                continue
            
            trips_lines.append(f"{route_id},{service_id},{trip_id},{headsign},{direction_id}")
            
            # stop_times oluştur
            try:
                base_saat = s['saat']
                h_val, m_val = map(int, base_saat.split(':')[:2])
                current_minutes = h_val * 60 + m_val
            except (ValueError, AttributeError, TypeError):
                current_minutes = 360  # 06:00 fallback
            
            prev_lat, prev_lon = None, None
            for idx, rd in enumerate(route_duraklar):
                sira = int(rd['sira'])
                stop_id_orig = rd['durak_id']
                stop_id = sanitize_id(stop_id_orig)
                
                used_stop_ids.add(stop_id_orig)
                
                # Mesafe bazlı süre tahmini
                added_mins = 0
                if idx > 0:
                    lat, lon = durak_dict.get(stop_id_orig, (None, None))
                    if lat and lon and prev_lat and prev_lon:
                        dist = haversine(prev_lat, prev_lon, lat, lon)
                        added_mins = ((dist / 6.1) + 35) / 60.0
                    else:
                        added_mins = 1.5
                
                current_minutes += added_mins
                
                total_sec = int(round(current_minutes * 60))
                arr_h = total_sec // 3600
                arr_m = (total_sec % 3600) // 60
                arr_s = total_sec % 60
                time_str = f"{arr_h:02d}:{arr_m:02d}:{arr_s:02d}"
                
                stop_times_lines.append(f"{trip_id},{time_str},{time_str},{stop_id},{sira}")
                
                lat, lon = durak_dict.get(stop_id_orig, (None, None))
                if lat and lon:
                    prev_lat, prev_lon = lat, lon

        zf.writestr("trips.txt", "\n".join(trips_lines) + "\n")
        zf.writestr("stop_times.txt", "\n".join(stop_times_lines) + "\n")
        
        # 6. stops.txt (sadece kullanılan duraklar — stop_without_stop_time düzeltmesi)
        stops_txt = "stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type\n"
        duraklar = c.execute(
            "SELECT DISTINCT d.id, d.kod, d.ad, d.lat, d.lon FROM durak d WHERE d.lat IS NOT NULL"
        ).fetchall()
        
        included_stops = 0
        filtered_stops = 0
        for d in duraklar:
            if d['id'] not in used_stop_ids:
                filtered_stops += 1
                continue
            stop_id = sanitize_id(d['id'])
            stop_code = sanitize_id(d['kod']) if d['kod'] else ''
            ad_clean = title_case_tr(str(d['ad']).replace(',', ' '))
            stops_txt += f"{stop_id},{stop_code},{ad_clean},{d['lat']},{d['lon']},0\n"
            included_stops += 1
        zf.writestr("stops.txt", stops_txt)
        
        print(f"   Stops: {included_stops} included, {filtered_stops} filtered out")
        print(f"   Trips: {skipped_trips} unusable trips skipped")
        
    with open('samsun_gtfs_v25.zip', 'wb') as f:
        f.write(zip_buffer.getvalue())
    print("   -> Success! Full GTFS Saved to samsun_gtfs_v25.zip")
    conn.close()

if __name__ == "__main__":
    build_full_gtfs()
