import requests
from pydantic import BaseModel
from typing import List, Optional
import math

# --- Modeller ---
class BusLocation(BaseModel):
    vehiclePlate: str
    latitude: float
    longitude: float
    speed: float
    
class Prediction(BaseModel):
    BusLineCode: str
    RemainingTimeCurr: int
    latitude: float  # Bu aslında aracın o anki konumu mu? API'de var mıydı?
                     # SmartStations cevabında 'latitude' ve 'longitude' var, ama bu durak mı araç mı?
                     # QRDurak analizinde gördük ki SmartStations içindeki lat/lon ARAÇ konumu gibi duruyor.
    longitude: float 
    
    # SmartStations cevabı:
    # { "BusLineCode": "E5", "RemainingTimeCurr": 3, "latitude": ..., "longitude": ... }
    # Eğer bu lat/lon ARAÇ konumuysa, zaten API bize aracın konumunu veriyor demektir.
    # Kullanıcının dediği: "hat 26... real time'da gerçek konumunu görebiliyoruz ya"
    # Yani biz RealTimeData endpoint'inden de teyit edelim.

# --- Yardımcı Fonksiyonlar ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Dünya yarıçapı (km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

class VerificationSystem:
    BASE_URL = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
    
    def __init__(self):
        self.session = requests.Session()
        
    def check_stop(self, stop_id: int):
        print(f"\n--- Durak Doğrulama: {stop_id} ---")
        
        # 1. Durağın Konumunu Al
        try:
            r = self.session.get(f"{self.BASE_URL}/StopsStations", params={"stopId": stop_id})
            stop_info = r.json()['data'][0]
            stop_lat = float(stop_info['latitude'])
            stop_lon = float(stop_info['longitude'])
            print(f"Durak Konumu: {stop_lat}, {stop_lon}")
        except:
            print("Durak bilgisi alınamadı.")
            return

        # 2. Tahminleri Al (SmartStations)
        try:
            r = self.session.get(f"{self.BASE_URL}/SmartStations", params={"stationId": stop_id})
            predictions = r.json()['data']
        except:
            print("Tahmin verisi alınamadı.")
            return

        if not predictions:
            print("Yaklaşan araç yok.")
            return
            
        print(f"{len(predictions)} araç yaklaşmakta...")
        
        for p in predictions:
            line = p['BusLineCode']
            time_est = p['RemainingTimeCurr']
            
            # API'nin verdiği araç konumu (Eğer varsa)
            bus_lat_api = float(p.get('latitude')) if p.get('latitude') else None
            bus_lon_api = float(p.get('longitude')) if p.get('longitude') else None
            
            status = "[OK] TUTARLI"
            mesafe_km = 0
            
            if bus_lat_api and bus_lon_api:
                # Mesafeyi hesapla
                mesafe_km = haversine(stop_lat, stop_lon, bus_lat_api, bus_lon_api)
                
                # Doğrulama Mantığı
                # Ortalama şehir içi hız: 30 km/s -> 0.5 km/dk
                # Eğer süre 1 dk ise ve mesafe > 2 km ise -> İMKANSIZ (120 km/s gitmesi lazım)
                
                beklenen_max_mesafe = (int(time_est) + 1) * 0.8  # (Dk + tolerans) * 0.8 km/dk (48 km/s)
                
                if mesafe_km > beklenen_max_mesafe and int(time_est) < 5:
                    status = "[!] SUPHELI (Uzakta ama sure az)"
                    
                if int(time_est) == 0 and mesafe_km > 0.5:
                     status = "[!] HATALI (0 dk diyor ama 500m'den uzak)"

            print(f"Hat: {line:<5} | Sure: {time_est:>2} dk | Mesafe: {mesafe_km:.2f} km | {status}")

if __name__ == "__main__":
    v = VerificationSystem()
    v.check_stop(5328)
