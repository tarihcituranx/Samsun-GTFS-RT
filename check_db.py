import sqlite3
import json

def check():
    print("Veritabanı kontrol ediliyor...")
    try:
        conn = sqlite3.connect('samsun_v25.db')
        c = conn.cursor()
        
        # 1. Hat var mı?
        print("\n--- TRAMVAY HATTI KONTROLU ---")
        c.execute("SELECT code, name, kat FROM hat WHERE code LIKE ? OR name LIKE ? OR kat='tramvay'", ('%TRAMVAY%', '%TRAMVAY%'))
        hatlar = c.fetchall()
        print(f"Bulunan Hat Sayısı: {len(hatlar)}")
        
        for h in hatlar:
            print(f"Hat: {h}")
            
            # 2. Duraklar var mı?
            c.execute("SELECT count(*) FROM hat_durak WHERE hat=?", (h[0],))
            count = c.fetchone()[0]
            print(f"  -> Durak Sayısı: {count}")
            
            if count > 0:
                c.execute("SELECT * FROM hat_durak WHERE hat=? ORDER BY sira LIMIT 3", (h[0],))
                print(f"  -> İlk 3 Durak: {c.fetchall()}")
            else:
                print("  -> UYARI: Hiç durak yok!")

        # 3. Teleferik ve Tekne Kontrolü
        print("\n--- DIGER ARACLAR ---")
        c.execute("SELECT code, name, kat FROM hat WHERE kat IN ('teleferik', 'tekne')")
        diger = c.fetchall()
        for d in diger:
            print(f"Hat: {d}")
            c.execute("SELECT count(*) FROM hat_durak WHERE hat=?", (d[0],))
            print(f"  -> Durak: {c.fetchone()[0]}")
        
        conn.close()
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    check()
