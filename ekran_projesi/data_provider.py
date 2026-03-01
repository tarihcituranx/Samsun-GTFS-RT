import sqlite3
import requests
import json
import math
import os
from datetime import datetime

# Config
DB_PATH = r"c:\Users\mete2\OneDrive\Masaüstü\test\samsun_v25.db"
ASIS_URL = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"

class DataProvider:
    # Samsun Valiliği Hava Durumu API
    WEATHER_URL = "https://www.samsun.gov.tr/ISAYWebPart/ValilikHeader/GetHavaDurumu?cKey=55"
    
    # Meteoroloji Hadise Kodları -> Türkçe
    HADISE_MAP = {
        "A": "Açık",
        "AB": "Az Bulutlu",
        "PB": "Parçalı Bulutlu",
        "CB": "Çok Bulutlu",
        "K": "Kapalı",
        "HY": "Hafif Yağmurlu",
        "Y": "Yağmurlu",
        "KY": "Kuvvetli Yağmurlu",
        "HK": "Hafif Kar",
        "K": "Karlı",
        "KK": "Kuvvetli Kar",
        "F": "Fırtınalı",
        "SIS": "Sisli",
        "P": "Puslu",
        "DY": "Dolu Yağışlı",
        "GSY": "Gök Gürültülü Sağanak Yağışlı",
        "HSY": "Hafif Sağanak",
        "SY": "Sağanak Yağışlı",
        "KKY": "Karla Karışık Yağmur"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SamsunScreen/1.0'})

    def get_db_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def fetch_weather(self):
        """Fetch weather from Samsun Governorship API (MGM data)"""
        try:
            r = self.session.get(self.WEATHER_URL, timeout=5)
            if r.ok:
                data = r.json()
                if data.get('status'):
                    obj = data.get('resultingObject', {})
                    temp = obj.get('sicaklik', '?')
                    code = obj.get('hadiseDurumu', 'PB')
                    desc = self.HADISE_MAP.get(code, code)
                    return {"temp": temp, "desc": desc, "code": code}
        except Exception as e:
            print(f"Weather fetch error: {e}")
        return {"temp": "?", "desc": "Bilinmiyor", "code": "?"}

    def fetch_events(self, limit=5):
        """Fetch Samsun events from biletinial.com API"""
        EVENTS_URL = "https://biletinial.com/GetAllEventsByCity"
        try:
            params = {
                'cityId': 43,  # Samsun
                'langId': 1,
                'countryId': 3,
                'langCode': 'tr',
                'pageNumber': 1,
                'pageSize': 20,
                'initial': 'true'
            }
            r = self.session.get(EVENTS_URL, params=params, timeout=10)
            if r.ok:
                data = r.json()
                events = data.get('Data', [])
                
                # Get upcoming events only (next 7 days)
                result = []
                for e in events[:limit]:
                    result.append({
                        'title': e.get('etkinlik', ''),
                        'venue': e.get('mekan', ''),
                        'date': e.get('tarih', ''),
                        'time': e.get('saat', ''),
                        'type': e.get('tip', ''),
                        'image': f"https://biletinial.com{e.get('pic', '')}",
                        'url': f"https://biletinial.com/tr/{e.get('tipForUrl', 'tiyatro')}/{e.get('url', '')}"
                    })
                return result
        except Exception as e:
            print(f"Events fetch error: {e}")
        return []

    def fetch_realtime_bus(self, line_code):
        """Fetch real-time bus locations for a specific line from ASIS API"""
        try:
            url = f"{ASIS_URL}/RealTimeData"
            params = {'lineCode': line_code}
            r = self.session.get(url, params=params, timeout=10)
            if r.ok:
                data = r.json()
                # Clean and parse data
                result = []
                data = data.get('data', data) if isinstance(data, dict) else data
                if not isinstance(data, list): return []
                
                for d in data:
                    try:
                        lat = float(str(d.get('enlem')).replace(',', '.'))
                        lon = float(str(d.get('boylam')).replace(',', '.'))
                        if 40 < lat < 43 and 34 < lon < 38:
                            result.append({
                                'plate': d.get('plaka'),
                                'lat': lat,
                                'lon': lon,
                                'speed': int(float(d.get('hiz', 0))),
                                'angle': float(d.get('yon', 0)),
                                'occupancy': int(d.get('seferYolcu', 0))
                            })
                    except: pass
                return result
            else:
                print(f"API Error: {r.status_code}")
                return []
        except Exception as e:
            print(f"Fetch Error: {e}")
            return []

    def get_route_stops(self, line_code):
        """
        Get stops for the line from local DB.
        Uses LIKE to match line code as the DB has verbose names.
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find the full line name first
        cursor.execute("SELECT DISTINCT hat FROM hat_durak WHERE hat LIKE ?", (f"%{line_code}%",))
        result = cursor.fetchone()
        
        if not result:
            print(f"Line not found for code: {line_code}")
            conn.close()
            return [], ""
            
        full_line_name = result[0]
        # print(f"Found full line name: {full_line_name}")
        
        # 2. Get stops for this exact line name
        cursor.execute("SELECT durak_id, ad, sira, lat, lon FROM hat_durak WHERE hat = ? ORDER BY sira", (full_line_name,))
        rows = cursor.fetchall()
        
        stops = []
        stops = []
        for r in rows:
            stops.append(dict(r))
        conn.close()
        return stops, full_line_name

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def estimate_arrival(self, bus_lat, bus_lon, stop_lat, stop_lon, speed_kmh):
        dist_m = self.haversine(bus_lat, bus_lon, stop_lat, stop_lon)
        if dist_m < 50: return 0
        road_dist_km = (dist_m * 1.4) / 1000.0
        effective_speed = max(speed_kmh, 20.0)
        minutes = int((road_dist_km / effective_speed * 60) * 1.1)
        return minutes if minutes > 0 else 1

    def get_screen_data(self, line_code, my_stop_seq):
        """
        Main function for the screen. 
        Returns local screen data: Next stops, Weather (cached), Bus ETA.
        """
        # 1. Get Line Details
        stops, line_name = self.get_route_stops(line_code)
        
        # Identify my stop
        my_stop = next((s for s in stops if s['sira'] == my_stop_seq), None)
        if not my_stop:
            return {"error": "Stop sequence not found"}

        # Filter stops strictly after my current sequence (for timeline)
        next_stops = [s for s in stops if s['sira'] >= my_stop_seq]
        
        # 2. Get Realtime Bus
        buses = self.fetch_realtime_bus(line_code)
        
        # 3. Smart Vehicle Selection (Logic from samsun.py)
        # Find the bus that is BEHIND me and closest to me
        best_bus = None
        min_eta = 9999
        
        if buses:
            for bus in buses:
                # Find which stop this bus is closest to (to determine its sequence)
                closest_stop_seq = -1
                min_stop_dist = 999999
                
                for s in stops:
                    d = self.haversine(bus['lat'], bus['lon'], s['lat'], s['lon'])
                    if d < min_stop_dist:
                        min_stop_dist = d
                        closest_stop_seq = s['sira']
                
                # Bus must be at a previous sequence (or same) to be incoming
                if closest_stop_seq != -1 and closest_stop_seq <= my_stop_seq:
                    # Calculate distance to ME
                    dist_to_me = self.haversine(bus['lat'], bus['lon'], my_stop['lat'], my_stop['lon'])
                    eta = self.estimate_arrival(0, 0, 0, 0, bus['speed']) # Hack: calculate_eta doesn't use coords, just dist
                    # Re-use estimate_arrival logic properly:
                    # estimate_arrival(self, bus_lat, bus_lon, stop_lat, stop_lon, speed_kmh)
                    eta = self.estimate_arrival(bus['lat'], bus['lon'], my_stop['lat'], my_stop['lon'], bus['speed'])
                    
                    if eta < min_eta:
                        min_eta = eta
                        best_bus = bus
                        best_bus['closest_stop_seq'] = closest_stop_seq
        
        # 4. Prepare Response
        stop_data = []
        
        for s in next_stops:
            stop_eta = "?"
            if best_bus:
                # ETA to this specific stop
                stop_eta = self.estimate_arrival(best_bus['lat'], best_bus['lon'], s['lat'], s['lon'], best_bus['speed'])

            stop_data.append({
                'name': s['ad'],
                'seq': s['sira'],
                'lat': s['lat'],
                'lon': s['lon'],
                'eta': stop_eta,
                'is_next': s['sira'] == my_stop_seq
            })
        
        # Format current_bus for frontend
        formatted_bus = None
        if best_bus:
            formatted_bus = {
                'plate': best_bus.get('plate', '?'),
                'lat': best_bus['lat'],
                'lon': best_bus['lon'],
                'speed': best_bus.get('speed', 0),
                'heading': best_bus.get('angle', 0),  # Map 'angle' to 'heading' for frontend
                'passengers': best_bus.get('occupancy', 0),
                'closest_stop_seq': best_bus.get('closest_stop_seq', 0)
            }
            
        return {
            "current_bus": formatted_bus,
            "stops": stop_data,
            "next_stop": next_stops[1]['ad'] if len(next_stops) > 1 else "SON DURAK",
            "eta": min_eta if best_bus else None,
            "has_live_data": best_bus is not None,
            "line_code": line_code,
            "line_name": line_name,
            "current_time": datetime.now().strftime("%H:%M"),
            "weather": self.fetch_weather()
        }

if __name__ == "__main__":
    dp = DataProvider()
    # Test with 26/17 and a random stop sequence
    data = dp.get_screen_data('26/17', 10)
    print(json.dumps(data, indent=2, ensure_ascii=False))
