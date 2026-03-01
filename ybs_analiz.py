"""
Odak ve Samair veri analizi - YBS API kullanarak
ASIS API erişilemezken bu script kullanılabilir
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import sqlite3
from datetime import datetime

YBS = "https://ybs.samsun.bel.tr/service"

def get_ybs_token():
    """YBS API token al"""
    try:
        r = requests.get(f"{YBS}/?method=getGuestToken", timeout=10)
        return r.json().get('token')
    except Exception as e:
        print(f"Token hatasi: {e}")
        return None

def ybs_request(method, token, referer='https://odak.samsun.bel.tr/', **params):
    """YBS API istegi"""
    p = {'method': method, 'token': token}
    p.update(params)
    headers = {'Referer': referer}
    try:
        r = requests.get(f"{YBS}/", params=p, headers=headers, timeout=20)
        res = r.json()
        return res.get('data', [])
    except Exception as e:
        print(f"YBS hatasi: {e}")
        return []

def main():
    print("=" * 60)
    print("Odak / Samair Veri Analizi (YBS API)")
    print("=" * 60)
    
    # Token al
    token = get_ybs_token()
    if not token:
        print("Token alinamadi!")
        return
    
    print(f"Token alindi: {token[:8]}...")
    
    # 1. Odak hatlari
    print("\n" + "=" * 60)
    print("ODAK TURISTIK HATLAR")
    print("=" * 60)
    
    odak_hatlar = ybs_request('odakSamsun_Crud', token, submethod='HatlarAllList')
    print(f"\nToplam {len(odak_hatlar)} Odak hatti bulundu:")
    
    odak_data = []
    for h in odak_hatlar:
        hid = str(h.get('id', ''))
        ad = h.get('hat_adi', '')
        print(f"  [{hid}] {ad}")
        
        # Durak bilgilerini cek
        duraklar = ybs_request('odakSamsun_Crud', token, submethod='GetHatDuraklar', id=hid)
        if duraklar:
            ilk_durak = duraklar[0] if duraklar else {}
            son_durak = duraklar[-1] if duraklar else {}
            print(f"      Durak: {len(duraklar)} adet")
            print(f"      Ilk: {ilk_durak.get('durak_adi', '?')} - {ilk_durak.get('durak_fiyat', '?')} TL")
            print(f"      Son: {son_durak.get('durak_adi', '?')} - {son_durak.get('durak_fiyat', '?')} TL")
        
        odak_data.append({
            'id': hid,
            'ad': ad,
            'durak_sayisi': len(duraklar) if duraklar else 0,
            'duraklar': duraklar
        })
    
    # 2. Samair duraklar
    print("\n" + "=" * 60)
    print("SAMAIR DURAKLAR (YBS API)")
    print("=" * 60)
    
    samair_duraklar = ybs_request('samair_duraklar_public', token, submethod='DuraklarList')
    if samair_duraklar:
        print(f"\nToplam {len(samair_duraklar)} Samair duragi bulundu:")
        for i, d in enumerate(samair_duraklar[:10], 1):
            fiyat = d.get('durak_fiyat', d.get('fiyat', '?'))
            print(f"  {i}. {d.get('durak_adi', '?')} - {fiyat} TL")
        if len(samair_duraklar) > 10:
            print(f"  ... ve {len(samair_duraklar) - 10} durak daha")
    else:
        print("  Samair durak bilgisi bulunamadi")
    
    # 3. Samair seferler
    print("\n" + "=" * 60)
    print("SAMAIR UCUS SEFERLERI (YBS API)")
    print("=" * 60)
    
    for hatid in [3, 4, 5, 9]:  # H1, H2, H3, H4
        hat_adi = {3: 'H1 OMU-Havalimani', 4: 'H2 TTTM-Havalimani', 
                   5: 'H3 Bafra-Havalimani', 9: 'H4 Carsamba-Havalimani'}
        seferler = ybs_request('samair_ucaksefersaatleri_public', token, submethod='HatlarList', hatid=hatid)
        print(f"\n{hat_adi.get(hatid, f'Hat {hatid}')}: {len(seferler)} sefer")
        if seferler and len(seferler) > 0:
            for s in seferler[:3]:
                print(f"    {s.get('saat', '?')} -> {s.get('varis_saati', '?')} | {s.get('ucak_firmasi', '?')}")
    
    # 4. Veritabani karsilastirma
    print("\n" + "=" * 60)
    print("VERITABANI KARSILASTIRMA")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('samsun_v25.db')
        cur = conn.cursor()
        
        # Mevcut Odak hatlari
        cur.execute('SELECT id, kod, ad FROM odak')
        db_odak = {str(r[0]): {'kod': r[1], 'ad': r[2]} for r in cur.fetchall()}
        
        # Mevcut Samair hatlari
        cur.execute('SELECT id, kod, ad FROM samair')
        db_samair = {str(r[0]): {'kod': r[1], 'ad': r[2]} for r in cur.fetchall()}
        
        print(f"\nVeritabaninda: {len(db_odak)} Odak, {len(db_samair)} Samair hatti")
        
        # API'de olup DB'de olmayan Odak hatlari
        api_odak_ids = {str(h.get('id', '')) for h in odak_hatlar}
        db_odak_ids = set(db_odak.keys())
        
        yeni_odak = api_odak_ids - db_odak_ids
        if yeni_odak:
            print(f"\nAPI'de olup DB'de OLMAYAN Odak hatlari: {yeni_odak}")
        else:
            print("\nTum Odak hatlari DB'de mevcut")
        
        conn.close()
    except Exception as e:
        print(f"DB hatasi: {e}")
    
    # JSON kaydet
    result = {
        'tarih': datetime.now().isoformat(),
        'odak_hatlar': odak_data,
        'samair_duraklar': samair_duraklar[:20] if samair_duraklar else [],
        'samair_durak_toplam': len(samair_duraklar) if samair_duraklar else 0
    }
    
    with open('ybs_analiz.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nSonuclar 'ybs_analiz.json' dosyasina kaydedildi.")

if __name__ == '__main__':
    main()
