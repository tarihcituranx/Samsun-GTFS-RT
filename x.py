#!/usr/bin/env python3
"""
API VERİ KARŞILAŞTIRMA ARACI
=============================
Bu script tüm API kaynaklarından veri çeker ve karşılaştırma yapılabilir 
formatta çıktı verir. Hat adı eşleştirmesi için kullanılır.
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import urllib3
import sys

sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SAMULAS_BASE_URL = "https://samulas.com.tr"
YBS_BASE_URL = "https://ybs.samsun.bel.tr/service/"
ASIS_URL = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"

def get_token():
    """YBS Token al"""
    try:
        r = requests.post(YBS_BASE_URL, data={'method': 'getGuestToken'}, verify=False, timeout=10)
        return r.json().get('token')
    except:
        return None

def clean_price(text):
    """Fiyat metnini sayıya çevirir"""
    if not text: return 0.0
    text = str(text).lower().replace('tl', '').replace('₺', '').strip().replace(',', '.')
    try:
        match = re.search(r"\d+(\.\d+)?", text)
        return float(match.group()) if match else 0.0
    except:
        return 0.0

# =====================================================
# 1. ASIS API - TÜM HATLAR (KAYNAK)
# =====================================================
def get_asis_lines():
    """ASIS API'den tüm hatları çeker (ana kaynak)"""
    print("\n" + "="*70)
    print("📡 [1] ASIS API - TÜM HATLAR (api.samsun.bel.tr)")
    print("="*70)
    try:
        r = requests.get(f"{ASIS_URL}/Lines", timeout=30)
        data = r.json().get('data', [])
        print(f"✅ Toplam {len(data)} hat bulundu\n")
        
        # Kategorilere ayır
        hatlar = {'R': [], 'T': [], 'E': [], 'H': [], 'Diger': []}
        for h in data:
            code = str(h.get('lineCode', '')).strip()
            name = h.get('lineName', code)
            if code.startswith('R'): hatlar['R'].append({'code': code, 'name': name})
            elif code.startswith('T'): hatlar['T'].append({'code': code, 'name': name})
            elif code.startswith('E'): hatlar['E'].append({'code': code, 'name': name})
            elif code.startswith('H'): hatlar['H'].append({'code': code, 'name': name})
            else: hatlar['Diger'].append({'code': code, 'name': name})
        
        for kat, lst in hatlar.items():
            if lst:
                print(f"\n{'🔄 Ring' if kat=='R' else '🚌 T Hatları' if kat=='T' else '🚀 Ekspres' if kat=='E' else '✈️ Havalimanı' if kat=='H' else '📌 Diğer'} ({len(lst)} hat):")
                for h in sorted(lst, key=lambda x: x['code'])[:10]:
                    print(f"   {h['code']:15} → {h['name']}")
                if len(lst) > 10:
                    print(f"   ... ve {len(lst)-10} hat daha")
        
        return data
    except Exception as e:
        print(f"❌ Hata: {e}")
        return []

