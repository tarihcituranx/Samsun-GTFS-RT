"""
Odak turistik hatları - OrjLines ve StopsStations karşılaştırma
"""
import sys, io, requests, json, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ASIS = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
YBS = "https://ybs.samsun.bel.tr/service"

def get_ybs_token():
    try:
        r = requests.get(f"{YBS}/?method=getGuestToken", timeout=10)
        return r.json().get('token')
    except:
        return None

def ybs_request(method, token, **params):
    p = {'method': method, 'token': token}
    p.update(params)
    try:
        r = requests.get(f"{YBS}/", params=p, headers={'Referer': 'https://odak.samsun.bel.tr/'}, timeout=20)
        return r.json().get('data', [])
    except:
        return []

def main():
    print("=" * 70)
    print("ODAK - ASIS OrjLines DURAK KARŞILAŞTIRMA")
    print("=" * 70)
    
    # Token
    token = get_ybs_token()
    print(f"YBS Token: {token[:8]}...")
    
    # 1. OrjLines'dan turistik hatları bul
    print("\n=== OrjLines Turistik Hatlar ===")
    r = requests.get(f"{ASIS}/OrjLines", timeout=15)
    orj_lines = r.json().get('data', [])
    
    turistik_keywords = ['KANYON', 'DELTA', 'BARAJ', 'LADİK', 'LADİK', 'ŞAHİNKAYA', 
                        'KIZILIRMAK', 'AYVACIK', 'TURİST', 'ODAK']
    
    turistik_hatlar = []
    for l in orj_lines:
        code = l.get('lineCode', '')
        name = l.get('lineName', '')
        if any(kw in name.upper() for kw in turistik_keywords):
            turistik_hatlar.append({'code': code, 'name': name})
            print(f"  [{code}] {name}")
    
    print(f"\nToplam {len(turistik_hatlar)} turistik hat OrjLines'da")
    
    # 2. YBS'den Odak hatlarını çek
    print("\n=== YBS Odak Hatları ===")
    odak_hatlar = ybs_request('odakSamsun_Crud', token, submethod='HatlarAllList')
    for h in odak_hatlar:
        print(f"  [{h.get('id')}] {h.get('hat_adi')}")
    
    # 3. Her turistik hat için ASIS durakları çek ve karşılaştır
    print("\n=== DURAK KARŞILAŞTIRMA ===")
    
    for th in turistik_hatlar:
        code = th['code']
        name = th['name']
        
        # ASIS StopsStations
        r = requests.get(f"{ASIS}/StopsStations", params={'lineCode': code}, timeout=15)
        asis_stops = r.json().get('data', [])
        
        print(f"\n--- {code} ---")
        print(f"ASIS: {name}")
        print(f"ASIS Durak sayısı: {len(asis_stops)}")
        
        # Eşleşen Odak hattını bul
        odak_match = None
        for oh in odak_hatlar:
            odak_ad = oh.get('hat_adi', '').upper()
            # Şahinkaya, Kızılırmak, Ayvacık, Ladik kelimelerini karşılaştır
            for kw in ['ŞAHİNKAYA', 'KIZILIRMAK', 'AYVACIK', 'LADİK']:
                if kw in name.upper() and kw in odak_ad:
                    # Gidiş/Dönüş kontrolü
                    if ('GİDİŞ' in name.upper() and 'GİDİŞ' in odak_ad) or \
                       ('DÖNÜŞ' in name.upper() and 'DÖNÜŞ' in odak_ad):
                        odak_match = oh
                        break
            if odak_match:
                break
        
        if odak_match:
            # YBS Odak durakları
            hid = str(odak_match.get('id'))
            ybs_stops = ybs_request('odakSamsun_Crud', token, submethod='GetHatDuraklar', id=hid)
            
            print(f"\nOdak eşleşme: [{hid}] {odak_match.get('hat_adi')}")
            print(f"YBS Durak sayısı: {len(ybs_stops)}")
            
            # Karşılaştırma
            print("\n  ASIS Durakları:")
            for i, s in enumerate(asis_stops[:8], 1):
                print(f"    {i}. {s.get('stopName')} (ID:{s.get('stopId')}) [{s.get('latitude'):.4f}, {s.get('longitude'):.4f}]")
            if len(asis_stops) > 8:
                print(f"    ... +{len(asis_stops)-8} durak")
            
            print("\n  YBS Durakları:")
            for i, d in enumerate(ybs_stops[:8], 1):
                print(f"    {i}. {d.get('durak_adi')} - {d.get('durak_fiyat')} TL")
            if len(ybs_stops) > 8:
                print(f"    ... +{len(ybs_stops)-8} durak")
            
            # Durak isim eşleşmesi kontrolü
            asis_names = [s.get('stopName', '').upper() for s in asis_stops]
            ybs_names = [d.get('durak_adi', '').upper() for d in ybs_stops]
            
            # Tam eşleşen duraklar
            eslesenler = set(asis_names) & set(ybs_names)
            print(f"\n  Eşleşen durak: {len(eslesenler)}")
            
            # Koordinat eşleştirme yapılabilir
            if eslesenler:
                print(f"  Eşleşenler: {list(eslesenler)[:5]}")
        else:
            print("  YBS Odak eşleşmesi bulunamadı")
            
            # ASIS durakları göster
            if asis_stops:
                print("\n  ASIS Durakları:")
                for i, s in enumerate(asis_stops[:5], 1):
                    print(f"    {i}. {s.get('stopName')}")

if __name__ == '__main__':
    main()
