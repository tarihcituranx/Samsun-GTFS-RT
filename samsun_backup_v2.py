#!/usr/bin/env python3
"""
🚌 SAMSUN TRANSIT - SUPER APP v25 (MASTER)
- Yol Tarifi Modülü (Konumdan Hedefe Hat Bulma)
- Samulaş Web Fiyat Çekme (samulas.com.tr)
- Samair Canlı Takip ve Uçuş Bilgileri Entegre
- T hatları = Otobüs (Tramvay Değil!)
- Odak Turistik Hatlar Entegrasyonu
"""

import os, sqlite3, time, threading, logging, json, re, math
from datetime import date, datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib.parse
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Log ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

DB = "samsun_v25.db"
ASIS = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
YBS = "https://ybs.samsun.bel.tr/service"
SAMULAS_URL = "https://samulas.com.tr"
GUNCELLEME_GUN = 7

# OrjLines -> Lines hat alias mapping (fiyat eşleştirmesi için)
HAT_ALIAS = {
    # Ekspres hatları (OrjLines'daki isim -> kısa kod)
    'SAMULAŞ EKSPRES 2-DÖNÜŞ': 'E2',
    'SAMULAŞ EKSPRES 2-GİDİŞ': 'E2',
    'SAMULAŞ EKSPRES 7-DÖNÜŞ': 'E7',
    'SAMULAŞ EKSPRES 7-GİDİŞ': 'E7',
    'SAMULAŞ EKSPRES 1-GİDİŞ': 'E1',
    'SAMULAŞ EKSPRES 1-DÖNÜŞ': 'E1',
    'SAMULAŞ EKSPRES 3-GİDİŞ': 'E3',
    'SAMULAŞ EKSPRES 3-DÖNÜŞ': 'E3',
    'SAMULAŞ EKSPRES 4-GİDİŞ': 'E4',
    'SAMULAŞ EKSPRES 4-DÖNÜŞ': 'E4',
    'SAMULAŞ EKSPRES 5-GİDİŞ': 'E5',
    'SAMULAŞ EKSPRES 5-DÖNÜŞ': 'E5',
    'SAMULAŞ EKSPRES 6-GİDİŞ': 'E6',
    'SAMULAŞ EKSPRES 6-DÖNÜŞ': 'E6',
    # Numerik hatlar
    '15/A BÜYÜK CAMİ-SOĞUKSU': '15',
    '15/B SOĞUKSU-BÜYÜK CAMİ': '15',
    '20 BEL.ELERİ-B.KOLPINAR': '20',
    '20 B.KOLPINAR-BEL.EVLERİ': '20',
    '22 SOĞUKSU-TÜRKİŞ': '22',
    '22 TÜRKİŞ-SOĞUKSU': '22',
    '25 OTOGAR-200 EVLER': '25',
    '25 200 EVLER-OTOGAR': '25',
    # R2 = 28 eşleştirmesi
    'R2 CEZAEVİ-BÜYÜK CAMİ': 'R2',
    'R2 BÜYÜK CAMİ-CEZAEVİ': 'R2',
    '28': 'R2',  # 28 = R2 alias
}

# Samulaş fiyat isimleri -> Hat kodu (web scraping eşleştirmesi)
SAMULAS_FIYAT_ESLESTIRME = {
    # E2 hatları
    'E2 SOĞUKSU - BALLICA': 'E2',
    'E2 BALLICA - SOĞUKSU': 'E2',
    # 15 hatları
    '15 SOĞUKSU - İLYASKÖY - BÜYÜK CAMİ': '15',
    '15 BÜYÜK CAMİ - SOĞUKSU': '15',
}

SAMAIR_HATLAR = {
    # Samair Hat ID Mapping (H1-H4 → YBS hatid)
    1: {
        'ad': 'H1 OMÜ - HAVALİMANI',
        'asis': ['H1 OMÜ - HAVALİMANI', 'H1 HAVALİMANI - OMÜ'],
        'ybs_hatid': [3]
    },
    2: {
        'ad': 'H2 TTTM - HAVALİMANI',
        'asis': ['H2 TTTM - HAVALİMANI', 'H2 HAVALİMANI - TTTM'],
        'ybs_hatid': [4]
    },
    3: {
        'ad': 'H3 BAFRA - HAVALİMANI',
        'asis': ['H3 BAFRA - HAVALİMANI', 'H3 HAVALİMANI - BAFRA'],
        'ybs_hatid': [5]
    },
    4: {
        'ad': 'H4 ÇARŞAMBA - HAVALİMANI',
        'asis': ['H4 ÇARŞAMBA - HAVALİMANI', 'H4 HAVALİMANI - ÇARŞAMBA'],
        'ybs_hatid': [9]
    }
}

# --- YARDIMCI FONKSİYONLAR ---

def parse_float(val):
    if not val: return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def clean_price(text):
    """Fiyat metnini sayıya çevirir (17,00 TL -> 17.0)"""
    if not text: return 0.0
    text = str(text).lower().replace('tl', '').replace('₺', '').strip()
    text = text.replace(',', '.')
    try:
        match = re.search(r"\d+(\.\d+)?", text)
        if match: return float(match.group())
        return 0.0
    except: return 0.0

