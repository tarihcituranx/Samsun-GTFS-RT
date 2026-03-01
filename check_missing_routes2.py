from samsun import Database, Http
import json

db = Database()
db.connect()
http = Http()

print("ASIS OrjLines çekiliyor...")
orj = http.asis("OrjLines")
if not orj:
    print("ASIS veri vermedi.")
    exit(1)

orj_codes = set()
orj_dict = {}
for line in orj:
    code = str(line.get('lineCode') or line.get('kodu') or '').strip()
    name = str(line.get('lineName') or line.get('adi') or '').strip()
    
    if any(k in name.upper() for k in ['GÖREVLİ', 'DENEME', 'TEST', 'OTOPARK', 'KUMBARA', 'SERGİ', 'PERSONEL', 'KART']):
        continue
    if not code:
        continue
        
    orj_codes.add(code)
    orj_dict[code] = name

print(f"ASIS OrjLines'tan {len(orj_codes)} geçerli hat bulundu.")

db_codes = set()
for r in db.get("SELECT code, name FROM hat"):
    db_codes.add(r['code'])

missing_in_db = orj_codes - db_codes
missing_in_asis = db_codes - orj_codes

print("\n--- Sistemde (DB) OLMAYAN ASIS Hatları ---")
for code in sorted(missing_in_db):
    print(f"  {code:20s} : {orj_dict[code]}")

print("\n--- Çarşamba / İlçe Hatları Kontrolü (DB) ---")
for r in db.get("SELECT code, name, tip FROM hat WHERE tip IN ('ilce', 'odak') OR code LIKE '%ÇARŞAMBA%' OR name LIKE '%ÇARŞAMBA%'"):
    print(f"  {r['code']:30s} : {r['name']} ({r['tip']})")
    
print("\n--- Çarşamba / İlçe Hatları Kontrolü (ASIS) ---")
for code, name in orj_dict.items():
    if 'ÇARŞAMBA' in name.upper() or 'CARSAMBA' in name.upper() or 'ÇARŞAMBA' in code.upper() or 'CARSAMBA' in code.upper():
        print(f"  {code:30s} : {name}")

db.conn.close()
