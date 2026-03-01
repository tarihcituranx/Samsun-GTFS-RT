import sqlite3
import json

def check():
    print("Tramvay Sefer Kontrolü...")
    try:
        conn = sqlite3.connect('samsun_v25.db')
        c = conn.cursor()
        
        hat_adi = "SAMULAŞ - TRAMVAY"
        
        # 1. Sefer Sayısı
        c.execute("SELECT count(*) FROM sefer WHERE hat=?", (hat_adi,))
        sefer_sayisi = c.fetchone()[0]
        print(f"Hat: {hat_adi}")
        print(f"Sefer Sayısı: {sefer_sayisi}")
        
        # 2. Örnek Seferler
        if sefer_sayisi > 0:
            c.execute("SELECT * FROM sefer WHERE hat=? LIMIT 5", (hat_adi,))
            seferler = c.fetchall()
            print("Örnek Seferler:")
            for s in seferler:
                print(s)
        else:
            print("UYARI: Hiç sefer saati bulunamadı!")
            
        conn.close()
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    check()
