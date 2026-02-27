import sqlite3
import zipfile
import io
import requests
from bs4 import BeautifulSoup

DB = 'samsun_v25.db'

def fetch_agency_info():
    print("Fetcing Agency Info from samulas.com.tr...")
    try:
        r = requests.get("https://samulas.com.tr/iletisim/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Telefon we know is usually "444 1 619" but let's see if we can locate it or email
        # The generic agency.txt format requires: agency_id, agency_name, agency_url, agency_timezone, agency_lang, agency_phone, agency_fare_url, agency_email
        email = "bilgi@samulas.com.tr"
        phone = "444 1 619"
        
        # Scrape links for mailto or tel
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
        
        # 1. agency.txt (Zenginleştirilmiş)
        agency_txt = "agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone,agency_email\n"
        agency_txt += f"samulas,Samulaş A.Ş.,https://samulas.com.tr,Europe/Istanbul,tr,{phone},{email}\n"
        zf.writestr("agency.txt", agency_txt)
        
        # 2. routes.txt
        routes_txt = "route_id,agency_id,route_short_name,route_long_name,route_type,route_color,route_text_color\n"
        hatlar = c.execute("SELECT code, name, tip, short_name FROM hat").fetchall()
        for h in hatlar:
            route_type = {
                'otobus': '3', 'tramvay': '0', 'ring': '3', 'ekspres': '3',
                'havalimani': '3', 'ilce': '3', 'teleferik': '6', 'tekne': '4'
            }.get(h['tip'], '3')
            color = {
                'otobus': '1877F2', 'tramvay': 'E67E22', 'ring': 'F39C12', 'ekspres': '9B59B6',
                'havalimani': 'E74C3C', 'ilce': '1ABC9C', 'teleferik': 'E91E63', 'tekne': '3498DB'
            }.get(h['tip'], '1877F2')
            r_short = str(h['short_name']).strip() if h['short_name'] else h['code']
            routes_txt += f"{h['code']},samulas,{r_short},{h['name']},{route_type},{color},FFFFFF\n"
        zf.writestr("routes.txt", routes_txt)
        
        # 3. stops.txt
        stops_txt = "stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type\n"
        duraklar = c.execute("SELECT DISTINCT d.id, d.kod, d.ad, d.lat, d.lon FROM durak d WHERE d.lat IS NOT NULL").fetchall()
        for d in duraklar:
            ad_clean = str(d['ad']).replace(',', ' ')
            stops_txt += f"{d['id']},{d['kod']},{ad_clean},{d['lat']},{d['lon']},0\n"
        zf.writestr("stops.txt", stops_txt)
        
        # 4. calendar.txt (NEW!)
        # Map our "gun" formats to bits: monday,tuesday,wednesday,thursday,friday,saturday,sunday
        # 1 = Haftaiçi (Haftaiçi), 2 = Cumartesi (Cumartesi), 3 = Pazar (Pazar), 4 = Her Gün
        calendar_txt = "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        calendar_txt += "1,1,1,1,1,1,0,0,20240101,20261231\n" # Haftaiçi
        calendar_txt += "2,0,0,0,0,0,1,0,20240101,20261231\n" # Cumartesi
        calendar_txt += "3,0,0,0,0,0,0,1,20240101,20261231\n" # Pazar
        calendar_txt += "4,1,1,1,1,1,1,1,20240101,20261231\n" # Her Gün
        zf.writestr("calendar.txt", calendar_txt)
        
        # 5. trips.txt (NEW!)
        trips_txt = "route_id,service_id,trip_id,trip_headsign,direction_id\n"
        stop_times_txt = "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        
        # Haversine mesafe hesaplama (Samsun trafik/ışık faktörlü)
        import math
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        seferler = c.execute("SELECT id, hat, saat, yon, gun FROM sefer").fetchall()
        
        # Cache durak coordinates for distance calculation
        durak_dict = {}
        for row in c.execute("SELECT id, lat, lon FROM durak").fetchall():
            durak_dict[row['id']] = (row['lat'], row['lon'])
            
        for s in seferler:
            route_id = s['hat']
            trip_id = f"T_{s['id']}"
            headsign = str(s['yon']).replace(',', ' ')
            
            # Match service_id
            gun_str = str(s['gun']).lower()
            service_id = "4"
            if "hafta" in gun_str: service_id = "1"
            elif "cumartesi" in gun_str: service_id = "2"
            elif "pazar" in gun_str: service_id = "3"
            
            direction_id = "0" if "GİDİŞ" in str(s['yon']).upper() else "1"
            
            trips_txt += f"{route_id},{service_id},{trip_id},{headsign},{direction_id}\n"
            
            # 6. stop_times.txt (Gerçekçi Mesafe & Trafik Işığı Bazlı)
            # Route'a ait durakları sırayla çek
            route_duraklar = c.execute("SELECT durak_id, sira FROM hat_durak WHERE hat=? ORDER BY sira ASC", (route_id,)).fetchall()
            
            try:
                base_saat = s['saat']
                h, m = map(int, base_saat.split(':')[:2])
                current_minutes = h * 60 + m
            except:
                current_minutes = 360 # 06:00 fallback
            
            prev_lat, prev_lon = None, None
            for idx, rd in enumerate(route_duraklar):
                sira = int(rd['sira'])
                stop_id = rd['durak_id']
                
                # Mesafe bazlı süre tahmini
                added_mins = 0
                if idx == 0:
                    added_mins = 0 # İlk durak direkt başlar
                else:
                    lat, lon = durak_dict.get(stop_id, (None, None))
                    if lat and lon and prev_lat and prev_lon:
                        dist = haversine(prev_lat, prev_lon, lat, lon)
                        # Samsun şehir içi ortalama hız: 22 km/s (6.1 m/s)
                        # Mesafe süresi + 35 saniye duraklama/ışık/trafik payı
                        saniye_farki = (dist / 6.1) + 35
                        added_mins = saniye_farki / 60.0
                    else:
                        added_mins = 1.5 # Koordinat yoksa standart 1.5 dk
                
                current_minutes += added_mins
                
                arr_h = int(current_minutes // 60)
                arr_m = int(current_minutes % 60)
                arr_s = int((current_minutes * 60) % 60)
                # GTFS requires times beyond 24:00 (e.g. 25:30:00) 
                time_str = f"{arr_h:02d}:{arr_m:02d}:{arr_s:02d}"
                
                stop_times_txt += f"{trip_id},{time_str},{time_str},{stop_id},{sira}\n"
                
                lat, lon = durak_dict.get(stop_id, (None, None))
                if lat and lon:
                    prev_lat, prev_lon = lat, lon

        zf.writestr("trips.txt", trips_txt)
        zf.writestr("stop_times.txt", stop_times_txt)
        
    with open('samsun_gtfs_v25.zip', 'wb') as f:
        f.write(zip_buffer.getvalue())
    print("   -> Success! Full GTFS Saved to samsun_gtfs_v25.zip")
    conn.close()

if __name__ == "__main__":
    build_full_gtfs()
