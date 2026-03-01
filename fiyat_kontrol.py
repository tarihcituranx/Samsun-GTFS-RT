#!/usr/bin/env python3
"""Fiyat Eşleşme Kontrol Raporu"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('samsun_v25.db')

print("="*60)
print("🔍 SAMSUN ULAŞIM - FİYAT & KAYNAK EŞLEŞTİRME RAPORU")
print("="*60)

# 1. SAMULAS FİYATLARI
print("\n📌 1. SAMULAŞ FİYATLARI (samulas.com.tr)")
print("-"*40)
rows = conn.execute("SELECT hat_adi, tam_fiyat, link FROM fiyat WHERE kaynak='samulas' ORDER BY tam_fiyat DESC").fetchall()
print(f"✅ Toplam {len(rows)} adet fiyat kaydı")
prices = {}
for r in rows:
    prices[r[1]] = prices.get(r[1], 0) + 1
print(f"   Fiyat dağılımı: {dict(sorted(prices.items(), reverse=True))}")

# HAT TABLOSU ile eşleşme kontrolü
print("\n📌 2. SAMULAS → HAT EŞLEŞTİRME ANALİZİ")
print("-"*40)
fiyatlar = conn.execute("SELECT hat_adi, tam_fiyat FROM fiyat WHERE kaynak='samulas'").fetchall()
hatlar = conn.execute("SELECT code, name FROM hat").fetchall()

eslesen = 0
eslesmeyenler = []
for f in fiyatlar:
    f_adi = f[0].upper()
    found = False
    for h in hatlar:
        h_code = h[0].upper()
        h_name = h[1].upper()
        # Eşleştirme: hat kodu veya ismi içerme kontrolü
        if f_adi.split()[0] == h_code.split()[0]:  # İlk kelime (R2, T3 vs) eşleşmesi
            found = True
            break
        if h_code in f_adi or f_adi in h_name:
            found = True
            break
    if found:
        eslesen += 1
    else:
        eslesmeyenler.append(f[0])

print(f"✅ Eşleşen: {eslesen}/{len(fiyatlar)} ({100*eslesen/len(fiyatlar):.1f}%)")
if eslesmeyenler:
    print(f"⚠️ Eşleşmeyen ({len(eslesmeyenler)}): {eslesmeyenler[:5]}...")

# 3. SAMAİR VERİLERİ
print("\n📌 3. SAMAİR (HAVALİMANI SERVİSİ)")
print("-"*40)
samair_hatlar = conn.execute("SELECT * FROM samair").fetchall()
print(f"✅ Kayıtlı hat sayısı: {len(samair_hatlar)}")
for h in samair_hatlar:
    print(f"   H{h[0]}: {h[1]}")

# Samair Durakları
print("\n   Durak Sayıları (Hat bazlı):")
for hid in range(1, 5):
    cnt = conn.execute("SELECT COUNT(*) FROM samair_durak WHERE hat=?", (hid,)).fetchone()[0]
    print(f"   H{hid}: {cnt} durak")

# Samair Seferleri
sefer_cnt = conn.execute("SELECT COUNT(*) FROM samair_sefer").fetchone()[0]
print(f"\n   ✈️ Toplam sefer kaydı: {sefer_cnt}")
for hid in range(1, 5):
    cnt = conn.execute("SELECT COUNT(*) FROM samair_sefer WHERE hat=?", (hid,)).fetchone()[0]
    print(f"   H{hid}: {cnt} sefer")

# 4. ODAK TURİSTİK
print("\n📌 4. ODAK TURİSTİK HATLAR")
print("-"*40)
odak_hatlar = conn.execute("SELECT * FROM odak").fetchall()
print(f"✅ Kayıtlı turistik hat: {len(odak_hatlar)}")
for h in odak_hatlar:
    durak_cnt = conn.execute("SELECT COUNT(*) FROM odak_durak WHERE hat=?", (h[0],)).fetchone()[0]
    # İlk durak fiyatını al
    ilk_durak = conn.execute("SELECT fiyat FROM odak_durak WHERE hat=? ORDER BY sira LIMIT 1", (h[0],)).fetchone()
    fiyat = ilk_durak[0] if ilk_durak else '-'
    print(f"   {h[2]} {h[1]}: {durak_cnt} durak, ₺{fiyat}")

# 5. ÖZET
print("\n" + "="*60)
print("📊 ÖZET RAPOR")
print("="*60)

# Tablolardaki toplam kayıtlar
cnt_hat = conn.execute("SELECT COUNT(*) FROM hat").fetchone()[0]
cnt_durak = conn.execute("SELECT COUNT(*) FROM durak").fetchone()[0]
cnt_fiyat = conn.execute("SELECT COUNT(*) FROM fiyat").fetchone()[0]
cnt_sefer = conn.execute("SELECT COUNT(*) FROM sefer").fetchone()[0]
cnt_samair_durak = conn.execute("SELECT COUNT(*) FROM samair_durak").fetchone()[0]
cnt_samair_sefer = conn.execute("SELECT COUNT(*) FROM samair_sefer").fetchone()[0]
cnt_odak = conn.execute("SELECT COUNT(*) FROM odak").fetchone()[0]
cnt_odak_durak = conn.execute("SELECT COUNT(*) FROM odak_durak").fetchone()[0]

print(f"""
📈 VERİTABANI DURUMU:
   ├─ Hat: {cnt_hat}
   ├─ Durak: {cnt_durak}
   ├─ Sefer: {cnt_sefer}
   ├─ Fiyat: {cnt_fiyat}
   ├─ Samair Hat: {len(samair_hatlar)}
   ├─ Samair Durak: {cnt_samair_durak}
   ├─ Samair Sefer: {cnt_samair_sefer}
   ├─ Odak Hat: {cnt_odak}
   └─ Odak Durak: {cnt_odak_durak}

🔗 EŞLEŞTİRME DURUMU:
   ✅ Samulaş Fiyat → Hat: {eslesen}/{len(fiyatlar)} ({100*eslesen/len(fiyatlar):.1f}%)
   ✅ Samair Hatlar: {len(samair_hatlar)} hat tanımlı
   ✅ Odak Hatlar: {cnt_odak} hat, {cnt_odak_durak} durak

⚠️ SORUNLAR:
""")

issues = []
if eslesen < len(fiyatlar) * 0.9:
    issues.append(f"   - Samulaş fiyatlarının %{100-100*eslesen/len(fiyatlar):.0f}'si eşleşmiyor")
if cnt_samair_sefer == 0:
    issues.append("   - Samair seferleri yüklenememiş (API güncelleme gerekli)")
if cnt_odak_durak == 0:
    issues.append("   - Odak durakları yüklenememiş")

if issues:
    for i in issues:
        print(i)
else:
    print("   ✅ Kritik sorun tespit edilmedi!")

conn.close()
