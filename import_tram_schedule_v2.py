import sqlite3
import datetime
from bs4 import BeautifulSoup
import re

HTML_FILE = 'tram_schedule.html'
DB_PATH = 'samsun_v25.db'

def parse_time(t_str):
    if not t_str: return None
    t_str = re.sub(r'<[^>]+>', '', t_str).strip()
    try:
        if t_str.count(':') == 2:
            return datetime.datetime.strptime(t_str, "%H:%M:%S").strftime("%H:%M")
        else:
            return datetime.datetime.strptime(t_str, "%H:%M").strftime("%H:%M")
    except:
        return None

def parse_freq(f_str):
    if not f_str: return None
    match = re.search(r'(\d+)', f_str)
    if match: return int(match.group(1))
    return None

def generate_trips(start_str, end_str, freq):
    trips = []
    if not freq: return trips
    
    start = datetime.datetime.strptime(start_str, "%H:%M")
    end = datetime.datetime.strptime(end_str, "%H:%M")
    
    curr = start
    while curr < end:
        trips.append(curr.strftime("%H:%M"))
        curr += datetime.timedelta(minutes=freq)
        
    return trips

def main():
    print(f"{HTML_FILE} okunuyor...")
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    hat_code = "SAMULAŞ - TRAMVAY"
    all_seferler = []
    
    # ID -> DB Gün Adı
    sections = {
        'haftaIci': 'Hafta İçi',
        'cumartesi': 'Cumartesi',
        'pazar': 'Pazar'
    }
    
    for div_id, db_day in sections.items():
        div = soup.find('div', id=div_id)
        if not div:
            print(f"UYARI: #{div_id} bulunamadı.")
            continue
        
        rows = div.find_all('tr')
        print(f"{db_day} için {len(rows)} satır taranıyor...")
        
        valid_rows = 0
        for row in rows:
            cols = row.find_all(['td'])
            
            # Pazar tablosunda th yok, direkt td var, o yüzden header check yapılmalı
            # Header satırlarında "Saat Aralığı" yazar
            row_text = row.get_text()
            if "Saat Aralığı" in row_text or "Yurtlar" in row_text:
                continue
                
            if len(cols) < 3: continue
            
            t1 = cols[0].get_text(strip=True)
            t2 = cols[1].get_text(strip=True)
            t_start = parse_time(t1)
            t_end = parse_time(t2)
            
            if not t_start or not t_end: continue
            
            # Col 2: Yurtlar Frekansı (Gidiş)
            # Pazar tablosu: 0:Start, 1:End, 2:Y-E, 3:E-B, 4:B-T, 5:T-B, 6:B-E, 7:E-Y
            # Hafta içi: Aynı
            # Cumartesi: Aynı
            
            g_freq = parse_freq(cols[2].get_text(strip=True))
            
            d_freq_idx = 5
            if len(cols) > d_freq_idx:
                d_freq = parse_freq(cols[d_freq_idx].get_text(strip=True))
            else:
                d_freq = g_freq
            
            valid_rows += 1
            
            # Gidiş
            for t in generate_trips(t_start, t_end, g_freq):
                all_seferler.append((hat_code, 'Gidiş', db_day, t))
                
            # Dönüş
            for t in generate_trips(t_start, t_end, d_freq):
                all_seferler.append((hat_code, 'Dönüş', db_day, t))
                
        print(f"  -> {valid_rows} geçerli satır işlendi.")

    if not all_seferler:
        print("HATA: Hiç sefer oluşturulamadı!")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sefer WHERE hat=?", (hat_code,))
    print(f"Eski veriler silindi.")
    c.executemany("INSERT INTO sefer (hat, yon, gun, saat) VALUES (?, ?, ?, ?)", all_seferler)
    conn.commit()
    print(f"Toplam {len(all_seferler)} sefer eklendi.")
    conn.close()

if __name__ == "__main__":
    main()
