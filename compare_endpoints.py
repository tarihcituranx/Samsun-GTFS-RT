#!/usr/bin/env python3
"""ASIS API Lines vs OrjLines Karşılaştırma"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

ASIS = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"

print("="*70)
print("ASIS API - Lines vs OrjLines KARŞILAŞTIRMASI")
print("="*70)

# İki endpoint'i çek
r1 = requests.get(f"{ASIS}/Lines", timeout=30)
lines = r1.json().get('data', [])
print(f"\n📡 /Lines: {len(lines)} hat")

r2 = requests.get(f"{ASIS}/OrjLines", timeout=30)
orjlines = r2.json().get('data', [])
print(f"📡 /OrjLines: {len(orjlines)} hat")

# Kod setleri
codes_lines = {h.get('lineCode', ''): h for h in lines}
codes_orj = {h.get('lineCode', ''): h for h in orjlines}

# Sadece OrjLines'da olanlar
sadece_orj = [h for code, h in codes_orj.items() if code not in codes_lines]

print(f"\n✨ Sadece OrjLines'da olan: {len(sadece_orj)} hat")
print("="*70)

# Kategorize et
kategoriler = {
    'EKSPRES (E)': [],
    'NUMERİK (15, 20, 22, 25, 28...)': [],
    'TURİSTİK (G)': [],
    'HAVAŞ EK (H5+)': [],
    'OTOPARK': [],
    'DİĞER': []
}

for h in sadece_orj:
    code = h.get('lineCode', '')
    name = h.get('lineName', '')
    
    if code.upper().startswith('E') and any(c.isdigit() for c in code):
        kategoriler['EKSPRES (E)'].append(h)
    elif code.split()[0].isdigit() or code.split('/')[0].isdigit():
        kategoriler['NUMERİK (15, 20, 22, 25, 28...)'].append(h)
    elif code.startswith('G'):
        kategoriler['TURİSTİK (G)'].append(h)
    elif code.startswith('H') and any(c.isdigit() for c in code):
        kategoriler['HAVAŞ EK (H5+)'].append(h)
    elif 'OTOPARK' in code.upper() or 'OTOPARK' in name.upper():
        kategoriler['OTOPARK'].append(h)
    else:
        kategoriler['DİĞER'].append(h)

for kat, liste in kategoriler.items():
    if liste:
        print(f"\n🔹 {kat} ({len(liste)} hat):")
        for h in liste:
            code = h.get('lineCode', '?')
            name = h.get('lineName', '?')
            print(f"   {code:40} | {name}")

# JSON yapısı farkı
print("\n" + "="*70)
print("📋 JSON YAPISININ KARŞILAŞTIRMASI")
print("="*70)

if lines:
    print("\n/Lines örnek kayıt:")
    örnek = lines[0]
    for k, v in örnek.items():
        print(f"   {k}: {v}")

if orjlines:
    print("\n/OrjLines örnek kayıt:")
    örnek = orjlines[0]
    for k, v in örnek.items():
        print(f"   {k}: {v}")

# E serisi detay
print("\n" + "="*70)
print("🚀 EKSPRES HATLARI DETAYI")
print("="*70)
ekspres_orj = [h for h in orjlines if h.get('lineCode','').upper().startswith('E') and any(c.isdigit() for c in h.get('lineCode',''))]
ekspres_lines = [h for h in lines if h.get('lineCode','').upper().startswith('E') and any(c.isdigit() for c in h.get('lineCode',''))]

print(f"\nOrjLines'daki E hatları: {len(ekspres_orj)}")
for h in ekspres_orj:
    print(f"   {h.get('lineCode'):30} | {h.get('lineName','')}")

print(f"\nLines'daki E hatları: {len(ekspres_lines)}")
for h in ekspres_lines:
    print(f"   {h.get('lineCode'):30} | {h.get('lineName','')}")

# Sonuç
print("\n" + "="*70)
print("📊 SONUÇ VE ÖNERİ")
print("="*70)
print(f"""
FARK: OrjLines {len(orjlines) - len(lines)} hat daha fazla içeriyor.

EKSİK OLAN KATEGORİLER:
- Ekspres hatları (E1-E7): {len(kategoriler['EKSPRES (E)'])} hat
- Numerik hatlar (15, 20, 22, 25, 28): {len(kategoriler['NUMERİK (15, 20, 22, 25, 28...)'])} hat  
- Turistik hatlar (G1-G4): {len(kategoriler['TURİSTİK (G)'])} hat
- Ek Havaş hatları (H5): {len(kategoriler['HAVAŞ EK (H5+)'])} hat

💡 ÖNERİ: Ana kodda /Lines yerine /OrjLines kullanılırsa:
   - Ekspres hatları dahil olur
   - Numerik hatlar (28 = R2 değil!) dahil olur
   - Turistik hatlar (G serisi) ASIS'ten de gelir
   - H5 Havza hattı dahil olur
""")

# JSON kaydet
output = {
    'lines_count': len(lines),
    'orjlines_count': len(orjlines),
    'sadece_orjlines': [{'code': h.get('lineCode'), 'name': h.get('lineName')} for h in sadece_orj],
    'kategoriler': {k: [h.get('lineCode') for h in v] for k, v in kategoriler.items()}
}
with open('lines_vs_orjlines.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("💾 Detay: lines_vs_orjlines.json")
