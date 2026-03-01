"""Odak gidis/donus durak karsilastirma"""
import sqlite3

conn = sqlite3.connect('samsun_v25.db')
cur = conn.cursor()

print("=== ODAK GIDIS/DONUS DURAK KARSILASTIRMA ===\n")

# Hat listesi
cur.execute('SELECT id, kod, ad FROM odak ORDER BY kod, ad')
hatlar = cur.fetchall()

# Gidis/Donus eslestir
gidis_donus = {}
for h in hatlar:
    kod = h[1]  # G1, G2, etc.
    if 'Gidiş' in h[2] or 'GİDİŞ' in h[2].upper():
        if kod not in gidis_donus:
            gidis_donus[kod] = {'gidis': None, 'donus': None}
        gidis_donus[kod]['gidis'] = h
    elif 'Dönüş' in h[2] or 'DÖNÜŞ' in h[2].upper():
        if kod not in gidis_donus:
            gidis_donus[kod] = {'gidis': None, 'donus': None}
        gidis_donus[kod]['donus'] = h
    else:
        # K1, K2, K3 gibi tek yonlu hatlar
        print(f"Tek yonlu: [{h[0]}] {h[1]} - {h[2]}")

print()
for kod, data in sorted(gidis_donus.items()):
    gidis = data['gidis']
    donus = data['donus']
    
    if gidis and donus:
        print(f"\n{'='*60}")
        print(f"HAT: {kod}")
        print(f"{'='*60}")
        print(f"Gidis [{gidis[0]}]: {gidis[2]}")
        print(f"Donus [{donus[0]}]: {donus[2]}")
        
        # Gidis duraklari
        cur.execute('SELECT sira, ad, fiyat FROM odak_durak WHERE hat=? ORDER BY sira', (gidis[0],))
        gidis_duraklar = cur.fetchall()
        
        # Donus duraklari
        cur.execute('SELECT sira, ad, fiyat FROM odak_durak WHERE hat=? ORDER BY sira', (donus[0],))
        donus_duraklar = cur.fetchall()
        
        print(f"\nGIDIS ({len(gidis_duraklar)} durak):")
        for d in gidis_duraklar:
            print(f"  {d[0]}. {d[1]} - {d[2]} TL")
        
        print(f"\nDONUS ({len(donus_duraklar)} durak):")
        for d in donus_duraklar:
            print(f"  {d[0]}. {d[1]} - {d[2]} TL")
        
        # Eslesme kontrolu
        gidis_adlar = [d[1] for d in gidis_duraklar]
        donus_adlar = [d[1] for d in donus_duraklar]
        
        # Ters sira kontrolu
        donus_ters = list(reversed(donus_adlar))
        eslesme = gidis_adlar == donus_ters
        print(f"\nTers sira eslesme: {'EVET' if eslesme else 'HAYIR'}")
        
        if not eslesme:
            print("Farklar:")
            for i, (g, d) in enumerate(zip(gidis_adlar, donus_ters)):
                if g != d:
                    print(f"  {i+1}. Gidis: {g}")
                    print(f"     Donus(ters): {d}")

conn.close()
