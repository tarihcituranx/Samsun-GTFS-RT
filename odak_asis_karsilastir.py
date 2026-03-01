"""
Odak hatlarini ASIS API ile karsilastir ve duraklari eslestir
Samair ornegindeki gibi StopsStations'dan gercek duraklari cek
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import sqlite3
import json
from datetime import datetime

# samsun.py'deki dogru API
ASIS = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
YBS = "https://ybs.samsun.bel.tr/service"

def get_asis_token():
    """ASIS API token al"""
    try:
        r = requests.get(f"{ASIS.replace('/Asis', '')}/Public/VisitorToken", timeout=10)
        data = r.json()
        return data.get('data', {}).get('token')
    except Exception as e:
        print(f"ASIS Token hatasi: {e}")
        return None

def get_ybs_token():
    """YBS API token al"""
    try:
        r = requests.get(f"{YBS}/?method=getGuestToken", timeout=10)
        return r.json().get('token')
    except:
        return None

def asis_request(endpoint, token, **params):
    """ASIS API istegi"""
    headers = {'Authorization': f'Bearer {token}'}
    try:
        r = requests.get(f"{ASIS}/{endpoint}", headers=headers, params=params, timeout=15)
        return r.json().get('data', [])
    except Exception as e:
        print(f"ASIS hatasi: {e}")
        return []

def ybs_request(method, token, **params):
    """YBS API istegi"""
    p = {'method': method, 'token': token}
    p.update(params)
    headers = {'Referer': 'https://odak.samsun.bel.tr/'}
    try:
        r = requests.get(f"{YBS}/", params=p, headers=headers, timeout=20)
        return r.json().get('data', [])
    except:
        return []

def main():
    print("=" * 70)
    print("ODAK HATLARI - ASIS vs YBS DURAK KARSILASTIRMA")
    print("=" * 70)
    
    # Token al
    asis_token = get_asis_token()
    ybs_token = get_ybs_token()
    
    if not asis_token:
        print("ASIS token alinamadi - sadece YBS kullanilacak")
    else:
        print(f"ASIS Token: {asis_token[:10]}...")
    
    if not ybs_token:
        print("YBS token alinamadi!")
        return
    print(f"YBS Token: {ybs_token[:10]}...")
    
    # 1. ASIS'ten tum hatlari cek
    print("\n" + "=" * 70)
    print("ASIS HATLARI TARAMA")
    print("=" * 70)
    
    if asis_token:
        lines = asis_request('Lines', asis_token)
        orj_lines = asis_request('OrjLines', asis_token)
        print(f"Lines: {len(lines)}, OrjLines: {len(orj_lines)}")
        
        # Turistik/Gezi hatlarini bul (G1, G2 gibi veya isimde kanyon, delta vs)
        turistik_keywords = ['KANYON', 'DELTA', 'BARAJ', 'LADİK', 'AKDAĞ', 'ŞAHİNKAYA', 
                             'KIZILIRMAK', 'AYVACIK', 'TURİSTİK', 'ODAK']
        
        potansiyel_odak = []
        for line in lines + orj_lines:
            code = line.get('lineCode', '')
            name = line.get('lineName', '')
            name_up = name.upper()
            
            if any(kw in name_up for kw in turistik_keywords):
                potansiyel_odak.append({'code': code, 'name': name, 'kaynak': 'ASIS'})
                print(f"  Bulundu: {code} - {name}")
    else:
        potansiyel_odak = []
        print("  ASIS erisimi yok, atlanıyor...")
    
    # 2. YBS'den Odak hatlarini cek
    print("\n" + "=" * 70)
    print("YBS ODAK HATLARI")
    print("=" * 70)
    
    odak_hatlar = ybs_request('odakSamsun_Crud', ybs_token, submethod='HatlarAllList')
    print(f"Toplam {len(odak_hatlar)} Odak hatti:")
    
    for h in odak_hatlar:
        hid = h.get('id', '')
        ad = h.get('hat_adi', '')
        print(f"  [{hid}] {ad}")
    
    # 3. Her Odak hatti icin durak karsilastirmasi
    print("\n" + "=" * 70)
    print("DURAK KARSILASTIRMA")
    print("=" * 70)
    
    karsilastirma = []
    
    for h in odak_hatlar:
        hid = str(h.get('id', ''))
        ad = h.get('hat_adi', '')
        
        # YBS'den duraklari cek
        ybs_duraklar = ybs_request('odakSamsun_Crud', ybs_token, submethod='GetHatDuraklar', id=hid)
        
        print(f"\n--- [{hid}] {ad} ---")
        print(f"YBS Durak sayisi: {len(ybs_duraklar)}")
        
        # ASIS'te bu hat var mi ara
        if asis_token:
            # Hat adinin bir kismini kullanarak ASIS'te ara
            # Ornegin "Şahinkaya Kanyonu Gidiş" -> "Şahinkaya" ile ara
            arama_kelime = ad.split()[0] if ad else ''
            
            asis_duraklar = []
            for p in potansiyel_odak:
                if arama_kelime.upper() in p['name'].upper():
                    # Bu hat icin ASIS duraklarini cek
                    stops = asis_request('StopsStations', asis_token, lineCode=p['code'])
                    if stops:
                        print(f"  ASIS eslesti: {p['code']} - {p['name']}")
                        print(f"  ASIS Durak sayisi: {len(stops)}")
                        asis_duraklar = stops
                        break
            
            if asis_duraklar:
                # Karsilastir
                ybs_adlar = [d.get('durak_adi', '') for d in ybs_duraklar]
                asis_adlar = [d.get('stopName', '') for d in asis_duraklar]
                
                print(f"\n  YBS Duraklar:")
                for i, d in enumerate(ybs_duraklar[:5], 1):
                    print(f"    {i}. {d.get('durak_adi', '')} - {d.get('durak_fiyat', '')} TL")
                if len(ybs_duraklar) > 5:
                    print(f"    ... +{len(ybs_duraklar)-5} durak daha")
                
                print(f"\n  ASIS Duraklar:")
                for i, d in enumerate(asis_duraklar[:5], 1):
                    print(f"    {i}. {d.get('stopName', '')}")
                if len(asis_duraklar) > 5:
                    print(f"    ... +{len(asis_duraklar)-5} durak daha")
                
                karsilastirma.append({
                    'odak_id': hid,
                    'odak_ad': ad,
                    'ybs_durak_sayisi': len(ybs_duraklar),
                    'asis_durak_sayisi': len(asis_duraklar),
                    'ybs_duraklar': ybs_adlar,
                    'asis_duraklar': asis_adlar
                })
            else:
                print(f"  ASIS eslesme bulunamadi")
                karsilastirma.append({
                    'odak_id': hid,
                    'odak_ad': ad,
                    'ybs_durak_sayisi': len(ybs_duraklar),
                    'asis_durak_sayisi': 0,
                    'ybs_duraklar': [d.get('durak_adi', '') for d in ybs_duraklar],
                    'asis_duraklar': []
                })
        else:
            print(f"  ASIS erisimi yok")
            for i, d in enumerate(ybs_duraklar[:3], 1):
                print(f"    {i}. {d.get('durak_adi', '')} - {d.get('durak_fiyat', '')} TL")
    
    # JSON kaydet
    result = {
        'tarih': datetime.now().isoformat(),
        'karsilastirma': karsilastirma,
        'potansiyel_odak_asis': potansiyel_odak
    }
    
    with open('odak_asis_karsilastirma.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nSonuclar 'odak_asis_karsilastirma.json' dosyasina kaydedildi.")

if __name__ == '__main__':
    main()
