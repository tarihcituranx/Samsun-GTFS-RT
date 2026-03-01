"""
Samsun Ekran Projesi - İçerik Toplayıcı
Etkinlikler, Duyurular ve Hava Durumu verilerini çeker.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

# Output file
OUTPUT_FILE = r"c:\Users\mete2\OneDrive\Masaüstü\test\ekran_projesi\content_data.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Meteoroloji Hadise Kodları
HADISE_MAP = {
    "A": "Açık", "AB": "Az Bulutlu", "PB": "Parçalı Bulutlu",
    "CB": "Çok Bulutlu", "K": "Kapalı", "HY": "Hafif Yağmurlu",
    "Y": "Yağmurlu", "KY": "Kuvvetli Yağmurlu", "HK": "Hafif Kar",
    "KK": "Kuvvetli Kar", "F": "Fırtınalı", "SIS": "Sisli",
    "P": "Puslu", "DY": "Dolu Yağışlı", "GSY": "Gök Gürültülü Sağanak"
}


def fetch_weather():
    """Samsun Valiliği API'den hava durumu çek (MGM verisi)"""
    url = "https://www.samsun.gov.tr/ISAYWebPart/ValilikHeader/GetHavaDurumu?cKey=55"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.ok:
            data = r.json()
            if data.get('status'):
                obj = data.get('resultingObject', {})
                temp = obj.get('sicaklik', '?')
                code = obj.get('hadiseDurumu', 'PB')
                desc = HADISE_MAP.get(code, code)
                return {"temp": temp, "desc": desc, "code": code}
    except Exception as e:
        print(f"Hava durumu hatası: {e}")
    return {"temp": "--", "desc": "Bilinmiyor", "code": "?"}


def fetch_events_sbb():
    """Samsun Belediyesi Etkinlikler sayfasından etkinlikleri çek"""
    url = "https://samsun.bel.tr/etkinliklerimiz"
    events = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Her etkinlik kartını bul (sayfadaki yapıya göre)
        # Tipik yapı: Tarih + Başlık + Link içeren kartlar
        # Date parsing: "22 Ocak 2026" formatında
        
        # Link'lerden etkinlik bul
        links = soup.select('a[href*="/haberler/"]')
        seen_titles = set()
        
        for link in links:
            title_tag = link.find(['h3', 'h4', 'h5', 'strong'])
            if not title_tag:
                # Link içinde direkt metin varsa
                text = link.get_text(strip=True)
                if len(text) > 20 and len(text) < 150:
                    title = text
                else:
                    continue
            else:
                title = title_tag.get_text(strip=True)
            
            # Duplicate kontrol
            if title in seen_titles or len(title) < 10:
                continue
            seen_titles.add(title)
            
            # Tarih bul (aynı kart içinde)
            parent = link.find_parent(['div', 'article', 'li'])
            date_text = ""
            if parent:
                # Tarih formatı: "22 Ocak 2026" veya benzeri
                date_match = re.search(r'(\d{1,2})\s*(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s*(\d{4})', 
                                       parent.get_text())
                if date_match:
                    date_text = f"{date_match.group(1)} {date_match.group(2)} {date_match.group(3)}"
            
            events.append({
                "type": "event",
                "source": "SBB",
                "title": title,
                "date": date_text,
                "url": link.get('href', '')
            })
            
            if len(events) >= 10:  # Max 10 etkinlik
                break
                
    except Exception as e:
        print(f"Etkinlik hatası: {e}")
    
    return events


def fetch_announcements_gov():
    """Samsun Valiliği Duyurular sayfasından duyuruları çek"""
    url = "https://www.samsun.gov.tr/duyurular"
    announcements = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Duyuru linkleri
        links = soup.select('a[href*="samsun.gov.tr/"]')
        seen = set()
        
        for link in links:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # Filtrele: duyuru gibi görünen linkler
            if ('duyurular' in href or 
                any(kw in title.lower() for kw in ['duyuru', 'ilan', 'sinav', 'program', 'teknofest', 'yatırım'])):
                
                if title in seen or len(title) < 15 or len(title) > 200:
                    continue
                seen.add(title)
                
                # Bazı gereksiz linkleri atla
                if any(skip in title.lower() for skip in ['resmi gazete', 'portal', 'takip edin', 'tümü', 'filtrele']):
                    continue
                
                # Fix URL: normalize domain
                if href.startswith('http'):
                    final_url = href
                elif href.startswith('/www.'):
                    final_url = f"https:{href}"
                elif href.startswith('/'):
                    final_url = f"https://www.samsun.gov.tr{href}"
                else:
                    final_url = f"https://www.samsun.gov.tr/{href}"
                
                announcements.append({
                    "type": "announcement",
                    "source": "Valilik",
                    "title": title,
                    "url": final_url
                })
                
                if len(announcements) >= 8:
                    break
                    
    except Exception as e:
        print(f"Duyuru hatası: {e}")
    
    return announcements


def main():
    print("=" * 50)
    print("Samsun Ekran Projesi - İçerik Toplayıcı")
    print("=" * 50)
    
    print("\n1. Hava Durumu çekiliyor...")
    weather = fetch_weather()
    print(f"   [OK] {weather['temp']}C - {weather['desc']}")
    
    print("\n2. Etkinlikler çekiliyor (SBB)...")
    events = fetch_events_sbb()
    print(f"   [OK] {len(events)} etkinlik bulundu")
    
    print("\n3. Duyurular çekiliyor (Valilik)...")
    announcements = fetch_announcements_gov()
    print(f"   [OK] {len(announcements)} duyuru bulundu")
    
    # JSON'a kaydet
    data = {
        "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "weather": weather,
        "events": events,
        "announcements": announcements,
        "content_items": events + announcements  # Birleşik liste (carousel için)
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SAVED] {OUTPUT_FILE}")
    print("=" * 50)
    
    # Preview
    print("\n[EVENTS]:")
    for e in events[:3]:
        print(f"   - {e['title'][:50]}... ({e.get('date', '')})")
    
    print("\n[ANNOUNCEMENTS]:")
    for a in announcements[:3]:
        print(f"   - {a['title'][:50]}...")


if __name__ == "__main__":
    main()