def fix_turkish(text):
    """API'den gelen bozuk Türkçe karakterleri düzelt (Windows-1254 -> UTF-8)"""
    if not text: return text
    text = str(text)
    # Bu karakterler API'de yanlış encoding ile geliyor
    replacements = {
        # Büyük harfler
        '¦': 'İ', '‹': 'İ', 'Ý': 'İ',
        '▄': 'Ü', 
        'Ì': 'Ş', '™': 'Ş', 'Þ': 'Ş',
        'Ã': 'Ç', '˙': 'Ç', 'Æ': 'Ç',
        'º': 'Ğ', '°': 'Ğ', 'Ð': 'Ğ',
        'Í': 'Ö', 'Ô': 'Ö',
        # Küçük harfler
        'ý': 'ı', '²': 'ı', 
        'Ó': 'ö',
        'ã': 'ü',
        'þ': 'ş', '³': 'ş',
        'ð': 'ğ', 'Ï': 'ğ',
        '®': 'ç', 'æ': 'ç',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def haversine(lat1, lon1, lat2, lon2):
    """İki koordinat arası mesafe (metre)"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calculate_eta(dist_m, speed_kmh):
    if dist_m < 50: return 0
    road_dist_km = (dist_m * 1.4) / 1000.0 # Kıvrım payı
    effective_speed = max(speed_kmh, 20.0) # Min ortalama hız
    minutes = int((road_dist_km / effective_speed * 60) * 1.1)
    return minutes if minutes > 0 else 1

def leaflet_indir():
    static = "static"
    if not os.path.exists(static): os.makedirs(static)
    css, js = os.path.join(static, "leaflet.css"), os.path.join(static, "leaflet.js")
    if os.path.exists(css) and os.path.exists(js):
        # Ikon kontrolu
        img_dir = os.path.join(static, "images")
        if not os.path.exists(img_dir): os.makedirs(img_dir)
        icons = ["marker-icon.png", "marker-icon-2x.png", "marker-shadow.png"]
        missing = [i for i in icons if not os.path.exists(os.path.join(img_dir, i))]
        if not missing: return True
    
    log.info("📦 Leaflet dosyaları eksik/kontrol ediliyor...")
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # CSS ve JS
        if not os.path.exists(css):
            r = s.get("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css", timeout=30)
            if r.ok:
                with open(css, 'w', encoding='utf-8') as f: f.write(r.text)
        
        if not os.path.exists(js):
            r = s.get("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", timeout=30)
            if r.ok:
                with open(js, 'w', encoding='utf-8') as f: f.write(r.text)

        # Ikonlar
        img_dir = os.path.join(static, "images")
        if not os.path.exists(img_dir): os.makedirs(img_dir)
        
        base_url = "https://unpkg.com/leaflet@1.9.4/dist/images/"
        for icon in ["marker-icon.png", "marker-icon-2x.png", "marker-shadow.png"]:
            target = os.path.join(img_dir, icon)
            if not os.path.exists(target):
                r = s.get(base_url + icon, timeout=30)
                if r.ok:
                    with open(target, 'wb') as f: f.write(r.content)
        
        return True
    except Exception as e:
        log.error(f"Leaflet indirme hatası: {e}")
        return False

# --- AĞ KATMANI ---

class Http:
    def __init__(self):
        self.s = requests.Session()
        self.s.mount("http://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.3)))
        self.s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://samair.samsun.bel.tr/'
        })
        self._tok = {}

    def asis(self, ep, **p):
        try:
            url = f"{ASIS}/{ep}"
            params = {k: str(v).strip() for k, v in p.items()}
            r = self.s.get(url, params=params, timeout=30)
            if r.ok:
                d = r.json()
                return d.get('data', []) if isinstance(d, dict) else d
        except: pass
        return []

    def ybs_token(self):
        if 'ybs' in self._tok and time.time() - self._tok['ybs']['t'] < 200:
            return self._tok['ybs']['v']
        try:
            r = self.s.get(f"{YBS}/?method=getGuestToken", timeout=10)
            if r.ok:
                tok = r.json().get('token')
                self._tok['ybs'] = {'v': tok, 't': time.time()}
                return tok
        except: pass
        return None

    def ybs(self, method, submethod=None, **kw):
        tok = self.ybs_token()
        if not tok: return []
        p = {'method': method, 'token': tok}
        if submethod: p['submethod'] = submethod
        p.update(kw)
        try:
            r = self.s.get(f"{YBS}/", params=p, timeout=30)
            if r.ok:
                res = r.json()
                if isinstance(res, dict) and res.get('status') == 'SUCCESS':
                    return res.get('data', [])
                return res.get('data', [])
        except: pass
        return []

# --- VERİTABANI ---

class Database:
    def __init__(self):
        self.conn = None
        self._lk = threading.Lock()
        self.durak_coords = {}

    def connect(self):
        yeni = not os.path.exists(DB)
        self.conn = sqlite3.connect(DB, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        if yeni: log.info(f"📀 Yeni DB: {DB}")
        else: log.info(f"📀 Mevcut DB: {DB}")
        self._load_durak_coords()
        self._load_tram_csv_corrections()
        return yeni

    def _load_tram_csv_corrections(self):
        """CSV'den tramvay durak düzeltmelerini yükle (DB'yi bozmadan)"""
        self.tram_corrections = {}
        csv_path = "ulasim.samulas.co.trRaylı Sistem kopyası kopyası- Samsun Hafif Raylı Sistem Hattı.csv"
        if not os.path.exists(csv_path): return
        
        try:
            import csv
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader) # Header
                for row in reader:
                    if len(row) < 2: continue
                    wkt, ad = row[0], row[1]
                    # POINT (36.397356 41.248158) -> Lat: 41.248158, Lon: 36.397356
                    if wkt.startswith("POINT"):
                        parts = wkt.replace("POINT (", "").replace(")", "").split()
                        if len(parts) == 2:
                            lon, lat = float(parts[0]), float(parts[1])
                            # Normalize name: "Örnek Sanayi İstasyonu" -> "Örnek Sanayi"
                            norm_ad = ad.replace(" İstasyonu", "").strip().lower()
                            self.tram_corrections[norm_ad] = (lat, lon)
            log.info(f"   📂 CSV'den {len(self.tram_corrections)} tramvay durağı koordinatı yüklendi.")
        except Exception as e:
            log.error(f"   ❌ CSV okuma hatası: {e}")

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS hat(code TEXT PRIMARY KEY, name TEXT, tip TEXT, kat TEXT, alias TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS durak(id TEXT PRIMARY KEY, kod TEXT, ad TEXT, lat REAL, lon REAL);
            CREATE TABLE IF NOT EXISTS hat_durak(id INTEGER PRIMARY KEY, hat TEXT, durak_id TEXT, ad TEXT, sira INT, lat REAL, lon REAL);
            CREATE TABLE IF NOT EXISTS sefer(id INTEGER PRIMARY KEY, hat TEXT, saat TEXT, yon TEXT, gun TEXT);
            CREATE TABLE IF NOT EXISTS odak(id TEXT PRIMARY KEY, ad TEXT, kod TEXT, gunler TEXT);
            CREATE TABLE IF NOT EXISTS odak_durak(id INTEGER PRIMARY KEY, hat TEXT, ad TEXT, kod TEXT, sira INT, lat REAL, lon REAL, fiyat TEXT, fiyat_ogr TEXT);
            CREATE TABLE IF NOT EXISTS samair(id INTEGER PRIMARY KEY, ad TEXT, kod TEXT);
            CREATE TABLE IF NOT EXISTS samair_durak(id INTEGER PRIMARY KEY, hat INTEGER, ad TEXT, kod TEXT, sira INT, lat REAL, lon REAL, fiyat TEXT);
            CREATE TABLE IF NOT EXISTS samair_sefer(id INTEGER PRIMARY KEY, hat INT, saat TEXT, varis TEXT, firma TEXT, ucak_saat TEXT, tarih TEXT, gun_format TEXT);
            -- Fiyat Tablosu (Samulaş, SamAir, Odak fiyatları)
            CREATE TABLE IF NOT EXISTS fiyat(
                id INTEGER PRIMARY KEY,
                kaynak TEXT,               -- 'samulas', 'samair', 'odak', 'asis'
                hat_adi TEXT,
                hat_code TEXT DEFAULT '',  -- Eşleşen hat kodu
                tam_fiyat REAL DEFAULT 0,
                indirimli_fiyat REAL DEFAULT 0,
                ogrenci_fiyat REAL DEFAULT 0,
                aktarma1 TEXT,
                aktarma2 REAL DEFAULT 0,
                link TEXT,
                guncelleme TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_hd ON hat_durak(hat);
            CREATE INDEX IF NOT EXISTS idx_sf ON sefer(hat);
            CREATE INDEX IF NOT EXISTS idx_sd ON samair_durak(hat);
            CREATE INDEX IF NOT EXISTS idx_dk_latlon ON durak(lat, lon);
            CREATE INDEX IF NOT EXISTS idx_fiyat_kaynak ON fiyat(kaynak);
        """)
        self.conn.commit()

    def _load_durak_coords(self):
        try:
            for r in self.get("SELECT kod, lat, lon FROM durak WHERE kod != ''"):
                if r['kod'] and r['lat'] and r['lon']: self.durak_coords[r['kod']] = (r['lat'], r['lon'])
        except: pass

    def get_meta(self, key):
        r = self.one("SELECT value FROM meta WHERE key=?", (key,))
        return r['value'] if r else None

    def set_meta(self, key, value):
        self.ex("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, value))

    def guncelleme_gerekli(self):
        if self.cnt('hat') == 0: return True
        son = self.get_meta('son_guncelleme')
        if not son: return True
        try: return (datetime.now() - datetime.strptime(son, "%Y-%m-%d")).days >= GUNCELLEME_GUN
        except: return True

    def samair_guncelleme_gerekli(self):
        if self.cnt('samair_sefer') == 0: return True
        son = self.get_meta('samair_last_update')
        if not son: return True
        try: return (datetime.now() - datetime.fromtimestamp(float(son))).total_seconds() > 3600
        except: return True

    def temizle(self):
        for t in ['hat', 'durak', 'hat_durak', 'sefer', 'odak', 'odak_durak', 'samair', 'samair_durak', 'samair_sefer']:
            self.ex(f"DELETE FROM {t}")
        log.info("   🗑️ Veritabanı temizlendi")

    def guncelleme_tamamlandi(self): self.set_meta('son_guncelleme', datetime.now().strftime("%Y-%m-%d"))
    def ex(self, q, p=()):
        with self._lk: self.conn.execute(q, p); self.conn.commit()
    def exm(self, q, d):
        with self._lk: self.conn.executemany(q, d); self.conn.commit()
    def get(self, q, p=()):
        with self._lk: return [dict(r) for r in self.conn.execute(q, p).fetchall()]
    def one(self, q, p=()):
        with self._lk:
            r = self.conn.execute(q, p).fetchone()
            return dict(r) if r else None
    def cnt(self, t):
        try: return self.one(f"SELECT COUNT(*) c FROM {t}")['c']
        except: return 0

# --- VERİ TOPLAYICI (COLLECTOR) ---

class Collector:
    def __init__(self, db, http):
        self.db = db
        self.http = http

    def kat(self, code, name):
        """Hat kategorisini belirle - T hatları OTOBÜS (tramvay değil!)"""
        c, n = code.upper(), name.upper()
        
        # 1. Ring hatları (En yüksek öncelik - R ile başlayanlar kesinlikle Ring'dir)
        if c.startswith('R') and len(c) > 1 and c[1].isdigit(): return 'ring'
        
        # 2. Yeni Kategoriler (Analiz Sonucu)
        if 'TRAMVAY' in c or 'TRAMVAY' in n: return 'tramvay'
        if 'TELEFERİK' in c or 'TELEFERİK' in n: return 'teleferik'
        if any(x in c or x in n for x in ['GEMİ', 'VAPUR', 'FERİBOT', 'TEKNE']): return 'tekne'
        
        # Havalimanı hatları
        if c.startswith('H') and len(c) > 1 and c[1].isdigit(): return 'havalimani'
        
        # Ekspres hatları
        if 'EKSPRES' in c or (c.startswith('E') and len(c) > 1 and c[1].isdigit()): return 'ekspres'
        # İlçe hatları
        if any(x in n for x in ['TERME','ÇARŞAMBA','BAFRA','HAVZA','LADİK','KAVAK','ASARCIK','SALIPAZARI','TEKKEKÖY']): return 'ilce'
        
        return 'otobus'

    def veri_cek(self):
        if not self.db.guncelleme_gerekli():
            log.info("📦 Ana veriler güncel.")
            self._inject_fixed_prices()
            self._fix_tram_schedules()
            self._fix_stop_coordinates()
            self._inject_boat_teleferik_schedules()
            return
        log.info("📥 Ana Güncelleme Başladı...")
        self.db.temizle()
        self._hatlar()
        self._duraklar()
        self._hat_duraklari()
        self._seferler()
        self._odak()
        self._samair_duraklar()
        self._samulas_fiyatlar()  # Samulaş web scraping
        self._inject_fixed_prices() # Sabit fiyatlar (Tramvay max, Teleferik vb.)
        self._fix_tram_schedules() # Tramvay seferlerini HTML'den düzelt
        self._fix_stop_coordinates() # Hatalı durak koordinatlarını düzelt
        self._inject_boat_teleferik_schedules() # Tekne ve Teleferik seferlerini ekle
        self.db.guncelleme_tamamlandi()
        self._ozet()

    def _ozet(self):
        log.info(f"   📊 Hat:{self.db.cnt('hat')} | Durak:{self.db.cnt('durak')} | Fiyat:{self.db.cnt('fiyat')}")

    def _samulas_fiyatlar(self):
        """Samulaş web sitesinden otobüs fiyatlarını çek ve hat eşleştirmesi yap"""
        log.info("   📥 Samulaş Fiyatları (Web Scraping)...")
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            log.info("      ⚠️ BeautifulSoup yüklü değil. Fiyatlar çekilemiyor.")
            return
        
        self.db.ex("DELETE FROM fiyat WHERE kaynak='samulas'")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        toplam = 0
        eslesen = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Hat tablosunu cache'le (eşleştirme için)
        hatlar = self.db.get("SELECT code, name, alias FROM hat")
        hat_codes = {h['code'].upper(): h['code'] for h in hatlar}
        hat_names = {h['name'].upper(): h['code'] for h in hatlar}
        hat_aliases = {h['alias'].upper(): h['code'] for h in hatlar if h['alias']}
        
        # 8 sayfa tara (samulas.com.tr/otobusler)
        for page in range(1, 9):
            try:
                res = requests.get(f"{SAMULAS_URL}/otobusler?page={page}", headers=headers, timeout=15)
                soup = BeautifulSoup(res.content, 'html.parser')
                
                # Otobüs detay linklerini bul
                links = []
                for a in soup.find_all('a', href=True):
                    if 'otobus-detay' in a['href']:
                        full_url = a['href'] if a['href'].startswith('http') else SAMULAS_URL + (a['href'] if a['href'].startswith('/') else '/' + a['href'])
                        if full_url not in links:
                            links.append(full_url)
                
                # Her otobüs detayına gir
                for url in links:
                    try:
                        r = requests.get(url, headers=headers, timeout=10)
                        s = BeautifulSoup(r.content, 'html.parser')
                        
                        # Hat adını al
                        name = "Bilinmiyor"
                        title_div = s.find('div', class_='section-title')
                        if title_div and title_div.find('h2'):
                            name = " ".join(title_div.find('h2').get_text(strip=True).split())
                        
                        # Fiyatı bul
                        cols = s.find_all('div', class_='col-6 p-2')
                        tam_fiyat = 0.0
                        for idx, col in enumerate(cols):
                            text = col.get_text(strip=True).lower()
                            if "tam" in text and "öğrenci" not in text and "abonman" not in text:
                                if idx + 1 < len(cols):
                                    tam_fiyat = clean_price(cols[idx+1].get_text(strip=True))
                                    break
                        
                        # İndirimli fiyat hesapla
                        indirimli, aktarma1, aktarma2 = 0, "Ücretsiz", 0
                        if tam_fiyat == 23.50:
                            indirimli, aktarma2 = 15.00, 6.50
                        elif tam_fiyat == 17.00:
                            indirimli, aktarma2 = 12.00, 6.50
                        
                        # Hat kodu eşleştir
                        hat_code = ''
                        name_upper = name.upper()
                        
                        # 0. SAMULAS_FIYAT_ESLESTIRME'de direkt eşleşme (özel durumlar)
                        if name in SAMULAS_FIYAT_ESLESTIRME:
                            hat_code = SAMULAS_FIYAT_ESLESTIRME[name]
                        # 1. İlk kelimeyi (hat kodu) kontrol et: "R2 XXX" -> "R2"
                        elif name.split():
                            ilk_kelime = name.split()[0].upper()
                            if ilk_kelime in hat_codes:
                                hat_code = hat_codes[ilk_kelime]
                            # 2. Tam isim eşleşmesi
                            elif name_upper in hat_names:
                                hat_code = hat_names[name_upper]
                            # 3. Alias eşleşmesi (E7, 28 -> R2 gibi)
                            elif ilk_kelime in hat_aliases:
                                hat_code = hat_aliases[ilk_kelime]
                            # 4. İsimden hat kodu çıkar (ilk 2-3 karakter)
                            else:
                                for code_up, code_orig in hat_codes.items():
                                    if name_upper.startswith(code_up) or code_up in name_upper:
                                        hat_code = code_orig
                                        break
                        
                        if hat_code:
                            eslesen += 1
                        
                        if name and tam_fiyat > 0:
                            self.db.ex("INSERT INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,aktarma1,aktarma2,link,guncelleme) VALUES(?,?,?,?,?,?,?,?,?)",
                                      ('samulas', name, hat_code, tam_fiyat, indirimli, aktarma1, aktarma2, url, now))
                            toplam += 1
                        time.sleep(0.1)
                    except: pass
            except: pass
        
        eslesen_oran = (eslesen / toplam * 100) if toplam > 0 else 0
        log.info(f"      ✅ {toplam} Samulaş fiyatı çekildi, {eslesen} eşleşti ({eslesen_oran:.0f}%)")

    def _hatlar(self):
        """Hatları çek - hem Lines hem OrjLines'tan, alias ile eşleştir"""
        log.info("   📥 Hatlar (Lines + OrjLines)...")
        
        # 1. Lines'tan ana hatları çek
        data_lines = self.http.asis('Lines')
        seen_codes = set()
        rows = []
        
        for d in data_lines:
            c = fix_turkish(str(d.get('lineCode','')).strip())
            name = fix_turkish(d.get('lineName', c))
            if c and c not in seen_codes:
                seen_codes.add(c)
                rows.append((c, name, d.get('tip','gidis'), self.kat(c, name), ''))
        
        log.info(f"      ✅ Lines: {len(rows)} hat")
        
        # 2. OrjLines'tan eksik hatları çek
        data_orj = self.http.asis('OrjLines')
        orj_count = 0
        
        for d in data_orj:
            c = fix_turkish(str(d.get('lineCode','')).strip())
            name = fix_turkish(d.get('lineName', c))
            
            if not c:
                continue
                
            # Alias kontrolü - OrjLines ismi HAT_ALIAS'ta varsa kısa koda çevir
            alias_code = HAT_ALIAS.get(c.upper(), '')
            
            # Otopark, gemi gibi şeyleri atla
            # Otopark, gemi gibi şeyleri atla (Artık Gemi ve Teleferik serbest)
            skip_keywords = ['OTOPARK', 'KENT MÜZESİ', 'GÖREVLİ', 'BAŞVURU', 'İADE', 'IADE', 'SAMULAŞ - AKTARMA', 'BANDIRMA VAPURU', 'AMAZON KÖYÜ']
            if any(kw in c.upper() or kw in name.upper() for kw in skip_keywords):
                continue
            
            if c not in seen_codes:
                seen_codes.add(c)
                rows.append((c, name, d.get('tip','gidis'), self.kat(c, name), alias_code))
                orj_count += 1
        
        log.info(f"      ✅ OrjLines ek: {orj_count} hat")
        
        if rows:
            self.db.exm("INSERT OR REPLACE INTO hat(code, name, tip, kat, alias) VALUES(?,?,?,?,?)", rows)
        log.info(f"      ✅ Toplam: {len(rows)} hat yüklendi")

    def _duraklar(self):
        log.info("   📥 Duraklar...")
        data = self.http.asis('StopsStations')
        rows, seen = [], set()
        for d in data:
            sid = str(d.get('stopId', '')).strip()
            if sid and sid not in seen:
                seen.add(sid)
                lat, lon = parse_float(d.get('latitude')), parse_float(d.get('longitude'))
                ad = fix_turkish(d.get('stopName', ''))
                m = re.match(r'^(\d+)', ad)
                kod = m.group(1) if m else ''
                if 40 < lat < 43 and 34 < lon < 38:
                    rows.append((sid, kod, ad, lat, lon))
                    if kod: self.db.durak_coords[kod] = (lat, lon)
        if rows: self.db.exm("INSERT OR REPLACE INTO durak VALUES(?,?,?,?,?)", rows)
        log.info(f"      ✅ {len(rows)} durak yüklendi")

    def _hat_duraklari(self):
        log.info("   📥 Güzergahlar...")
        hatlar = self.db.get("SELECT code FROM hat")
        for i, h in enumerate(hatlar):
            code = h['code']
            data = self.http.asis('StopsStations', lineCode=code)
            if data:
                rows = []
                for d in data:
                    lat, lon = parse_float(d.get('latitude')), parse_float(d.get('longitude'))
                    if 40 < lat < 43 and 34 < lon < 38:
                        ad = fix_turkish(d.get('stopName', ''))
                        rows.append((code, d.get('stopId', ''), ad, int(d.get('orderId', 0)), lat, lon))
                if rows: self.db.exm("INSERT INTO hat_durak(hat,durak_id,ad,sira,lat,lon) VALUES(?,?,?,?,?,?)", rows)
            if (i+1)%20==0: log.info(f"      {i+1}/{len(hatlar)}...")
            time.sleep(0.02)

    def _seferler(self):
        log.info("   📥 Seferler...")
        hatlar = self.db.get("SELECT code FROM hat")
        today = date.today()
        hi = today + timedelta(days=(7 - today.weekday()) if today.weekday() >= 5 else 0)
        hs = today + timedelta(days=(5 - today.weekday()) if today.weekday() != 5 else 0)
        for i, h in enumerate(hatlar):
            code = h['code']
            for gun, t in [('hi', hi), ('hs', hs)]:
                for d in self.http.asis('Schedules', lineCode=code, scheduleDate=t.strftime("%Y-%m-%d")):
                    saat = d.get('time', d.get('saat', ''))
                    if saat: self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (code, saat, d.get('yon', ''), gun))
            if (i+1)%20==0: log.info(f"      {i+1}/{len(hatlar)}...")
            time.sleep(0.02)

    def _fix_stop_coordinates(self):
        """Hatalı durak koordinatlarını düzelt - DEVRE DIŞI (CSV kullanılıyor)"""
        return
        # Eski kodlar iptal...
        # updates = { ... }
        # for durak, (lat, lon) in updates.items(): ... - Tekkeköy'den önce gelmeli
        # API: 36.466 (Tekkeköy 36.452'nin doğusunda - YANLIŞ)
        # Düzeltme: 36.446 civarı olmalı
        log.info("   🛠️ Hatalı durak koordinatları düzeltildi.")

    def _inject_boat_teleferik_schedules(self):
        """Tekne, Feribot ve Teleferik Seferlerini Ekle"""
        # 1. Samsunum-1 (Samsun Liman)
        hati = self.db.get("SELECT code FROM hat WHERE name LIKE '%SAMSUNUM1%'")
        if hati:
            code = hati[0]['code']
            self.db.ex("DELETE FROM sefer WHERE hat=?", (code,))
            self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (code, '15:00', 'Ring', 'Hafta Sonu'))
            
        # 2. Samsunum-2 (Ayvacık) - Çalışmıyor
        hati = self.db.get("SELECT code FROM hat WHERE name LIKE '%SAMSUNUM2%'")
        if hati:
            code = hati[0]['code']
            self.db.ex("DELETE FROM sefer WHERE hat=?", (code,))
            self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (code, 'ÇALIŞMAMAKTADIR', 'DSİ Çalışması', 'Her Gün'))

        # 3. Samsunum-3 (Vezirköprü) - Doluluğa göre
        hati = self.db.get("SELECT code FROM hat WHERE name LIKE '%SAMSUNUM3%'")
        if hati:
            code = hati[0]['code']
            self.db.ex("DELETE FROM sefer WHERE hat=?", (code,))
            self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (code, 'Doldukça Kalkar', 'Ring', 'Her Gün'))

        # 4. Altınkaya 55 Feribot
        hati = self.db.get("SELECT code FROM hat WHERE name LIKE '%ALTINKAYA%'")
        if hati:
            code = hati[0]['code']
            self.db.ex("DELETE FROM sefer WHERE hat=?", (code,))
            # Kayıkbaşı Kalkış
            for t in ["06:30", "08:00", "09:30", "14:00", "17:30", "19:30"]:
                self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (code, t, 'Kayıkbaşı > Kuruçay', 'Her Gün'))
            # Kuruçay Kalkış
            for t in ["07:30", "08:30", "11:00", "15:30", "18:30", "20:30"]:
                self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (code, t, 'Kuruçay > Kayıkbaşı', 'Her Gün'))

        # 5. Teleferik
        # 10:30 - 22:00
        hati = self.db.get("SELECT code FROM hat WHERE name LIKE '%TELEFERİK%'")
        if hati:
            code = hati[0]['code']
            self.db.ex("DELETE FROM sefer WHERE hat=?", (code,))
            self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (code, '10:30 - 22:00', 'Sürekli', 'Her Gün'))

        log.info("   🚢 Tekne ve Teleferik seferleri eklendi.")

    def _odak(self):
        """Odak Turistik Hatları - HatlarAllList ile tüm hatları çeker (Ladik, Şahinkaya dahil)"""
        log.info("   📥 Odak Turistik Hatlar...")
        # x.py'deki gibi HatlarAllList kullan (daha fazla hat getirir)
        hatlar = self.http.ybs('odakSamsun_Crud', 'HatlarAllList', referer='https://odak.samsun.bel.tr/')
        if not hatlar:
            # Fallback: eski endpoint
            hatlar = self.http.ybs('odakSamsun_Crud', 'HatlarList', referer='https://odak.samsun.bel.tr/')
        if not hatlar:
            log.info("      ⚠️ Odak hatları çekilemedi")
            return
        
        # YBS API'den gelen Gidiş/Dönüş isimleri ters olabiliyor
        # İlk durak TTTM ise Gidiş, değilse Dönüş
        # Bu mapping ile düzeltiyoruz (API tutarsızlığı)
        ODAK_ISIM_DUZELTME = {
            '1': 'Dönüş',  # Şahinkaya -> TTTM (API'de Gidiş yazıyor)
            '2': 'Gidiş',  # TTTM -> Şahinkaya (API'de Dönüş yazıyor)
            '3': 'Dönüş',  # Kızılırmak -> TTTM
            '4': 'Gidiş',  # TTTM -> Kızılırmak
            '5': 'Dönüş',  # Ayvacık -> TTTM
            '6': 'Gidiş',  # TTTM -> Ayvacık
        }
        
        log.info(f"      📍 {len(hatlar)} turistik hat bulundu")
        for h in hatlar:
            hid = str(h.get('id', ''))
            hat_adi = h.get('hat_adi', '')
            
            # Gidiş/Dönüş isim düzeltmesi (API tutarsızlığı)
            if hid in ODAK_ISIM_DUZELTME:
                dogru_yon = ODAK_ISIM_DUZELTME[hid]
                if 'Gidiş' in hat_adi or 'Dönüş' in hat_adi:
                    hat_adi = hat_adi.replace('Gidiş', 'TEMP').replace('Dönüş', 'TEMP')
                    hat_adi = hat_adi.replace('TEMP', dogru_yon)
            
            self.db.ex("INSERT OR REPLACE INTO odak VALUES(?,?,?,?)", (hid, hat_adi, h.get('hat_aciklama', ''), h.get('hat_gunleri', '')))
            duraklar = self.http.ybs('odakSamsun_Crud', 'GetHatDuraklar', referer='https://odak.samsun.bel.tr/', id=hid)
            for i, d in enumerate(duraklar, 1):
                dk, lat, lon = d.get('durak_kodu', ''), 0, 0
                if dk in self.db.durak_coords: lat, lon = self.db.durak_coords[dk]
                # Fiyatları clean_price ile temizle
                fiyat = clean_price(d.get('durak_fiyat', ''))
                fiyat_ogr = clean_price(d.get('durak_fiyat_ogr', ''))
                self.db.ex("INSERT INTO odak_durak(hat,ad,kod,sira,lat,lon,fiyat,fiyat_ogr) VALUES(?,?,?,?,?,?,?,?)",
                          (hid, d.get('durak_adi', ''), dk, i, lat, lon, fiyat, fiyat_ogr))

    def _fix_tram_schedules(self):
        """Tramvay seferlerini (tram_schedule.html) dosyasından okuyup düzelt"""
        log.info("   🛠️ Tramvay Seferleri Düzeltiliyor (HTML'den)...")
        html_file = 'tram_schedule.html'
        if not os.path.exists(html_file):
            log.info(f"      ⚠️ {html_file} bulunamadı, atlanıyor.")
            return

        try:
            from bs4 import BeautifulSoup
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            hat_code = "SAMULAŞ - TRAMVAY"
            self.db.ex("DELETE FROM sefer WHERE hat=?", (hat_code,))
            
            count = 0
            
            def parse_time(t_str):
                import re
                t_str = re.sub(r'<[^>]+>', '', str(t_str)).strip()
                try:
                    if t_str.count(':') == 2: return datetime.strptime(t_str, "%H:%M:%S").strftime("%H:%M")
                    return datetime.strptime(t_str, "%H:%M").strftime("%H:%M")
                except: return None
            
            def parse_freq(f_str):
                import re
                match = re.search(r'(\d+)', str(f_str))
                return int(match.group(1)) if match else None

            sections = {'haftaIci': 'Hafta İçi', 'cumartesi': 'Cumartesi', 'pazar': 'Pazar'}
            
            for div_id, db_day in sections.items():
                div = soup.find('div', id=div_id)
                if not div: continue
                
                rows = div.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 3: continue
                    t1, t2 = cols[0].get_text(strip=True), cols[1].get_text(strip=True)
                    if "Saat" in t1 or "Yurtlar" in t1: continue
                    
                    start, end = parse_time(t1), parse_time(t2)
                    if not start or not end: continue
                    
                    g_freq = parse_freq(cols[2].get_text(strip=True))
                    d_freq = parse_freq(cols[5].get_text(strip=True)) if len(cols) > 5 else g_freq
                    
                    # Generate
                    s = datetime.strptime(start, "%H:%M")
                    e = datetime.strptime(end, "%H:%M")
                    
                    # Gidiş
                    curr = s
                    while curr < e:
                        self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (hat_code, curr.strftime("%H:%M"), 'Gidiş', db_day))
                        curr += timedelta(minutes=g_freq)
                        count += 1
                        
                    # Dönüş
                    curr = s
                    while curr < e:
                        self.db.ex("INSERT INTO sefer(hat,saat,yon,gun) VALUES(?,?,?,?)", (hat_code, curr.strftime("%H:%M"), 'Dönüş', db_day))
                        curr += timedelta(minutes=d_freq)
                        count += 1
            
            log.info(f"      ✅ {count} tramvay seferi eklendi.")
        except Exception as e:
            log.error(f"      ❌ Tramvay düzeltme hatası: {e}")

    def _inject_fixed_prices(self):
        """Sabit fiyatları tabloya ekle (User input)"""
        log.info("   💰 Sabit Fiyatlar Ekleniyor...")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 1. Tramvay (Maksimum ücret)
        self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?)",
                  ('fixed', 'Tramvay', 'SAMULAŞ - TRAMVAY', 26.50, 16.50, 'Ücretsiz', now))
        
        # 2. Teleferik
        self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?)",
                  ('fixed', 'Teleferik', 'TELEFERİK', 25.00, 15.00, 'Yok', now))
        
        # 3. Ringler (R hatları)
        ringler = self.db.get("SELECT code, name FROM hat WHERE code LIKE 'R%' OR name LIKE 'RING%'")
        for r in ringler:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?)",
                  ('fixed', r['name'], r['code'], 17.00, 12.00, '6.50 TL', now))
             
        # 4. Ekspresler
        ekspres = self.db.get("SELECT code, name FROM hat WHERE code LIKE 'E%' OR name LIKE 'E%'")
        for e in ekspres:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?)",
                  ('fixed', e['name'], e['code'], 23.50, 15.00, 'Ücretsiz', now))

        # 5. Tekneler (Samsunum)
        tekneler = self.db.get("SELECT code, name FROM hat WHERE name LIKE '%SAMSUNUM%' OR name LIKE '%GEMİ%'")
        for t in tekneler:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?)",
                  ('fixed', t['name'], t['code'], 200.00, 150.00, 'Yok', now))

        # 6. Altınkaya Feribot
        feribot = self.db.get("SELECT code, name FROM hat WHERE name LIKE '%ALTINKAYA%' OR name LIKE '%FERİBOT%'")
        for f in feribot:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?)",
                  ('fixed', f['name'], f['code'], 15.00, 7.00, 'Yok', now))
        
        log.info("      ✅ Fiyatlar güncellendi.")


    def _samair_duraklar(self):
        """Samair durakları - Önce YBS API, sonra ASIS fallback"""
        log.info("   📥 Samair Durakları...")
        self.db.ex("DELETE FROM samair_durak")
        
        # YBS API ile dene (x.py'deki gibi - samair_duraklar_public)
        try:
            ybs_duraklar = self.http.ybs('samair_duraklar_public', 'DuraklarList')
            if ybs_duraklar:
                log.info(f"      ✅ YBS'den {len(ybs_duraklar)} Samair durağı çekildi")
                # YBS durakları genel, hat bazlı değil - bunları kaydet
                for i, d in enumerate(ybs_duraklar, 1):
                    lat, lon = parse_float(d.get('lat', d.get('latitude', 0))), parse_float(d.get('lon', d.get('longitude', 0)))
                    fiyat = clean_price(d.get('durak_fiyat', d.get('fiyat', '')))
                    self.db.ex("INSERT INTO samair_durak(hat,ad,kod,sira,lat,lon,fiyat) VALUES(?,?,?,?,?,?,?)",
                              (0, d.get('durak_adi', ''), d.get('durak_kodu', ''), i, lat, lon, fiyat))
        except Exception as e:
            log.info(f"      ⚠️ YBS Samair API hatası: {e}")
        
        # Her hat için ASIS üzerinden güzergah çek
        for hid, hat_info in SAMAIR_HATLAR.items():
            ana_ad = hat_info['ad']
            self.db.ex("INSERT OR REPLACE INTO samair VALUES(?,?,?)", (hid, ana_ad, ana_ad))
            
            toplam_durak = []
            for tam_ad in hat_info['asis']:
                duraklar = self.http.asis('StopsStations', lineCode=tam_ad)
                if duraklar:
                    for d in duraklar:
                        lat = parse_float(d.get('latitude'))
                        lon = parse_float(d.get('longitude'))
                        if 40 < lat < 43 and 34 < lon < 38:
                            durak_tuple = (d.get('stopName', ''), lat, lon)
                            if durak_tuple not in [(td['ad'], td['lat'], td['lon']) for td in toplam_durak]:
                                toplam_durak.append({
                                    'ad': d.get('stopName', ''),
                                    'kod': d.get('stopId', ''),
                                    'sira': int(d.get('orderId', 0)),
                                    'lat': lat,
                                    'lon': lon
                                })
            
            toplam_durak.sort(key=lambda x: x['sira'])
            for idx, d in enumerate(toplam_durak, 1):
                self.db.ex("INSERT INTO samair_durak(hat,ad,kod,sira,lat,lon,fiyat) VALUES(?,?,?,?,?,?,?)",
                          (hid, d['ad'], d['kod'], idx, d['lat'], d['lon'], ''))
            
            log.info(f"      ✈️ H{hid} ({ana_ad}): {len(toplam_durak)} durak")

    def samair_seferler_guncelle(self, force=False):
        if not force and not self.db.samair_guncelleme_gerekli(): return
        log.info("   ✈️ Samair Seferleri Güncelleniyor...")
        toplam = 0
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Her UI hattı için YBS'deki karşılık gelen hatid'leri kullan
        for ui_hatid, hat_info in SAMAIR_HATLAR.items():
            for ybs_hatid in hat_info['ybs_hatid']:
                seferler = self.http.ybs('samair_ucaksefersaatleri_public', 'HatlarList', hatid=ybs_hatid)
                if seferler:
                    for sf in seferler:
                        api_id = int(sf.get('id', 0))
                        if api_id == 0: continue
                        s, v = sf.get('saat', '') or '', sf.get('varis_saati', '') or ''
                        
                        # Tarih formatını düzenle
                        tarih = sf.get('tarih', '')
                        gun_format = sf.get('formatted_date', '')
                        
                        self.db.ex("INSERT OR REPLACE INTO samair_sefer(id,hat,saat,varis,firma,ucak_saat,tarih,gun_format) VALUES(?,?,?,?,?,?,?,?)",
                                  (api_id, ui_hatid, s[:5], v[:5], sf.get('ucak_firmasi', ''), sf.get('ucak_saatleri', ''), tarih, gun_format))
                        toplam += 1
        
        if toplam > 0:
            self.db.set_meta('samair_last_update', str(time.time()))
            self.db.set_meta('samair_last_update_str', now_str)
            log.info(f"      ✅ {toplam} uçuş bilgisi güncellendi.")

    def canli(self, code):
        data = self.http.asis('RealTimeData', lineCode=code)
        result = []
        for d in data:
            try:
                lat, lon = parse_float(d.get('enlem')), parse_float(d.get('boylam'))
                if 40 < lat < 43 and 34 < lon < 38:
                    result.append({'plaka': d.get('plaka', '?'), 'lat': lat, 'lon': lon, 'hiz': int(float(d.get('hiz', 0))), 'yon': float(d.get('yon', 0)), 'yolcu': int(d.get('seferYolcu', 0))})
            except: pass
        return result

    def yakin_durak(self, arac, duraklar):
        if not duraklar: return ""
        min_d, yakin = 999999, ""
        for d in duraklar:
            if d.get('lat') and d.get('lon'):
                dx, dy = (arac['lat'] - d['lat']) * 111000, (arac['lon'] - d['lon']) * 85000
                dist = (dx*dx + dy*dy) ** 0.5
                if dist < min_d: min_d, yakin = dist, d.get('ad', '')
        return yakin if min_d < 200 else ""

    def yakindaki_duraklar(self, lat, lon):
        all_stops = self.db.get("SELECT kod, ad, lat, lon FROM durak WHERE lat > 0")
        yakindakiler = []
        for s in all_stops:
            dist = haversine(lat, lon, s['lat'], s['lon'])
            if dist < 1000:
                s['dist'] = int(dist)
                yakindakiler.append(s)
        yakindakiler.sort(key=lambda x: x['dist'])
        return yakindakiler[:20]

    def durak_bilgi(self, durak_kodu):
        # 1. API Tahminlerini Al (SmartStations) - Double Check için
        api_preds = {}
        try:
             # ASIS API'den o durak için tahminleri çek
             smart_data = self.http.asis('SmartStations', stationId=durak_kodu)
             if smart_data:
                 for sd in smart_data:
                     try:
                         line = sd.get('BusLineCode')
                         time_min = int(sd.get('RemainingTimeCurr', 99))
                         api_preds[line] = time_min
                     except: pass
        except: pass

        hatlar = self.db.get("""SELECT DISTINCT h.code, h.name, h.kat, hd.sira FROM hat_durak hd JOIN hat h ON hd.hat = h.code WHERE hd.durak_id = (SELECT id FROM durak WHERE kod = ?) ORDER BY h.code""", (durak_kodu,))
        sonuc = []
        for h in hatlar:
            araclar = self.canli(h['code'])
            gelen_arac = None
            min_eta = 999
            route = self.db.get("SELECT durak_id, sira, lat, lon FROM hat_durak WHERE hat=? ORDER BY sira", (h['code'],))
            my_stop = next((r for r in route if r['sira'] == h['sira']), None)
            if my_stop:
                for a in araclar:
                    dist_to_me = haversine(a['lat'], a['lon'], my_stop['lat'], my_stop['lon'])
                    closest_stop_seq = -1
                    min_d_stop = 99999
                    for r in route:
                        d = haversine(a['lat'], a['lon'], r['lat'], r['lon'])
                        if d < min_d_stop: min_d_stop = d; closest_stop_seq = r['sira']
                    if closest_stop_seq != -1 and closest_stop_seq < my_stop['sira']:
                        eta = calculate_eta(dist_to_me, a['hiz'])
                        if eta < min_eta:
                            min_eta = eta
                            
                            # --- DOĞRULAMA MANTIĞI ---
                            # Bizim hesapladığımız ETA vs API'nin verdiği süre
                            api_time = api_preds.get(h['code'])
                            verify_status = "OK"
                            verify_msg = "Doğrulandı"
                            
                            if api_time is not None:
                                diff = abs(eta - api_time)
                                if diff > 5: # 5 dakikadan fazla fark varsa
                                    verify_status = "WARN"
                                    verify_msg = f"API Farkı: {diff} dk"
                                elif eta < 2 and api_time > 10:
                                    verify_status = "ERR"
                                    verify_msg = "Konum/Süre Uyuşmazlığı"
                            else:
                                verify_status = "INFO"
                                verify_msg = "Hesaplandı"
                                
                            gelen_arac = {
                                'plaka': a['plaka'], 
                                'durak_kaldi': my_stop['sira'] - closest_stop_seq, 
                                'tahmini_dk': eta, 
                                'hiz': a['hiz'], 
                                'doluluk': a['yolcu'],
                                'lat': a['lat'],
                                'lon': a['lon'],
                                'verify': {'status': verify_status, 'msg': verify_msg, 'api_time': api_time}
                            }
            sonuc.append({'hat': h['code'], 'ad': h['name'], 'kat': h['kat'], 'gelen': gelen_arac})
        sonuc.sort(key=lambda x: x['gelen'] is None)
        return sonuc

    def yol_tarifi(self, lat1, lon1, lat2, lon2):
        # 1. Başlangıç ve Bitişe yakın durakları bul (300m)
        start_stops = self.db.get("SELECT id, hat, sira, ad FROM hat_durak WHERE hat_durak.durak_id IN (SELECT id FROM durak WHERE (lat-?)*(lat-?) + (lon-?)*(lon-?) < 0.00001)", (lat1, lat1, lon1, lon1))
        end_stops = self.db.get("SELECT id, hat, sira, ad FROM hat_durak WHERE hat_durak.durak_id IN (SELECT id FROM durak WHERE (lat-?)*(lat-?) + (lon-?)*(lon-?) < 0.00001)", (lat2, lat2, lon2, lon2))
        
        # 2. Ortak Hatları Bul (Aktarmasız)
        routes = []
        for s in start_stops:
            for e in end_stops:
                if s['hat'] == e['hat'] and s['sira'] < e['sira']:
                    # Hattın canlı bilgisini al
                    araclar = self.canli(s['hat'])
                    en_yakin_arac_dk = 999
                    for a in araclar:
                        # Basitçe araca olan mesafeyi al (Geliştirilebilir)
                        dist = haversine(lat1, lon1, a['lat'], a['lon'])
                        eta = calculate_eta(dist, a['hiz'])
                        if eta < en_yakin_arac_dk: en_yakin_arac_dk = eta
                    
                    routes.append({
                        'hat': s['hat'],
                        'bin': s['ad'],
                        'in': e['ad'],
                        'durak_sayisi': e['sira'] - s['sira'],
                        'arac_var_mi': len(araclar) > 0,
                        'geliyor_dk': en_yakin_arac_dk if len(araclar) > 0 else None
                    })
        
        # En iyi rotaları sırala (Canlı araç varsa öne al, sonra durak sayısına göre)
        routes.sort(key=lambda x: (not x['arac_var_mi'], x['geliyor_dk'] if x['geliyor_dk'] else 999))
        return routes[:5]

    def esles(self, code):
        cur = self.db.one("SELECT tip, kat FROM hat WHERE code=?", (code,))
        if not cur: return ""
        for h in self.db.get("SELECT code, tip FROM hat WHERE kat=?", (cur['kat'],)):
            if h['code'] == code: continue
            if code.split()[0] == h['code'].split()[0] and h['tip'] != cur['tip']: return h['code']
        return ""

    def analiz_hatlar_tipleri(self):
        log.info("🔍 Hat Tipleri Analizi Başlıyor...")
        try:
            # 1. Lines
            lines = self.http.asis('Lines')
            tipler = {}
            for l in lines:
                t = l.get('lineType', -1)
                if t not in tipler: tipler[t] = []
                tipler[t].append(f"{l.get('lineCode')} - {l.get('lineName')}")
            
            with open("hat_analiz_lines.txt", "w", encoding="utf-8") as f:
                f.write("--- LINES ANALIZİ ---\n")
                if not tipler: f.write("Veri yok.\n")
                for t, lst in tipler.items():
                    f.write(f"\nTip {t}: {len(lst)} adet\n")
                    for x in lst[:10]: f.write(f"  {x}\n")
            
            # 2. OrjLines
            lines = self.http.asis('OrjLines')
            tipler = {}
            with open("hat_analiz_full.txt", "w", encoding="utf-8") as f:
                 f.write("--- TÜM HATLAR (ORJLINES) ---\n")
                 for l in lines:
                     c = l.get('lineCode')
                     n = l.get('lineName')
                     f.write(f"{c} | {n}\n")
                     
                     t = l.get('lineType', -1)
                     if t not in tipler: tipler[t] = []
                     tipler[t].append(f"{c} - {n}")
            
            with open("hat_analiz_orj.txt", "w", encoding="utf-8") as f:
                f.write("--- ORJLINES ANALIZİ ---\n")
                if not tipler: f.write("Veri yok.\n")
                for t, lst in tipler.items():
                    f.write(f"\nTip {t}: {len(lst)} adet\n")
                    for x in lst[:10]: f.write(f"  {x}\n")
                    
        except Exception as e:
            log.error(f"Analiz hatası: {e}")

