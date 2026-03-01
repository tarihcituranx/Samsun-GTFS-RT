"""
Samair durak fiyatlarini YBS API'den zenginlestir
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import sqlite3

YBS = "https://ybs.samsun.bel.tr/service"

def get_ybs_token():
    try:
        r = requests.get(f"{YBS}/?method=getGuestToken", timeout=10)
        return r.json().get('token')
    except Exception as e:
        print(f"Token hatasi: {e}")
        return None

def ybs_request(method, token, **params):
    p = {'method': method, 'token': token}
    p.update(params)
    try:
        r = requests.get(f"{YBS}/", params=p, timeout=20)
        return r.json().get('data', [])
    except:
        return []

def main():
    print("Samair Fiyat Zenginlestirme")
    print("=" * 50)
    
    token = get_ybs_token()
    if not token:
        print("Token alinamadi!")
        return
    
    # YBS'den Samair duraklarini cek
    duraklar = ybs_request('samair_duraklar_public', token, submethod='DuraklarList')
    if not duraklar:
        print("Durak verisi bulunamadi")
        return
    
    print(f"{len(duraklar)} Samair duragi bulundu")
    
    # Veritabanini guncelle
    conn = sqlite3.connect('samsun_v25.db')
    cur = conn.cursor()
    
    # Mevcut durak sayisi
    cur.execute('SELECT COUNT(*) FROM samair_durak')
    mevcut = cur.fetchone()[0]
    print(f"Veritabaninda mevcut: {mevcut} durak")
    
    # Hat 0 icin (genel Samair duraklari) fiyatlari guncelle
    guncellenen = 0
    for d in duraklar:
        durak_adi = d.get('durak_adi', '')
        fiyat = d.get('durak_fiyat', d.get('fiyat', ''))
        
        if durak_adi and fiyat:
            # Durak adina gore esle ve guncelle
            cur.execute('''UPDATE samair_durak SET fiyat = ? 
                          WHERE ad LIKE ? AND (fiyat = '' OR fiyat IS NULL OR fiyat = '0')''',
                       (str(fiyat), f'%{durak_adi[:20]}%'))
            if cur.rowcount > 0:
                guncellenen += cur.rowcount
    
    conn.commit()
    
    # Fiyati dolu olan duraklari say
    cur.execute("SELECT COUNT(*) FROM samair_durak WHERE fiyat != '' AND fiyat != '0'")
    fiyatli = cur.fetchone()[0]
    
    print(f"\nSonuc:")
    print(f"  Guncellenen: {guncellenen} durak")
    print(f"  Fiyatli durak: {fiyatli}/{mevcut}")
    
    # Ornek goster
    print("\nOrnek duraklar:")
    cur.execute("SELECT hat, ad, fiyat FROM samair_durak WHERE fiyat != '' LIMIT 8")
    for r in cur.fetchall():
        print(f"  Hat {r[0]}: {r[1][:30]} - {r[2]} TL")
    
    conn.close()
    print("\nTamamlandi!")

if __name__ == '__main__':
    main()
