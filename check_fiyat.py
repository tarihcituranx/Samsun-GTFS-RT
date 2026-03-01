#!/usr/bin/env python3
"""Fiyat eşleştirme durumunu kontrol et"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

c = sqlite3.connect('samsun_v25.db')
c.row_factory = sqlite3.Row

print("="*60)
print("FIYAT EŞLEŞTİRME DETAYI")
print("="*60)

# Toplam ve eşleşen
toplam = c.execute("SELECT COUNT(*) FROM fiyat WHERE kaynak='samulas'").fetchone()[0]
eslesen = c.execute("SELECT COUNT(*) FROM fiyat WHERE kaynak='samulas' AND hat_code != ''").fetchone()[0]

print(f"\n✅ Toplam: {toplam}")
print(f"✅ Eşleşen: {eslesen} ({eslesen/toplam*100:.1f}%)")
print(f"❌ Eşleşmeyen: {toplam - eslesen}")

print("\n--- EŞLEŞMEYEN HATLAR ---")
for r in c.execute("SELECT hat_adi, hat_code FROM fiyat WHERE kaynak='samulas' AND hat_code = ''"):
    print(f"  ❌ {r['hat_adi']}")

print("\n--- TÜM EŞLEŞMELER ---")
for r in c.execute("SELECT hat_adi, hat_code FROM fiyat WHERE kaynak='samulas' ORDER BY hat_code"):
    status = "✅" if r['hat_code'] else "❌"
    print(f"  {status} {r['hat_adi']:45} -> {r['hat_code'] or 'EŞLEŞMEDİ'}")