# --- ARAYÜZ (HTML/JS) ---

HTML = '''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🚌 Samsun Transit</title>
<link rel="stylesheet" href="/static/leaflet.css"/>
<script src="/static/leaflet.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui,-apple-system,sans-serif;background:#f5f5f5}#map{height:100vh;width:100%}.pnl{position:absolute;top:10px;right:10px;z-index:1000;background:#fff;padding:14px;border-radius:14px;box-shadow:0 4px 20px rgba(0,0,0,.1);width:380px;max-height:92vh;overflow-y:auto}
h2{color:#1a1a2e;margin-bottom:12px;font-size:1rem}
.tabs{display:flex;gap:5px;margin-bottom:12px}
.tab{flex:1;padding:8px;text-align:center;background:#f0f0f0;border-radius:8px;cursor:pointer;font-size:.75rem;font-weight:600}.tab:hover{background:#e0e0e0}.tab.on{background:#1877f2;color:#fff}
.src{width:100%;padding:10px;border:1px solid #ddd;border-radius:8px;margin-bottom:10px;font-size:.85rem}
.kg{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-bottom:10px}.kb{background:#f5f5f5;padding:6px 2px;border-radius:6px;text-align:center;cursor:pointer;font-size:.55rem}.kb.on{background:#1877f2;color:#fff}
.lst{max-height:340px;overflow-y:auto}
.it{padding:9px 10px;margin:3px 0;background:#fafafa;border-radius:7px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;border-left:4px solid #ccc;font-size:.8rem}.it:hover{background:#e8f4fd}
.it.otobus{border-color:#1877f2} .it.ekspres{border-color:#9b59b6} .it.ring{border-color:#f39c12} .it.havalimani{border-color:#e74c3c} .it.ilce{border-color:#1abc9c}
.it.tramvay{border-color:#e67e22} .it.teleferik{border-color:#e91e63} .it.tekne{border-color:#3498db}
.bd{padding:2px 6px;border-radius:8px;font-size:.55rem;font-weight:700}.bd.g{background:#1877f2;color:#fff}.bd.d{background:#e74c3c;color:#fff}
.bk{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:10px;border-radius:8px;cursor:pointer;width:100%;margin-bottom:10px;font-weight:600}
.drk{padding:8px;margin:3px 0;background:#fff;border-radius:6px;display:flex;align-items:center;gap:8px;cursor:pointer;border:1px solid #eee;font-size:.75rem}.drk:hover{border-color:#1877f2;background:#f8fbff}
.drk .no{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:700;color:#fff;flex-shrink:0;background:#34495e}
.sfr{background:#f0f8ff;padding:8px;margin:4px 0;border-radius:6px;font-size:.7rem;border-left:3px solid #8e44ad}.sfr .st{font-weight:700;color:#8e44ad;font-size:.8rem}.sfr .fr{color:#444;font-weight:600}.sfr .dt{color:#888;font-size:.6rem;display:block;margin-top:2px}
.tel{background:#fff3e0;padding:10px;border-radius:8px;margin:8px 0;text-align:center}.tel a{color:#e65100;font-weight:700;font-size:1rem;text-decoration:none}
.no-data{text-align:center;padding:30px;color:#888}.loading{text-align:center;padding:25px;color:#888}.footer{font-size:.55rem;color:#aaa;margin-top:12px;text-align:center}
.dhead{background:#34495e;color:#fff;padding:6px 10px;font-size:.75rem;font-weight:700;border-radius:6px;margin:10px 0 4px 0}
.arac{display:flex;justify-content:space-between;padding:8px;background:#fff;border-radius:6px;margin:4px 0;border-left:3px solid #f39c12;font-size:.75rem}.arac .pl{font-weight:700;color:#d35400}
.saatlar{display:grid;grid-template-columns:repeat(auto-fill,minmax(50px,1fr));gap:5px}.saatlar span{background:#fff;padding:5px;border-radius:4px;text-align:center;font-size:.75rem;font-weight:600;border:1px solid #eee}
.live-badge{background:#27ae60;color:#fff;padding:3px 8px;border-radius:4px;font-size:.7rem;font-weight:700;margin-top:4px;display:inline-block;animation:blink 2s infinite}
@keyframes blink{0%{opacity:1}50%{opacity:.7}100%{opacity:1}}
.rota-box{background:#fff8e1;padding:10px;border-left:4px solid #f1c40f;margin-bottom:8px;border-radius:4px;cursor:pointer}
.sec{background:#34495e;color:#fff;padding:6px 10px;font-size:.75rem;font-weight:700;border-radius:6px;margin:10px 0 8px 0}
.hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.pbtn{background:#e74c3c;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:.7rem;font-weight:600}
.ig{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:10px 0}.ic{background:#f8f9fa;padding:12px;border-radius:8px;text-align:center}.ic .v{font-size:1.5rem;font-weight:700;color:#1877f2}.ic .l{font-size:.7rem;color:#666;margin-top:4px}
.fiyat{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:12px;border-radius:8px;margin:10px 0;text-align:center}.fiyat .t{font-size:.7rem;opacity:.9}.fiyat .pv{font-size:1.8rem;font-weight:700;margin:5px 0}.fiyat .s{font-size:.65rem;opacity:.8}
.araclar{background:#fff;padding:10px;border-radius:8px;margin:10px 0;border:1px solid #eee}.araclar .t{font-size:.8rem;font-weight:700;margin-bottom:8px;color:#34495e}
.saat{background:#fff;padding:10px;border-radius:8px;margin:10px 0;border:1px solid #eee}.saat .t{font-size:.8rem;font-weight:700;margin-bottom:8px;color:#34495e}
.saattab{display:flex;gap:5px;margin-bottom:8px}.saattab div{flex:1;padding:6px;text-align:center;background:#f5f5f5;border-radius:6px;cursor:pointer;font-size:.7rem;font-weight:600}.saattab div:hover{background:#e0e0e0}.saattab div.on{background:#1877f2;color:#fff}
.inf{flex:1}.ad{font-weight:600;color:#2c3e50}.fyt{display:block;font-size:.65rem;color:#7f8c8d;margin-top:2px}
.vtg{background:#27ae60;color:#fff;padding:2px 6px;border-radius:4px;font-size:.6rem;font-weight:700;margin-left:8px}
.toast{visibility:hidden;min-width:250px;background-color:#333;color:#fff;text-align:center;border-radius:8px;padding:12px;position:fixed;z-index:9999;left:50%;bottom:30px;transform:translateX(-50%);font-size:0.8rem;box-shadow:0 4px 12px rgba(0,0,0,0.3)}
.toast.show{visibility:visible;animation:fadein 0.5s, fadeout 0.5s 2.5s}
@keyframes fadein{from{bottom:0;opacity:0}to{bottom:30px;opacity:1}}
@keyframes fadeout{from{bottom:30px;opacity:1}to{bottom:0;opacity:0}}
</style>
</head>
<body>
<div id="toast" class="toast">Mesaj</div>
<div id="map"></div>
<div class="pnl">
<div id="disclaimer" style="background:#fff3cd;color:#856404;padding:10px;font-size:0.65rem;text-align:center;border-bottom:1px solid #ffeeba">
    ⚠️ <b>YASAL UYARI:</b> Bu uygulama Samsun Büyükşehir Belediyesi veya Asis Elektronik ile resmi bağlantılı değildir. 
    Veriler açık kaynaklardan sağlanmaktadır. Kesin bilgi için resmi kurumlarla iletişime geçiniz.
</div>
<h2>🚌 Samsun Transit</h2>
<div class="tabs"><div class="tab on" data-t="hat">🚌 Hatlar</div><div class="tab" data-t="odak">🎯 Odak</div><div class="tab" data-t="samair">✈️ Samair</div><div class="tab" data-t="rota" onclick="shRotaUI()">📍 Git</div></div>
<div id="ct"></div>
<div class="footer" id="footer">
    Veriler anlık değişebilir. Resmi uygulama değildir. <br>
    📞 <b>İletişim:</b> Samsun içi <a href="tel:153">153</a>, dışı <a href="tel:03624311012">0362 431 10 12</a>
</div>
</div>
<!-- Bilgilendirme Modalı -->
<div id="infoModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;align-items:center;justify-content:center">
    <div style="background:#fff;padding:20px;border-radius:10px;width:80%;max-width:400px;text-align:center">
        <h3 style="color:#d35400;margin-bottom:10px">⚠️ Önemli Bilgilendirme</h3>
        <p style="font-size:0.9rem;color:#333;margin-bottom:15px">
            Görüntülenen fiyatlar ve sefer bilgileri tahmini olabilir. 
            Özellikle <b>Odak (Turistik)</b> hatlarında fiyatlar tam/indirimli farklılık gösterebilir.
        </p>
        <p style="font-size:0.8rem;color:#666;margin-bottom:20px">
            Kesin bilgi için lütfen araç kaptanlarına danışınız.<br>
            📞 Samsun içi: <a href="tel:153">153</a><br>
            📞 Samsun dışı: <a href="tel:03624311012">0362 431 10 12</a>
        </p>
        <button onclick="document.getElementById('infoModal').style.display='none'" style="background:#1877f2;color:#fff;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;font-weight:bold">Anladım</button>
    </div>
</div>
<script>
const map=L.map('map').setView([41.29,36.33],12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
let M={}, V={}, H=[], cur='hat', sK=null, liveT=null, userLoc=null, targetLoc=null;
const K={dil:{i:'🌐',n:'Tümü',c:'#333'},otobus:{i:'🚌',n:'Otobüs',c:'#1877f2'},ekspres:{i:'🚀',n:'Ekspres',c:'#9b59b6'},tramvay:{i:'🚋',n:'Tramvay',c:'#e67e22'},ring:{i:'🔄',n:'Ring',c:'#f39c12'},tekne:{i:'🛥️',n:'Tekne',c:'#3498db'},teleferik:{i:'🚠',n:'Teleferik',c:'#e91e63'},havalimani:{i:'✈️',n:'H.limanı',c:'#e74c3c'},ilce:{i:'🏘️',n:'İlçe',c:'#1abc9c'}};

const busIcon=(c,p)=>L.divIcon({className:'',html:`<div style="position:relative"><div style="width:30px;height:30px;background:${c};border-radius:50%;border:2px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;font-size:14px">🚌</div><div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:#222;color:#fff;padding:1px 5px;border-radius:3px;font-size:9px;white-space:nowrap;z-index:99">${p}</div></div>`,iconSize:[30,30],iconAnchor:[15,15]});
const bI=busIcon;
const stopIcon=(n)=>L.divIcon({className:'',html:`<div style="width:18px;height:18px;background:#34495e;border-radius:50%;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.3);color:#fff;font-size:9px;display:flex;align-items:center;justify-content:center;font-weight:700">${n}</div>`,iconSize:[18,18],iconAnchor:[9,9]});
const dI=(n,c)=>L.divIcon({className:'',html:`<div style="width:18px;height:18px;background:${c};border-radius:50%;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.3);color:#fff;font-size:9px;display:flex;align-items:center;justify-content:center;font-weight:700">${n}</div>`,iconSize:[18,18],iconAnchor:[9,9]});
const clr=()=>{if(liveT)clearInterval(liveT);Object.values(M).forEach(m=>map.removeLayer(m));Object.values(V).forEach(m=>map.removeLayer(m));M={};V={};};

// Konum
function showToast(msg) {
    const x = document.getElementById("toast");
    x.innerText = msg;
    x.className = "toast show";
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
}

async function init(){
    // DEBUG: Samsun Cumhuriyet Meydanı (Default)
    const defLoc = {lat: 41.2925, lon: 36.3315};
    
    if(navigator.geolocation){
        navigator.geolocation.getCurrentPosition(async p=>{
            const lat=p.coords.latitude, lon=p.coords.longitude;
            // Samsun dışında ise Meydan'a sabitle (User Request)
            if(lat < 41.0 || lat > 41.6 || lon < 35.0 || lon > 37.0){
                userLoc = defLoc;
                map.setView([defLoc.lat,defLoc.lon],15);
                L.marker([defLoc.lat,defLoc.lon]).addTo(map).bindPopup("Varsayılan Konum (Samsun)").openPopup();
                const d = await(await fetch(`/api/yakin?lat=${defLoc.lat}&lon=${defLoc.lon}`)).json();
                shYakin(d);
                showToast("Samsun dışındasınız, varsayılan konuma gidildi.");
            } else {
                userLoc = {lat, lon};
                map.setView([lat,lon],15);
                L.marker([lat,lon]).addTo(map).bindPopup("Siz Buradasınız").openPopup();
                const d = await(await fetch(`/api/yakin?lat=${lat}&lon=${lon}`)).json();
                shYakin(d);
            }
        }, ()=>{ 
            // Konum alınamazsa Meydan'a git
            userLoc = defLoc;
            map.setView([defLoc.lat,defLoc.lon],15);
            L.marker([defLoc.lat,defLoc.lon]).addTo(map).bindPopup("Samsun Meydan").openPopup();
            loadHats(); 
            showToast("Konum izni alınamadı, varsayılan konum yüklendi.");
        });
    } else {
        userLoc = defLoc;
        map.setView([defLoc.lat,defLoc.lon],15);
        loadHats();
        showToast("Tarayıcınız konum servisini desteklemiyor.");
    }
    
    // Sağ tık ile hedef seçme (Rota için)
    map.on('contextmenu', function(e){
        targetLoc = e.latlng;
        L.popup().setLatLng(e.latlng).setContent('<button onclick="calcRota()">Buraya Nasıl Giderim?</button>').openOn(map);
    });
}

async function loadHats(){ try{H=await(await fetch('/api/hat')).json();shH()}catch(e){} }

function shYakin(duraklar){
    clr();
    let x=`<div class="sec">📍 Yakınınızdaki Duraklar</div><div class="lst">`;
    if(duraklar.length){
        duraklar.forEach((d,i)=>{
            x+=`<div class="drk" onclick="shDurakDetay('${d.kod}')"><span class="no">${i+1}</span><div class="inf" style="margin-left:10px"><b>${d.ad}</b><br><small>${d.dist}m uzakta</small></div></div>`;
            M['d'+d.kod]=L.marker([d.lat,d.lon],{icon:stopIcon(i+1)}).addTo(map).bindPopup(d.ad);
        });
    } else x+=`<div class="no-data">Yakında durak bulunamadı.</div>`;
    x+=`<button class="bk" style="margin-top:10px" onclick="loadHats()">Tüm Hatları Göster</button></div>`;
    document.getElementById('ct').innerHTML=x;
}

// Rota Hesaplama
async function shRotaUI(){
    clr();
    document.getElementById('ct').innerHTML=`<div class="sec">📍 Yol Tarifi</div>
    <div style="padding:10px;text-align:center;color:#666">
        <p>1. Konumunuz otomatik alındı.</p>
        <p>2. Haritada gitmek istediğiniz yere <b>sağ tıklayın</b> (veya basılı tutun).</p>
        <p>3. "Buraya Nasıl Giderim?" butonuna basın.</p>
    </div>`;
}

async function calcRota(){
    if(!userLoc || !targetLoc) return alert("Konum alınamadı!");
    document.getElementById('ct').innerHTML='<div class="loading">Güzergah aranıyor...</div>';
    try {
        const routes = await(await fetch(`/api/rota?lat1=${userLoc.lat}&lon1=${userLoc.lon}&lat2=${targetLoc.lat}&lon2=${targetLoc.lng}`)).json();
        let x=`<div class="sec">📍 Bulunan Güzergahlar</div><div class="lst">`;
        if(routes.length){
            routes.forEach(r=>{
                x+=`<div class="rota-box" onclick="shL('${encodeURIComponent(r.hat)}')">
                    <div style="font-weight:bold;font-size:1rem">🚌 ${r.hat}</div>
                    <div style="font-size:0.8rem;margin:5px 0">⬇️ ${r.bin} <br> 🏁 ${r.in}</div>
                    <div style="font-size:0.75rem;color:#d35400">
                        ${r.arac_var_mi ? `🟢 Araç Geliyor (${r.geliyor_dk} dk)` : '🔴 Şu an araç yok'}
                        <span style="float:right">${r.durak_sayisi} Durak</span>
                    </div>
                </div>`;
            });
        } else x+=`<div class="no-data">Aktarmasız hat bulunamadı.</div>`;
        document.getElementById('ct').innerHTML=x+'</div>';
    } catch(e){ console.error(e); }
}

async function shDurakDetay(kod){
    document.getElementById('ct').innerHTML='<div class="loading">Durak bilgileri alınıyor...</div>';
    try {
        const inf = await(await fetch(`/api/durak_panel/${kod}`)).json();
        let x=`<button class="bk" onclick="init()">← Geri</button><div class="sec">🚏 Duraktan Geçen Hatlar</div><div class="lst">`;
        
        // Haritayı temizle ama Durağı koru
        Object.values(V).forEach(m=>map.removeLayer(m)); V={};
        const activeBuses = [];
        
        if(inf.length){
            inf.forEach(h=>{
                x+=`<div class="it ${h.kat}" onclick="shL('${encodeURIComponent(h.hat)}')">
                    <div><b>${h.hat}</b> - ${h.ad}</div>
                    ${h.gelen?(() => {
                        // CANLI ARAÇ HARİTAYA EKLENİYOR
                        // Gelen aracın konumu (durak_bilgi backend update edilmesi lazım demiştim, ama durak_bilgi içinde gelen_arac objesine lat/lon eklemedim henüz!)
                        // Backend'i güncellemem lazım önce!
                        // Neyse, mevcut gelen_arac objesinde lat/lon yoksa haritaya koyamam.
                        // Backend'i güncellemek için bir sonraki adıma geçeceğim.
                        // Şimdilik sadece badge gösteriyorum.
                        
                        let vb = '';
                        if(h.gelen.verify){
                            const v = h.gelen.verify;
                            if(v.status==='OK') vb='<span style="color:#fff;background:#27ae60;padding:1px 3px;border-radius:3px;font-size:0.55rem;margin-left:4px">✅ Doğrulandı</span>';
                            else if(v.status==='WARN') vb=`<span style="color:#fff;background:#f39c12;padding:1px 3px;border-radius:3px;font-size:0.55rem;margin-left:4px">⚠️ ${v.msg}</span>`;
                            else if(v.status==='ERR') vb=`<span style="color:#fff;background:#c0392b;padding:1px 3px;border-radius:3px;font-size:0.55rem;margin-left:4px">❌ ${v.msg}</span>`;
                            else vb=`<span style="color:#fff;background:#3498db;padding:1px 3px;border-radius:3px;font-size:0.55rem;margin-left:4px">ℹ️ ${v.msg}</span>`;
                        }
                        
                        // Aracı haritaya ekleme (Eğer lat/lon varsa)
                        if(h.gelen.lat && h.gelen.lon){
                            const m = L.marker([h.gelen.lat, h.gelen.lon], {icon: bI(K[h.kat].c, h.gelen.plaka)}).addTo(map).bindPopup(`<b>${h.hat}</b><br>${h.gelen.tahmini_dk} dk`);
                            V['v'+h.gelen.plaka] = m;
                            activeBuses.push([h.gelen.lat, h.gelen.lon]);
                        }
                        
                        return `<div class="live-badge">⏱️ ${h.gelen.tahmini_dk} dk (${h.gelen.durak_kaldi} durak)${vb} <br> <span style="font-weight:400;font-size:0.6rem">Hız: ${h.gelen.hiz} km/s • ${h.gelen.doluluk} yolcu</span></div>`;
                    })():''}
                </div>`;
            });
            
            // Haritayı durak ve araçları kapsayacak şekilde odakla
            if(activeBuses.length > 0){
                // Durak konumu için M['d'+kod] kullanılabilir ama elimizde lat/lon yok şu an bu fonksiyon içinde.
                // Stop marker zaten haritada var.
                const group = L.featureGroup(Object.values(V));
                map.fitBounds(group.getBounds().pad(0.2));
            }
            
        } else x+=`<div class="no-data">Hat bilgisi yok</div>`;
        document.getElementById('ct').innerHTML=x+'</div>';
    } catch(e){}
}

// Sekmeler
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
    t.classList.add('on'); cur=t.dataset.t; clr();
    if(cur==='rota') shRotaUI();
    else if(cur==='hat') loadHats();
    else if(cur==='odak') shO();
    else shS();
});

function shH(){const bk={}; H.forEach(h=>{const k=h.kat||'otobus';(bk[k]=bk[k]||[]).push(h)});let x=`<input class="src" placeholder="Hat ara..." oninput="flt(this.value)"><div class="kg">`;Object.entries(K).forEach(([k,v])=>{const cnt=k==='dil'?H.length:(bk[k]?bk[k].length:0);x+=`<div class="kb ${sK===k?'on':''}" onclick="selK('${k}')"><div class="i">${v.i}</div>${v.n} <span style="font-size:0.55rem;opacity:0.8;display:block">(${cnt})</span></div>`});x+=`</div><div class="lst" id="lst">`;(sK&&sK!=='dil'?bk[sK]||[]:H).forEach(h=>{x+=`<div class="it ${h.kat||'otobus'}" onclick="shL('${encodeURIComponent(h.code)}')">${h.name||h.code}</div>`});document.getElementById('ct').innerHTML=x+`</div>`;}
window.selK=k=>{sK=sK===k?null:k;shH()};window.flt=q=>{q=q.toLowerCase();const bk={};H.forEach(h=>{const k=h.kat||'otobus';(bk[k]=bk[k]||[]).push(h)});const f=(sK&&sK!=='dil'?bk[sK]||[]:H).filter(h=>(h.code+h.name).toLowerCase().includes(q));document.getElementById('lst').innerHTML=f.map(h=>{const g=h.tip==='gidis',k=h.kat||'otobus';return`<div class="it ${k}" onclick="shL('${encodeURIComponent(h.code)}')">${h.name||h.code}</div>`}).join('')};

async function upV(e, col){try {const aa=await(await fetch('/api/hat/arac/'+e)).json();Object.values(V).forEach(m=>map.removeLayer(m)); V={};let html = '';document.querySelectorAll('.drk .vtg').forEach(el=>el.remove());if(Array.isArray(aa) && aa.length > 0){document.getElementById('acnt').innerText=aa.length;aa.forEach(a=>{V['v'+a.plaka]=L.marker([a.lat,a.lon],{icon:bI(col,a.plaka)}).addTo(map);const yak=a.yakin||'';html += `<div class="arac" onclick="map.setView([${a.lat},${a.lon}],16)"><div><div class="pl">${a.plaka}</div><div class="inf">${yak?'📍 '+yak:''}</div></div><div style="text-align:right"><div style="font-weight:700">${a.hiz} km/s</div><div class="inf">${a.yolcu} yolcu</div></div></div>`;if(yak){const rows = document.querySelectorAll('.drk');rows.forEach(r=>{if(r.innerText.includes(yak)) {if(!r.querySelector('.vtg')) r.innerHTML += `<span class="vtg">🚌 ${a.plaka}</span>`;}});}});document.getElementById('vlist').innerHTML = html;} else {document.getElementById('acnt').innerText='0';document.getElementById('vlist').innerHTML = '<div style="text-align:center;padding:10px;color:#999;font-size:0.7rem">Aktif araç yok</div>';}} catch(e){}}

async function shL(e){clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';try{const[inf,dr,sf,ar,pr,fy]=await Promise.all([fetch('/api/hat/info/'+e),fetch('/api/hat/durak/'+e),fetch('/api/hat/sefer/'+e),fetch('/api/hat/arac/'+e),fetch('/api/hat/esles/'+e),fetch('/api/hat/fiyat/'+e)].map(p=>p.then(r=>r.json())));const nm=inf.name||decodeURIComponent(e),k=inf.kat||'otobus',ki=K[k]||K.otobus,g=inf.tip==='gidis',col=ki.c;const da=Array.isArray(dr)?dr:[],sa=Array.isArray(sf)?sf:[],aa=Array.isArray(ar)?ar:[];const tamF=(fy.tam_fiyat||17).toFixed(2),indF=(fy.indirimli_fiyat||12).toFixed(2);let x=`<button class="bk" onclick="shH()">← Hatlar</button><div class="hdr"><div style="font-weight:700;font-size:.9rem">${ki.i} ${nm}</div>`;if(pr.code)x+=`<button class="pbtn" onclick="shL('${encodeURIComponent(pr.code)}')">${g?'Dönüş →':'← Gidiş'}</button>`;x+=`</div><div class="ig"><div class="ic"><div class="v">${da.length}</div><div class="l">Durak</div></div><div class="ic"><div class="v" id="acnt">${aa.length}</div><div class="l">Araç</div></div></div>`;
    
    // --- BİLGİLENDİRME KUTULARI (Kullanıcı İsteği) ---
    
    // 1. SAMSUNUM-1
    if(nm.includes('SAMSUNUM-1')){
        x+=`<div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:12px;margin:10px 0;font-size:0.75rem;color:#856404">
            <h4 style="margin-bottom:8px;color:#d35400">⚠️ DEĞERLİ YOLCULARIMIZIN DİKKATİNE!</h4>
            <p>Hava koşullarına bağlı olarak sefer saatlerimizde değişiklikler ve aksamalar yaşanabilmektedir. Yolculuk planlamanızı yaparken bu durumu göz önünde bulundurmanızı rica ederiz.</p>
            <p style="margin-top:8px"><b>Sefer Süresi:</b> 1 saat 15 dakika</p>
            <p><b>Ücret:</b> Tam 200 TL / Öğrenci 150 TL</p>
            <p style="margin-top:8px">📞 İletişim: <b>0362 431 10 12</b></p>
        </div>`;
    }
    
    // 2. SAMSUNUM-2 (AYVACIK)
    else if(nm.includes('SAMSUNUM-2')){
        x+=`<div style="background:#f8d7da;border:1px solid #f5c6cb;border-radius:8px;padding:12px;margin:10px 0;font-size:0.75rem;color:#721c24">
            <h4 style="margin-bottom:8px">🛑 ÇALIŞMAMAKTADIR</h4>
            <p>DSİ Bölge Müdürlüğü'nün çalışmalarından dolayı su verilememesi sebebiyle Samsunum-2 Gemisi çalışamamaktadır.</p>
            <p style="margin-top:8px">Anlayışınız ve sabrınız için teşekkür ederiz.</p>
        </div>`;
    }
    
    // 3. SAMSUNUM-3 (VEZİRKÖPRÜ)
    else if(nm.includes('SAMSUNUM-3')){
        x+=`<div style="background:#d1ecf1;border:1px solid #bee5eb;border-radius:8px;padding:12px;margin:10px 0;font-size:0.75rem;color:#0c5460">
            <h4 style="margin-bottom:8px">ℹ️ Sefer Bilgisi</h4>
            <p>Sefer saatleri <b>doluluğa göre</b> belirlenir.</p>
            <p>Hava koşullarına bağlı aksamalar yaşanabilir.</p>
            <p style="margin-top:8px"><b>Sefer Süresi:</b> 1 saat 15 dk</p>
            <p><b>Ücret:</b> Tam 200 TL / Öğrenci 150 TL</p>
        </div>`;
    }

    // 4. ALTINKAYA 55 (FERİBOT)
    else if(nm.includes('ALTINKAYA') || nm.includes('FERİBOT')){
         x+=`<div style="background:#e2e3e5;border:1px solid #d6d8db;border-radius:8px;padding:12px;margin:10px 0;font-size:0.7rem;color:#383d41">
            <h4 style="margin-bottom:8px">⛴️ Altınkaya 55 Feribot Tarifesi</h4>
            <p><b>Yolcu:</b> Tam 15 TL / Öğrenci 7 TL</p>
            <p><b>Araçlar:</b></p>
            <ul style="padding-left:15px;margin:5px 0">
                <li>Otomobil/Minibüs: 75 TL</li>
                <li>Römorklu Traktör/Kamyonet: 90 TL</li>
                <li>Kamyon (Boş): 290 TL / (Dolu): 580 TL</li>
                <li>Otobüs: 290 TL (10m üstü 410 TL)</li>
            </ul>
            <p style="margin-top:5px;font-size:0.65rem">** Belirtilen saat dışındaki seferlerde gece tarifesi (%50 zamlı) uygulanır.</p>
        </div>`;
    }

    // 5. TELEFERİK
    else if(nm.includes('TELEFERİK')){
         x+=`<div style="background:#fce4ec;border:1px solid #f8bbd0;border-radius:8px;padding:12px;margin:10px 0;font-size:0.75rem;color:#880e4f">
            <h4 style="margin-bottom:8px">🚠 Batıpark - Amisos Tepesi</h4>
            <div style="font-size:0.7rem;margin-bottom:10px;line-height:1.4">
                2005 yılında faaliyete başlayan teleferik hattı 323 metre uzunluğundadır.
                Batı Park ile Baruthane Tümülüsleri arasında hizmet vermektedir.
            </div>
            <p><b>🕘 Çalışma Saatleri:</b> 10:30 - 22:00</p>
             <p><b>Kalkış:</b> Batıpark</p>
             <p><b>Varış:</b> Amisos Tepesi (Baruthane)</p>
             <p style="margin-top:8px">📞 Bilgi: <b>0362 431 10 12</b></p>
        </div>`;
    }
    
    // 6. TRAMVAY INFO
    else if(nm.includes('TRAMVAY')){
        x+=`<div style="background:#fff3cd;border:1px solid #ffeeba;border-radius:8px;padding:8px;margin:10px 0;font-size:0.75rem;text-align:center;color:#856404">
             ℹ️ <b>Bilgi:</b> Güncel sefer saatleri ve durak bilgileri için <a href="tel:03624311012">0362 431 10 12</a> nolu hattı arayabilirsiniz.
        </div>
        
        <!-- TRAMVAY SEFER SIKLIKLARI TABLOSU -->
        <div style="margin:10px 0;border:1px solid #ddd;border-radius:8px;overflow:hidden">
            <div style="display:flex;background:#f3f3f3;border-bottom:1px solid #ddd">
                <div onclick="openTramTab('hi', this)" style="flex:1;padding:10px;text-align:center;cursor:pointer;font-weight:bold;background:#fff;border-bottom:2px solid #007bff">Hafta İçi</div>
                <div onclick="openTramTab('cmt', this)" style="flex:1;padding:10px;text-align:center;cursor:pointer;border-bottom:2px solid transparent">Cumartesi</div>
                <div onclick="openTramTab('pzr', this)" style="flex:1;padding:10px;text-align:center;cursor:pointer;border-bottom:2px solid transparent">Pazar</div>
            </div>
            
            <div id="tramTabContent" style="padding:10px;background:#fff;overflow-x:auto">
                <div id="tab_hi" style="display:block">
                    <h5 style="margin:5px 0 10px;text-align:center">Hafta İçi Sefer Aralıkları</h5>
                    <table border="1" cellpadding="5" cellspacing="0" style="width:100%;font-size:0.65rem;border-collapse:collapse;text-align:center">
                        <thead><tr style="background:#f8f9fa"><th colspan="2">Saat</th><th colspan="2">Sefer Sıklığı (Dk)</th></tr><tr><th>Başlangıç</th><th>Bitiş</th><th>Yurtlar -> Tekkeköy</th><th>Tekkeköy -> Yurtlar</th></tr></thead>
                        <tbody>
                            <tr><td>06:15</td><td>07:00</td><td>14</td><td>16</td></tr>
                            <tr><td>07:00</td><td>07:30</td><td>14</td><td>16</td></tr>
                            <tr><td>07:30</td><td>08:00</td><td>5</td><td>8</td></tr>
                            <tr><td>08:00</td><td>09:00</td><td>8</td><td>10</td></tr>
                            <tr><td>09:00</td><td>17:00</td><td>7</td><td>12-14</td></tr>
                            <tr><td>17:00</td><td>17:30</td><td>7</td><td>10</td></tr>
                            <tr><td>17:30</td><td>18:30</td><td>14</td><td>14</td></tr>
                            <tr><td>18:30</td><td>20:00</td><td>14</td><td>14</td></tr>
                            <tr><td>20:00</td><td>21:00</td><td>16</td><td>16</td></tr>
                            <tr><td>21:00</td><td>23:30</td><td>20</td><td>20</td></tr>
                            <tr><td>23:30</td><td>23:45</td><td>15</td><td>15</td></tr>
                        </tbody>
                    </table>
                </div>
                
                <div id="tab_cmt" style="display:none">
                    <h5 style="margin:5px 0 10px;text-align:center">Cumartesi Sefer Aralıkları</h5>
                    <table border="1" cellpadding="5" cellspacing="0" style="width:100%;font-size:0.65rem;border-collapse:collapse;text-align:center">
                        <thead><tr style="background:#f8f9fa"><th colspan="2">Saat</th><th colspan="2">Sefer Sıklığı (Dk)</th></tr><tr><th>Başlangıç</th><th>Bitiş</th><th>Yurtlar -> Tekkeköy</th><th>Tekkeköy -> Yurtlar</th></tr></thead>
                        <tbody>
                            <tr><td>06:15</td><td>07:30</td><td>16</td><td>16</td></tr>
                            <tr><td>07:30</td><td>12:00</td><td>16</td><td>16</td></tr>
                            <tr><td>12:00</td><td>18:00</td><td>12</td><td>12</td></tr>
                            <tr><td>18:00</td><td>20:00</td><td>14</td><td>14</td></tr>
                            <tr><td>20:00</td><td>20:30</td><td>16</td><td>16</td></tr>
                            <tr><td>20:30</td><td>23:00</td><td>20</td><td>20</td></tr>
                            <tr><td>23:00</td><td>23:45</td><td>30</td><td>20</td></tr>
                        </tbody>
                    </table>
                </div>
                
                <div id="tab_pzr" style="display:none">
                    <h5 style="margin:5px 0 10px;text-align:center">Pazar Sefer Aralıkları</h5>
                    <table border="1" cellpadding="5" cellspacing="0" style="width:100%;font-size:0.65rem;border-collapse:collapse;text-align:center">
                        <thead><tr style="background:#f8f9fa"><th colspan="2">Saat</th><th colspan="2">Sefer Sıklığı (Dk)</th></tr><tr><th>Başlangıç</th><th>Bitiş</th><th>Yurtlar -> Tekkeköy</th><th>Tekkeköy -> Yurtlar</th></tr></thead>
                        <tbody>
                            <tr><td>06:15</td><td>11:30</td><td>18</td><td>18</td></tr>
                            <tr><td>11:30</td><td>18:00</td><td>14</td><td>14</td></tr>
                            <tr><td>18:00</td><td>22:00</td><td>16</td><td>16</td></tr>
                            <tr><td>22:00</td><td>23:00</td><td>20</td><td>20</td></tr>
                            <tr><td>23:00</td><td>23:45</td><td>30</td><td>30</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>`;
    }

    x+=`<div class="fiyat"><div class="t">Bilet</div><div class="pv">₺${tamF}</div><div class="s">İndirimli ₺${indF}${fy.aktarma1?' | Aktarma: '+fy.aktarma1:''}</div></div>`;x+=`<div class="araclar"><div class="t">🚌 Canlı Araçlar</div><div id="vlist">Yükleniyor...</div></div>`;if(sa.length){const hi=sa.filter(s=>s.gun==='hi').sort((a,b)=>(a.saat||'').localeCompare(b.saat||'')),hs=sa.filter(s=>s.gun==='hs').sort((a,b)=>(a.saat||'').localeCompare(b.saat||''));
    
    // CUSTOM for Boats/Teleferik (Her Gün / Hafta Sonu)
    const hergun = sa.filter(s=>s.gun==='Her Gün').sort((a,b)=>(a.saat||'').localeCompare(b.saat||''));
    const haftasonu = sa.filter(s=>s.gun==='Hafta Sonu').sort((a,b)=>(a.saat||'').localeCompare(b.saat||''));
    
    if(hergun.length){
        x+=`<div class="saat"><div class="t">📅 Sefer Saatleri (Her Gün)</div><div class="saatlar">${hergun.map(s=>`<span>${s.saat}${s.yon?'<br><small>'+s.yon+'</small>':''}</span>`).join('')}</div></div>`;
    }
    if(haftasonu.length){
        x+=`<div class="saat"><div class="t">📅 Sefer Saatleri (Hafta Sonu)</div><div class="saatlar">${haftasonu.map(s=>`<span>${s.saat}${s.yon?'<br><small>'+s.yon+'</small>':''}</span>`).join('')}</div></div>`;
    }
    
    if(hi.length||hs.length){x+=`<div class="saat"><div class="t">📅 Saatler</div><div class="saattab"><div class="on" onclick="schT('hi',this)">Hİ (${hi.length})</div><div onclick="schT('hs',this)">HS (${hs.length})</div></div><div class="saatlar" id="scht">${hi.slice(0,40).map(s=>`<span>${s.saat}</span>`).join('')}${hi.length>40?`<span>+${hi.length-40}</span>`:''}</div></div>`;window._s={hi,hs}}}if(da.length){x+=`<div class="sec">📍 Duraklar (${da.length})</div>`;const co=[];da.forEach((d,i)=>{x+=`<div class="drk" onclick="map.setView([${d.lat},${d.lon}],17)"><span class="no" style="background:${col}">${i+1}</span><span class="inf"><span class="ad">${d.ad}</span></span></div>`;if(d.lat&&d.lon){co.push([d.lat,d.lon]);M['d'+i]=L.marker([d.lat,d.lon],{icon:dI(i+1,col)}).addTo(map)}});if(co.length)map.fitBounds(co,{padding:[40,40]})}else x+=`<div class="no-data"><div class="icon">📍</div>Durak bilgisi yok</div>`;document.getElementById('ct').innerHTML=x;upV(e,col); liveT=setInterval(()=>upV(e,col),5000);}catch(e){console.error(e);document.getElementById('ct').innerHTML=`<button class="bk" onclick="shH()">← Hatlar</button><div class="no-data"><div class="icon">❌</div>Hata</div>`}}
window.shL=shL;
window.schT=(t,b)=>{document.querySelectorAll('.saattab div').forEach(x=>x.classList.remove('on'));b.classList.add('on');const d=window._s?.[t]||[];document.getElementById('scht').innerHTML=d.slice(0,40).map(s=>`<span>${s.saat}</span>`).join('')+(d.length>40?`<span>+${d.length-40}</span>`:'')};
window.openTramTab = function(tabId, el) {
    document.getElementById('tab_hi').style.display = 'none';
    document.getElementById('tab_cmt').style.display = 'none';
    document.getElementById('tab_pzr').style.display = 'none';
    document.getElementById('tab_' + tabId).style.display = 'block';
    
    let tabs = el.parentNode.children;
    for(let i=0; i<tabs.length; i++) {
        tabs[i].style.borderBottom = '2px solid transparent';
        tabs[i].style.fontWeight = 'normal';
        tabs[i].style.backgroundColor = 'transparent';
    }
    el.style.borderBottom = '2px solid #007bff';
    el.style.fontWeight = 'bold';
    el.style.backgroundColor = '#fff';
};

async function shO(){
    clr();
    document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';
    // Odak uyarısını her seferinde göster
    document.getElementById('infoModal').style.display='flex';
    try{
        const d=await(await fetch('/api/odak')).json();
        if(!d||!d.length){document.getElementById('ct').innerHTML='<div class="no-data"><div class="icon">🎯</div>Veri yok</div>';return}
        let x=`<div class="sec">🎯 Odak Samsun Gezileri</div><div class="tel">📞 Bilgi: <a href="tel:03624311012">0362 431 10 12</a></div>
        <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:8px;margin:8px 0;font-size:0.65rem;text-align:center;color:#856404">
            ⚠️ <b>DİKKAT:</b> Fiyatlar değişiklik gösterebilir. Tam/İndirimli tarifeleri için lütfen teyit ediniz.
        </div>
        <div class="lst">${d.map(o=>`<div class="it odak" onclick="shOD('${o.id}')">${o.kod} ${o.ad}</div>`).join('')}</div>`;
        document.getElementById('ct').innerHTML=x
    }catch(e){console.error(e)}
}

async function shOD(id){clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';try{const[hl,dr]=await Promise.all([fetch('/api/odak').then(r=>r.json()),fetch('/api/odak/'+id+'/durak').then(r=>r.json())]);const h=(hl||[]).find(x=>x.id==id)||{},da=Array.isArray(dr)?dr:[],ilk=da[0]||{};let x=`<button class="bk" onclick="shO()">← Odak</button><div style="font-weight:700;margin-bottom:10px;font-size:1rem">🎯 ${h.kod||''} ${h.ad||''}</div>`;x+=`<div class="ig"><div class="ic"><div class="v">${da.length}</div><div class="l">Durak</div></div><div class="ic"><div class="v">₺${ilk.fiyat||'?'}</div><div class="l">Tam</div></div></div>`;x+=`<div class="tel">📞 Bilgi: <a href="tel:03624311012">0362 431 10 12</a></div>`;if(da.length){x+=`<div class="sec">📍 Güzergah</div>`;const co=[];da.forEach((d,i)=>{x+=`<div class="drk" onclick="map.setView([${d.lat},${d.lon}],16)"><span class="no" style="background:#27ae60">${i+1}</span><span class="inf"><span class="ad">${d.ad}</span><span class="fyt">₺${d.fiyat||'?'} / ₺${d.fiyat_ogr||'?'} <br> <small>(Sol: Tam, Sağ: İndirimli)</small></span></span></div>`;if(d.lat>0&&d.lon>0){co.push([d.lat,d.lon]);M['o'+i]=L.marker([d.lat,d.lon],{icon:dI(i+1,'#27ae60')}).addTo(map)}});if(co.length)map.fitBounds(co,{padding:[40,40]})}document.getElementById('ct').innerHTML=x}catch(e){console.error(e)}}
window.shOD=shOD;

async function shS(){clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';try{const d=await(await fetch('/api/samair')).json();if(!d||!d.length){document.getElementById('ct').innerHTML='<div class="no-data"><div class="icon">✈️</div>Veri yok</div>';return}let x=`<div class="sec">✈️ Samair Havalimanı Servisi</div><div class="tel">📞 Bilgi: <a href="tel:03624311012">0362 431 10 12</a></div><div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:8px;margin:8px 0;font-size:0.65rem;text-align:center;color:#856404">⚠️ Bu veriler proje amaçlı test verileridir. Kesin bilgi için yukarıdaki numarayı arayınız.<br>📍 Veriler her saat başı otomatik güncellenir.</div><div class="lst">${d.map(h=>`<div class="it samair" onclick="shSD(${h.id}, '${h.kod}')">${h.ad}</div>`).join('')}</div>`;document.getElementById('ct').innerHTML=x}catch(e){console.error(e)}}

async function shSD(id, kod){clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';try{const[hl,dr,sf]=await Promise.all([fetch('/api/samair').then(r=>r.json()),fetch('/api/samair/'+id+'/durak').then(r=>r.json()),fetch('/api/samair/'+id+'/sefer').then(r=>r.json())]);const h=(hl||[]).find(x=>x.id==id)||{},da=Array.isArray(dr)?dr:[],seferler=sf.data||[],last_up=sf.last_update||'';let x=`<button class="bk" onclick="shS()">← Samair</button><div style="font-weight:700;margin-bottom:10px;font-size:1rem">✈️ ${h.ad||''}</div>`;x+=`<div class="ig"><div class="ic"><div class="v">${da.length}</div><div class="l">Durak</div></div><div class="ic"><div class="v" id="acnt">0</div><div class="l">Araç</div></div></div>`;x+=`<div class="araclar"><div class="t">✈️ Canlı Araçlar</div><div id="vlist">Yükleniyor...</div></div>`;x+=`<div class="tel">📞 Bilgi: <a href="tel:03624311012">0362 431 10 12</a></div>`;if(seferler.length){x+=`<div class="sec">✈️ Uçuş & Servis Saatleri</div>${last_up?`<div style="text-align:center;font-size:0.6rem;color:#888;margin-bottom:5px">Son Güncelleme: ${last_up}</div>`:''}`;let cDay = "";seferler.forEach(s=>{if(s.gun_format !== cDay) { x += `<div class="dhead">${s.gun_format}</div>`; cDay = s.gun_format; }x+=`<div class="sfr"><div class="st">${s.saat} → ${s.varis}</div><div class="fr">${s.firma} - ${s.ucak_saat}</div></div>`;});}else{x+=`<div class="no-data"><div class="icon">✈️</div>Uçuş bilgisi bekleniyor...</div>`}if(da.length){x+=`<div class="sec">📍 Duraklar (${da.length})</div>`;const co=[];da.forEach((d,i)=>{x+=`<div class="drk" onclick="map.setView([${d.lat},${d.lon}],16)"><span class="no" style="background:#8e44ad">${i+1}</span><span class="inf"><span class="ad">${d.ad}</span><span class="fyt">₺${d.fiyat||'?'}</span></span></div>`;if(d.lat>0&&d.lon>0){co.push([d.lat,d.lon]);M['s'+i]=L.marker([d.lat,d.lon],{icon:dI(i+1,'#8e44ad')}).addTo(map)}});if(co.length)map.fitBounds(co,{padding:[40,40]})}document.getElementById('ct').innerHTML=x;upV(kod,'#8e44ad'); liveT=setInterval(()=>upV(kod,'#8e44ad'),5000);}catch(e){console.error(e)}}
window.shSD=shSD;

function showDisclaimer(){
    if(!localStorage.getItem('disclaimerShown')){
        document.getElementById('infoModal').style.display='flex';
        localStorage.setItem('disclaimerShown', 'true');
    }
}

init();
showDisclaimer();
</script>
</body>
</html>'''

