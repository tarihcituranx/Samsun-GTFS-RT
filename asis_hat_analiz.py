import requests
import json
import urllib3

urllib3.disable_warnings()

ASIS_URL = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://samair.samsun.bel.tr/'
}

def analiz_et():
    print("API'den hatlar cekiliyor...")
    
    # Endpoint isimlerinden 'Get' kaldirildi (samsun.py'deki gibi)
    endpoints = ["OrjLines", "Lines", "ActiveLines", "LineList"]
    hatlar = []
    basarili_ep = ""

    for ep in endpoints:
        print(f"Endpoint deneniyor: {ep}...")
        try:
            r = requests.post(f"{ASIS_URL}/{ep}", json={}, headers=HEADERS, verify=False, timeout=30)
            if r.ok:
                try:
                    data = r.json()
                    # Eger 'result' yoksa direkt listeyi donduruyor olabilir mi?
                    if isinstance(data, list):
                        hatlar = data
                    else:
                        hatlar = data.get('result', [])
                    
                    if hatlar:
                        print(f"[BASARILI] {ep} ({len(hatlar)} hat dondu)")
                        basarili_ep = ep
                        break
                    else:
                        print(f"[UYARI] {ep}: Yanit bos veya 'result' bos.")
                except:
                    print(f"[HATA] {ep}: JSON parse hatasi.")
            else:
                print(f"[HATA] {ep}: HTTP {r.status_code}")
        except Exception as e:
            print(f"[HATA] {ep}: Hata - {e}")

    if not hatlar:
        print("\nHicbir servisten hat verisi alinamadi.")
        return

    tipler = {}
    print(f"\nToplam {len(hatlar)} hat analizi ({basarili_ep}):\n")

    for h in hatlar:
        lt = h.get('lineType', -1)
        kodu = h.get('lineCode', 'Bilinmiyor')
        adi = h.get('lineName', 'Isimsiz')
        
        if lt not in tipler:
            tipler[lt] = []
        
        tipler[lt].append(f"{kodu} - {adi}")

    print("--- HAT TIPLERI ANALIZI (LineType) ---")
    for tip, liste in tipler.items():
        print(f"\nTip: {tip} (Adet: {len(liste)})")
        # Ilk 15 ornegi yazdir
        for l in liste[:15]:
            print(f"  - {l}")
        if len(liste) > 15:
            print(f"  ... ve {len(liste)-15} daha fazla")

if __name__ == "__main__":
    analiz_et()