# =====================================================
# 2. SAMULAS WEB - OTOBUS FİYATLARI
# =====================================================
def get_samulas_prices():
    """Samulaş web sitesinden fiyatları çeker"""
    print("\n" + "="*70)
    print("🌐 [2] SAMULAS WEB - OTOBÜS FİYATLARI (samulas.com.tr)")
    print("="*70)
    
    all_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for page in range(1, 9):
        try:
            res = requests.get(f"{SAMULAS_BASE_URL}/otobusler?page={page}", headers=headers, timeout=15)
            soup = BeautifulSoup(res.content, 'html.parser')
            
            links = []
            for a in soup.find_all('a', href=True):
                if 'otobus-detay' in a['href']:
                    full_url = a['href'] if a['href'].startswith('http') else SAMULAS_BASE_URL + (a['href'] if a['href'].startswith('/') else '/' + a['href'])
                    if full_url not in links:
                        links.append(full_url)
            
            for url in links:
                try:
                    r = requests.get(url, headers=headers, timeout=10)
                    s = BeautifulSoup(r.content, 'html.parser')
                    
                    name = "?"
                    title_div = s.find('div', class_='section-title')
                    if title_div and title_div.find('h2'):
                        name = " ".join(title_div.find('h2').get_text(strip=True).split())
                    
                    cols = s.find_all('div', class_='col-6 p-2')
                    tam_fiyat = 0.0
                    for idx, col in enumerate(cols):
                        text = col.get_text(strip=True).lower()
                        if "tam" in text and "öğrenci" not in text and "abonman" not in text:
                            if idx + 1 < len(cols):
                                tam_fiyat = clean_price(cols[idx+1].get_text(strip=True))
                                break
                    
                    # Hat kodunu çıkar (ilk kelime genellikle kod)
                    parts = name.split()
                    kod = parts[0] if parts else '?'
                    
                    all_data.append({'kod': kod, 'tam_ad': name, 'fiyat': tam_fiyat})
                except: pass
        except: pass
    
    print(f"✅ Toplam {len(all_data)} fiyat kaydı çekildi\n")
    
    # Fiyata göre grupla
    fiyat_gruplari = {}
    for d in all_data:
        key = d['fiyat']
        if key not in fiyat_gruplari:
            fiyat_gruplari[key] = []
        fiyat_gruplari[key].append(d)
    
    for fiyat in sorted(fiyat_gruplari.keys(), reverse=True):
        print(f"\n💰 {fiyat:.2f} TL ({len(fiyat_gruplari[fiyat])} hat):")
        for h in fiyat_gruplari[fiyat][:8]:
            print(f"   {h['kod']:8} → {h['tam_ad'][:50]}")
        if len(fiyat_gruplari[fiyat]) > 8:
            print(f"   ... ve {len(fiyat_gruplari[fiyat])-8} hat daha")
    
    return all_data

# =====================================================
# 3. SAMAIR - YBS API
# =====================================================
def get_samair_data(token):
    """Samair verilerini çeker - duraklar ve fiyatlar"""
    print("\n" + "="*70)
    print("✈️ [3] SAMAIR - YBS API (Havalimanı Servisi)")
    print("="*70)
    
    if not token:
        print("❌ Token yok!")
        return [], []
    
    # YBS Duraklar
    print("\n📍 A) YBS - samair_duraklar_public/DuraklarList:")
    duraklar_ybs = []
    try:
        params = {'method': 'samair_duraklar_public', 'submethod': 'DuraklarList', 'token': token}
        r = requests.get(YBS_BASE_URL, params=params, verify=False, timeout=10)
        data = r.json().get('data', [])
        print(f"   ✅ {len(data)} durak bulundu")
        for d in data[:10]:
            fiyat = clean_price(d.get('durak_fiyat', d.get('fiyat', '')))
            print(f"      {d.get('durak_kodu', '?'):10} | {d.get('durak_adi', '?')[:30]:30} | Fiyat: {fiyat} TL")
            duraklar_ybs.append({
                'kod': d.get('durak_kodu'),
                'ad': d.get('durak_adi'),
                'fiyat': fiyat,
                'lat': d.get('lat', d.get('latitude')),
                'lon': d.get('lon', d.get('longitude'))
            })
        if len(data) > 10:
            for d in data[10:]:
                fiyat = clean_price(d.get('durak_fiyat', d.get('fiyat', '')))
                duraklar_ybs.append({
                    'kod': d.get('durak_kodu'),
                    'ad': d.get('durak_adi'),
                    'fiyat': fiyat,
                    'lat': d.get('lat', d.get('latitude')),
                    'lon': d.get('lon', d.get('longitude'))
                })
            print(f"      ... ve {len(data)-10} durak daha")
    except Exception as e:
        print(f"   ❌ Hata: {e}")
    
    # ASIS üzerinden Samair hatları
    print("\n📍 B) ASIS - Havalimanı Hattı Durakları:")
    samair_asis = {}
    samair_hatlar = [
        ('H1 OMÜ - HAVALİMANI', 'H1'),
        ('H1 HAVALİMANI - OMÜ', 'H1'),
        ('H2 TTTM - HAVALİMANI', 'H2'),
        ('H2 HAVALİMANI - TTTM', 'H2'),
        ('H3 BAFRA - HAVALİMANI', 'H3'),
        ('H3 HAVALİMANI - BAFRA', 'H3'),
        ('H4 ÇARŞAMBA - HAVALİMANI', 'H4'),
        ('H4 HAVALİMANI - ÇARŞAMBA', 'H4'),
    ]
    for hat_code, hat_short in samair_hatlar:
        try:
            r = requests.get(f"{ASIS_URL}/StopsStations", params={'lineCode': hat_code}, timeout=10)
            data = r.json().get('data', [])
            if data:
                if hat_short not in samair_asis:
                    samair_asis[hat_short] = []
                for d in data:
                    samair_asis[hat_short].append({
                        'kod': d.get('stopId'),
                        'ad': d.get('stopName'),
                        'lat': d.get('latitude'),
                        'lon': d.get('longitude')
                    })
        except: pass
    
    for hat, duraklar in samair_asis.items():
        print(f"   {hat}: {len(duraklar)} durak (ASIS)")
        for d in duraklar[:3]:
            print(f"      {d['kod']:10} | {d['ad'][:40]}")
        if len(duraklar) > 3:
            print(f"      ...")
    
    # Sefer Bilgileri
    print("\n📍 C) YBS - Sefer Saatleri (samair_ucaksefersaatleri_public):")
    seferler = []
    for hatid in range(1, 11):
        try:
            params = {'method': 'samair_ucaksefersaatleri_public', 'submethod': 'HatlarList', 'hatid': hatid, 'token': token}
            r = requests.get(YBS_BASE_URL, params=params, verify=False, timeout=10)
            data = r.json().get('data') or r.json().get('root') or []
            if data:
                print(f"   hatid={hatid}: {len(data)} sefer")
                for s in data[:2]:
                    print(f"      {s.get('saat', '?')[:5]} → {s.get('varis_saati', '?')[:5]} | {s.get('ucak_firmasi', '?')} | {s.get('tarih', '?')}")
                seferler.extend([{**s, 'hatid': hatid} for s in data])
        except: pass
    
    return duraklar_ybs, seferler

