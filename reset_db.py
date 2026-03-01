#!/usr/bin/env python3
"""DB'yi temizleyip fiyat eşleştirmeyi test et"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

c = sqlite3.connect('samsun_v25.db')

# Meta sil (güncelleme tetiklensin)
c.execute("DELETE FROM meta WHERE key='son_guncelleme'")
c.execute("DELETE FROM fiyat")
c.commit()

print("Meta ve fiyat temizlendi. Şimdi samsun.py yeniden çalıştırılmalı.")
print("Port 8000 meşgulse, önce python process'ini sonlandırın:")
print("  taskkill /F /IM python.exe")
