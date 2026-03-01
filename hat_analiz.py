"""
OrjLines'da olup Odak/Samair'de olmayan hatları tespit et
YBS API'den hat ID'lerini çekerek karşılaştır
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
from datetime import datetime

ASIS_BASE = "https://sfrb.samsun.bel.tr/api"
YBS = "https://ybs.samsun.bel.tr/service"

def get_asis_token():
    """ASIS API token al"""
    try:
        r = requests.get(f"{ASIS_BASE}/Public/VisitorToken", timeout=10)
        return r.json().get('data', {}).get('token')
    except:
        return None

def get_ybs_token():
    """YBS API token al"""
    try:
        r = requests.get(f"{YBS}/?method=getGuestToken", timeout=10)
        return r.json().get('token')
    except:
        return None

def asis_request(endpoint, token, **params):
    """ASIS API isteği"""
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get(f"{ASIS_BASE}/Announce/{endpoint}", headers=headers, params=params, timeout=15)
    return r.json().get('data', [])

def ybs_request(method, token, referer='https://odak.samsun.bel.tr/', **params):
    """YBS API isteği"""
    p = {'method': method, 'token': token}
    p.update(params)
    headers = {'Referer': referer}
    r = requests.get(f"{YBS}/", params=p, headers=headers, timeout=15)
    res = r.json()
    return res.get('data', [])

def main():
    print("=" * 60)
    print("🔍 OrjLines / Odak / Samair Hat Karşılaştırma")
    print("=" * 60)
    
    # Token al
    asis_token = get_asis_token()
    ybs_token = get_ybs_token()
    
    if not asis_token or not ybs_token:
        print("❌ Token alınamadı!")
        return
    
    print("✅ Token alındı\n")
    
    # 1. ASIS Lines ve OrjLines çek
    lines = asis_request('Lines', asis_token)
    orj_lines = asis_request('OrjLines', asis_token)
    
    print(f"📊 ASIS Lines: {len(lines)} hat")
    print(f"📊 ASIS OrjLines: {len(orj_lines)} hat")
    
    # Lines kodları
    lines_codes = {str(l.get('lineCode', '')).strip().upper() for l in lines if l.get('lineCode')}
    
    # OrjLines kodları (Lines'ta olmayanlar)
    orj_only = []
    for o in orj_lines:
        code = str(o.get('lineCode', '')).strip()
        if code.upper() not in lines_codes:
            orj_only.append({
                'code': code,
                'name': o.get('lineName', code)
            })
    
    print(f"\n📍 OrjLines'ta olup Lines'ta OLMAYAN: {len(orj_only)} hat")
    
    # 2. Odak hatlarını çek
    odak_hatlar = ybs_request('odakSamsun_Crud', ybs_token, submethod='HatlarAllList')
    print(f"\n📊 Odak Hatları: {len(odak_hatlar)} hat")
    
    odak_ids = set()
    odak_names = set()
    for h in odak_hatlar:
        odak_ids.add(str(h.get('id', '')))
        name = h.get('hat_adi', '').upper()
        if name:
            odak_names.add(name)
    
    print(f"   Odak ID'ler: {sorted(odak_ids)}")
    
    # 3. Samair hatlarını kontrol et (YBS API)
    samair_hatlar = []
    for hatid in [3, 4, 5, 9]:  # H1,H2,H3,H4 için test
        result = ybs_request('samair_ucaksefersaatleri_public', ybs_token, submethod='HatlarList', hatid=hatid)
        if result:
            samair_hatlar.append({'id': hatid, 'count': len(result)})
    
    print(f"\n📊 Samair YBS Hat ID'ler: {[h['id'] for h in samair_hatlar]}")
    
    # 4. OrjOnly içinde potansiyel Odak/Samair hatları ara
    print("\n" + "=" * 60)
    print("🔍 DETAYLI ANALİZ - OrjLines'ta olup diğerlerinde olmayanlar")
    print("=" * 60)
    
    turistik = []
    havalimani = []
    ekspres = []
    diger = []
    
    skip_keywords = ['OTOPARK', 'VAPUR', 'GEMİ', 'TELEFERİK', 'KENT MÜZESİ', 'GÖREVLİ', 'AMAZON', 'FERİBOT']
    
    for h in orj_only:
        code_up = h['code'].upper()
        name_up = h['name'].upper()
        
        # Skip gereksiz olanları
        if any(kw in code_up or kw in name_up for kw in skip_keywords):
            continue
        
        # Kategorize et
        if 'EKSPRES' in name_up or code_up.startswith('E') and len(code_up) > 1:
            ekspres.append(h)
        elif code_up.startswith('G') or 'TURİSTİK' in name_up or 'KANYON' in name_up:
            turistik.append(h)
        elif code_up.startswith('H') and 'HAVALİMANI' in name_up:
            havalimani.append(h)
        else:
            diger.append(h)
    
    if ekspres:
        print(f"\n🚀 Ekspres Hatlar ({len(ekspres)}):")
        for h in ekspres[:10]:
            print(f"   - {h['code']}: {h['name']}")
    
    if turistik:
        print(f"\n🎯 Potansiyel Turistik Hatlar ({len(turistik)}):")
        for h in turistik[:10]:
            # Odak'ta var mı kontrol et
            in_odak = any(h['name'].upper() in n for n in odak_names)
            status = "✅ Odak'ta VAR" if in_odak else "❌ Odak'ta YOK"
            print(f"   - {h['code']}: {h['name']} [{status}]")
    
    if havalimani:
        print(f"\n✈️ Havalimanı Hatları ({len(havalimani)}):")
        for h in havalimani[:10]:
            print(f"   - {h['code']}: {h['name']}")
    
    if diger:
        print(f"\n📦 Diğer ({len(diger)}):")
        for h in diger[:15]:
            print(f"   - {h['code']}: {h['name']}")
    
    # 5. Odak durak fiyatlarını kontrol et
    print("\n" + "=" * 60)
    print("💰 ODAK DURAK FİYATLARI KONTROLÜ")
    print("=" * 60)
    
    for h in odak_hatlar[:3]:
        hid = str(h.get('id', ''))
        name = h.get('hat_adi', '')
        duraklar = ybs_request('odakSamsun_Crud', ybs_token, submethod='GetHatDuraklar', id=hid)
        
        if duraklar:
            print(f"\n📍 {name} (ID: {hid}):")
            for d in duraklar[:3]:
                fiyat = d.get('durak_fiyat', '?')
                fiyat_ogr = d.get('durak_fiyat_ogr', '?')
                print(f"   - {d.get('durak_adi', '?')}: ₺{fiyat} / ₺{fiyat_ogr}")
    
    # 6. Samair fiyatlarını kontrol et (YBS API)
    print("\n" + "=" * 60)
    print("💰 SAMAİR DURAK FİYATLARI KONTROLÜ (YBS API)")
    print("=" * 60)
    
    samair_duraklar = ybs_request('samair_duraklar_public', ybs_token, submethod='DuraklarList')
    if samair_duraklar:
        print(f"\n✅ Samair durakları: {len(samair_duraklar)} adet")
        for d in samair_duraklar[:5]:
            print(f"   - {d.get('durak_adi', '?')}: ₺{d.get('durak_fiyat', d.get('fiyat', '?'))}")
    else:
        print("   ⚠️ Samair durak API'si veri döndürmedi")
    
    print("\n" + "=" * 60)
    print("📊 ÖZET")
    print("=" * 60)
    print(f"   Lines: {len(lines)} | OrjLines: {len(orj_lines)} | Fark: {len(orj_only)}")
    print(f"   Odak: {len(odak_hatlar)} | Samair YBS ID: {len(samair_hatlar)}")
    
    # JSON kaydet
    result = {
        'tarih': datetime.now().isoformat(),
        'lines_count': len(lines),
        'orjlines_count': len(orj_lines),
        'orjlines_only': orj_only,
        'odak_hatlar': [{'id': h.get('id'), 'ad': h.get('hat_adi')} for h in odak_hatlar],
        'samair_ybs_ids': samair_hatlar,
        'ekspres': ekspres,
        'turistik': turistik,
        'havalimani': havalimani
    }
    
    with open('hat_analiz.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 Sonuçlar 'hat_analiz.json' dosyasına kaydedildi.")

if __name__ == '__main__':
    main()
