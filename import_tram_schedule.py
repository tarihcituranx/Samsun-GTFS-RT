import sqlite3
import datetime

def generate_schedule():
    print("Tramvay Seferleri Oluşturuluyor...")
    
    # Tablo Verisi (Start, End, G_Freq, D_Freq)
    # G_Freq: Yurtlar -> Tekkeköy (Yurtlar Kalkış)
    # D_Freq: Tekkeköy -> Yurtlar (Tekkeköy Kalkış)
    intervals = [
        ("06:15", "07:00", 14, 16),
        ("07:00", "07:30", 14, 16),
        ("07:30", "08:00", 5, 8),
        ("08:00", "09:00", 8, 10),
        ("09:00", "10:00", 7, 12),
        ("10:00", "17:00", 7, 14), # HTML'de 09:00 yaziyordu ama siraya gore 10:00 olmali
        ("17:00", "17:30", 7, 10),
        ("17:30", "18:30", 14, 14),
        ("18:30", "20:00", 14, 14),
        ("20:00", "21:00", 16, 16),
        ("21:00", "23:30", 20, 20),
        ("23:30", "23:45", 15, 15)
    ]

    conn = sqlite3.connect('samsun_v25.db')
    c = conn.cursor()
    
    hat_code = "SAMULAŞ - TRAMVAY"
    
    # 1. Mevcut seferleri temizle
    c.execute("DELETE FROM sefer WHERE hat=?", (hat_code,))
    print(f"Eski seferler temizlendi.")
    
    seferler = []
    
    for start_str, end_str, g_freq, d_freq in intervals:
        start = datetime.datetime.strptime(start_str, "%H:%M")
        end = datetime.datetime.strptime(end_str, "%H:%M")
        
        # Gidiş Seferleri (Yurtlar Kalkış)
        curr = start
        while curr < end:
            saat = curr.strftime("%H:%M")
            seferler.append((hat_code, 'Gidiş', 'Hafta İçi', saat))
            curr += datetime.timedelta(minutes=g_freq)
            
        # Dönüş Seferleri (Tekkeköy Kalkış)
        curr = start
        while curr < end:
            saat = curr.strftime("%H:%M")
            seferler.append((hat_code, 'Dönüş', 'Hafta İçi', saat))
            curr += datetime.timedelta(minutes=d_freq)
            
    # Son sefer (23:45) dahil etmek için (Aralık sonunu kontrol et)
    # Döngü < end olduğu için tam 23:45 eklenmeyebilir. Manuel ekleyelim.
    seferler.append((hat_code, 'Gidiş', 'Hafta İçi', '23:45'))
    seferler.append((hat_code, 'Dönüş', 'Hafta İçi', '23:45'))

    # Veritabanına ekle
    c.executemany("INSERT INTO sefer (hat, yon, gun, saat) VALUES (?, ?, ?, ?)", seferler)
    conn.commit()
    print(f"{len(seferler)} adet sefer eklendi.")
    conn.close()

if __name__ == "__main__":
    generate_schedule()
