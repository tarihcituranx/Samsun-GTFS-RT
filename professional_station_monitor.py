import requests
from pydantic import BaseModel, Field
from typing import List, Optional
import time

# --- Pydantic Modelleri (Tip Güvenliği ve Validasyon) ---
class IncomingBus(BaseModel):
    BusLineCode: str
    RemainingTimeCurr: int
    latitude: float
    longitude: float
    
class StopInfo(BaseModel):
    stopName: str
    latitude: float
    longitude: float

class StationResponse(BaseModel):
    data: List[IncomingBus] = Field(default_factory=list)

class StopInfoResponse(BaseModel):
    data: List[StopInfo] = Field(default_factory=list)

# --- Profesyonel API İstemcisi ---
class ProfessionalStationMonitor:
    BASE_URL = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SamsunTransit/v25 (Professional Monitor)",
            "Accept": "application/json"
        })

    def get_stop_info(self, stop_id: int) -> Optional[StopInfo]:
        """
        Durak bilgilerini çeker.
        Endpoint: /StopsStations
        """
        try:
            url = f"{self.BASE_URL}/StopsStations"
            # Parametreler query string olarak güvenli şekilde eklenir
            response = self.session.get(url, params={"stopId": stop_id}, timeout=10)
            response.raise_for_status()
            
            # Pydantic ile validasyon
            data = StopInfoResponse(**response.json())
            
            if data.data:
                return data.data[0]
            return None
            
        except Exception as e:
            print(f"[HATA] Durak bilgisi alınamadı ({stop_id}): {e}")
            return None

    def get_incoming_buses(self, stop_id: int) -> List[IncomingBus]:
        """
        Durağa yaklaşan araçları çeker.
        Endpoint: /SmartStations
        """
        try:
            url = f"{self.BASE_URL}/SmartStations"
            response = self.session.get(url, params={"stationId": stop_id}, timeout=10)
            response.raise_for_status()
            
            # Pydantic ile validasyon - Veri bozuksa burada yakalanır
            data = StationResponse(**response.json())
            return data.data
            
        except requests.exceptions.HTTPError as e:
            print(f"[HATA] API Hatası: {e}")
            return []
        except Exception as e:
            print(f"[HATA] Veri işleme hatası: {e}")
            return []

    def monitor(self, stop_id: int, duration_sec: int = 60):
        """
        Belirtilen süre boyunca durağı izler.
        """
        print(f"\n--- Profesyonel Durak Takibi Başlatılıyor (ID: {stop_id}) ---")
        
        info = self.get_stop_info(stop_id)
        if not info:
            print("Durak bulunamadı veya erişilemiyor.")
            return

        print(f"Durak: {info.stopName}")
        print(f"Konum: {info.latitude}, {info.longitude}")
        print("-" * 40)

        start_time = time.time()
        while time.time() - start_time < duration_sec:
            buses = self.get_incoming_buses(stop_id)
            
            # Ekranı temizle (opsiyonel, burada sadece print ediyoruz)
            print(f"\n[Güncelleme {time.strftime('%H:%M:%S')}] Yaklaşan Araçlar:")
            
            if not buses:
                print("   (Şu an yaklaşan araç yok)")
            else:
                # Süreye göre sırala
                buses.sort(key=lambda x: x.RemainingTimeCurr)
                
                for bus in buses:
                    # Renklendirme ve formatlama
                    status = "[GELIYOR]" if bus.RemainingTimeCurr < 2 else "[YOLDA]"
                    print(f"   * Hat {bus.BusLineCode:<5} | {bus.RemainingTimeCurr:>2} dk | {status}")
            
            # API'yi yormamak için bekleme (Polling Frequency Controls)
            # Amatör kod: 20sn hardcoded. Biz burada yapılandırabiliriz.
            time.sleep(10) 

if __name__ == "__main__":
    # Test için 5328 (Türkiş) durağını 30 saniye izleyelim
    monitor = ProfessionalStationMonitor()
    monitor.monitor(5328, duration_sec=30)