# --- WEB SUNUCUSU ---

def create_app(db, col):
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError:
        log.error("Lütfen: pip install fastapi uvicorn")
        return None

    app = FastAPI(title="Samsun Transit")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    if os.path.exists("static"): app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def home(): return HTML

    @app.get("/api/yakin")
    async def api_yakin(lat: float, lon: float):
        return JSONResponse(col.yakindaki_duraklar(lat, lon))

    @app.get("/api/durak_panel/{kod}")
    async def api_durak_panel(kod: str):
        return JSONResponse(col.durak_bilgi(kod))

    @app.get("/api/rota")
    async def api_rota(lat1: float, lon1: float, lat2: float, lon2: float):
        return JSONResponse(col.yol_tarifi(lat1, lon1, lat2, lon2))

    # --- Standart API Endpointleri ---
    @app.get("/api/hat")
    async def api_hat(): return JSONResponse(db.get("SELECT * FROM hat ORDER BY kat, name"))
    
    @app.get("/api/hat/info/{code:path}")
    async def api_hat_one(code: str):
        c = urllib.parse.unquote(code).strip()
        res = db.one("SELECT * FROM hat WHERE code=?", (c,))
        if not res: res = db.one("SELECT * FROM hat WHERE code LIKE ?", (c+'%',))
        return JSONResponse(res or {})
    
    @app.get("/api/hat/durak/{code:path}")
    async def api_durak(code: str):
        c = urllib.parse.unquote(code).strip()
        res = db.get("SELECT * FROM hat_durak WHERE hat=? ORDER BY sira", (c,))
        if not res: res = db.get("SELECT * FROM hat_durak WHERE hat LIKE ? ORDER BY sira", (c+'%',))
        
        # Tramvay düzeltmelerini uygula (DB'ye dokunmadan)
        if "TRAMVAY" in c.upper() and hasattr(col, 'tram_corrections'):
            try:
                # Convert sqlite3.Row to dict to modify
                res_mod = [dict(r) for r in res]
                for r in res_mod:
                    # Normalize: "Örnek Sanayi İstasyonu" -> "örnek sanayi"
                    norm = r['ad'].replace(" İstasyonu", "").strip().lower()
                    if norm in col.tram_corrections:
                        lat, lon = col.tram_corrections[norm]
                        r['lat'] = lat
                        r['lon'] = lon
                return JSONResponse(res_mod)
            except Exception as e:
                log.error(f"Tramvay düzeltme hatası: {e}")
                
        return JSONResponse(res)
    
    @app.get("/api/hat/sefer/{code:path}")
    async def api_sefer(code: str):
        c = urllib.parse.unquote(code).strip()
        res = db.get("SELECT * FROM sefer WHERE hat=?", (c,))
        if not res: res = db.get("SELECT * FROM sefer WHERE hat LIKE ?", (c+'%',))
        return JSONResponse(res)
    
    @app.get("/api/hat/fiyat/{code:path}")
    async def api_fiyat(code: str):
        """Hat fiyatını getir - hat_code ve hat_adi ile çoklu eşleştirme"""
        c = urllib.parse.unquote(code).strip()
        
        # 1. Önce hat_code ile direkt ara
        res = db.one("SELECT * FROM fiyat WHERE hat_code=?", (c,))
        
        # 2. Hat adıyla ara
        if not res:
            hat = db.one("SELECT name FROM hat WHERE code=?", (c,))
            if hat:
                res = db.one("SELECT * FROM fiyat WHERE hat_adi=?", (hat['name'],))
        
        # 3. İlk kelime (hat kodu) ile fuzzy ara
        if not res:
            ilk = c.split()[0] if c.split() else c
            res = db.one("SELECT * FROM fiyat WHERE hat_adi LIKE ?", (f'{ilk}%',))
        
        # 4. LIKE ile kısmi eşleşme
        if not res:
            res = db.one("SELECT * FROM fiyat WHERE hat_adi LIKE ?", (f'%{c}%',))
        
        return JSONResponse(res or {"tam_fiyat": 17.0, "indirimli_fiyat": 12.0, "aktarma1": "Ücretsiz"})
    
    @app.get("/api/hat/arac/{code:path}")
    async def api_arac(code: str):
        c = urllib.parse.unquote(code).strip()
        
        # Önce Samair hattı mı kontrol et
        samair_hat = None
        for hid, hat_info in SAMAIR_HATLAR.items():
            for tam_ad in hat_info['asis']:
                if c in tam_ad or tam_ad in c:
                    samair_hat = tam_ad
                    break
            if samair_hat:
                break
        
        if samair_hat:
            # Samair hattıysa tüm varyantlardan araç bul
            araclar = col.canli(samair_hat)
            duraklar = db.get("SELECT * FROM samair_durak WHERE hat IN (SELECT id FROM samair WHERE kod LIKE ?) ORDER BY sira", (f'%{c}%',))
        else:
            # Normal hat
            araclar = col.canli(c)
            duraklar = db.get("SELECT * FROM hat_durak WHERE hat LIKE ? ORDER BY sira", (c+'%',))
        
        for a in araclar: 
            a['yakin'] = col.yakin_durak(a, duraklar)
        return JSONResponse(araclar)
    
    @app.get("/api/hat/esles/{code:path}")
    async def api_esles(code: str): return JSONResponse({"code": col.esles(urllib.parse.unquote(code))})
    
    @app.get("/api/odak")
    async def api_odak(): return JSONResponse(db.get("SELECT * FROM odak ORDER BY kod"))
    
    @app.get("/api/odak/{id}/durak")
    async def api_odak_d(id: str): return JSONResponse(db.get("SELECT * FROM odak_durak WHERE hat=? ORDER BY sira", (id,)))
    
    @app.get("/api/samair")
    async def api_samair(): return JSONResponse(db.get("SELECT * FROM samair ORDER BY id"))
    
    @app.get("/api/samair/{id}/durak")
    async def api_samair_durak(id: int): return JSONResponse(db.get("SELECT * FROM samair_durak WHERE hat=? ORDER BY sira", (id,)))
    
    @app.get("/api/samair/{id}/sefer")
    async def api_samair_sefer(id: int):
        count = db.one("SELECT COUNT(*) c FROM samair_sefer WHERE hat=?", (id,))['c']
        col.samair_seferler_guncelle(force=(count==0))
        rows = db.get("SELECT * FROM samair_sefer WHERE hat=? ORDER BY tarih, saat", (id,))
        return JSONResponse({"data": rows, "last_update": db.get_meta('samair_last_update_str')})

    return app

