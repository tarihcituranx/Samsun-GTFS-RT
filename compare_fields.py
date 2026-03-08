import json

with open(r'c:\Users\mete2\OneDrive\Masaüstü\test\bbk_ciktilar\bbk_50937281_attempt1.json','r',encoding='utf-8') as f:
    d = json.load(f)
bq = d['bbk_queries']
iss = bq['iss_araclari']
alaz = bq['alaznet_sorgu']

# ISS ALL fields
print('=== ISS FIBER DATA (all keys) ===')
for k,v in iss['result']['fiber']['data'].items():
    print(f'  {k:20s} = {v}')

print()
print('=== ISS VDSL DATA (all keys) ===')
for k,v in iss['result']['vdsl']['data'].items():
    print(f'  {k:20s} = {v}')

print()
print('=== ISS ADSL DATA (all keys) ===')
for k,v in iss['result']['adsl']['data'].items():
    print(f'  {k:20s} = {v}')

print()
print('=== ALAZNET DETAY Veriler ===')
for item in alaz['detay'].get('Veriler',[]):
    if isinstance(item,dict):
        print(f"  {item.get('name','?'):20s} = {item.get('value','?')}")

print()
print('=== ALAZNET DETAY FiberVeriler ===')
for item in alaz['detay'].get('FiberVeriler',[]):
    if isinstance(item,dict):
        print(f"  {item.get('name','?'):20s} = {item.get('value','?')}")

print()
print('=== ALAZNET DETAY VdslVeriler ===')
for item in alaz['detay'].get('VdslVeriler',[]):
    if isinstance(item,dict):
        print(f"  {item.get('name','?'):20s} = {item.get('value','?')}")

print()
print('=== ALAZNET SCALAR FIELDS ===')
det = alaz['detay']
for k in ['SantralAdi','SantralMesafe','AdslDurum','VdslDurum','FiberDurum','BosPort','VdslBosPort','FiberBosPort','AdslMaksimumHiz','VdslMaksimumHiz']:
    print(f'  {k:20s} = {det.get(k)}')

# ISS top-level tech info
print()
print('=== ISS TOP-LEVEL TECH ===')
for tech in ['fiber','vdsl','adsl']:
    t = iss['result'][tech]
    print(f'  {tech}: status={t.get("status")} down={t.get("down_speed")} up={t.get("up_speed")} port={t.get("port")}')

# ISS address
print()
print('=== ISS ADDRESS ===')
addr = iss['result'].get('address',{})
if isinstance(addr, dict):
    for k,v in addr.items():
        print(f'  {k} = {v}')
