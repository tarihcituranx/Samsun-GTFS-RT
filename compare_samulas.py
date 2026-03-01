import json
import sqlite3
import requests

def compare():
    print("--- 1. Samulaş (YENİ API) Hatlarını Çek ---")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get('https://samulas.com.tr/api/v1/lines/list?page=1&limit=500', headers=headers, timeout=10)
        samulas_data = r.json().get('data', {}).get('data', [])
        print(f"Başarıyla {len(samulas_data)} hat çekildi.")
    except Exception as e:
        print(f"Hata: {e}")
        return

    # Extract unique line codes and names from Samulaş
    samulas_lines = {}
    for d in samulas_data:
        # We will use 'line_code' as the main identifier, and 'text' as name
        lc = d.get('line_code', '').strip()
        name = d.get('text', '').strip()
        short = d.get('short_line_name', '').strip()
        if lc:
            samulas_lines[lc] = {'name': name, 'short': short}

    print("\n--- 2. Yerel ASIS Veritabanını (samsun_v25.db) Çek ---")
    try:
        conn = sqlite3.connect('samsun_v25.db')
        c = conn.cursor()
        c.execute("SELECT code, name FROM hat")
        db_hatlar = c.fetchall()
        
        asis_lines = {}
        for row in db_hatlar:
            code = row[0]
            name = row[1]
            source = 'Lines' 
            asis_lines[code] = {'name': name, 'source': source}
        print(f"Yerel DB'de {len(db_hatlar)} aktif otobüs/tramvay hattı var.")
    except Exception as e:
        print(f"DB Hatası: {e}")
        return

    print("\n--- 3. Karşılaştırma Sonuçları ---")
    
    # What's in Samulaş API but NOT in our DB?
    missing_in_db = []
    for code, info in samulas_lines.items():
        if code not in asis_lines:
            # Let's also check if it matches up with just names. The API keys sometimes mismatch.
            missing_in_db.append((code, info['name']))
            
    print(f"\n[-] Samulaş Yeni API'de OLAN ama Bizim ASIS DB'de (Lines/OrjLines) OLMAYAN Hatlar: {len(missing_in_db)}")
    for c, n in missing_in_db[:15]:
        print(f"   -> Kod: '{c}' | Ad: '{n}'")
    if len(missing_in_db) > 15: print(f"   ... ve {len(missing_in_db)-15} tane daha.")


    # What's in our ASIS DB but NOT in the new Samulaş API?
    missing_in_samulas = []
    for code, info in asis_lines.items():
        if code not in samulas_lines:
            missing_in_samulas.append((code, info['name'], info['source']))

    print(f"\n[+] Bizim ASIS DB'de OLAN ama Yeni Samulaş API'de OLMAYAN Hatlar: {len(missing_in_samulas)}")
    for c, n, s in missing_in_samulas[:15]:
        print(f"   -> Kod: '{c}' | Kaynak: {s} | Ad: '{n}'")
    if len(missing_in_samulas) > 15: print(f"   ... ve {len(missing_in_samulas)-15} tane daha.")


    print("\n--- Analiz Özeti ---")
    print("Yeni API'de güzergah start/end koordinatları da görüyorum ('first_station', 'last_station').")
    print("Bizim sisteme bu yeni API'yi entegre edip ASIS fallback'i (yedek) yapıp yapmamayı düşünebiliriz.")

if __name__ == "__main__":
    compare()