# =====================================================
# 4. ODAK - TURİSTİK HATLAR
# =====================================================
def get_odak_data(token):
    """Odak turistik hat verilerini çeker"""
    print("\n" + "="*70)
    print("🎯 [4] ODAK SAMSUN - TURİSTİK HATLAR (YBS API)")
    print("="*70)
    
    if not token:
        print("❌ Token yok!")
        return []
    
    # Hat listesi
    print("\n📍 A) odakSamsun_Crud/HatlarAllList:")
    hatlar = []
    try:
        params = {'method': 'odakSamsun_Crud', 'submethod': 'HatlarAllList', 'token': token}
        r = requests.get(YBS_BASE_URL, params=params, verify=False, timeout=10)
        data = r.json().get('data', [])
        print(f"   ✅ {len(data)} turistik hat bulundu\n")
        
        for h in data:
            hid = h.get('id')
            hat_adi = h.get('hat_adi', '?')
            hat_aciklama = h.get('hat_aciklama', '')
            print(f"   ID={hid:3} | {hat_aciklama:5} {hat_adi}")
            
            # Durak detaylarını çek
            try:
                params2 = {'method': 'odakSamsun_Crud', 'submethod': 'GetHatDuraklar', 'token': token, 'id': hid}
                r2 = requests.get(YBS_BASE_URL, params=params2, verify=False, timeout=10)
                duraklar = r2.json().get('data', [])
                if duraklar:
                    for d in duraklar[:2]:
                        fiyat = clean_price(d.get('durak_fiyat', ''))
                        fiyat_ogr = clean_price(d.get('durak_fiyat_ogr', ''))
                        print(f"         └─ {d.get('durak_adi', '?')[:35]:35} | Fiyat: {fiyat} / {fiyat_ogr} TL")
                    if len(duraklar) > 2:
                        print(f"         └─ ... ({len(duraklar)} durak toplam)")
                hatlar.append({'id': hid, 'ad': hat_adi, 'kod': hat_aciklama, 'durak_sayisi': len(duraklar)})
            except: pass
    except Exception as e:
        print(f"   ❌ Hata: {e}")
    
    return hatlar

