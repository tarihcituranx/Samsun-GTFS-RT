"""Odak gidis/donus duzeltme"""
import requests
import sqlite3

ASIS = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"

# ASIS'teki dogru eslesme
# G1 SAMSUN - SAHINKAYA = Gidis (TTTM'den baslayip Sahinkaya'ya gider)
# G1 SAHINKAYA - SAMSUN = Donus (Sahinkaya'dan baslayip TTTM'ye doner)

DOĞRU_ESLESTIRME = {
    # YBS ID: {asis_kodu, dogru_isim, doğru_sira}
    1: {'asis': 'G1 ŞAHİNKAYA - SAMSUN', 'isim': 'Şahinkaya Kanyonu Dönüş', 'ters': False},  # Mevcut sıra doğru
    2: {'asis': 'G1 SAMSUN - ŞAHİNKAYA', 'isim': 'Şahinkaya Kanyonu Gidiş', 'ters': False},  # Mevcut sıra doğru
    3: {'asis': 'G2 KIZILIRMAK - SAMSUN', 'isim': 'Kızılırmak Deltası Dönüş', 'ters': False},
    4: {'asis': 'G2 SAMSUN - KIZILIRMAK', 'isim': 'Kızılırmak Deltası Gidiş', 'ters': False},
    5: {'asis': 'G3 AYVACIK - SAMSUN', 'isim': 'Ayvacık Baraj Gölü Dönüş', 'ters': False},
    6: {'asis': 'G3 SAMSUN - AYVACIK', 'isim': 'Ayvacık Baraj Gölü Gidiş', 'ters': False},
    12: {'asis': 'G4 SAMSUN - LADİK AKDAĞ', 'isim': 'Ladik Akdağ Gidiş', 'ters': False},  # Zaten dogru
    13: {'asis': 'G4 LADİK AKDAĞ - SAMSUN', 'isim': 'Ladik Akdağ Dönüş', 'ters': False},
}

conn = sqlite3.connect('samsun_v25.db')
cur = conn.cursor()

print("=== ODAK GIDIS/DONUS DUZELTME ===\n")

# YBS'deki mevcut durumu goster
print("Mevcut durum:")
cur.execute("SELECT id, ad FROM odak WHERE id IN (1,2,3,4,5,6,12,13) ORDER BY id")
for r in cur.fetchall():
    cur.execute("SELECT ad FROM odak_durak WHERE hat=? ORDER BY sira LIMIT 1", (r[0],))
    ilk = cur.fetchone()
    cur.execute("SELECT ad FROM odak_durak WHERE hat=? ORDER BY sira DESC LIMIT 1", (r[0],))
    son = cur.fetchone()
    print(f"  Hat {r[0]}: {r[1]}")
    print(f"        Ilk: {ilk[0] if ilk else '?'} -> Son: {son[0] if son else '?'}")

print("\n" + "="*50)
print("KARAR: Isim degistir (durak sirasi ASIS'ten geliyor, dogru)")
print("="*50 + "\n")

# YBS Hat 1 = Sahinkaya'dan basliyor = aslinda DONUS
# YBS Hat 2 = TTTM'den basliyor = aslinda GIDIS

# Isimleri duzelt
duzeltmeler = [
    (1, "Şahinkaya Kanyonu Dönüş"),  # Sahinkaya -> TTTM = Donus
    (2, "Şahinkaya Kanyonu Gidiş"),  # TTTM -> Sahinkaya = Gidis  
    (3, "Kızılırmak Deltası Dönüş"), # Kizilirmak -> TTTM = Donus
    (4, "Kızılırmak Deltası Gidiş"), # TTTM -> Kizilirmak = Gidis
    (5, "Ayvacık Baraj Gölü Dönüş"), # Ayvacik -> TTTM = Donus
    (6, "Ayvacık Baraj Gölü Gidiş"), # TTTM -> Ayvacik = Gidis
]

for hid, yeni_isim in duzeltmeler:
    cur.execute("SELECT ad FROM odak WHERE id=?", (hid,))
    eski = cur.fetchone()
    if eski:
        print(f"Hat {hid}: '{eski[0]}' -> '{yeni_isim}'")
        cur.execute("UPDATE odak SET ad=? WHERE id=?", (yeni_isim, hid))

conn.commit()

print("\n=== DOGRULAMA ===")
cur.execute("SELECT id, ad FROM odak WHERE id IN (1,2,3,4,5,6,12,13) ORDER BY id")
for r in cur.fetchall():
    cur.execute("SELECT ad FROM odak_durak WHERE hat=? ORDER BY sira LIMIT 1", (r[0],))
    ilk = cur.fetchone()
    cur.execute("SELECT ad FROM odak_durak WHERE hat=? ORDER BY sira DESC LIMIT 1", (r[0],))
    son = cur.fetchone()
    print(f"  Hat {r[0]}: {r[1]}")
    print(f"        {ilk[0] if ilk else '?'} -> {son[0] if son else '?'}")

conn.close()
print("\nTamamlandi!")