def main():
    import sys
    # Windows terminal encoding fix
    if sys.platform == 'win32':
        try: sys.stdout.reconfigure(encoding='utf-8')
        except: pass
    
    print("=" * 55)
    print("  SAMSUN TRANSIT - SUPER APP v25 (MASTER)")
    print("=" * 55)
    
    leaflet_indir()
    db = Database()
    yeni_db = db.connect()
    col = Collector(db, Http())

    log.info("=" * 50)
    col.veri_cek()
    
    # Samair seferlerini açılışta bir kez kontrol et
    # Samair seferlerini açılışta bir kez kontrol et
    col.samair_seferler_guncelle()

    app = create_app(db, col)
    if not app: return

    # Saatlik Samair güncelleme thread'i
    import threading
    def samair_hourly_update():
        import time as t
        while True:
            t.sleep(3600)  # 1 saat bekle
            try:
                log.info("⏰ Samair seferleri güncelleniyor (saatlik)...")
                col.samair_seferler_guncelle(force=True)
            except Exception as e:
                log.error(f"Samair güncelleme hatası: {e}")
    
    update_thread = threading.Thread(target=samair_hourly_update, daemon=True)
    update_thread.start()
    log.info("✓ Samair otomatik güncelleme aktif (her saat)")

    log.info("=" * 50)
    log.info("  Web: http://localhost:8000")
    log.info("=" * 50)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

if __name__ == "__main__":
    main()