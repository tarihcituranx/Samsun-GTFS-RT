from samsun import DB, Http, _tr_lower, _tr_upper_first, title_case_tr
import re

db = DB('samsun_v25.db')
http = Http()

print("ASIS OrjLines çekiliyor...")
orj = http.asis("OrjLines")
if not orj:
    print("ASIS 404/405 döndü veya kapalı.")
    exit(1)

orj_codes = set()
orj_dict = {}
for line in orj:
    code = line.get('lineCode') or line.get('kodu') or ''
    name = line.get('lineName') or line.get('adi') or ''
    code = str(code).strip()
    name = str(name).strip()
    
    # Gereksizleri atla
    if any(k in name.upper() for k in ['GÖREVLİ', 'DENEME', 'TEST', 'OTOPARK', 'KUMBARA', 'SERGİ', 'PERSONEL']):
        continue
    if not code:
        continue
        
    orj_codes.add(code)
    orj_dict[code] = name

print(f"ASIS OrjLines'tan {len(orj_codes)} geçerli hat bulundu.")

db_codes = set()
for r in db.get("SELECT code FROM hat"):
    db_codes.add(r['code'])

missing_in_db = orj_codes - db_codes
missing_in_asis = db_codes - orj_codes

print("\n--- Sistemde (DB) OLMAYAN ASIS Hatları ---")
for code in sorted(missing_in_db):
    print(f"  {code:20s} : {orj_dict[code]}")

print("\n--- ASIS'te OLMAYAN Sistem (DB) Hatları ---")
for code in sorted(missing_in_asis):
    print(f"  {code}")

# İlçe hatları kontrolü
print("\n--- İlçe/Özel Hat Kontrolü (DB) ---")
for r in db.get("SELECT code, name, tip FROM hat WHERE tip IN ('ilce', 'odak') OR code LIKE '%ÇARŞAMBA%' OR name LIKE '%ÇARŞAMBA%'"):
    print(f"  {r['code']:20s} : {r['name']} ({r['tip']})")
