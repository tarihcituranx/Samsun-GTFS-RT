import requests
import json
import time

def scrape_durak(stop_id):
    print(f"--- Durak ID: {stop_id} Analizi ---")
    
    # 1. Durak Bilgisi
    url_info = f"https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/StopsStations?stopId={stop_id}"
    try:
        r = requests.get(url_info)
        data = r.json()
        if data.get('data'):
            durak = data['data'][0]
            print(f"Durak Adı: {durak.get('stopName')}")
            print(f"Konum: {durak.get('latitude')}, {durak.get('longitude')}")
        else:
            print("Durak bilgisi bulunamadı.")
    except Exception as e:
        print(f"Durak bilgisi hatası: {e}")

    # 2. Akıllı Durak (Yaklaşan Otobüsler)
    url_smart = f"https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/SmartStations?stationId={stop_id}"
    try:
        r = requests.get(url_smart)
        data = r.json()
        print(f"\nYaklaşan Araçlar ({len(data.get('data', []))} adet):")
        for bus in data.get('data', []):
            line = bus.get('BusLineCode')
            sure = bus.get('RemainingTimeCurr')
            print(f"- Hat: {line} | Süre: {sure} dk")
            
    except Exception as e:
        print(f"Akıllı durak hatası: {e}")

if __name__ == "__main__":
    scrape_durak(5328)
