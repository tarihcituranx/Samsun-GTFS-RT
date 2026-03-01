import sqlite3
import os
import shutil
from pathlib import Path

# Paths
SOURCE_DB = '../samsun_v25.db'
TARGET_DB = 'samsun_mobil.db'

print(f"Büyük veritabanı (Sunucu) okunuyor: {SOURCE_DB}")
if os.path.exists(TARGET_DB):
    os.remove(TARGET_DB)

src_conn = sqlite3.connect(SOURCE_DB)
src_conn.row_factory = sqlite3.Row
tgt_conn = sqlite3.connect(TARGET_DB)

print("Mobil uyumlu hafif veritabanı (samsun_mobil.db) oluşturuluyor...")

# 1. Hat Tablosu (Sadece gerekli sütunlar)
tgt_conn.execute('''
    CREATE TABLE hat (
        code TEXT PRIMARY KEY,
        name TEXT,
        tip TEXT,
        gtfs_route_id TEXT,
        gtfs_route_short_name TEXT,
        gtfs_route_long_name TEXT,
        gtfs_route_type TEXT,
        gtfs_route_color TEXT
    )
''')
hat_rows = src_conn.execute("SELECT code, name, tip, gtfs_route_id, gtfs_route_short_name, gtfs_route_long_name, gtfs_route_type, gtfs_route_color FROM hat").fetchall()
tgt_conn.executemany("INSERT INTO hat VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
    [(r['code'], r['name'], r['tip'], r['gtfs_route_id'], r['gtfs_route_short_name'], r['gtfs_route_long_name'], r['gtfs_route_type'], r['gtfs_route_color']) for r in hat_rows])

# 2. Durak Tablosu
tgt_conn.execute('''
    CREATE TABLE durak (
        id TEXT PRIMARY KEY,
        ad TEXT,
        lat REAL,
        lon REAL,
        gtfs_stop_id TEXT,
        gtfs_stop_name TEXT
    )
''')
durak_rows = src_conn.execute("SELECT id, ad, lat, lon, gtfs_stop_id, gtfs_stop_name FROM durak").fetchall()
tgt_conn.executemany("INSERT INTO durak VALUES (?, ?, ?, ?, ?, ?)", 
    [(r['id'], r['ad'], r['lat'], r['lon'], r['gtfs_stop_id'], r['gtfs_stop_name']) for r in durak_rows])

# 3. Hat-Durak İlişkisi (Güzergahlar)
tgt_conn.execute('''
    CREATE TABLE hat_durak (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hat TEXT,
        durak_id TEXT,
        sira INTEGER,
        ad TEXT,
        lat REAL,
        lon REAL
    )
''')
# Index for fast lookup on the phone
tgt_conn.execute("CREATE INDEX idx_hat_durak_hat ON hat_durak(hat)")
hd_rows = src_conn.execute("SELECT hat, durak_id, sira, ad, lat, lon FROM hat_durak").fetchall()
tgt_conn.executemany("INSERT INTO hat_durak (hat, durak_id, sira, ad, lat, lon) VALUES (?, ?, ?, ?, ?, ?)", 
    [(r['hat'], r['durak_id'], r['sira'], r['ad'], r['lat'], r['lon']) for r in hd_rows])

# 4. Fiyat Tablosu
tgt_conn.execute('''
    CREATE TABLE fiyat (
        hat_code TEXT PRIMARY KEY,
        hat_adi TEXT,
        tam_fiyat REAL,
        indirimli_fiyat REAL,
        aktarma1 TEXT
    )
''')
fiyat_rows = src_conn.execute("SELECT hat_code, hat_adi, tam_fiyat, indirimli_fiyat, aktarma1 FROM fiyat").fetchall()
tgt_conn.executemany("INSERT OR IGNORE INTO fiyat VALUES (?, ?, ?, ?, ?)", 
    [(r['hat_code'], r['hat_adi'], r['tam_fiyat'], r['indirimli_fiyat'], r['aktarma1']) for r in fiyat_rows])

# 5. Samair Durak Tablosu (Sabit havalimanı durak ve rotaları)
tgt_conn.execute('''
    CREATE TABLE samair_durak (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hat INTEGER,
        ad TEXT,
        kod TEXT,
        sira INTEGER,
        lat REAL,
        lon REAL,
        fiyat TEXT
    )
''')
sd_rows = src_conn.execute("SELECT hat, ad, kod, sira, lat, lon, fiyat FROM samair_durak").fetchall()
tgt_conn.executemany("INSERT INTO samair_durak (hat, ad, kod, sira, lat, lon, fiyat) VALUES (?, ?, ?, ?, ?, ?, ?)", 
    [(r['hat'], r['ad'], r['kod'], r['sira'], r['lat'], r['lon'], r['fiyat']) for r in sd_rows])

tgt_conn.commit()

# Vacuum database to shrink size for mobile
print("Veritabanı mobil cihazlar için sıkıştırılıyor (VACUUM)...")
tgt_conn.execute("VACUUM")

src_size = os.path.getsize(SOURCE_DB) / (1024*1024)
tgt_size = os.path.getsize(TARGET_DB) / (1024*1024)

print("-" * 50)
print("Islem Tamamlandi!")
print(f"Orijinal DB Boyutu : {src_size:.2f} MB")
print(f"Mobil DB Boyutu   : {tgt_size:.2f} MB")
print(f"Kuculme Orani     : %{100 - (tgt_size/src_size*100):.1f}")
print("-" * 50)

src_conn.close()
tgt_conn.close()
