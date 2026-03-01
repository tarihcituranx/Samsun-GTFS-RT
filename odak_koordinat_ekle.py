"""
Odak durakları - ASIS StopsStations'dan koordinat ve sıra düzeltmesi
"""
import sys, io, requests, json, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ASIS = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
YBS = "https://ybs.samsun.bel.tr/service"

# ASIS OrjLines kodu -> YBS Odak ID eşleştirmesi
ODAK_ESLESTIRME = {
    # Gidiş hatları (son durak = başlangıç noktası)
    'G1 ŞAHİNKAYA - SAMSUN': {'ybs_id': 1, 'tip': 'gidis'},  # Şahinkaya -> TTTM
    'G1 SAMSUN - ŞAHİNKAYA': {'ybs_id': 2, 'tip': 'donus'},  # TTTM -> Şahinkaya
    'G2 KIZILIRMAK - SAMSUN': {'ybs_id': 3, 'tip': 'gidis'},
    'G2 SAMSUN - KIZILIRMAK': {'ybs_id': 4, 'tip': 'donus'},
    'G3 AYVACIK - SAMSUN': {'ybs_id': 5, 'tip': 'gidis'},
    'G3 SAMSUN - AYVACIK': {'ybs_id': 6, 'tip': 'donus'},
    'G4 LADİK AKDAĞ - SAMSUN': {'ybs_id': 12, 'tip': 'gidis'},
    'G4 SAMSUN - LADİK AKDAĞ': {'ybs_id': 13, 'tip': 'donus'},
}

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
    print("ODAK DURAK ZENGINLEŞTIRME - ASIS Koordinatları Ekleme")
    print("=" * 70)
    
    token = get_ybs_token()
    print(f"YBS Token: {token[:8]}...")
    
    # Veritabanı bağlantısı
    conn = sqlite3.connect('samsun_v25.db')
    cur = conn.cursor()
    
    # OrjLines'dan turistik hatları çek
    r = requests.get(f"{ASIS}/OrjLines", timeout=15)
    orj_lines = r.json().get('data', [])
    
    guncellenen = 0
    for line in orj_lines:
        code = line.get('lineCode', '')
        name = line.get('lineName', '')
        
        # Eşleştirme kontrolü
        if code not in ODAK_ESLESTIRME:
            continue
        
        eslesme = ODAK_ESLESTIRME[code]
        ybs_id = eslesme['ybs_id']
        tip = eslesme['tip']
        
        print(f"\n--- {code} -> YBS ID {ybs_id} ({tip}) ---")
        
        # ASIS durakları
        r = requests.get(f"{ASIS}/StopsStations", params={'lineCode': code}, timeout=15)
        asis_stops = r.json().get('data', [])
        
        # YBS durakları
        ybs_stops = ybs_request('odakSamsun_Crud', token, submethod='GetHatDuraklar', id=ybs_id)
        
        print(f"ASIS: {len(asis_stops)} durak, YBS: {len(ybs_stops)} durak")
        
        # Durak eşleştirme ve koordinat güncelleme
        for i, asis_d in enumerate(asis_stops, 1):
            asis_name = asis_d.get('stopName', '').upper().strip()
            asis_lat = asis_d.get('latitude', 0)
            asis_lon = asis_d.get('longitude', 0)
            asis_id = asis_d.get('stopId', '')
            
            # YBS'de benzer isimli durak ara
            best_match = None
            best_score = 0
            
            for ybs_d in ybs_stops:
                ybs_name = ybs_d.get('durak_adi', '').upper().strip()
                
                # Basit isim eşleştirme
                if asis_name == ybs_name:
                    best_match = ybs_d
                    best_score = 100
                    break
                
                # Kısmi eşleşme
                asis_words = set(asis_name.split())
                ybs_words = set(ybs_name.split())
                common = asis_words & ybs_words
                if len(common) > 0:
                    score = len(common) / max(len(asis_words), len(ybs_words)) * 100
                    if score > best_score:
                        best_score = score
                        best_match = ybs_d
            
            if best_match and best_score >= 50:
                ybs_name = best_match.get('durak_adi', '')
                print(f"  {i}. {asis_name[:25]:25} <-> {ybs_name[:25]:25} ({best_score:.0f}%)")
                
                # Veritabanında koordinatları güncelle
                cur.execute('''UPDATE odak_durak SET lat=?, lon=?, kod=? 
                              WHERE hat=? AND UPPER(ad) LIKE ?''',
                           (asis_lat, asis_lon, str(asis_id), ybs_id, f'%{ybs_name[:15].upper()}%'))
                if cur.rowcount > 0:
                    guncellenen += cur.rowcount
            else:
                print(f"  {i}. {asis_name[:30]} -> EŞLEŞMEDİ")
    
    conn.commit()
    
    # Sonuç kontrolü
    cur.execute("SELECT COUNT(*) FROM odak_durak WHERE lat != 0 AND lon != 0")
    koordinatli = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM odak_durak")
    toplam = cur.fetchone()[0]
    
    print(f"\n" + "=" * 70)
    print(f"SONUÇ: {guncellenen} durak güncellendi")
    print(f"Koordinatlı durak: {koordinatli}/{toplam}")
    
    # Örnek göster
    print("\nÖrnek güncellenmiş duraklar:")
    cur.execute("SELECT hat, ad, lat, lon, kod FROM odak_durak WHERE lat != 0 LIMIT 10")
    for r in cur.fetchall():
        print(f"  Hat {r[0]}: {r[1][:30]} [{r[2]:.4f}, {r[3]:.4f}] Kod:{r[4]}")
    
    conn.close()

if __name__ == '__main__':
    main()