# =====================================================
# 5. KARŞILAŞTIRMA
# =====================================================
def compare_data(asis_lines, samulas_prices):
    """ASIS ve Samulaş verilerini karşılaştır"""
    print("\n" + "="*70)
    print("🔍 [5] KARŞILAŞTIRMA - ASIS vs SAMULAS")
    print("="*70)
    
    # ASIS hat kodlarını set olarak al
    asis_codes = {str(h.get('lineCode', '')).strip().upper() for h in asis_lines}
    
    # Samulaş'tan gelen kodları karşılaştır
    eslesen = []
    eslesmeyenler = []
    
    for sam in samulas_prices:
        kod = sam['kod'].upper().strip()
        tam_ad = sam['tam_ad'].upper()
        
        # Direkt eşleşme
        if kod in asis_codes:
            eslesen.append({'samulas': sam['tam_ad'], 'asis': kod, 'fiyat': sam['fiyat']})
        else:
            # İlk kelimeyi dene (R2, E1 gibi)
            ilk_kelime = tam_ad.split()[0] if tam_ad.split() else ''
            found = False
            for a_code in asis_codes:
                if a_code.startswith(ilk_kelime.split()[0][:2]) or ilk_kelime.startswith(a_code.split()[0][:2]):
                    eslesen.append({'samulas': sam['tam_ad'], 'asis': a_code, 'fiyat': sam['fiyat']})
                    found = True
                    break
            if not found:
                eslesmeyenler.append(sam)
    
    print(f"\n✅ Eşleşen: {len(eslesen)}/{len(samulas_prices)}")
    print(f"⚠️ Eşleşmeyen: {len(eslesmeyenler)}/{len(samulas_prices)}")
    
    if eslesmeyenler:
        print("\n❌ EŞLEŞTİRİLEMEYEN HATLAR:")
        for e in eslesmeyenler:
            print(f"   {e['kod']:8} | {e['tam_ad'][:50]} | {e['fiyat']} TL")
    
    print("\n💡 ÖNERİ: Eşleşmeyen hatları manuel olarak eşleştirmek için:")
    print("   samsun.py içinde HAT_FIYAT_MAPPING dictionary'si oluşturabilirsiniz.")

# =====================================================
# ANA PROGRAM
# =====================================================
def main():
    print("="*70)
    print("🔍 SAMSUN ULAŞIM - API VERİ KARŞILAŞTIRMA ARACI")
    print("   Bu araç tüm veri kaynaklarını tarar ve karşılaştırır.")
    print("="*70)
    
    # Token al
    print("\n🔑 YBS Token alınıyor...")
    token = get_token()
    if token:
        print(f"   ✅ Token: {token[:20]}...")
    else:
        print("   ❌ Token alınamadı!")
    
    # 1. ASIS Hatları
    asis_lines = get_asis_lines()
    
    # 2. Samulaş Fiyatları
    samulas_prices = get_samulas_prices()
    
    # 3. Samair
    samair_duraklar, samair_seferler = get_samair_data(token)
    
    # 4. Odak
    odak_hatlar = get_odak_data(token)
    
    # 5. Karşılaştırma
    compare_data(asis_lines, samulas_prices)
    
    print("\n" + "="*70)
    print("📊 ÖZET")
    print("="*70)
    print(f"""
   ASIS Hatlar:     {len(asis_lines)}
   Samulaş Fiyat:   {len(samulas_prices)}
   Samair Durak:    {len(samair_duraklar)}
   Samair Sefer:    {len(samair_seferler)}
   Odak Hat:        {len(odak_hatlar)}
""")
    
    # JSON olarak kaydet
    output = {
        'asis_lines': [{'code': h.get('lineCode'), 'name': h.get('lineName')} for h in asis_lines],
        'samulas_prices': samulas_prices,
        'samair_duraklar': samair_duraklar,
        'odak_hatlar': odak_hatlar
    }
    
    with open('api_karsilastirma.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("💾 Detaylı veri: api_karsilastirma.json dosyasına kaydedildi.")
    print("="*70)

if __name__ == "__main__":
    main()