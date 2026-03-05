import requests
import json
import time

def scrape_durak(stop_id):
    print(f"--- Durak ID: {stop_id} Analizi ---")
    
    # 1. Durak Bilgisi
    url_info = f"http://127.0.0.1:8000/api/durak_panel/{stop_id}"
    try:
        r = requests.get(url_info)
        data = r.json()
        if data and data.get('ad'):
            print(f"Durak Adı: {data.get('ad')}")
            print(f"Konum: {data.get('lat')}, {data.get('lon')}")
        else:
            print("Durak bilgisi bulunamadı.")
    except Exception as e:
        print(f"Durak bilgisi hatası: {e}")

    # 2. Akıllı Durak (Yaklaşan Otobüsler)
    url_smart = f"http://127.0.0.1:8000/api/proxy/smart_stations?stationId={stop_id}"
    try:
        r = requests.get(url_smart)
        data = r.json()
        print(f"\nYaklaşan Araçlar ({len(data)} adet):")
        for bus in data:
            line = bus.get('BusLineCode')
            sure = bus.get('RemainingTimeCurr')
            print(f"- Hat: {line} | Süre: {sure} dk")
            
    except Exception as e:
        print(f"Akıllı durak hatası: {e}")

if __name__ == "__main__":
    scrape_durak(5328)
