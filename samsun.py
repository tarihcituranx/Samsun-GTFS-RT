#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚌 SAMSUN TRANSIT - SUPER APP v25 (MASTER)
- Yol Tarifi Modülü (Konumdan Hedefe Hat Bulma)
- Samulaş Web Fiyat Çekme (samulas.com.tr)
- Samair Canlı Takip ve Uçuş Bilgileri Entegre
- T hatları = Otobüs (Tramvay Değil!)
- Odak Turistik Hatlar Entegrasyonu
"""

import asyncio
import httpx
import os
import sqlite3
import unicodedata
import threading
import time
import json
import logging
import math
import requests
import urllib3
import re
import urllib.parse
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, date, timedelta
from fastapi import FastAPI, BackgroundTasks, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from google.transit import gtfs_realtime_pb2

# LOGGING AYARLARI
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger("SamsunTransit")

# GLOBAL GTFS-RT FEED
import threading as _gtfs_threading
gtfs_feed = gtfs_realtime_pb2.FeedMessage()
_gtfs_feed_lock = _gtfs_threading.Lock()  # Thread-safe GTFS-RT erişimi

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Başlatma zamanı (uptime hesaplama)
_START_TIME = time.time()

# On-Demand GTFS-RT: Sadece aktif olarak izlenen hatları sorgula
_active_lines = {}  # {hat_code: son_istek_zamani}
_active_lines_lock = threading.Lock()
_ACTIVE_TTL = 300  # 5 dakika boyunca aktif say

# Admin runtime config (DB'den yüklenir, restart gerektirmez)
_admin_config = {
    'gtfs_rt_enabled': True,
    'gtfs_rt_interval': 60,     # saniye
    'gtfs_rt_mode': 'ondemand', # 'ondemand' veya 'all'
    'gtfs_rt_max_lines': 10,    # 'all' modunda max hat sayısı
    'samair_interval': 7200,    # 2 saat
}
_api_stats = {'asis_calls': 0, 'ybs_calls': 0, 'last_reset': time.time()}

DB = "samsun_v26.db"
ASIS = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
YBS = "https://ybs.samsun.bel.tr/service"
SAMULAS_URL = "https://samulas.com.tr"
GUNCELLEME_GUN = 7

# Fiyat hesaplama sabitleri (Samulaş web scraping'den gelen tam fiyattan indirimli ve aktarma hesaplama)
INDIRIMLI_ORAN = 0.70      # İndirimli = Tam × %70
AKTARMA_ORAN = 0.375       # Aktarma = Tam × %37.5 (maks 30 TL altı hatlar)

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
    # Samair Hat ID Mapping (H1-H5 → YBS hatid)
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
    },
    5: {
        'ad': 'H5 HAVZA - HAVALİMANI',
        'asis': ['H5 HAVZA - HAVALİMANI', 'H5 HAVALİMANI - HAVZA'],
        'ybs_hatid': []  # TODO: hat_kesi_sorgu.py çıktısından doldur
    }
}

# --- GTFS YARDIMCI FONKSİYONLARI ---

_ASCII_MAP = str.maketrans({
    'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's',
    'Ç': 'C', 'ç': 'c', 'Ğ': 'G', 'ğ': 'g',
    'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o',
})

def sanitize_id(text):
    """ID alanları için: Türkçe karakterleri ASCII'ye çevir, boşluk/özel karakter temizle."""
    if not text: return str(text) if text is not None else ''
    t = str(text).translate(_ASCII_MAP)
    t = re.sub(r'[^A-Za-z0-9_\-./]', '_', t)
    t = re.sub(r'_+', '_', t).strip('_')
    return t

def _tr_lower(text):
    """Türkçe kurallarına uygun küçük harf: I→ı, İ→i, diğerleri standart."""
    result = []
    for ch in text:
        if ch == 'I': result.append('ı')
        elif ch == 'İ': result.append('i')
        else: result.append(ch.lower())
    return ''.join(result)

def _tr_upper_first(ch):
    """Tek karakter Türkçe büyük harf: i→İ, ı→I."""
    if ch == 'i': return 'İ'
    elif ch == 'ı': return 'I'
    else: return ch.upper()

def title_case_tr(text):
    """Türkçe uyumlu Title Case ('SOĞUKSU' → 'Soğuksu')."""
    if not text: return text
    words = str(text).split()
    result = []
    small_words = {'ve', 'ile', 'ya', 'da', 'de', 'den', 'dan', 'ne', 'bir'}
    for i, word in enumerate(words):
        if word in ('-', '–'):
            result.append(word); continue
        if word.isdigit():
            result.append(word); continue
        parts = []
        for part in re.split(r'(\(|\))', word):
            if part in ('(', ')'): parts.append(part); continue
            if not part: continue
            low = _tr_lower(part)
            if i > 0 and low in small_words:
                parts.append(low)
            else:
                first = _tr_upper_first(low[0])
                parts.append(first + low[1:])
        result.append(''.join(parts))
    return ' '.join(result)

def extract_short_name(code, short_name):
    """route_short_name max 12 karakter. Hat numarasını çıkarır.
    Öncelik: code'dan hat numarası > uygun short_name > fallback.
    Samulaş V1 bazen short_line_name olarak dahili ID (402, 416) döner;
    bunlar kullanılmamalı."""
    code_str = str(code).strip() if code else ''
    short_str = str(short_name).strip() if short_name else ''

    # 1) code'dan hat numarasını çıkarmayı dene
    #    Önce harf+sayı: R2, R11B, H1, G3, E6 vb.
    m_code = re.match(r'^([A-Za-zÇçĞğÖöÜüŞşİı]\d+[A-Za-z]?)', code_str)
    if m_code and len(m_code.group(1)) <= 12:
        return m_code.group(1).upper().translate(_ASCII_MAP)

    #    Sonra sayı+harf: 13, 15, 20, 24A, 12/17 vb.
    m_num = re.match(r'^(\d+(?:/\d+)?[A-Za-z]?)', code_str)
    if m_num and len(m_num.group(1)) <= 12:
        extracted = m_num.group(1)
        # 3 haneli+ numara code'un bir parçası mı yoksa tümü mü?
        if int(re.match(r'^(\d+)', extracted).group(1)) < 100:
            return extracted

    # 2) short_name akıllıca kullan —  sadece gerçek rota adıysa
    if short_str:
        # Harf+sayı pattern (R2, E6, H1, TRAM vb.) → kullan
        m_short_alpha = re.match(r'^([A-Za-z]\d+[A-Za-z]?)', short_str)
        if m_short_alpha and len(m_short_alpha.group(1)) <= 12:
            return m_short_alpha.group(1).upper().translate(_ASCII_MAP)
        # Küçük sayı (<100): gerçek hat numarası olabilir
        m_short_num = re.match(r'^(\d+)', short_str)
        if m_short_num and int(m_short_num.group(1)) < 100:
            return short_str[:12]

    # 3) Özel hat isimleri
    code_ascii = code_str.upper().translate(_ASCII_MAP)
    combined = f"{code_ascii} {short_str.upper().translate(_ASCII_MAP)}"

    if 'TELEFERIK' in combined: return 'TLFRK'
    if combined.startswith('SAMULAS EKSPRES 302'): return 'E1'
    m_sn = re.search(r'SAMSUNUM\s*(\d+)', combined)
    if m_sn: return f'SN{m_sn.group(1)}'
    if 'ALTINKAYA' in combined: return 'AK55'
    if 'TRAMVAY' in combined: return 'TRAM'

    # İlçe hatları
    ilce = [
        (r'SAMSUN\s*-\s*TERME', 'SAM-TRM'), (r'TERME\s*-\s*SAMSUN', 'TRM-SAM'),
        (r'SAMSUN\s*-\s*CARSAMBA', 'SAM-CRS'), (r'CARSAMBA\s*-\s*SAMSUN', 'CRS-SAM'),
        (r'SAMSUN\s*-\s*BAFRA', 'SAM-BFR'), (r'BAFRA\s*-\s*SAMSUN', 'BFR-SAM'),
        (r'SAMSUN\s*-\s*HAVZA', 'SAM-HVZ'), (r'HAVZA\s*-\s*SAMSUN', 'HVZ-SAM'),
    ]
    for pattern, short in ilce:
        if re.search(pattern, combined): return short

    # 4) EKSPRES kısa adı: "SAMULAŞ EKSPRES 6-GİDİŞ" → E6
    m_eks = re.search(r'EKSPRES\s*(\d+)', combined)
    if m_eks: return f'E{m_eks.group(1)}'
    if 'EKSPRES' in combined:
        m_eks2 = re.search(r'EKSPRES\s*([A-Z])', combined)
        return f'E{m_eks2.group(1)}' if m_eks2 else 'EXP'

    # 5) Fallback: code'un ilk 12 karakteri
    fallback = code_str.split(' ')[0] if ' ' in code_str else code_str
    return fallback[:12].rstrip(' -')

def clean_long_name(gtfs_short, long_name, db_short=''):
    """route_long_name başından short_name prefix'ini kaldır."""
    if not long_name: return ''
    ln = str(long_name).strip()
    for prefix in [gtfs_short, db_short]:
        if not prefix: continue
        pf = str(prefix).strip()
        if ln == pf: continue
        if ln.startswith(pf + ' '):
            cleaned = ln[len(pf):].strip().lstrip('- ').strip()
            if cleaned: return cleaned
    m = re.match(r'^(\d+[/]?[A-Za-z]?|[A-Za-z]\d+[A-Za-z]?)\s+(.+)', ln)
    if m:
        code = m.group(1)
        if code == gtfs_short or code == db_short: return m.group(2).strip()
    return ln

def gun_to_service(gun_str):
    """Gün stringini GTFS service_id'ye çevir."""
    g = str(gun_str).lower()
    if 'hafta' in g: return '1'
    elif 'cumartesi' in g: return '2'
    elif 'pazar' in g: return '3'
    return '4'

def gtfs_route_type(tip):
    """Hat tipini GTFS route_type'a çevir."""
    return {'otobus': '3', 'tramvay': '0', 'ring': '3', 'ekspres': '3',
            'havalimani': '3', 'ilce': '3', 'teleferik': '6', 'tekne': '4'}.get(tip, '3')

def gtfs_route_color(tip):
    """Hat tipine göre GTFS route_color."""
    return {'otobus': '1877F2', 'tramvay': 'E67E22', 'ring': 'F39C12', 'ekspres': '9B59B6',
            'havalimani': 'E74C3C', 'ilce': '1ABC9C', 'teleferik': 'E91E63', 'tekne': '3498DB'}.get(tip, '1877F2')

# --- YARDIMCI FONKSİYONLAR ---

def parse_int(val):
    """Güvenli integer dönüşümü (API parametreleri için)"""
    if val is None: 
        return None
    try: 
        return int(val)
    except: 
        return None

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
        _retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        
        self.s = requests.Session()
        self.s.mount("http://", HTTPAdapter(max_retries=_retry))
        self.s.mount("https://", HTTPAdapter(max_retries=_retry))
        self.s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://samair.samsun.bel.tr/'
        })
        
        # ============================================================
        # 🌐 TÜRK PROXY — Credential'lar ENV VAR'dan okunur (GitHub'a sızmaz!)
        # Render.com Dashboard > Environment > Aşağıdakileri ekle:
        #   PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS
        # ============================================================
        proxy_host = os.environ.get('PROXY_HOST')
        proxy_port = os.environ.get('PROXY_PORT')
        proxy_user = os.environ.get('PROXY_USER')
        proxy_pass = os.environ.get('PROXY_PASS')
        
        if proxy_host and proxy_port and proxy_user:
            proxy_url = f"http://{proxy_user}:{proxy_pass or ''}@{proxy_host}:{proxy_port}"
            self.s.proxies = {"http": proxy_url, "https": proxy_url}
            log.info(f"🌐 Proxy aktif: {proxy_host}:{proxy_port} (Tüm API istekleri)")
        else:
            log.warning("⚠️ Proxy ayarlanmamış! PROXY_HOST/PORT/USER env var eksik. Direkt bağlantı kullanılacak.")
        
        self.session = self.s  # Alias (proxy endpoint'leri self.session kullanıyor)
        
        self._tok = {}
        self._tok_lock = threading.Lock()
        self._cache = {}

    def asis(self, ep, **p):
        """
        ASIS API çağrısı - Swagger spesifikasyonuna uyumlu
        self.s session'ını kullanır (proxy, retry, header ayarları miras alınır)
        """
        import urllib.parse
        
        try:
            url = f"{ASIS}/{ep}"
            params = {}
            
            for k, v in p.items():
                if v is None: continue
                if k in ['stopId', 'stationId']:
                    v_int = parse_int(v)
                    if v_int is not None:
                        params[k] = v_int
                    else:
                        continue
                else:
                    # String parametreler için temizle
                    params[k] = str(v).strip()
            
            log.debug(f"→ ASIS {ep} | Params: {params}")
            
            # Türkçe karakterleri doğru encode et
            query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            full_url = f"{url}?{query_string}" if params else url
            
            # self.s kullan — proxy config, retry config hepsi burada
            r = self.s.get(full_url, timeout=12)
            
            if r.ok:
                d = r.json()
                result = d.get('data', []) if isinstance(d, dict) else d
                return result
            else:
                log.error(f"✗ ASIS {ep} | HTTP {r.status_code}")
                    
        except requests.exceptions.Timeout:
            log.error(f"⏱ ASIS {ep} | Timeout")
        except requests.exceptions.ConnectionError as e:
            log.error(f"🔌 ASIS {ep} | Bağlantı hatası: {e}")
        except json.JSONDecodeError as e:
            log.error(f"📄 ASIS {ep} | JSON parse hatası: {e}")
        except Exception as e:
            log.error(f"❌ ASIS {ep} | Genel hata: {e}")
        
        return []

    def ybs_token(self):
        with self._tok_lock:
            if 'ybs' in self._tok and time.time() - self._tok['ybs']['t'] < 200:
                return self._tok['ybs']['v']
        try:
            r = self.session.get(f"{YBS}/?method=getGuestToken", timeout=10)
            if r.ok:
                tok = r.json().get('token')
                with self._tok_lock:
                    self._tok['ybs'] = {'v': tok, 't': time.time()}
                return tok
        except Exception as e:
            log.warning(f"YBS token hatası: {type(e).__name__}: {e}")
        return None

    def ybs(self, method, submethod=None, **kw):
        tok = self.ybs_token()
        if not tok: return []
        p = {'method': method, 'token': tok}
        if submethod: p['submethod'] = submethod
        p.update(kw)
        try:
            r = self.session.get(f"{YBS}/", params=p, timeout=30)
            if r.ok:
                res = r.json()
                if isinstance(res, dict) and res.get('status') == 'SUCCESS':
                    return res.get('data', [])
                return res.get('data', [])
        except Exception as e:
            log.warning(f"YBS {method}/{submethod} hatası: {type(e).__name__}: {e}")
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
            CREATE TABLE IF NOT EXISTS hat(
                code TEXT PRIMARY KEY, name TEXT, tip TEXT, kat TEXT,
                alias TEXT DEFAULT '', short_name TEXT DEFAULT '',
                gtfs_route_id TEXT DEFAULT '',
                gtfs_route_short_name TEXT DEFAULT '',
                gtfs_route_long_name TEXT DEFAULT '',
                gtfs_route_type TEXT DEFAULT '3',
                gtfs_route_color TEXT DEFAULT '1877F2'
            );
            CREATE TABLE IF NOT EXISTS durak(
                id TEXT PRIMARY KEY, kod TEXT, ad TEXT, lat REAL, lon REAL,
                gtfs_stop_id TEXT DEFAULT '',
                gtfs_stop_name TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS hat_durak(id INTEGER PRIMARY KEY, hat TEXT, durak_id TEXT, ad TEXT, sira INT, lat REAL, lon REAL);
            CREATE TABLE IF NOT EXISTS sefer(
                id INTEGER PRIMARY KEY, hat TEXT, saat TEXT, yon TEXT, gun TEXT,
                gtfs_trip_id TEXT DEFAULT '',
                gtfs_route_id TEXT DEFAULT '',
                gtfs_service_id TEXT DEFAULT '4'
            );
            CREATE TABLE IF NOT EXISTS odak(id TEXT PRIMARY KEY, ad TEXT, kod TEXT, gunler TEXT);
            CREATE TABLE IF NOT EXISTS odak_durak(id INTEGER PRIMARY KEY, hat TEXT, ad TEXT, kod TEXT, sira INT, lat REAL, lon REAL, fiyat TEXT, fiyat_ogr TEXT);
            CREATE TABLE IF NOT EXISTS samair(id INTEGER PRIMARY KEY, ad TEXT, kod TEXT);
            CREATE TABLE IF NOT EXISTS samair_durak(id INTEGER PRIMARY KEY, hat INTEGER, ad TEXT, kod TEXT, sira INT, lat REAL, lon REAL, fiyat TEXT);
            CREATE TABLE IF NOT EXISTS samair_sefer(id INTEGER PRIMARY KEY, hat INT, saat TEXT, varis TEXT, firma TEXT, ucak_saat TEXT, tarih TEXT, gun_format TEXT);
            CREATE TABLE IF NOT EXISTS fiyat(
                id INTEGER PRIMARY KEY,
                kaynak TEXT, hat_adi TEXT, hat_code TEXT DEFAULT '',
                tam_fiyat REAL DEFAULT 0, indirimli_fiyat REAL DEFAULT 0,
                ogrenci_fiyat REAL DEFAULT 0, aktarma1 TEXT, aktarma2 REAL DEFAULT 0,
                link TEXT, guncelleme TEXT
            );
            CREATE TABLE IF NOT EXISTS hat_yon(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hat TEXT NOT NULL, yon_id TEXT NOT NULL, yon_adi TEXT,
                UNIQUE(hat, yon_id)
            );
            CREATE TABLE IF NOT EXISTS gtfs_shape(
                shape_id TEXT NOT NULL,
                shape_pt_lat REAL NOT NULL, shape_pt_lon REAL NOT NULL,
                shape_pt_sequence INTEGER NOT NULL, shape_dist_traveled REAL,
                PRIMARY KEY (shape_id, shape_pt_sequence)
            );
            CREATE TABLE IF NOT EXISTS app_config(
                key TEXT PRIMARY KEY, value TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_hd ON hat_durak(hat);
            CREATE INDEX IF NOT EXISTS idx_sf ON sefer(hat);
            CREATE INDEX IF NOT EXISTS idx_sd ON samair_durak(hat);
            CREATE INDEX IF NOT EXISTS idx_dk_latlon ON durak(lat, lon);
            CREATE INDEX IF NOT EXISTS idx_fiyat_kaynak ON fiyat(kaynak);
            CREATE INDEX IF NOT EXISTS idx_hat_yon ON hat_yon(hat);
            CREATE INDEX IF NOT EXISTS idx_shape ON gtfs_shape(shape_id);
        """)
        # Mevcut DB'ler için GTFS sütunlarını ekle (ALTER TABLE migration)
        _migrations = [
            ('hat', 'gtfs_route_id', "TEXT DEFAULT ''"),
            ('hat', 'gtfs_route_short_name', "TEXT DEFAULT ''"),
            ('hat', 'gtfs_route_long_name', "TEXT DEFAULT ''"),
            ('hat', 'gtfs_route_type', "TEXT DEFAULT '3'"),
            ('hat', 'gtfs_route_color', "TEXT DEFAULT '1877F2'"),
            ('durak', 'gtfs_stop_id', "TEXT DEFAULT ''"),
            ('durak', 'gtfs_stop_name', "TEXT DEFAULT ''"),
            ('sefer', 'gtfs_trip_id', "TEXT DEFAULT ''"),
            ('sefer', 'gtfs_route_id', "TEXT DEFAULT ''"),
            ('sefer', 'gtfs_service_id', "TEXT DEFAULT '4'"),
        ]
        for tbl, col, dtype in _migrations:
            try:
                self.conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {dtype}")
            except Exception:
                pass  # Sütun zaten var
        self.conn.commit()

    def _load_durak_coords(self):
        try:
            for r in self.get("SELECT kod, lat, lon FROM durak WHERE kod != ''"):
                if r['kod'] and r['lat'] and r['lon']: self.durak_coords[r['kod']] = (r['lat'], r['lon'])
        except Exception as e:
            log.warning(f"Durak koordinat yükleme hatası: {e}")

    def get_meta(self, key):
        r = self.one("SELECT value FROM meta WHERE key=?", (key,))
        return r['value'] if r else None

    def set_meta(self, key, value):
        self.ex("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, value))

    def guncelleme_gerekli(self):
        if self.cnt('hat') == 0: return True
        son = self.get_meta('son_guncelleme')
        if not son: return True
        try:
            return (datetime.now() - datetime.strptime(son, "%Y-%m-%d")).days >= GUNCELLEME_GUN
        except Exception as e:
            log.warning(f"Güncelleme tarihi parse hatası: {e}")
            return True

    def samair_guncelleme_gerekli(self):
        if self.cnt('samair_sefer') == 0: return True
        son = self.get_meta('samair_last_update')
        if not son: return True
        try:
            return (datetime.now() - datetime.fromtimestamp(float(son))).total_seconds() > 3600
        except Exception as e:
            log.warning(f"Samair güncelleme tarihi parse hatası: {e}")
            return True

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
        try:
            return self.one(f"SELECT COUNT(*) c FROM {t}")['c']
        except Exception as e:
            log.warning(f"Tablo sayım hatası ({t}): {e}")
            return 0

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
        
        # 2. Odak turistik hatlar (G ile başlayanlar veya isimde Odak geçenler)
        if c.startswith('G_') or c.startswith('G1') or c.startswith('G2') or c.startswith('G3') or c.startswith('G4') or 'ODAK' in n: return 'odak'
        
        # 3. Yeni Kategoriler (Analiz Sonucu)
        if 'TRAMVAY' in c or 'TRAMVAY' in n: return 'tramvay'
        if 'TELEFERİK' in c or 'TELEFERİK' in n: return 'teleferik'
        if 'SAMSUNUM' in c or 'SAMSUNUM' in n or 'ALTINKAYA' in n or any(x in n for x in ['BANDIRMA', 'VAPUR']) or ('FERİBOT' in n and 'TELEFERİK' not in n): return 'tekne'
        # Havalimanı hatları
        if c.startswith('H') and len(c) > 1 and c[1].isdigit(): return 'havalimani'
        
        # Ekspres hatları
        if 'EKSPRES' in c or (c.startswith('E') and len(c) > 1 and c[1].isdigit()): return 'ekspres'
        # İlçe hatları
        if any(x in n for x in ['TERME','ÇARŞAMBA','BAFRA','HAVZA','LADİK','KAVAK','ASARCIK','SALIPAZARI','TEKKEKÖY', 'ALAÇAM', 'AYVACIK', 'VEZİRKÖPRÜ', 'YAKAKENT', '19 MAYIS', 'ONDOKUZMAYIS']): return 'ilce'
        
        return 'otobus'

    def veri_cek(self):
        if not self.db.guncelleme_gerekli():
            log.info("📦 Ana veriler güncel.")
            self._recompute_gtfs_columns()  # GTFS short name'leri her zaman güncel tut
            self._inject_fixed_prices()
            self._fix_tram_schedules()
            self._fix_stop_coordinates()
            self._inject_boat_teleferik_schedules()
            
            # GTFS Shapes kontrol et
            if self.db.cnt('gtfs_shape') == 0:
                log.info("📐 GTFS Shapes eksik, oluşturuluyor...")
                self.gtfs_generate_shapes()
            
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
        
        # YENİ: GTFS Shapes oluştur
        self.gtfs_generate_shapes()
        
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
                res = self.http.session.get(f"{SAMULAS_URL}/otobusler?page={page}", headers=headers, timeout=15)
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
                        r = self.http.session.get(url, headers=headers, timeout=10)
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
                        
                        # İndirimli fiyat hesapla (dinamik oran: ~%70 tam fiyat)
                        indirimli, aktarma1, aktarma2 = 0, "Ücretsiz", 0
                        if tam_fiyat > 0:
                            indirimli = round(tam_fiyat * INDIRIMLI_ORAN, 2)
                            aktarma2 = round(tam_fiyat * AKTARMA_ORAN, 2) if tam_fiyat <= 30 else 0
                        
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
                            toplam += 1  # Counter artırılmalı — önceden eksikti
                            self.db.ex("INSERT INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,aktarma1,aktarma2,link,guncelleme) VALUES(?,?,?,?,?,?,?,?,?)",
                                      ('samulas', name, hat_code, tam_fiyat, indirimli, aktarma1, aktarma2, url, now))
        
                    except: pass # for url in links
            except: pass # for page in range
        
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
        # (YENİ) 3. Samulaş V1 API'den Short Name ve İstasyon Çekimi (GTFS Zenginleştirme)
        try:
            r = requests.get("https://samulas.com.tr/api/v1/lines/list?page=1&limit=500", timeout=10)
            if r.ok:
                v1_data = r.json().get('data', {}).get('data', [])
                basarili_short = 0
                for d in v1_data:
                    c = str(d.get('line_code', '')).strip()
                    s = str(d.get('short_line_name', '')).strip()
                    if c and s:
                        self.db.ex("UPDATE hat SET short_name=? WHERE code=?", (s, c))
                        basarili_short += 1
                
                # Kalan (V1'de olmayan) hatlar için Regex Fallback
                self.db.ex("UPDATE hat SET short_name = SUBSTR(code, 1, INSTR(code, ' ') - 1) WHERE short_name = '' AND code LIKE '% %' AND (code LIKE 'H%' OR code LIKE 'R%' OR code LIKE 'E%')")
                self.db.ex("UPDATE hat SET short_name = code WHERE short_name = ''")
                
                log.info(f"      ✅ Yeni Samulaş V1'den {basarili_short} short_name çekildi. Kalanlar otomatik atandı.")
        except Exception as e:
            log.warning(f"      ⚠️ Samulaş V1 entegre edilemedi: {e}")
        
        # 4. GTFS sütunlarını hesapla ve güncelle (Tüm hatlar için)
        all_hatlar = self.db.get("SELECT code, name, tip, kat, short_name FROM hat")
        for h in all_hatlar:
            g_route_id = sanitize_id(h['code'])
            g_short = extract_short_name(h['code'], h['short_name'])
            db_short = str(h['short_name']).strip() if h['short_name'] else ''
            raw_long = str(h['name']).strip() if h['name'] else h['code']
            g_long = title_case_tr(clean_long_name(g_short, raw_long, db_short)).replace(',', ' -')
            # KAT kullanılmalı (tip="gidis/donus", kat="otobus/ekspres/tramvay"...)
            g_type = gtfs_route_type(h['kat'])
            g_color = gtfs_route_color(h['kat'])
            self.db.ex(
                "UPDATE hat SET gtfs_route_id=?, gtfs_route_short_name=?, gtfs_route_long_name=?, gtfs_route_type=?, gtfs_route_color=? WHERE code=?",
                (g_route_id, g_short, g_long, g_type, g_color, h['code'])
            )
        log.info(f"      ✅ {len(all_hatlar)} hat için GTFS alanları hesaplandı")

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
                    g_stop_id = sanitize_id(sid)
                    g_stop_name = title_case_tr(ad.replace(',', ' '))
                    rows.append((sid, kod, ad, lat, lon, g_stop_id, g_stop_name))
                    if kod: self.db.durak_coords[kod] = (lat, lon)
        if rows: self.db.exm("INSERT OR REPLACE INTO durak(id,kod,ad,lat,lon,gtfs_stop_id,gtfs_stop_name) VALUES(?,?,?,?,?,?,?)", rows)
        log.info(f"      ✅ {len(rows)} durak yüklendi (GTFS alanları dahil)")

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
            g_route_id = sanitize_id(code)
            for gun, t in [('hi', hi), ('hs', hs)]:
                service_id = gun_to_service(gun)
                for d in self.http.asis('Schedules', lineCode=code, scheduleDate=t.strftime("%Y-%m-%d")):
                    # API 'saat' döndürür — 'time' alanı yoktur
                    saat = d.get('saat', '')
                    # yon: API "G"/"D" döndürür — okunabilir forma çevir
                    yon_raw = d.get('yon', '')
                    yon = {'G': 'Gidiş', 'D': 'Dönüş'}.get(yon_raw, yon_raw)
                    if saat:
                        self.db.ex(
                            "INSERT INTO sefer(hat,saat,yon,gun,gtfs_route_id,gtfs_service_id) VALUES(?,?,?,?,?,?)",
                            (code, saat, yon, gun, g_route_id, service_id)
                        )
                        # gtfs_trip_id için son eklenen id'yi al
                        last_id = self.db.one("SELECT last_insert_rowid() as lid")
                        if last_id:
                            tid = sanitize_id(f"T_{last_id['lid']}")
                            self.db.ex("UPDATE sefer SET gtfs_trip_id=? WHERE id=?", (tid, last_id['lid']))
            if (i+1)%20==0: log.info(f"      {i+1}/{len(hatlar)}...")
            time.sleep(0.02)
        log.info(f"      ✅ Seferler yüklendi (GTFS alanları dahil)")

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
            
            # Durakları manuel ekle (ASIS'te hatalı/eksik)
            self.db.ex("DELETE FROM hat_durak WHERE hat=?", (code,))
            
            # Alt İstasyon (Batıpark)
            self.db.ex("INSERT OR REPLACE INTO durak(id, kod, ad, lat, lon) VALUES(?,?,?,?,?)", ('T1', 'T1', 'Batıpark', 41.321704, 36.323564))
            self.db.ex("INSERT INTO hat_durak(hat, durak_id, ad, sira, lat, lon) VALUES(?,?,?,?,?,?)", (code, 'T1', 'Batıpark', 1, 41.321704, 36.323564))
            
            # Üst İstasyon (Amisos Tepesi)
            self.db.ex("INSERT OR REPLACE INTO durak(id, kod, ad, lat, lon) VALUES(?,?,?,?,?)", ('T2', 'T2', 'Amisos Tepesi', 41.318940, 36.322448))
            self.db.ex("INSERT INTO hat_durak(hat, durak_id, ad, sira, lat, lon) VALUES(?,?,?,?,?,?)", (code, 'T2', 'Amisos Tepesi', 2, 41.318940, 36.322448))

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
            # Batch insert (tek commit ile performans artışı)
            batch_data = []
            for i, d in enumerate(duraklar, 1):
                dk, lat, lon = d.get('durak_kodu', ''), 0, 0
                if dk in self.db.durak_coords: lat, lon = self.db.durak_coords[dk]
                fiyat = clean_price(d.get('durak_fiyat', ''))
                fiyat_ogr = clean_price(d.get('durak_fiyat_ogr', ''))
                batch_data.append((hid, d.get('durak_adi', ''), dk, i, lat, lon, fiyat, fiyat_ogr))
            if batch_data:
                self.db.exm("INSERT INTO odak_durak(hat,ad,kod,sira,lat,lon,fiyat,fiyat_ogr) VALUES(?,?,?,?,?,?,?,?)", batch_data)

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

    def _get_route_price(self, code):
        """Hat fiyatını DB'den çek, bulunamazsa ortalama döndür"""
        try:
            res = self.db.one("SELECT tam_fiyat FROM fiyat WHERE hat_code=?", (code,))
            if res and res.get('tam_fiyat'): return f"{res['tam_fiyat']:.2f}"
            # Hat adıyla dene
            hat = self.db.one("SELECT name FROM hat WHERE code=?", (code,))
            if hat:
                res = self.db.one("SELECT tam_fiyat FROM fiyat WHERE hat_adi=?", (hat['name'],))
                if res and res.get('tam_fiyat'): return f"{res['tam_fiyat']:.2f}"
            # Ortalama fallback
            avg = self.db.one("SELECT ROUND(AVG(tam_fiyat),2) as t FROM fiyat WHERE tam_fiyat>0 AND kaynak='samulas'")
            if avg and avg.get('t'): return f"{avg['t']:.2f}"
        except: pass
        return "20.00"

    def _inject_fixed_prices(self):
        """Sabit fiyatları tabloya ekle (User input)"""
        log.info("   💰 Sabit Fiyatlar Ekleniyor...")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 1. Tramvay (Maksimum ücret 1-42 İstasyon: 34.00, Eğitim: 20.00)
        self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', 'Tramvay', 'SAMULAŞ - TRAMVAY', 34.00, 20.00, 20.00, 'Ücretsiz', now))
        
        # 2. Teleferik (Tam: 50.00, Eğitim/İndirimli: 30.00)
        self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', 'Teleferik', 'TELEFERİK', 50.00, 30.00, 30.00, 'Yok', now))
        
        # 3. Ringler (R hatları - Otobüs tarifesini desteklemek için özel ücret grubu) -> Tam: 22.00, Eğitim: 16.00
        ringler = self.db.get("SELECT code, name FROM hat WHERE code LIKE 'R%' OR name LIKE 'RING%'")
        for r in ringler:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', r['name'], r['code'], 22.00, 16.00, 16.00, 'Ücretsiz', now))
             
        # 4. Ekspresler (Tam: 30.00, Eğitim: 20.00)
        ekspres = self.db.get("SELECT code, name FROM hat WHERE code LIKE 'E%' OR name LIKE 'E%'")
        for e in ekspres:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', e['name'], e['code'], 30.00, 20.00, 20.00, 'Ücretsiz', now))

        # 4.5 Merkez Otobüs Hatları (Tüm standart hatlar - Tam: 30.00, Eğitim: 20.00)
        # Ek olarak veritabanına varsayılan şehir içi otobüs hattı kategorisi tablosu ile varsayılan fiyattan da eklendi.
        otobusler = self.db.get("SELECT code, name FROM hat WHERE kat='otobus'")
        for o in otobusler:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', o['name'], o['code'], 30.00, 20.00, 20.00, 'Ücretsiz', now))

        # 5. Tekneler (Samsunum - Merkez/Ayvacık/Vezirköprü - Tam: 250.00, Öğrenci: 200.00)
        tekneler = self.db.get("SELECT code, name FROM hat WHERE name LIKE '%SAMSUNUM%' OR name LIKE '%GEMİ%'")
        for t in tekneler:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', t['name'], t['code'], 250.00, 200.00, 200.00, 'Yok', now))

        # 6. Altınkaya Feribot
        feribot = self.db.get("SELECT code, name FROM hat WHERE name LIKE '%ALTINKAYA%' OR name LIKE '%FERİBOT%'")
        for f in feribot:
             self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', f['name'], f['code'], 15.00, 7.00, 7.00, 'Yok', now))
        
        # 7. Samair/Havalimanı Servisleri (H1-H5 - SAMAIR fiyatı sabit: 120.00)
        samair_hatlar = self.db.get("SELECT code, name FROM hat WHERE code LIKE 'H_%%-%%-%%'")
        for sh in samair_hatlar:
            self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', sh['name'], sh['code'], 120.00, 60.00, 60.00, 'Yok', now))
        if not samair_hatlar:
            # Fallback: SAMAIR_HATLAR'dan al
            for hatid, info in SAMAIR_HATLAR.items():
                ad = info['ad']
                self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                      ('fixed', ad, ad, 120.00, 60.00, 60.00, 'Yok', now))
        
        # 8. Odak Turistik Hatlar (G1-G4 - Samsunum Odak Harici Hatları - İsteğer göre düzenlenebilir ama Gemi tarifesi eklendi -> Tam: 250.00, Eğitim: 200.00)
        odak_hatlar = self.db.get("SELECT code, name FROM hat WHERE code LIKE 'G_%%'")
        for oh in odak_hatlar:
            self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', oh['name'], oh['code'], 250.00, 200.00, 200.00, 'Yok', now))
        
        # 9. İlçe Hatları (Samsun-Terme, Samsun-Çarşamba - Özel listelere göre bırakılmıştır: varsayılan 60.00)
        ilce_hatlar = self.db.get("SELECT code, name FROM hat WHERE tip='ilce'")
        for ih in ilce_hatlar:
            self.db.ex("INSERT OR REPLACE INTO fiyat(kaynak,hat_adi,hat_code,tam_fiyat,indirimli_fiyat,ogrenci_fiyat,aktarma1,guncelleme) VALUES(?,?,?,?,?,?,?,?)",
                  ('fixed', ih['name'], ih['code'], 60.00, 30.00, 30.00, 'Yok', now))
        
        log.info("      ✅ Fiyatlar güncellendi.")

    def _recompute_gtfs_columns(self):
        """GTFS sütunlarını mevcut DB verisinden yeniden hesapla.
        Her başlatmada çalışır — short name ID'lerinin doğru olmasını garanti eder."""
        all_hatlar = self.db.get("SELECT code, name, tip, kat, short_name FROM hat")
        for h in all_hatlar:
            g_route_id = sanitize_id(h['code'])
            g_short = extract_short_name(h['code'], h['short_name'])
            db_short = str(h['short_name']).strip() if h['short_name'] else ''
            raw_long = str(h['name']).strip() if h['name'] else h['code']
            g_long = title_case_tr(clean_long_name(g_short, raw_long, db_short)).replace(',', ' -')
            # KAT kullanılmalı (tip="gidis/donus", kat="otobus/ekspres/tramvay"...)
            g_type = gtfs_route_type(h['kat'])
            g_color = gtfs_route_color(h['kat'])
            self.db.ex(
                "UPDATE hat SET gtfs_route_id=?, gtfs_route_short_name=?, gtfs_route_long_name=?, gtfs_route_type=?, gtfs_route_color=? WHERE code=?",
                (g_route_id, g_short, g_long, g_type, g_color, h['code'])
            )
        # Duraklar
        for d in self.db.get("SELECT id, ad FROM durak"):
            gid = sanitize_id(d['id'])
            gname = title_case_tr(str(d['ad']))
            self.db.ex("UPDATE durak SET gtfs_stop_id=?, gtfs_stop_name=? WHERE id=?", (gid, gname, d['id']))
        # Seferler (sadece boş olanlar)
        for s in self.db.get("SELECT id, hat, gun FROM sefer WHERE gtfs_trip_id='' OR gtfs_trip_id IS NULL"):
            tid = sanitize_id(f"T_{s['id']}")
            rid = sanitize_id(s['hat'])
            sid = gun_to_service(s['gun'])
            self.db.ex("UPDATE sefer SET gtfs_trip_id=?, gtfs_route_id=?, gtfs_service_id=? WHERE id=?",
                      (tid, rid, sid, s['id']))
        log.info(f"      ✅ GTFS sütunları güncellendi ({len(all_hatlar)} hat)")


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
                price = '120.0'
                if 'ybs_duraklar' in locals() and ybs_duraklar:
                    for yd in ybs_duraklar:
                        ykod = str(yd.get('durak_kodu', ''))
                        if ykod and str(d['ad']).startswith(ykod + ' -'):
                            price = clean_price(yd.get('durak_fiyat', '120.0'))
                            if not price: price = '120.0'
                            break

                self.db.ex("INSERT INTO samair_durak(hat,ad,kod,sira,lat,lon,fiyat) VALUES(?,?,?,?,?,?,?)",
                          (hid, d['ad'], d['kod'], idx, d['lat'], d['lon'], price))
            
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
                        
                        # 1. Eski kayıtları temizle (Dünden öncekiler)
                        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                        self.db.ex("DELETE FROM samair_sefer WHERE tarih < ?", (yesterday,))
                        
                        self.db.ex("INSERT OR REPLACE INTO samair_sefer(id,hat,saat,varis,firma,ucak_saat,tarih,gun_format) VALUES(?,?,?,?,?,?,?,?)",
                                  (api_id, ui_hatid, s[:5], v[:5], sf.get('ucak_firmasi', ''), sf.get('ucak_saatleri', ''), tarih, gun_format))
                        toplam += 1
        
        if toplam > 0:
            self.db.set_meta('samair_last_update', str(time.time()))
            self.db.set_meta('samair_last_update_str', now_str)
            log.info(f"      ✅ {toplam} uçuş bilgisi güncellendi.")

    def canli(self, code, use_cache=False):
        """Canlı araç verisi çek (opsiyonel 5sn cache)"""
        if use_cache and code in self.http._cache:
            cached_data, cached_time = self.http._cache[code]
            if time.time() - cached_time < 5:
                return cached_data
        
        data = self.http.asis('RealTimeData', lineCode=code)
        result = []
        for d in data:
            try:
                lat, lon = parse_float(d.get('enlem')), parse_float(d.get('boylam'))
                if 40 < lat < 43 and 34 < lon < 38:
                    # Tarih/saat parse
                    tarih_raw = d.get('tarih') or d.get('editDate') or ''
                    saat_str = ''
                    if tarih_raw:
                        try: saat_str = tarih_raw.split('T')[1][:5]
                        except: pass
                    
                    # Renk → durum
                    renk = str(d.get('renk', '')).upper()
                    durum = 'normal'
                    if renk == 'FF0000': durum = 'dikkat'
                    elif renk == 'FFFF00': durum = 'uyari'
                    
                    # Mesafe → km
                    mesafe_m = int(float(d.get('mesafe', 0)))
                    mesafe_km = round(mesafe_m / 1000, 1)
                    
                    result.append({
                        'plaka': d.get('plaka', '?'),
                        'lat': lat, 'lon': lon,
                        'hiz': int(float(d.get('hiz', 0))),
                        'yon': float(d.get('yon', 0)),
                        'yolcu': int(d.get('seferYolcu', 0)),
                        'gunluk_yolcu': int(d.get('gunlukYolcu', 0)),
                        'max_hiz': int(float(d.get('maxHiz', 0))),
                        'mesafe_km': mesafe_km,
                        'durum': durum,
                        'saat': saat_str,
                        'hasilat': round(float(d.get('toplamHasilat', 0)), 2),
                    })
            except Exception as e:
                log.debug(f"Canlı veri parse hatası ({code}): {e}")
        
        # Cache'e kaydet
        self.http._cache[code] = (result, time.time())
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
        # SQL bounding box filtresi (idx_dk_latlon indeksi kullanılır)
        # 0.01 ≈ ~1km — önce SQL'de daralt, sonra Python'da hassas mesafe
        nearby = self.db.get(
            "SELECT kod, ad, lat, lon FROM durak WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
            (lat - 0.01, lat + 0.01, lon - 0.01, lon + 0.01)
        )
        yakindakiler = []
        for s in nearby:
            # Override with explicit Tram coordinates if it's a tram stop
            if hasattr(self.db, 'tram_corrections'):
                for csv_name, coords in self.db.tram_corrections.items():
                    cv_low = csv_name.lower().replace(' i̇stasyonu', '').replace(' istasyonu', '')
                    ad_low = s['ad'].lower()
                    if cv_low in ad_low or ad_low in cv_low:
                        s['lat'] = coords[0]
                        s['lon'] = coords[1]
                        break
                        
            dist = haversine(lat, lon, s['lat'], s['lon'])
            if dist < 1200: # 1.2 KM'ye çıkardık sonuç bulma ihtimali için
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

        # id veya kod ile durak bul
        hatlar = self.db.get("""SELECT DISTINCT h.code, h.name, h.kat, hd.sira FROM hat_durak hd JOIN hat h ON hd.hat = h.code WHERE hd.durak_id = (SELECT id FROM durak WHERE id = ? OR kod = ? LIMIT 1) ORDER BY h.code""", (durak_kodu, durak_kodu))
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

    def yakin_duraklar(self, lat, lon, mesafe=500):
        # Basit kare kutu hesabı (performans için) - 0.005 yaklaşık 500m
        lat, lon = float(lat), float(lon)
        return self.db.get(f"SELECT id, ad, lat, lon FROM durak WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?", (lat-0.005, lat+0.005, lon-0.005, lon+0.005))

    def get_tahmini_kalkis(self, hat_kodu, durak_sira):
        """Hat için tahmini kalkış saati hesapla (Basit mantık)"""
        try:
            now = datetime.now()
            current_time_str = now.strftime("%H:%M")
            
            # Seferleri çek (Sadece bugünkü gibi düşünüyoruz basitlik için)
            seferler = self.db.get("SELECT saat FROM sefer WHERE hat=? ORDER BY saat", (hat_kodu,))
            if not seferler: return None
            
            next_sefer = None
            for s in seferler:
                if s['saat'] > current_time_str:
                    next_sefer = s['saat']
                    break
            
            if not next_sefer: next_sefer = seferler[0]['saat'] # Ertesi gün sabah
            
            # Saat hesaplama
            h, m = map(int, next_sefer.split(':'))
            kalkis_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if kalkis_dt < now: kalkis_dt += timedelta(days=1)
            
            # Durağa varış süresi (Ortalama 2 dk/durak, Tramvay 1.5 dk)
            # Tramvay kontrolü için hat kodu veya tipine bakılabilir ama basitçe 2 dk alalım
            sure_dk = durak_sira * 2
            varis_dt = kalkis_dt + timedelta(minutes=sure_dk)
            
            return varis_dt.strftime("%H:%M")
        except Exception as e:
            log.debug(f"Tahmini kalkış hesaplama hatası ({hat_kodu}): {e}")
            return None

    def groq_rota_tavsiye(self, routes_data, start_info, end_info):
        """Groq AI ile rota önerilerini akıllıca sıralar ve açıklama ekler"""
        import os, json
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or not routes_data:
            return routes_data
        
        # Rotaları özetle (polyline'ları göndermeyiz, çok uzun)
        routes_summary = []
        for i, r in enumerate(routes_data):
            summary = {
                "index": i,
                "type": r.get("type", "?"),
                "total_score": r.get("total_score", 999),
                "desc_text": r.get("desc", "").replace("<", " ").replace(">", " ")[:500]
            }
            routes_summary.append(summary)
        
        system_prompt = """Sen Samsun Büyükşehir Belediyesi toplu ulaşım sisteminin UZMAN rota danışmanısın.
Görevin: Algoritmik olarak üretilmiş rota seçeneklerini DEĞERLENDİRMEK, SIRALAMAK ve her birine kısa Türkçe açıklama yazmaktır.

SEN YENİ ROTA ÜRETMEZSİN. Sadece verilen rotaları değerlendirirsin.
Sadece sana verilen bilgilere dayanarak karar ver. Bilmediğin veya emin olmadığın konularda tahminde BULUNMA.

═══════════════════════════════════════
 SAMSUN TOPLU TAŞIMA SİSTEMİ BİLGİLERİ
═══════════════════════════════════════

🚋 TRAMVAY (Samulaş T1 Hattı):
- Güzergah: Gar ↔ Tekkeköy (toplam ~20 km, ~45 dk)
- ÇİFT YÖNLÜ çalışır (aynı hat kodu ile gidiş VE dönüş yapılır)
- Sefer sıklığı: ~10 dakikada bir (06:00-23:30)
- Duraklar: Gar, Cumhuriyet Meydanı, 19 Mayıs, Liman, Halkevi, Piazza, Tekkeköy vb.
- Genellikle sahil şeridindeki yolculuklar için EN HIZLI seçenektir
- Tramvay güzergahı kıyı boyunca DOĞU-BATI ekseninde uzanır

🚌 OTOBÜSLER:
- TEK YÖNLÜ çalışır: Gidiş ve dönüş FARKLI hat kodlarıdır
  Örnek: "22 TÜRKİŞ-SOĞUKSU" = gidiş, "22 SOĞUKSU-TÜRKİŞ" = dönüş
- Hat adındaki ilk yer BAŞLANGIÇ, ikinci yer BİTİŞ noktasıdır
- Sira numarası küçükten büyüğe gider: s1.sira < s2.sira ise DOĞRU YÖN demektir

🔄 AKTARMA KURALLARI:
- 1 saat içinde Otobüs↔Otobüs veya Otobüs↔Tramvay aktarması ÜCRETSİZDİR
- 1 saat sonrası aktarma: 8,00 TL
- Düşük ücretli → Yüksek ücretli hatta geçişte fark ücreti alınır

⛔ HARİÇ TUTULAN HATLAR (rotalamaya dahil DEĞİLDİR):
- Odak: Turistik hatlar (farklı fiyatlandırma)
- Samair: Havalimanı servisi
- Tekne: Deniz ulaşımı
- Teleferik: Amisos Tepesi teleferik hattı
- İlçe: Şehirlerarası ilçe hatları

═══════════════════════════════════════
 SAMSUN COĞRAFİ BİLGİLER
═══════════════════════════════════════
- Samsun kıyı şeridi DOĞU-BATI yönünde uzanır
- Batıda Atakum, merkezde İlkadım/Meydan, doğuda Canik/Tekkeköy
- Tramvay sahil boyunca Batı↔Doğu ekseninde çalışır
- Cumhuriyet Meydanı şehrin merkezi ve ana aktarma noktasıdır
- Latitude ~41.27-41.33, Longitude batıda ~36.25, doğuda ~36.45
- Longitude ARTAN yönde gitmek = DOĞUYA gitmek
- Longitude AZALAN yönde gitmek = BATIYA gitmek

═══════════════════════════════════════
 DEĞERLENDİRME KRİTERLERİ (Öncelik Sırasıyla)
═══════════════════════════════════════

1. YÖN KONTROLÜ (EN KRİTİK):
   - Rota, başlangıçtan hedefe doğru İLERLEMELİ
   - Ters yöne gidip geri dönen rotalar KÖTÜDÜR (yüksek skor ver)
   - Hat adındaki yön bilgisi ile koordinat yönü uyuşmalı

2. SÜRE MANTIKLıLıĞı:
   - total_score < 60: Çok iyi
   - total_score 60-120: Kabul edilebilir
   - total_score 120-300: Kötü (ancak alternatif yoksa olabilir)
   - total_score > 500: MANTIK DIŞI — büyük olasılıkla sefer bitmiş, ertesi güne sarkmış
   - 1000+ dk süre gösteren rotaları ASLA önerme (skor 95+)

3. DİREKT vs AKTARMALI:
   - Direkt hat HER ZAMAN aktarmalıdan üstündür (süre farkı 15 dk'dan az ise)
   - Aktarma bekleme süresi genellikle 5-15 dk arasıdır

4. TRAMVAY TERCİHİ:
   - Tramvay içeren rotalar daha güvenilirdir (düzenli sefer)
   - Sahil hattına paralel yolculuklarda tramvay idealdir

5. YÜRÜME MESAFESİ:
   - Durağa yürüme mesafesi 500m altında: iyi
   - 500m-1km: kabul edilebilir
   - 1km üstü: kötü

═══════════════════════════════════════
 ÇIKTI FORMATI
═══════════════════════════════════════
SADECE aşağıdaki JSON formatında yanıt ver. Başka HİÇBİR ŞEY yazma.

{"ranking": [
  {"index": <orijinal_index>, "yeni_skor": <1-100>, "tavsiye": "<Türkçe 1-2 cümle açıklama>"},
  ...
]}

KURALLAR:
- "yeni_skor": 1 = mükemmel, 100 = çok kötü
- "tavsiye": Kullanıcıya yönelik samimi ama profesyonel Türkçe. Neden iyi/kötü olduğunu kısaca açıkla.
- Mantıksız rotaları 90+ skor ver ve nedenini açıkla
- İyi rotaları 1-30 arası skor ver
- Orta rotaları 30-60 arası skor ver
- YENİ ROTA ÜRETMEZSİN, sadece mevcut rotaları değerlendirirsin
- Tavsiye metninde emoji kullanma
"""

        user_prompt = f"""Kullanıcı şuradan: {start_info}
Kullanıcı şuraya gitmek istiyor: {end_info}

Aşağıdaki rota seçeneklerini değerlendir:
{json.dumps(routes_summary, ensure_ascii=False, indent=2)}

GÖREV: Her rotayı değerlendir ve JSON olarak döndür. Format:
{{
  "ranking": [
    {{"index": 0, "yeni_skor": 10, "tavsiye": "Bu rotayı tercih edin çünkü..."}},
    ...
  ]
}}

Kurallar:
- "index" orijinal rota indexi
- "yeni_skor" 1-100 arası (1=en iyi)
- "tavsiye" kısa Türkçe açıklama (max 2 cümle)
- Mantıksız rotaları yüksek skor ver (90+)
- SADECE JSON döndür, başka bir şey yazma"""

        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024,
                    "response_format": {"type": "json_object"}
                },
                timeout=8
            )
            
            if resp.status_code == 200:
                result = resp.json()
                content = result['choices'][0]['message']['content']
                ai_data = json.loads(content)
                return ai_data.get('ranking', [])
        except Exception as e:
            log.debug(f"Groq AI hatası: {e}")
        
        return []

    def _groq_postprocess(self, all_routes, lat1, lon1, lat2, lon2):
        """Groq AI ile rotaları yeniden sıralar ve açıklama ekler"""
        if not all_routes:
            return all_routes
        
        start_info = f"({lat1:.4f}, {lon1:.4f})"
        end_info = f"({lat2:.4f}, {lon2:.4f})"
        
        ranking = self.groq_rota_tavsiye(all_routes, start_info, end_info)
        
        if not ranking:
            return all_routes
        
        # AI sonuçlarını uygula
        index_map = {r['index']: r for r in ranking if 'index' in r}
        
        for i, route in enumerate(all_routes):
            ai = index_map.get(i)
            if ai:
                route['total_score'] = ai.get('yeni_skor', route['total_score'])
                tavsiye = ai.get('tavsiye', '')
                if tavsiye:
                    # Tavsiyeyi HTML desc'e ekle
                    ai_html = f'<div style="background:linear-gradient(135deg,#eff6ff,#dbeafe);padding:8px 12px;font-size:0.75rem;color:#1e40af;border-radius:0 0 12px 12px;border-top:1px solid #bfdbfe"><span style="font-weight:700">🤖 AI Tavsiye:</span> {tavsiye}</div>'
                    # route-card kapanış div'inden önce ekle
                    route['desc'] = route['desc'].rstrip()
                    if route['desc'].endswith('</div>'):
                        # Son </div>'den önce ekle (route-card'ın kapanışı)
                        last_div = route['desc'].rfind('</div>')
                        route['desc'] = route['desc'][:last_div] + ai_html + route['desc'][last_div:]
        
        # Yeniden sırala
        all_routes.sort(key=lambda x: x['total_score'])
        
        return all_routes

    def get_osrm_foot_path(self, lat1, lon1, lat2, lon2):
        """OSRM kullanarak iki nokta arası yürüme rotası çıkarır"""
        try:
            url = f"http://router.project-osrm.org/route/v1/foot/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if data.get('routes') and len(data['routes']) > 0:
                    coords = data['routes'][0]['geometry']['coordinates']
                    # OSRM lon,lat döndürür; Leaflet lat,lon ister
                    return [[c[1], c[0]] for c in coords], data['routes'][0]['distance']
        except Exception:
            pass
        return None, None

    def akilli_rota(self, lat1, lon1, lat2, lon2):
        """Başlangıç ve bitiş koordinatlarından rota hesapla (Puanlama Algoritması)"""
        all_routes = []
        now = datetime.now()
        
        # 1. Yakın durakları bul (Genel arama, SQL limitli)
        # NOT: SQL'de Haversine yok, kare alan (box) ile çekiyoruz.
        # Çektikten sonra Python tarafında MESAFE'ye göre sıralayıp EN YAKIN olanı seçeceğiz.
        
        # Başlangıç durak adayları
        start_candidates = self.db.get("""
            SELECT DISTINCT durak_id, ad, hat, lat, lon FROM hat_durak 
            WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?
        """, (lat1-0.015, lat1+0.015, lon1-0.015, lon1+0.015))
        
        # Bitiş durak adayları
        end_candidates = self.db.get("""
            SELECT DISTINCT durak_id, ad, hat, lat, lon FROM hat_durak 
            WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?
        """, (lat2-0.015, lat2+0.015, lon2-0.015, lon2+0.015))

        # --- KOORDİNAT DÜZELTME VE MESAFE SIRALAMA ---
        def process_candidates(candidates, target_lat, target_lon):
            processed = []
            for c in candidates:
                # CSV Düzeltmesi (Varsa)
                # Durak adını normalize etip eşleştirmeye çalışalım
                d_ad = c['ad'].lower()
                
                # Tramvay mı?
                is_tram = 'tramvay' in str(c.get('hat', '')).lower() or 'samulaş' in str(c.get('hat', '')).lower()
                
                real_lat, real_lon = c['lat'], c['lon']
                
                if is_tram and hasattr(self.db, 'tram_corrections'):
                    # CSV'deki durak isimleri ile eşleştirme denemesi
                    # Veritabanındaki ad: "10012 - GAR" -> "gar"
                    # CSV'deki ad: "Gar İstasyonu"
                    for csv_name, coords in self.db.tram_corrections.items():
                        if csv_name in d_ad or d_ad in csv_name or \
                           (csv_name.replace(' istasyonu','') in d_ad) or \
                           ('türkiş' in d_ad and 'türkiş' in csv_name):
                             real_lat, real_lon = coords
                             break
                
                dist = haversine(target_lat, target_lon, real_lat, real_lon)
                processed.append({**c, 'dist': dist, 'lat': real_lat, 'lon': real_lon})
            
            # Mesafeye göre sırala (En yakın en üstte)
            processed.sort(key=lambda x: x['dist'])
            return processed

        start_stops = process_candidates(start_candidates, lat1, lon1)[:10] # En yakın 10 durak
        end_stops = process_candidates(end_candidates, lat2, lon2)[:10]     # En yakın 10 durak
        
        if not start_stops or not end_stops: return []
        
        # Durak ID listeleri (SQL için)
        start_ids = list(set([s['durak_id'] for s in start_stops if s['durak_id']]))
        end_ids = list(set([s['durak_id'] for s in end_stops if s['durak_id']]))
        
        if not start_ids or not end_ids: return []
        
        start_placeholders = ','.join(['?' for _ in start_ids])
        end_placeholders = ','.join(['?' for _ in end_ids])
        
        # 2. Direkt Hatlar
        try:
            q_direct = f"""
            SELECT h.code, h.name, h.kat, s1.ad as s_ad, s1.sira as s_sira, s2.ad as e_ad, 
                   s1.durak_id as s_id, s2.durak_id as e_id,
                   s1.lat as s_lat, s1.lon as s_lon, s2.lat as e_lat, s2.lon as e_lon,
                   ABS(s2.sira - s1.sira) as durak_sayisi
            FROM hat h
            JOIN hat_durak s1 ON h.code = s1.hat
            JOIN hat_durak s2 ON h.code = s2.hat
            WHERE s1.durak_id IN ({start_placeholders}) AND s2.durak_id IN ({end_placeholders})
            AND s1.sira != s2.sira
            AND (
                (h.kat != 'tramvay' AND s1.sira < s2.sira)
                OR
                (h.kat = 'tramvay')
            )
            AND h.kat NOT IN ('odak', 'samair', 'tekne', 'teleferik', 'ilce')
            GROUP BY h.code
            """
            direct_res = self.db.get(q_direct, tuple(start_ids + end_ids))
            
            for r in direct_res or []:
                # Süre Hesabı
                durak_sayisi = r['durak_sayisi']
                yolculuk_sure = int(durak_sayisi * (1.5 if r['kat'] == 'tramvay' else 2))
                
                # Tahmini Kalkış
                if r['kat'] == 'tramvay':
                    # Tramvay sefer simülasyonu (Her 10 dk bir)
                    sim_dk = (now.minute // 10 + 1) * 10
                    if sim_dk >= 60:
                        kalkis_dt = (now + timedelta(hours=1)).replace(minute=sim_dk-60, second=0)
                    else:
                        kalkis_dt = now.replace(minute=sim_dk, second=0)
                    kalkis_saati_str = kalkis_dt.strftime("%H:%M")
                else:
                    kalkis_saati_str = self.get_tahmini_kalkis(r['code'], r['s_sira']) or now.strftime("%H:%M")
                
                try:
                    kh, km = map(int, kalkis_saati_str.split(':'))
                    kalkis_dt = now.replace(hour=kh, minute=km, second=0)
                    if kalkis_dt < now: kalkis_dt += timedelta(days=1)
                    
                    bekleme_sure = int((kalkis_dt - now).total_seconds() / 60)
                    varis_dt = kalkis_dt + timedelta(minutes=yolculuk_sure)
                    varis_saati_str = varis_dt.strftime("%H:%M")
                except:
                    bekleme_sure = 10 # Fallback
                    varis_saati_str = "?"
                
                # Yürüme mesafesi (Başlangıç -> Durak + Durak -> Bitiş)
                # Buradaki start_stops içinde r['s_id'] olan durağın koordinatını bulmamız lazım ama basitlik için query'de join yapmadık.
                # Ortalamalama bir yürüme süresi ekleyelim veya 0 kabul edelim şimdilik.
                yurume_sure = 5 
                
                # Puanlama (Düşük puan daha iyi)
                puan = bekleme_sure + yolculuk_sure + yurume_sure
                if r['kat'] == 'tramvay': puan -= 10 # Tramvay bonusu (Konfor)
                
                # Google Maps Linkleri
                map_walk_start = f"https://www.google.com/maps/dir/?api=1&destination={r['s_ad'].replace(' ', '+')}&travelmode=walking"
                
                # Polyline path generation (Direct Route)
                path_coords = []
                try:
                    p_min = min(r['s_sira'], r['e_sira'])
                    p_max = max(r['s_sira'], r['e_sira'])
                    path_rows = self.db.get("SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira", (r['code'], p_min, p_max))
                    if path_rows:
                        # Order properly if the bus travels in reverse sequence in the table logically
                        if r['s_sira'] > r['e_sira']: path_rows.reverse()
                        path_coords = [[pr['lat'], pr['lon']] for pr in path_rows]
                except Exception as e:
                    print("Direct path error:", e)

                # OSRM Walking Polylines
                s_walk_poly, _ = self.get_osrm_foot_path(lat1, lon1, r['s_lat'], r['s_lon']) if r.get('s_lat') else (None, None)
                e_walk_poly, _ = self.get_osrm_foot_path(r['e_lat'], r['e_lon'], lat2, lon2) if r.get('e_lat') else (None, None)

                all_routes.append({
                    'total_score': puan,
                    'type': 'DIRECT',
                    'polyline': path_coords,
                    'walk_start': s_walk_poly,
                    'walk_end': e_walk_poly,
                    'desc': f"""
                    <div class="route-card direct">
                        <div class="route-header">
                            <span class="route-icon">{icon}</span>
                            <div style="flex:1">
                                <div class="route-code">{r['code']}</div>
                                <div class="route-info">{bekleme_sure} dk bekleyin</div>
                            </div>
                            <div style="text-align:right">
                                <span class="route-time">{yolculuk_sure} dk</span>
                                <div style="font-size:0.7rem;color:#666">{kalkis_saati_str} - {varis_saati_str}</div>
                            </div>
                        </div>
                        <div style="background:#f1f8ff;padding:5px 10px;font-size:0.8rem;text-align:center;border-bottom:1px solid #ddd">
                            Tahmini Ücret: <b>{self._get_route_price(r['code'])} TL</b> (Tam)
                        </div>
                        <div class="route-details timeline">
                            <div class="step">
                                <div class="time">{now.strftime("%H:%M")}</div>
                                <div class="dot start" style="background:#555"></div>
                                <div class="content">
                                    <b>Başlangıç</b>
                                    <div class="sub"><a href="{map_walk_start}" target="_blank" style="color:#007bff">🚶 Durağa Yürü ↗</a></div>
                                </div>
                            </div>
                            <div class="step">
                                <div class="time">{kalkis_saati_str}</div>
                                <div class="dot start"></div>
                                <div class="content">
                                    <b>{r['s_ad']}</b>
                                    <div class="sub">Buradan binin</div>
                                    <button onclick="shL('{r['code']}', true)" style="margin-top:5px;font-size:0.7rem;padding:2px 5px;border:1px solid #ccc;border-radius:3px;cursor:pointer">📡 Canlı Konum</button>
                                </div>
                            </div>
                            <div class="step">
                                <div class="time">{varis_saati_str}</div>
                                <div class="dot end"></div>
                                <div class="content"><b>{r['e_ad']}</b><div class="sub">İniş durağı</div></div>
                            </div>
                        </div>
                        <div style="font-size:0.7rem;color:#999;text-align:center;padding:5px">Bilgiler tahminidir. Trafik yoğunluğuna göre değişebilir.</div>
                    </div>
                    """
                })
        except Exception as e:
            print("Direkt hata:", e)

        # 3. Aktarmalı Hatlar
        try:
            q_transfer = f"""
            SELECT 
                h1.code as hat1, h1.kat as kat1,
                s1.ad as start_stop, s1.sira as s1_sira, s1.lat as s_lat, s1.lon as s_lon,
                t1.ad as transfer_name, t1.sira as t1_sira,
                h2.code as hat2, h2.kat as kat2,
                t2.sira as t2_sira,
                s2.ad as end_stop, s2.lat as e_lat, s2.lon as e_lon,
                s2.sira as e_sira,
                (t1.sira - s1.sira) as durak1,
                (s2.sira - t2.sira) as durak2
            FROM hat_durak s1
            JOIN hat_durak t1 ON s1.hat = t1.hat AND s1.sira < t1.sira
            JOIN hat_durak t2 ON t1.durak_id = t2.durak_id AND t1.hat != t2.hat
            JOIN hat_durak s2 ON t2.hat = s2.hat AND t2.sira < s2.sira
            JOIN hat h1 ON s1.hat = h1.code
            JOIN hat h2 ON s2.hat = h2.code
            WHERE s1.durak_id IN ({start_placeholders})
            AND s2.durak_id IN ({end_placeholders})
            AND h1.kat NOT IN ('odak', 'samair', 'tekne', 'teleferik', 'ilce')
            AND h2.kat NOT IN ('odak', 'samair', 'tekne', 'teleferik', 'ilce')
            GROUP BY h1.code, h2.code
            LIMIT 10
            """
            trans_res = self.db.get(q_transfer, tuple(start_ids + end_ids))
            
            for r in trans_res or []:
                yolculuk_sure = int((r['durak1'] + r['durak2']) * 2)
                
                # Kalkış 1
                kalkis1_str = self.get_tahmini_kalkis(r['hat1'], r['s1_sira']) or now.strftime("%H:%M")
                
                try:
                    kh, km = map(int, kalkis1_str.split(':'))
                    kalkis1_dt = now.replace(hour=kh, minute=km, second=0)
                    if kalkis1_dt < now: kalkis1_dt += timedelta(days=1)
                    
                    bekleme1 = int((kalkis1_dt - now).total_seconds() / 60)
                    varis1_dt = kalkis1_dt + timedelta(minutes=r['durak1']*2)
                    varis1_str = varis1_dt.strftime("%H:%M")
                    
                    # Kalkış 2 (En az 5 dk sonrası)
                    min_kalkis2 = varis1_dt + timedelta(minutes=5)
                    # get_tahmini_kalkis sadece şu anki zamana göre bakıyor, o yüzden burada manuel bir öteleme yapmamız gerekebilir
                    # Şimdilik basitçe +5 dk diyelim
                    kalkis2_dt = min_kalkis2
                    kalkis2_str = kalkis2_dt.strftime("%H:%M")
                    
                    varis2_dt = kalkis2_dt + timedelta(minutes=r['durak2']*2)
                    varis2_str = varis2_dt.strftime("%H:%M")
                    
                    toplam_sure = int((varis2_dt - now).total_seconds() / 60)
                except:
                    bekleme1 = 10
                    toplam_sure = 60
                    kalkis1_str = "?"
                    varis2_str = "?"
                
                puan = toplam_sure + 15 # Aktarma cezası
                if r['kat1'] == 'tramvay' or r['kat2'] == 'tramvay': puan -= 5
                
                icon1 = "🚋" if r['kat1'] == 'tramvay' else "🚌"
                icon2 = "🚋" if r['kat2'] == 'tramvay' else "🚌"
                
                # Polyline path generation (Transfer Route)
                path_coords = []
                try:
                    # Leg 1
                    p1_min = min(r['s1_sira'], r['t1_sira'])
                    p1_max = max(r['s1_sira'], r['t1_sira'])
                    path1_rows = self.db.get("SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira", (r['hat1'], p1_min, p1_max))
                    if path1_rows:
                        if r['s1_sira'] > r['t1_sira']: path1_rows.reverse()
                        path_coords.extend([[pr['lat'], pr['lon']] for pr in path1_rows])
                    
                    # Leg 2
                    p2_min = min(r['t2_sira'], r['e_sira'])
                    p2_max = max(r['t2_sira'], r['e_sira'])
                    path2_rows = self.db.get("SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira", (r['hat2'], p2_min, p2_max))
                    if path2_rows:
                        if r['t2_sira'] > r['e_sira']: path2_rows.reverse()
                        path_coords.extend([[pr['lat'], pr['lon']] for pr in path2_rows])
                except Exception as e:
                    print("Transfer path error:", e)

                # OSRM Walking Polylines
                s_walk_poly, _ = self.get_osrm_foot_path(lat1, lon1, r.get('s_lat', 0), r.get('s_lon', 0)) if r.get('s_lat') else (None, None)
                e_walk_poly, _ = self.get_osrm_foot_path(r.get('e_lat', 0), r.get('e_lon', 0), lat2, lon2) if r.get('e_lat') else (None, None)

                all_routes.append({
                    'total_score': puan,
                    'type': 'TRANSFER',
                    'polyline': path_coords,
                    'walk_start': s_walk_poly,
                    'walk_end': e_walk_poly,
                    'desc': f"""
                    <div class="route-card transfer">
                        <div class="route-header">
                            <span class="route-info">{toplam_sure} dk • 1 Aktarma</span>
                            <div style="font-size:0.7rem;color:#666">{kalkis1_str} - {varis2_str}</div>
                        </div>
                        <div style="background:#fff3cd;padding:5px 10px;font-size:0.8rem;text-align:center;border-bottom:1px solid #ddd;color:#856404">
                            Tahmini Ücret: <b>Ücretsiz Aktarma</b>
                        </div>
                        <div class="route-details timeline">
                            <div class="step">
                                <div class="time">{kalkis1_str}</div>
                                <div class="dot start"></div>
                                <div class="content">
                                    <span class="route-badge">{icon1} {r['hat1']}</span> {r['start_stop']}
                                    <button onclick="shL('{r['hat1']}')" style="display:block;margin-top:3px;font-size:0.65rem;border:1px solid #ccc">📡 Canlı</button>
                                </div>
                            </div>
                            <div class="step transfer-point">
                                <div class="time">{varis1_str}</div>
                                <div class="dot transfer"></div>
                                <div class="content">
                                    <b>{r['transfer_name']}</b>
                                    <div class="sub">İn ve Aktarma Yap (~5 dk)</div>
                                </div>
                            </div>
                            <div class="step">
                                <div class="time">{kalkis2_str}</div>
                                <div class="dot start"></div>
                                <div class="content"><span class="route-badge">{icon2} {r['hat2']}</span> Biniş</div>
                            </div>
                            <div class="step">
                                <div class="time">{varis2_str}</div>
                                <div class="dot end"></div>
                                <div class="content"><b>{r['end_stop']}</b></div>
                            </div>
                        </div>
                         <div style="font-size:0.7rem;color:#999;text-align:center;padding:5px">Bilgiler tahminidir.</div>
                    </div>
                    """
                })
        except Exception as e:
            print("Transfer hata:", e)
            
        # Puanlamaya göre sırala (Küçük puan daha iyi)
        all_routes.sort(key=lambda x: x['total_score'])
        
        # Groq AI Post-Processing
        try:
            all_routes = self._groq_postprocess(all_routes[:8], lat1, lon1, lat2, lon2)
        except Exception as e:
            log.debug(f"Groq postprocess atlandı: {e}")
        
        return all_routes[:5]

    def yol_tarifi(self, lat1, lon1, lat2, lon2):
        return self.akilli_rota(lat1, lon1, lat2, lon2)

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

    # ============================================================
    # GTFS İYİLEŞTİRMELERİ - VALIDATOR FIX
    # ============================================================
    
    def calculate_realistic_stop_times(self, duraklar, hat_code, ilk_kalkis="06:00:00"):
        """
        Gerçekçi durak saatleri hesapla - mesafeye göre (GTFS Validator FIX)
        
        Args:
            duraklar: [{lat, lon, sira, ad}, ...]
            hat_code: Hat kodu (kategori belirlemek için)
            ilk_kalkis: İlk durak kalkış saati
        
        Returns:
            [(arrival_time, departure_time), ...]
        """
        
        # Hat tipine göre ortalama hız (km/h)
        hat_bilgi = self.db.one("SELECT tip FROM hat WHERE code=?", (hat_code,))
        hat_tipi = hat_bilgi['tip'] if hat_bilgi else 'otobus'
        
        HIZ_AYARLARI = {
            'otobus': 25,      # Şehir içi otobüs
            'ring': 30,        # Ring hatları (daha hızlı)
            'ekspres': 35,     # Ekspres hatlar
            'havalimani': 50,  # Havalimanı (kısmen otoyol)
            'ilce': 60,        # İlçeler arası (çoğunlukla otoyol)
            'tramvay': 20,     # Tramvay
            'teleferik': 15,   # Teleferik
            'tekne': 40,       # Deniz otobüsü
        }
        
        ortalama_hiz = HIZ_AYARLARI.get(hat_tipi, 25)
        
        # Durak başına ek bekleme süresi (dakika)
        DURAK_BEKLEME = {
            'otobus': 1.0,
            'ring': 0.5,
            'ekspres': 0.5,
            'havalimani': 2.0,  # Terminal durağında daha uzun
            'ilce': 3.0,        # Otogar/terminal durağında daha uzun
            'tramvay': 1.0,
            'teleferik': 0,
            'tekne': 2.0,
        }
        
        bekleme_dk = DURAK_BEKLEME.get(hat_tipi, 1.0)
        
        stop_times = []
        toplam_sure = 0  # dakika
        
        for i, durak in enumerate(duraklar):
            # İlk durağın saati
            if i == 0:
                arrival = departure = ilk_kalkis
            else:
                # Önceki duraktan mesafe hesapla
                onceki = duraklar[i - 1]
                mesafe_km = haversine(
                    onceki['lat'], onceki['lon'],
                    durak['lat'], durak['lon']
                ) / 1000.0
                
                # Kıvrım payı ekle (yol mesafesi > kuş uçuşu)
                yol_mesafe = mesafe_km * 1.3
                
                # Süre hesapla (dakika)
                seyahat_dk = (yol_mesafe / ortalama_hiz) * 60
                
                # Minimum seyahat süresi (çok yakın duraklar için)
                if seyahat_dk < 0.5:
                    seyahat_dk = 0.5
                
                # Son durak değilse bekleme ekle
                if i < len(duraklar) - 1:
                    toplam_sure += seyahat_dk + bekleme_dk
                else:
                    toplam_sure += seyahat_dk
                
                # Saat formatına çevir (import dosya başında zaten var)
                baslangic = datetime.strptime(ilk_kalkis, "%H:%M:%S")
                varis_zamani = baslangic + timedelta(minutes=toplam_sure)
                
                arrival = varis_zamani.strftime("%H:%M:%S")
                
                # Durakta bekleme süresi
                if i < len(duraklar) - 1:
                    kalkis_zamani = varis_zamani + timedelta(minutes=bekleme_dk)
                    departure = kalkis_zamani.strftime("%H:%M:%S")
                else:
                    departure = arrival  # Son durakta kalkış yok
            
            stop_times.append((arrival, departure))
        
        return stop_times

    def create_shape_from_stops(self, duraklar, hat_code):
        """
        Duraklardan shape çizgisi oluştur (GTFS shapes.txt için)
        
        Args:
            duraklar: [{lat, lon, sira}, ...]
            hat_code: Hat kodu (shape_id olacak)
        
        Returns:
            shape_points: [(lat, lon, sequence, dist_traveled), ...]
        """
        if len(duraklar) < 2:
            return []
        
        shape_points = []
        total_dist = 0.0
        
        for i, durak in enumerate(duraklar):
            lat = durak['lat']
            lon = durak['lon']
            seq = i + 1
            
            # Mesafe hesapla
            if i > 0:
                onceki = duraklar[i - 1]
                segment_dist = haversine(
                    onceki['lat'], onceki['lon'],
                    lat, lon
                )
                total_dist += segment_dist
            
            shape_points.append((lat, lon, seq, total_dist))
        
        return shape_points

    def save_shapes_to_db(self, hat_code, shape_points):
        """Shape noktalarını DB'ye kaydet"""
        shape_id = f"shape_{hat_code}"
        
        # Önce mevcut shape'i sil
        self.db.ex("DELETE FROM gtfs_shape WHERE shape_id=?", (shape_id,))
        
        # Yeni shape'i kaydet
        data = []
        for lat, lon, seq, dist in shape_points:
            data.append((shape_id, lat, lon, seq, dist))
        
        self.db.exm(
            "INSERT INTO gtfs_shape(shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence, shape_dist_traveled) VALUES(?,?,?,?,?)",
            data
        )
        
        return shape_id

    def gtfs_generate_shapes(self):
        """Tüm hatlar için shape oluştur ve DB'ye kaydet"""
        log.info("📐 GTFS Shapes oluşturuluyor...")
        
        hatlar = self.db.get("SELECT code FROM hat")
        toplam = 0
        
        for h in hatlar:
            code = h['code']
            duraklar = self.db.get(
                "SELECT lat, lon, sira FROM hat_durak WHERE hat=? ORDER BY sira",
                (code,)
            )
            
            if len(duraklar) >= 2:
                shape_points = self.create_shape_from_stops(duraklar, code)
                if shape_points:
                    self.save_shapes_to_db(code, shape_points)
                    toplam += 1
        
        log.info(f"   ✅ {toplam} hat için shape oluşturuldu")


HTML = '''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🇹🇷 🚌 Samsun Ulaşım Sistemi</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/leaflet.css"/>
<script src="/static/leaflet.js"></script>
<style>
:root{
  --bg:#ffffff;--bg2:#f8fafc;--bg3:#f1f5f9;--text:#1e293b;--text2:#64748b;--text3:#94a3b8;
  --panel:rgba(255,255,255,0.92);--panel-border:rgba(0,0,0,0.08);
  --card:#ffffff;--card-border:#e2e8f0;--card-hover:#f8fafc;
  --accent:#2563eb;--accent2:#3b82f6;--accent-bg:rgba(37,99,235,0.08);
  --green:#16a34a;--red:#dc2626;--orange:#ea580c;--purple:#9333ea;--pink:#ec4899;--teal:#0d9488;
  --shadow:0 4px 24px rgba(0,0,0,0.06);--shadow2:0 8px 32px rgba(0,0,0,0.1);
  --radius:14px;--radius2:10px;
  --tile-url:https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png;
}
[data-theme="dark"]{
  --bg:#0f172a;--bg2:#1e293b;--bg3:#334155;--text:#e2e8f0;--text2:#94a3b8;--text3:#64748b;
  --panel:rgba(15,23,42,0.92);--panel-border:rgba(255,255,255,0.08);
  --card:#1e293b;--card-border:#334155;--card-hover:#334155;
  --accent:#3b82f6;--accent2:#60a5fa;--accent-bg:rgba(59,130,246,0.15);
  --shadow:0 4px 24px rgba(0,0,0,0.3);--shadow2:0 8px 32px rgba(0,0,0,0.4);
  --tile-url:https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);transition:background .3s,color .3s}
#map{height:100vh;width:100%;position:fixed;top:0;left:0}
.pnl{position:fixed;top:10px;right:10px;z-index:1000;background:var(--panel);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);padding:0;border-radius:var(--radius);box-shadow:var(--shadow2);width:380px;max-height:92vh;border:1px solid var(--panel-border);display:flex;flex-direction:column;transition:background .3s}
.pnl-header{padding:12px 16px;border-bottom:1px solid var(--card-border);flex-shrink:0;position:relative}
.pnl-body{overflow-y:auto;padding:12px 14px;flex:1;transition:opacity 0.2s}
.pnl-toggle { position:fixed; left:50%; transform:translateX(-50%); background:var(--accent); border:none; width:56px; height:36px; border-radius:0 0 18px 18px; display:none; align-items:center; justify-content:center; cursor:pointer; z-index:1001; color:#fff; box-shadow:0 4px 16px rgba(0,0,0,0.3); transition:transform .2s,top .3s ease; }
.pnl-toggle:active { transform:translateX(-50%) scale(0.92); }
@media(max-width:480px){
  .pnl-toggle { display:flex; }
  .pnl{width:calc(100% - 16px);right:8px;top:8px;max-height:94vh;border-radius:12px;transition:max-height .3s ease;overflow:hidden}
  .pnl.minimized{max-height:72px;overflow:visible}
  .pnl.minimized .pnl-body, .pnl.minimized .pnl-footer { display:none; }
}
.pnl-footer{padding:10px 14px;border-top:1px solid var(--card-border);font-size:.65rem;color:var(--text);font-weight:600;text-align:center;flex-shrink:0;background:var(--bg2)}
.pnl-footer a{color:var(--accent);text-decoration:none}
/* Top bar */
.top-bar{display:flex;flex-direction:column;gap:12px;margin-bottom:12px}
.brand{display:flex;align-items:center;justify-content:center;gap:16px;width:100%}
.brand img{height:54px;width:auto;transition:transform .2s;filter:drop-shadow(0 2px 4px rgba(0,0,0,.2))}
.brand img:hover{transform:scale(1.05)}
.top-actions{display:flex;gap:8px;align-items:center;justify-content:flex-end;width:100%}
.right-btns{display:flex;gap:6px;align-items:center}
.theme-btn{background:var(--bg3);border:none;width:40px;height:40px;border-radius:10px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.2rem;transition:all .2s;color:var(--text);border:1px solid var(--card-border)}
.theme-btn:hover{background:var(--accent-bg);transform:scale(1.1)}

/* Warning */
.warn-bar{background:#fff3cd;color:#856404;padding:6px 12px;font-size:.6rem;text-align:center;border-bottom:1px solid #ffeeba}
[data-theme="dark"] .warn-bar{background:rgba(255,243,205,0.1);color:#fbbf24;border-color:rgba(251,191,36,0.2)}

/* Tabs */
.tabs{display:flex;gap:3px;padding:8px 14px;border-bottom:1px solid var(--card-border);flex-shrink:0}
.tab{flex:1;padding:8px 4px;text-align:center;background:transparent;border:none;border-radius:var(--radius2);cursor:pointer;font-size:.72rem;font-weight:600;color:var(--text2);transition:all .2s;font-family:inherit;display:flex;flex-direction:column;align-items:center;gap:4px}
.tab svg{width:20px;height:20px;stroke-width:1.5;margin-bottom:2px;transition:color 0.2s}
.tab:hover{background:var(--bg3);color:var(--text)}
.tab.on{background:var(--accent);color:#fff}
.tab.on svg{color:#fff !important}

/* Search */
.src{width:100%;padding:10px 12px 10px 36px;border:1px solid var(--card-border);border-radius:var(--radius2);font-size:.82rem;background:var(--bg2);color:var(--text);transition:all .2s;outline:none;font-family:inherit}
.src:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-bg)}
.src-wrap{position:relative;margin-bottom:10px}
.src-wrap svg{position:absolute;left:10px;top:50%;transform:translateY(-50%);width:16px;height:16px;color:var(--text3)}

/* Category Grid */
.kg{display:flex;gap:6px;flex-wrap:wrap;padding-bottom:8px;margin-bottom:10px;justify-content:center}
.kb{display:flex;flex-direction:column;align-items:center;gap:3px;padding:8px 8px;border-radius:var(--radius2);cursor:pointer;font-size:.55rem;font-weight:600;color:var(--text);transition:all .2s;white-space:nowrap;min-width:48px;max-width:70px;background:var(--bg2);border:1px solid var(--card-border);flex:0 0 auto}
.kb:hover{background:var(--bg3);border-color:var(--accent)}
.kb.on{background:var(--accent-bg);color:var(--accent);border-color:var(--accent)}
.kb .i{font-size:1.1rem}

/* List */
.lst{max-height:340px;overflow-y:auto;scrollbar-width:thin}

/* Line Items */
.it{padding:10px 12px;margin:4px 0;background:var(--card);border-radius:var(--radius2);cursor:pointer;display:flex;justify-content:space-between;align-items:center;border-left:4px solid var(--text3);font-size:.8rem;transition:all .15s;border:1px solid var(--card-border);border-left:4px solid var(--text3)}
.it:hover{background:var(--card-hover);transform:translateX(2px);box-shadow:var(--shadow)}
.it.otobus{border-left-color:#2563eb}.it.ekspres{border-left-color:#9333ea}.it.ring{border-left-color:#f59e0b}
.it.havalimani{border-left-color:#dc2626}.it.ilce{border-left-color:#0d9488}.it.tramvay{border-left-color:#ea580c}
.it.teleferik{border-left-color:#ec4899}.it.tekne{border-left-color:#0284c7}.it.odak{border-left-color:#16a34a}

/* Buttons */
.bk{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border:none;padding:10px;border-radius:var(--radius2);cursor:pointer;width:100%;margin-bottom:10px;font-weight:600;font-size:.8rem;transition:all .2s;font-family:inherit}
.bk:hover{opacity:.9;transform:translateY(-1px)}

/* Section headers */
.sec{background:var(--bg3);color:var(--text);padding:8px 12px;font-size:.75rem;font-weight:700;border-radius:var(--radius2);margin:10px 0 6px 0}
.dhead{background:var(--bg3);color:var(--text);padding:6px 10px;font-size:.75rem;font-weight:700;border-radius:6px;margin:10px 0 4px 0}

/* Durak cards */
.drk{padding:8px 10px;margin:3px 0;background:var(--card);border-radius:8px;display:flex;align-items:center;gap:8px;cursor:pointer;border:1px solid var(--card-border);font-size:.75rem;transition:all .15s}
.drk:hover{border-color:var(--accent);background:var(--card-hover)}
.drk .no{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:700;color:#fff;flex-shrink:0;background:#34495e}

/* Price box */
.fiyat{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:14px;border-radius:var(--radius2);margin:10px 0;text-align:center}
.fiyat .t{font-size:.7rem;opacity:.9}.fiyat .pv{font-size:1.8rem;font-weight:700;margin:4px 0}.fiyat .s{font-size:.65rem;opacity:.8}

/* Info cards */
.ig{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:10px 0}
.ic{background:var(--bg2);padding:12px;border-radius:var(--radius2);text-align:center;border:1px solid var(--card-border)}
.ic .v{font-size:1.4rem;font-weight:700;color:var(--accent)}.ic .l{font-size:.7rem;color:var(--text2);margin-top:2px}

/* Vehicle cards */
.arac{display:flex;justify-content:space-between;padding:8px;background:var(--card);border-radius:8px;margin:4px 0;border-left:3px solid #f59e0b;font-size:.75rem;border:1px solid var(--card-border);border-left:3px solid #f59e0b}
.arac .pl{font-weight:700;color:var(--orange)}
.araclar{background:var(--card);padding:10px;border-radius:var(--radius2);margin:10px 0;border:1px solid var(--card-border)}
.araclar .t{font-size:.8rem;font-weight:700;margin-bottom:8px;color:var(--text)}

/* Schedule */
.saat{background:var(--card);padding:10px;border-radius:var(--radius2);margin:10px 0;border:1px solid var(--card-border)}
.saat .t{font-size:.8rem;font-weight:700;margin-bottom:8px;color:var(--text)}
.saatlar{display:grid;grid-template-columns:repeat(auto-fill,minmax(50px,1fr));gap:4px}
.saatlar span{background:var(--bg2);padding:5px;border-radius:6px;text-align:center;font-size:.72rem;font-weight:600;border:1px solid var(--card-border);color:var(--text)}
.saattab{display:flex;gap:4px;margin-bottom:8px}
.saattab div{flex:1;padding:6px;text-align:center;background:var(--bg2);border-radius:6px;cursor:pointer;font-size:.7rem;font-weight:600;color:var(--text2);transition:all .2s;border:1px solid var(--card-border)}
.saattab div:hover{background:var(--bg3)}.saattab div.on{background:var(--accent);color:#fff;border-color:var(--accent)}

/* Sefer cards */
.sfr{background:var(--bg2);padding:8px;margin:4px 0;border-radius:8px;font-size:.7rem;border-left:3px solid var(--purple)}
.sfr .st{font-weight:700;color:var(--purple);font-size:.8rem}.sfr .fr{color:var(--text2);font-weight:600}

/* Badges */
.bd{padding:2px 6px;border-radius:8px;font-size:.55rem;font-weight:700}.bd.g{background:var(--accent);color:#fff}.bd.d{background:var(--red);color:#fff}
.vtg{background:var(--green);color:#fff;padding:2px 6px;border-radius:4px;font-size:.6rem;font-weight:700;margin-left:8px}
.live-badge{background:var(--green);color:#fff;padding:4px 8px;border-radius:6px;font-size:.7rem;font-weight:700;margin-top:4px;display:inline-block;animation:blink 2s infinite}
@keyframes blink{0%{opacity:1}50%{opacity:.7}100%{opacity:1}}
.tel{background:var(--bg2);padding:10px;border-radius:var(--radius2);margin:8px 0;text-align:center;border:1px solid var(--card-border)}
.tel a{color:var(--accent);font-weight:700;font-size:.9rem;text-decoration:none}
.no-data{text-align:center;padding:30px;color:var(--text3)}.loading{text-align:center;padding:25px;color:var(--text3)}
.inf{flex:1}.ad{font-weight:600;color:var(--text)}.fyt{display:block;font-size:.65rem;color:var(--text2);margin-top:2px}
.hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.pbtn{background:var(--red);color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:.7rem;font-weight:600;font-family:inherit}

/* Toast */
.toast{visibility:hidden;min-width:250px;background:var(--bg3);color:var(--text);text-align:center;border-radius:12px;padding:12px 16px;position:fixed;z-index:9999;left:50%;bottom:30px;transform:translateX(-50%);font-size:.8rem;box-shadow:var(--shadow2);backdrop-filter:blur(12px);border:1px solid var(--card-border)}
.toast.show{visibility:visible;animation:fadein .4s,fadeout .4s 2.6s}
@keyframes fadein{from{bottom:0;opacity:0}to{bottom:30px;opacity:1}}
@keyframes fadeout{from{bottom:30px;opacity:1}to{bottom:0;opacity:0}}
@keyframes pulse{0%{transform:translateX(-50%) scale(1)}50%{transform:translateX(-50%) scale(1.05)}100%{transform:translateX(-50%) scale(1)}}

/* Route cards */
.route-card{background:var(--card);border-radius:12px;box-shadow:var(--shadow);margin-bottom:12px;overflow:hidden;transition:transform .2s;border-left:5px solid var(--accent);border:1px solid var(--card-border);border-left:5px solid var(--accent)}
.route-card:hover{transform:translateY(-2px)}.route-card.direct{border-left-color:var(--green)}.route-card.transfer{border-left-color:#f59e0b}
.route-header{background:var(--bg2);padding:10px 15px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--card-border)}
.route-icon{font-size:1.3em;margin-right:8px}.route-code{font-weight:700;font-size:1.1em;color:var(--text)}.route-info{font-weight:600;color:var(--text2);font-size:.85em}.route-time{font-weight:700;color:var(--text2);font-size:.85em}
.route-details{padding:12px;font-size:.9em;line-height:1.6;color:var(--text)}
.step{margin:5px 0;display:flex;align-items:center}.step i{width:20px;text-align:center;margin-right:10px}
.route-details.timeline{padding:0}
.timeline .step{display:flex;position:relative;padding-bottom:15px}.timeline .step:last-child{padding-bottom:0}
.timeline .time{width:50px;text-align:right;font-weight:700;color:var(--text2);font-size:.85rem;padding-right:10px;padding-top:2px}
.timeline .content{flex:1;padding-left:15px;font-size:.9rem;padding-top:2px;color:var(--text)}.timeline .content .sub{font-size:.75rem;color:var(--text3);margin-top:2px}
.timeline .dot{width:12px;height:12px;border-radius:50%;background:var(--text3);border:2px solid var(--card);box-shadow:0 0 0 2px var(--text3);position:absolute;left:56px;top:6px;z-index:2}
.timeline .dot.start{background:var(--green);box-shadow:0 0 0 2px var(--green)}.timeline .dot.end{background:var(--red);box-shadow:0 0 0 2px var(--red)}.timeline .dot.transfer{background:#f59e0b;box-shadow:0 0 0 2px #f59e0b}
.timeline .line{position:absolute;left:61px;top:0;bottom:0;width:2px;background:var(--card-border);z-index:1}
.route-badge{background:var(--bg2);padding:2px 8px;border-radius:4px;font-weight:700;font-size:.85rem;margin-right:5px;color:var(--text)}
.rota-box{background:var(--bg2);padding:10px;border-left:4px solid #f59e0b;margin-bottom:8px;border-radius:6px;cursor:pointer}

/* ===== RESPONSIVE SCALING ===== */
html{font-size:clamp(14px, 1.5vw, 22px)}
@media(min-width:768px) and (max-width:1199px){
  .pnl{width:420px}
  .brand img{height:clamp(50px,7vw,70px)}
  .tab{font-size:clamp(.7rem,1vw,.85rem);padding:10px 6px}
  .tab svg{width:clamp(20px,2.5vw,28px);height:clamp(20px,2.5vw,28px)}
  .kb{font-size:clamp(.55rem,.8vw,.7rem);padding:10px;min-width:56px;max-width:80px}
  .kb .i{font-size:clamp(1.1rem,1.5vw,1.4rem)}
  .it{font-size:clamp(.78rem,1vw,.92rem);padding:12px 14px}
  .bk{font-size:clamp(.78rem,1vw,.92rem);padding:12px}
  .src{font-size:clamp(.8rem,1vw,.95rem);padding:12px 14px 12px 40px}
  .sec{font-size:clamp(.75rem,1vw,.88rem);padding:10px 14px}
  .drk{font-size:clamp(.75rem,.9vw,.88rem);padding:10px 12px}
  .drk .no{width:28px;height:28px;font-size:clamp(.65rem,.8vw,.75rem)}
  .ic .v{font-size:clamp(1.4rem,2vw,1.8rem)}
  .ic .l{font-size:clamp(.7rem,.9vw,.82rem)}
  .araclar .t,.saat .t{font-size:clamp(.8rem,1vw,.95rem)}
  .sfr{font-size:clamp(.7rem,.9vw,.82rem)}
  .sfr .st{font-size:clamp(.8rem,1vw,.92rem)}
  .tel a{font-size:clamp(.85rem,1.1vw,1rem)}
  .warn-bar{font-size:clamp(.6rem,.75vw,.72rem)}
  .pnl-footer{font-size:clamp(.6rem,.75vw,.72rem)}
}
@media(min-width:1200px){
  .pnl{width:clamp(400px,28vw,520px)}
  .brand img{height:clamp(56px,4.5vw,80px)}
  .tab{font-size:clamp(.75rem,.65vw,.95rem);padding:12px 8px}
  .tab svg{width:clamp(22px,1.8vw,32px);height:clamp(22px,1.8vw,32px)}
  .kb{font-size:clamp(.58rem,.5vw,.75rem);padding:10px 12px;min-width:60px;max-width:90px}
  .kb .i{font-size:clamp(1.2rem,1.2vw,1.6rem)}
  .it{font-size:clamp(.82rem,.7vw,1rem);padding:14px 16px}
  .bk{font-size:clamp(.82rem,.7vw,1rem);padding:14px}
  .src{font-size:clamp(.82rem,.7vw,1rem);padding:14px 16px 14px 44px}
  .sec{font-size:clamp(.78rem,.65vw,.95rem);padding:10px 16px}
  .drk{font-size:clamp(.78rem,.65vw,.92rem);padding:12px 14px}
  .drk .no{width:clamp(26px,2vw,34px);height:clamp(26px,2vw,34px);font-size:clamp(.65rem,.55vw,.8rem)}
  .ic .v{font-size:clamp(1.5rem,1.4vw,2.2rem)}
  .ic .l{font-size:clamp(.72rem,.6vw,.92rem)}
  .araclar .t,.saat .t{font-size:clamp(.85rem,.7vw,1.05rem)}
  .arac{font-size:clamp(.78rem,.65vw,.95rem)}
  .sfr{font-size:clamp(.72rem,.6vw,.88rem)}
  .sfr .st{font-size:clamp(.82rem,.7vw,1rem)}
  .tel a{font-size:clamp(.9rem,.8vw,1.15rem)}
  .warn-bar{font-size:clamp(.62rem,.5vw,.78rem)}
  .pnl-footer{font-size:clamp(.62rem,.5vw,.78rem)}
  .fiyat .pv{font-size:clamp(1.8rem,1.8vw,2.8rem)}
  .fiyat .t{font-size:clamp(.72rem,.6vw,.9rem)}
  .toast{font-size:clamp(.8rem,.7vw,1rem);min-width:clamp(250px,20vw,400px)}
  .theme-btn{width:clamp(40px,3vw,52px);height:clamp(40px,3vw,52px);font-size:clamp(1.2rem,1.1vw,1.6rem)}
  .route-code{font-size:clamp(1.1em,1vw,1.4em)}
  .route-info,.route-time{font-size:clamp(.85em,.7vw,1.05em)}
  .route-details{font-size:clamp(.9em,.75vw,1.1em)}
}
@media(min-width:1600px){
  .pnl{width:clamp(480px,26vw,600px)}
}
</style>
</head>

<body>
<div id="toast" class="toast">Mesaj</div>
<div id="map"></div>
<div class="pnl">
<div class="warn-bar">
    ⚠️ <b>YASAL UYARI:</b> Resmi uygulama değildir. Veriler açık kaynaklardan sağlanmaktadır.
</div>
<div class="pnl-header">
    <div class="top-bar">
        <div class="brand">
            <img id="sbbLogo" src="/static/images/sbb_v2.png?v=2" title="Samsun Büyükşehir Belediyesi">
            <img id="samulasLogo" src="/static/images/samulas.png?v=2" title="Samulaş">
        </div>
        <div class="top-actions" style="justify-content:center">
            <div id="weatherWidget" style="font-size:0.85rem;font-weight:700;display:flex;align-items:center;gap:6px;color:var(--text);padding:4px 10px;background:var(--bg3);border-radius:20px;box-shadow:var(--shadow1)">⏳ --°C</div>
            <div class="right-btns">
                <button class="theme-btn" id="settingsBtn" onclick="toggleSettings()" title="Ayarlar">⚙️</button>
                <button class="theme-btn" id="themeToggle" onclick="toggleTheme()" title="Tema Değiştir">🌙</button>
            </div>
        </div>
        <div id="settingsPanel" style="display:none;position:absolute;top:110px;right:10px;background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:14px;box-shadow:var(--shadow2);z-index:100;width:240px;font-size:.75rem">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><div style="font-weight:700;font-size:.85rem">⚙️ Ayarlar</div><button onclick="closeSettings()" style="background:none;border:none;font-size:1.1rem;cursor:pointer;color:var(--text)">✕</button></div>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:6px 0;border-bottom:1px solid var(--card-border)"><input type="checkbox" id="chkHasilat" onchange="saveSetting('showHasilat',this.checked)" style="width:16px;height:16px;accent-color:var(--accent)"> 💰 Günlük Hasılat</label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:6px 0;border-bottom:1px solid var(--card-border)"><input type="checkbox" id="chkLabels" onchange="saveSetting('showLabels',this.checked)" style="width:16px;height:16px;accent-color:var(--accent)" checked> 🏷️ Durak İsimleri</label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:6px 0;border-bottom:1px solid var(--card-border)"><input type="checkbox" id="chkRoute" onchange="saveSetting('showRoute',this.checked)" style="width:16px;height:16px;accent-color:var(--accent)" checked> 🗺️ Güzergah Çizgisi</label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:6px 0;border-bottom:1px solid var(--card-border)"><input type="checkbox" id="chkAutoRefresh" onchange="saveSetting('autoRefresh',this.checked)" style="width:16px;height:16px;accent-color:var(--accent)" checked> 🔄 Otomatik Yenileme (5sn)</label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:6px 0;border-bottom:1px solid var(--card-border)"><input type="checkbox" id="chkAllStops" onchange="saveSetting('showAllStops',this.checked);toggleAllStops(this.checked)" style="width:16px;height:16px;accent-color:var(--accent)"> 📍 Tüm Durakları Göster</label>
            <button onclick="resetSettings()" style="margin-top:10px;width:100%;padding:8px;background:var(--bg3);border:1px solid var(--card-border);border-radius:8px;cursor:pointer;font-size:.7rem;font-weight:600;color:var(--text);font-family:inherit">🔄 Varsayılana Çevir</button>
        </div>
    </div>
</div>
<div class="tabs">
    <div class="tab on" data-t="hat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:24px;height:24px;margin-bottom:2px;color:#3b82f6"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M2 9h20"/><circle cx="7" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/><path d="M7 17.5v1M17 17.5v1"/><path d="M2 13h1M21 13h1"/><path d="M7 9v5M12 9v5M17 9v5"/></svg> Hatlar</div>
    <div class="tab" data-t="yakin"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:24px;height:24px;margin-bottom:2px"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> Yakın</div>
    <div class="tab" data-t="odak"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:24px;height:24px;margin-bottom:2px;color:#16a34a"><path d="M12 2L2 22h20L12 2z"/><path d="M12 8v6M12 18h.01"/></svg> Odak</div>
    <div class="tab" data-t="samair" style="justify-content:center"><img src="/static/images/samair.png" style="height:28px;width:auto;object-fit:contain;margin-bottom:0"> Samair</div>
    <div class="tab" data-t="rota" onclick="shRotaUI()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:24px;height:24px;margin-bottom:2px"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg> Git</div>
</div>
<div class="pnl-toggle" id="pnlToggle" onclick="togglePnl()" title="Paneli Küçült/Büyüt">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width:16px;height:16px"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
</div>
<div class="pnl-body" id="ct"></div>
<div class="pnl-footer">
    ⚠️ <b>YASAL UYARI:</b> Değerler anlık değişebilir. Resmi uygulama değildir.<br>
    📞 İletişim: Samsun içi <a href="tel:153">153</a>, dışı <a href="tel:03624311012">0362 431 10 12</a><br>
    <div style="display:flex;gap:12px;justify-content:center;align-items:center;margin-top:4px">
    <a href="https://github.com/tarihcituranx" target="_blank" style="display:inline-flex;align-items:center;gap:4px;color:var(--text3);text-decoration:none;font-size:.6rem"><svg viewBox="0 0 16 16" fill="currentColor" style="width:14px;height:14px"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>tarihcituranx</a>
    <a href="https://samsunkesfet.com" target="_blank" style="color:var(--text3);text-decoration:none;font-size:.6rem">🏛️ samsunkesfet.com</a>
    </div>
</div>
</div>
<!-- Aktarma Kuralları Modalı -->
<div id="aktarmaModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:9999;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px)">
    <div style="background:var(--panel);width:100%;max-width:400px;border-radius:16px;padding:20px;box-shadow:var(--shadow2);border:1px solid var(--card-border);max-height:85vh;overflow-y:auto">
        <h3 style="margin-bottom:12px;color:var(--text);display:flex;align-items:center;gap:8px">🔄 Aktarma Kuralları</h3>
        
        <div style="font-size:0.75rem;color:var(--text);line-height:1.5;margin-bottom:16px">
            <h4 style="color:var(--accent);margin:10px 0 4px 0">1 saat içinde yapılan:</h4>
            <ul style="margin-left:20px;color:var(--text2)">
                <li>Otobüs → Otobüs</li>
                <li>Otobüs → Hafif Raylı Sistem</li>
                <li>Hafif Raylı Sistem → Otobüs</li>
            </ul>
            <p style="margin-top:4px">Aktarmalar <b>ÜCRETSİZDİR</b>.</p>

            <h4 style="color:var(--orange);margin:12px 0 4px 0">1 saat sonrasında yapılan aktarmalar:</h4>
            <p style="color:var(--text2)">8,00 TL ücretlendirilir.</p>

            <h4 style="color:var(--accent);margin:12px 0 4px 0">Düşük ücretli hattan yüksek ücretli hatta geçiş:</h4>
            <p style="color:var(--text2)">Aradaki ücret farkı tahsil edilir.</p>

            <h4 style="color:var(--green);margin:12px 0 4px 0">Aynı veya daha düşük ücretli hatta geçiş:</h4>
            <p style="color:var(--text2)">Ek ücret alınmaz.</p>

            <br>
            <h4 style="color:var(--red);margin:10px 0 4px 0">İADE / ÜCRET DÜZELTME DURUMLARI</h4>
            <ul style="margin-left:20px;color:var(--text2)">
                <li style="margin-bottom:4px">1 saat içindeki ücretsiz aktarmalarda ücret iadesi yapılmaz (zaten ücret alınmaz).</li>
                <li style="margin-bottom:4px">Daha düşük ücretli hatta geçişlerde iade yapılmaz; sistem ek ücret tahsil etmez.</li>
                <li style="margin-bottom:4px">Yüksek ücretli hatta geçişte fark ücreti alınır; iade söz konusu değildir.</li>
                <li style="margin-bottom:4px">1 saat sonrasında yapılan aktarmalarda tahsil edilen 8,00 TL iade edilmez.</li>
                <li style="margin-bottom:4px">Abonman binişlerinde ücret iadesi uygulanmaz (biniş hakkı düşer).</li>
                <li style="margin-bottom:4px">Kart kaybı durumunda kart bedeli iade edilmez.</li>
            </ul>
        </div>
        <button onclick="document.getElementById('aktarmaModal').style.display='none'" style="background:var(--accent);color:#fff;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;font-weight:600;font-family:inherit;width:100%">Kapat</button>
    </div>
</div>

<!-- Bilgilendirme Modalı -->
<div id="infoModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;align-items:center;justify-content:center">
    <div style="background:var(--card);padding:24px;border-radius:16px;width:85%;max-width:400px;text-align:center;border:1px solid var(--card-border)">
        <h3 style="color:var(--orange);margin-bottom:10px">⚠️ Önemli Bilgilendirme</h3>
        <p style="font-size:0.85rem;color:var(--text);margin-bottom:15px">
            Görüntülenen fiyatlar ve sefer bilgileri tahmini olabilir. 
            Özellikle <b>Odak (Turistik)</b> hatlarında fiyatlar farklılık gösterebilir.
        </p>
        <p style="font-size:0.75rem;color:var(--text2);margin-bottom:20px">
            Kesin bilgi için lütfen araç kaptanlarına danışınız.<br>
            📞 Samsun içi: <a href="tel:153" style="color:var(--accent)">153</a><br>
            📞 Samsun dışı: <a href="tel:03624311012" style="color:var(--accent)">0362 431 10 12</a>
        </p>
        <div style="display:flex;align-items:center;justify-content:space-between">
            <label style="font-size:0.7rem;color:var(--text2);display:flex;align-items:center;gap:5px;cursor:pointer"><input type="checkbox" id="chkGosterme"> Bir daha gösterme</label>
            <button onclick="closeInfoModal()" style="background:var(--accent);color:#fff;border:none;padding:8px 20px;border-radius:8px;cursor:pointer;font-weight:600;font-family:inherit">Anladım</button>
        </div>
    </div>
</div>

<script>
function closeInfoModal() {
    if(document.getElementById('chkGosterme').checked) {
        localStorage.setItem('hideInfoModal', 'true');
    }
    document.getElementById('infoModal').style.display='none';
}
window.addEventListener('DOMContentLoaded', () => {
    if(localStorage.getItem('hideInfoModal') !== 'true') {
        document.getElementById('infoModal').style.display='flex';
    }
});
// ===== THEME SYSTEM =====
function getPreferredTheme(){
    const saved=localStorage.getItem('theme');
    if(saved) return saved;
    return window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';
}
function applyTheme(t){
    document.documentElement.setAttribute('data-theme',t);
    const btn=document.getElementById('themeToggle');
    if(btn) btn.textContent=t==='dark'?'☀️':'🌙';
    localStorage.setItem('theme',t);
    
    // Logo Degisimi
    const sbb=document.querySelector('.brand img[title="Samsun Büyükşehir Belediyesi"]') || document.getElementById('sbbLogo');
    const sam=document.querySelector('.brand img[title="Samulaş"]') || document.getElementById('samulasLogo');
    if(sbb) sbb.src=t==='dark'?'/static/images/sbb_dark.png':'/static/images/sbb_v2.png?v=2';
    if(sam) sam.src=t==='dark'?'/static/images/samulas_3.png':'/static/images/samulas.png?v=2';

    if(typeof updateMapTiles==='function') updateMapTiles(t);
}
function toggleTheme(){
    const cur=document.documentElement.getAttribute('data-theme')||'light';
    applyTheme(cur==='dark'?'light':'dark');
}
window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',e=>{
    if(!localStorage.getItem('theme')) applyTheme(e.matches?'dark':'light');
});

// ===== MAP =====
const map=L.map('map',{zoomControl:true,attributionControl:false}).setView([41.29,36.33],12);
let _tileLayer=null;
function updateMapTiles(theme){
    if(_tileLayer) map.removeLayer(_tileLayer);
    const url=theme==='dark'
        ?'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        :'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    const attr=theme==='dark'
        ?'&copy; <a href="https://carto.com/attributions">CARTO</a>'
        :'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
    _tileLayer=L.tileLayer(url,{attribution:attr,maxZoom:19}).addTo(map);
}
updateMapTiles(getPreferredTheme());
applyTheme(getPreferredTheme());

// ===== GLOBALS =====
let M={}, V=[], H=[], cur='hat', sK=null, liveT=null, userLoc=null, targetLoc=null;
const K={dil:{i:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>',n:'Tümü',c:'#333'},
otobus:{i:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%;color:#3b82f6"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M2 9h20"/><circle cx="7" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/><path d="M7 17.5v1M17 17.5v1"/><path d="M2 13h1M21 13h1"/><path d="M7 9v5M12 9v5M17 9v5"/></svg>',n:'Otobüs',c:'#3b82f6'},
ekspres:{i:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%;color:#8b5cf6"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M2 9h20"/><circle cx="7" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/><path d="M7 17.5v1M17 17.5v1"/><path d="M2 13h1M21 13h1"/><path d="M7 9v5M12 9v5M17 9v5"/></svg>',n:'Ekspres',c:'#8b5cf6'},
tramvay:{i:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%;color:#10b981"><rect x="4" y="5" width="16" height="14" rx="2"/><path d="M4 10h16"/><path d="M8 5V3M16 5V3"/><path d="M3 3h18"/><circle cx="8.5" cy="17" r="1.2"/><circle cx="15.5" cy="17" r="1.2"/><path d="M6 21l2-2.5M18 21l-2-2.5"/><path d="M8 10v5M12 10v5M16 10v5"/></svg>',n:'Tramvay',c:'#10b981'},
ring:{i:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%;color:#f59e0b"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M2 9h20"/><circle cx="7" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/><path d="M7 17.5v1M17 17.5v1"/><path d="M2 13h1M21 13h1"/><path d="M7 9v5M12 9v5M17 9v5"/></svg>',n:'Ring',c:'#f59e0b'},
tekne:{i:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%;color:#0ea5e9"><path d="M3 17l1.5-7h15l1.5 7"/><path d="M2 20c1.5-2 3-2 4.5 0s3 2 4.5 0 3 2 4.5 0 3-2 4.5 0"/><rect x="7" y="7" width="10" height="3" rx="1"/><path d="M12 7V4M9 4h6"/><path d="M5 10h14"/></svg>',n:'Vapur',c:'#0ea5e9'},
odak:{i:'<img src="/static/images/odak.png" style="width:100%;height:100%;object-fit:contain">',n:'',c:'transparent'},
teleferik:{i:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%;color:#ec4899"><path d="M2 6l20-2"/><path d="M7 6l-1 2h12l-1-2"/><rect x="6" y="8" width="12" height="8" rx="2"/><path d="M9 8v8M15 8v8"/><circle cx="12" cy="5.5" r="1"/></svg>',n:'Teleferik',c:'#ec4899'},
havalimani:{i:'<img src="/static/images/samair.png" style="width:100%;height:100%;object-fit:contain">',n:'',c:'transparent'},
ilce:{i:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%;color:#ef4444"><path d="M1 10l2-5h14l4 5v6H1z"/><path d="M1 10h19"/><circle cx="6" cy="18" r="1.5"/><circle cx="16" cy="18" r="1.5"/><path d="M6 16.5V19M16 16.5V19"/><rect x="4" y="11" width="4" height="3" rx="0.5"/><rect x="10" y="11" width="4" height="3" rx="0.5"/></svg>',n:'İlçe',c:'#ef4444'}};

const busIcon=(c,p)=>L.divIcon({className:'',html:`<div style="position:relative"><div style="width:30px;height:30px;background:${c};border-radius:50%;border:2px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;font-size:14px">🚌</div><div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:#222;color:#fff;padding:1px 5px;border-radius:3px;font-size:9px;white-space:nowrap;z-index:99">${p}</div></div>`,iconSize:[30,30],iconAnchor:[15,15]});
const bI=busIcon;
const stopIcon=(n)=>L.divIcon({className:'',html:`<div style="width:18px;height:18px;background:#34495e;border-radius:50%;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.3);color:#fff;font-size:9px;display:flex;align-items:center;justify-content:center;font-weight:700">${n}</div>`,iconSize:[18,18],iconAnchor:[9,9]});
const dI=(n,c)=>L.divIcon({className:'',html:`<div style="width:18px;height:18px;background:${c};border-radius:50%;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.3);color:#fff;font-size:9px;display:flex;align-items:center;justify-content:center;font-weight:700">${n}</div>`,iconSize:[18,18],iconAnchor:[9,9]});
const clr=()=>{if(liveT)clearInterval(liveT);Object.values(M).forEach(m=>map.removeLayer(m));Object.values(V).forEach(m=>map.removeLayer(m));M={};V={};};

function showToast(msg){const x=document.getElementById("toast");x.innerText=msg;x.className="toast show";setTimeout(()=>{x.className=x.className.replace("show","")},3000)}

// ===== INIT =====
const weaI={'-9999':'cloudy','A':'clear-day','AB':'cloudy-1-day','PB':'cloudy-2-day','CB':'cloudy-3-day','HY':'rainy-1','Y':'rainy-2','KY':'rainy-3','KKY':'rain-and-snow-mix','HK':'snowy-1','K':'snowy-2','YY':'snowy-3','S':'fog','D':'haze','P':'haze','GSY':'thunderstorms','KGY':'thunderstorms','SY':'thunderstorms','MSY':'thunderstorms','DY':'thunderstorms','R':'wind','GKR':'wind','GG':'thunderstorms','GKR':'wind'};
const hadiseAd={'-9999':'Bilinmiyor','A':'Açık','AB':'Az Bulutlu','PB':'Parçalı Bulutlu','CB':'Çok Bulutlu','HY':'Hafif Yağmurlu','Y':'Yağmurlu','KY':'Kuvvetli Yağmur','KKY':'Karla Karışık Yağmur','HK':'Hafif Kar','K':'Kar Yağışlı','YY':'Yoğun Kar','S':'Sisli','D':'Dumanlı','P':'Puslu','GSY':'Gök Gürültülü Sağanak','KGY':'Kuvvetli Sağanak','SY':'Sağanak Yağışlı','MSY':'Mevzii Sağanak','DY':'Dolu','R':'Rüzgarlı','GKR':'Kum Fırtınası','GG':'Gök Gürültülü'};
async function fetchWeather() {
    try {
        const res = await fetch('/api/hava');
        const data = await res.json();
        const wWidget = document.getElementById('weatherWidget');
        if (data && data.sicaklik !== undefined && data.sicaklik !== null) {
            const temp = Number(data.sicaklik).toFixed(1);
            const isNight = new Date().getHours() < 6 || new Date().getHours() > 19;
            let iconName = weaI[data.hadise] || 'cloudy';
            // Adjust for night icons
            if (isNight && iconName.includes('-day')) iconName = iconName.replace('-day', '-night');
            
            let trTime = '';
            if (data.zaman) {
                const d = new Date(data.zaman); // Parses UTC correctly from MGM 'Z' format
                trTime = d.toLocaleTimeString('tr-TR', {timeZone: 'Europe/Istanbul', hour: '2-digit', minute:'2-digit'});
            }
            
            const hadiseName = hadiseAd[data.hadise] || data.hadise || '';
            wWidget.innerHTML = `<div style="display:flex;align-items:center;gap:8px"><img src="/static/weather-icons/animated/${iconName}.svg" style="height:40px;width:40px;filter:drop-shadow(0px 2px 3px rgba(0,0,0,0.2))"> <div style="display:flex;flex-direction:column;align-items:flex-start"><span style="font-size:0.9rem;font-weight:800">${temp}°C</span><span style="font-size:0.55rem;font-weight:500;color:var(--text2);margin-top:-2px">${hadiseName}</span></div></div>`;
            wWidget.title = `Samsun Atakum\nGüncelleme: ${trTime}`;
        } else {
            wWidget.style.display = 'none';
        }
    } catch {
        document.getElementById('weatherWidget').style.display = 'none';
    }
}

async function requestLocation(){
    const defLoc={lat:41.2925,lon:36.3315};
    if(!navigator.geolocation){userLoc=defLoc;map.setView([defLoc.lat,defLoc.lon],15);loadHats();showToast("Tarayıcınız konum servisini desteklemiyor.");return}
    // Remove locate button if exists
    const existBtn=document.getElementById('locateBtn');if(existBtn)existBtn.remove();
    navigator.geolocation.getCurrentPosition(async p=>{
        const lat=p.coords.latitude,lon=p.coords.longitude;
        if(lat<41.0||lat>41.6||lon<35.0||lon>37.0){
            userLoc=defLoc;map.setView([defLoc.lat,defLoc.lon],15);
            L.marker([defLoc.lat,defLoc.lon]).addTo(map).bindPopup("Varsayılan Konum (Samsun)").openPopup();
            showToast("Samsun dışındasınız, varsayılan konuma gidildi.");
        }else{
            userLoc={lat,lon};map.setView([lat,lon],15);
            const userMarker=L.marker([lat,lon]).addTo(map).bindPopup("📍 Siz Buradasınız<br><small>Konum belirleniyor...</small>").openPopup();
            try{
                const geoRes=await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&zoom=18&addressdetails=1&accept-language=tr`);
                const geo=await geoRes.json();
                const addr=geo.address||{};
                const locName=addr.road||addr.neighbourhood||addr.suburb||addr.town||addr.city||geo.display_name||'';
                const district=addr.suburb||addr.neighbourhood||addr.town||'';
                userMarker.setPopupContent(`📍 <b>Siz Buradasınız</b><br><span style="font-size:.75rem;color:#666">${locName}${district&&district!==locName?', '+district:''}</span>`).openPopup();
            }catch(e){userMarker.setPopupContent("📍 Siz Buradasınız").openPopup();}
        }
        loadHats();
        const lb=document.getElementById('locateBtn');if(lb)lb.remove();
    },(err)=>{
        const reasons={1:'Konum izni reddedildi',2:'Konum bilgisi alınamadı',3:'Konum isteği zaman aşımına uğradı'};
        userLoc=defLoc;map.setView([defLoc.lat,defLoc.lon],15);L.marker([defLoc.lat,defLoc.lon]).addTo(map).bindPopup("Samsun Meydan").openPopup();loadHats();
        showToast(reasons[err.code]||'Konum hatası: '+err.message);console.warn('Geolocation error:',err.code,err.message);
        // Show locate button for retry (mobile needs user gesture)
        if(!document.getElementById('locateBtn')){
            const btn=document.createElement('button');btn.id='locateBtn';
            btn.innerHTML='📍 Konumumu Bul';
            btn.style.cssText='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:9999;padding:12px 24px;background:var(--accent,#3b82f6);color:#fff;border:none;border-radius:12px;font-size:.85rem;font-weight:700;cursor:pointer;box-shadow:0 4px 15px rgba(0,0,0,.3);animation:pulse 2s infinite';
            btn.onclick=()=>requestLocation();
            document.body.appendChild(btn);
        }
    },{enableHighAccuracy:true,timeout:15000,maximumAge:60000});
}
async function init(){
    applyTheme(localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'));
    fetchWeather();
    setInterval(fetchWeather, 900000);
    requestLocation();
    map.on('contextmenu',function(e){targetLoc=e.latlng;L.popup().setLatLng(e.latlng).setContent('<button onclick="calcRota()">Buraya Nasıl Giderim?</button>').openOn(map)});
}

let lastNearbyStops=[];
async function loadHats(){try{H=await(await fetch('/api/hat')).json();shH()}catch(e){}}

function shYakin(duraklar){
    if(duraklar) lastNearbyStops=duraklar; else duraklar=lastNearbyStops;
    clr();
    let x=`<div class="sec">📍 Yakınınızdaki Duraklar</div>`;
    x+=`<div class="src-wrap" style="margin:10px 0"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg><input class="src" id="durakInput" placeholder="Durak Ara (Ör: Türkiş, 12055...)" style="padding-left:36px" onkeyup="if(event.key==='Enter') araDurak()"></div><button class="bk" onclick="araDurak()" style="margin-bottom:12px">🔍 Durak Ara</button>`;
    
    x+=`<div class="lst" id="yakinList">`;
    if(duraklar && duraklar.length){
        duraklar.forEach((d,i)=>{
            x+=`<div class="drk" onclick="shDurakDetay('${d.id||d.kod}')"><span class="no">${i+1}</span><div class="inf" style="margin-left:10px"><b>${d.ad}</b><br><small style="color:var(--text2)">${d.dist?d.dist+'m uzakta':'Mesafe Bilinmiyor'}</small></div></div>`;
            M['d'+(d.id||d.kod)]=L.marker([d.lat,d.lon],{icon:stopIcon(i+1)}).addTo(map).bindPopup(d.ad);
        });
    }else x+=`<div class="no-data">Yakında durak bulunamadı. Lütfen arama yapın.</div>`;
    x+=`<button class="bk" style="margin-top:10px" onclick="loadHats()">Tüm Hatları Göster</button></div>`;
    document.getElementById('ct').innerHTML=x;
}
async function araDurak(){
    const q=document.getElementById('durakInput')?.value?.trim();
    if(!q)return;
    document.getElementById('yakinList').innerHTML='<div class="loading">Aranıyor...</div>';
    try{
        const res = await (await fetch(`/api/durak_ara?q=${encodeURIComponent(q)}`)).json();
        if(res.length){
            let h='';
            res.forEach((d,i)=>{
                h+=`<div class="drk" onclick="shDurakDetay('${d.id||d.kod}');if(window.innerWidth<=480)togglePnl(true)"><span class="no">🚏</span><div class="inf" style="margin-left:10px"><b>${d.ad}</b><br><small style="color:var(--text2)">${d.kod?'Kod: '+d.kod:'ID: '+d.id}</small></div></div>`;
                if(i===0){ map.setView([d.lat, d.lon], 16); }
            });
            document.getElementById('yakinList').innerHTML=h;
        }else{
            document.getElementById('yakinList').innerHTML='<div class="no-data">Durak bulunamadı.</div>';
        }
    }catch(e){
        document.getElementById('yakinList').innerHTML='<div class="no-data">Arama hatası.</div>';
    }
}

// ===== ROTA =====
async function shRotaUI(){clr();document.getElementById('ct').innerHTML=`<div class="sec">🧭 Yol Tarifi</div><div style="padding:10px"><div style="display:flex;align-items:center;gap:6px;margin-bottom:8px"><div style="flex:1"><div style="font-size:.6rem;font-weight:600;color:var(--text3);margin-bottom:2px">🟢 Başlangıç</div><div class="src-wrap"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg><input class="src" id="rotaStart" placeholder="Konumum" style="padding-left:36px"></div></div><button onclick="const a=document.getElementById('rotaStart'),b=document.getElementById('rotaInput');const t=a.value;a.value=b.value;b.value=t" style="background:var(--bg3);border:1px solid var(--card-border);border-radius:8px;padding:6px 8px;cursor:pointer;color:var(--text);font-size:.7rem;margin-top:12px" title="Yer Değiştir">⇅</button></div><div style="margin-bottom:8px"><div style="font-size:.6rem;font-weight:600;color:var(--text3);margin-bottom:2px">🔴 Hedef</div><div class="src-wrap"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg><input class="src" id="rotaInput" placeholder="Nereye? (Ör: Atakum, OMÜ, Meydan...)" style="padding-left:36px"></div></div><button class="bk" onclick="calcRotaFromInput()">🧭 Rota Hesapla</button><div style="text-align:center;color:var(--text3);font-size:.65rem;margin-top:4px">veya haritada sağ tıklayarak hedef seçin</div><div style="margin-top:10px;font-size:.7rem;color:var(--orange);text-align:center">⚠️ Aktarmalı Akıllı Rota hesaplanır.</div></div>`}

async function calcRotaFromInput(){const startVal=document.getElementById('rotaStart')?.value?.trim();const q=document.getElementById('rotaInput')?.value?.trim();if(!q){showToast('Lütfen bir hedef girin');return}const useMyLoc=!startVal||startVal.toLowerCase()==='konumum';if(useMyLoc&&!userLoc)return alert("Konum alınamadı!");document.getElementById('ct').innerHTML='<div class="loading">📍 Rota hesaplanıyor...<br><small>'+(startVal||'Konumum')+' → '+q+'</small></div>';try{let url;if(useMyLoc){url=`/api/rota?lat1=${userLoc.lat}&lon1=${userLoc.lon}&end=${encodeURIComponent(q)}`}else{url=`/api/rota?start=${encodeURIComponent(startVal)}&end=${encodeURIComponent(q)}`}const res=await(await fetch(url)).json();if(res.error){document.getElementById('ct').innerHTML=`<button class="bk" onclick="shRotaUI()">← Yeniden Ara</button><div class="no-data">${res.error}</div>`;return}drawRotaResults(res,(startVal||'Konumum')+' → '+q)}catch(e){document.getElementById('ct').innerHTML='<button class="bk" onclick="shRotaUI()">← Geri</button><div class="no-data">Rota hesaplanamadı.</div>'}}

async function calcRota(){if(!userLoc||!targetLoc)return alert("Konum alınamadı!");document.getElementById('ct').innerHTML='<div class="loading">Akıllı Rota Hesaplanıyor...<br><small>Otobüs ve Tramvay Aktarmaları Taranıyor</small></div>';try{const res=await(await fetch(`/api/rota?lat1=${userLoc.lat}&lon1=${userLoc.lon}&lat2=${targetLoc.lat}&lon2=${targetLoc.lng}`)).json();if(res.error){document.getElementById('ct').innerHTML=`<button class="bk" onclick="shRotaUI()">← Yeniden Ara</button><div class="no-data">${res.error}</div>`;return}drawRotaResults(res)}catch(e){document.getElementById('ct').innerHTML='<button class="bk" onclick="shRotaUI()">← Geri</button><div class="no-data">Rota hesaplanamadı.</div>'}}

function drawRotaResults(res,query){Object.keys(M).filter(k=>k.startsWith('rota_')||k.startsWith('walk_')).forEach(k=>{map.removeLayer(M[k]);delete M[k]});let x=`<button class="bk" onclick="shRotaUI();if(window.innerWidth<=480)togglePnl(false)">← Yeni Arama</button><div class="sec">🗺 Gezi Planı${query?' - '+query:''}</div><div class="lst">`;if(res.length){res.forEach((r,i)=>{x+=r.desc;if(r.polyline&&r.polyline.length>1){const color=r.type==='DIRECT'?'#d946ef':'#c2410c';const pl=L.polyline(r.polyline,{color:color,weight:6,opacity:0.85}).addTo(map);M['rota_'+i]=pl;if(i===0)map.fitBounds(pl.getBounds(),{padding:[40,40]})}if(r.walk_start&&r.walk_start.length>1){const wl=L.polyline(r.walk_start,{color:'#06b6d4',weight:4,opacity:0.9,dashArray:'8,6'}).addTo(map);M['walk_s'+i]=wl}if(r.walk_end&&r.walk_end.length>1){const wl=L.polyline(r.walk_end,{color:'#06b6d4',weight:4,opacity:0.9,dashArray:'8,6'}).addTo(map);M['walk_e'+i]=wl}})}else{x+=`<div class="no-data">Uygun toplu taşıma rotası bulunamadı.<br><small>Mesafeler çok uzak olabilir.</small></div>`}document.getElementById('ct').innerHTML=x+'</div>'}

async function shDurakDetay(kod){document.getElementById('ct').innerHTML='<div class="loading">Durak bilgileri alınıyor...</div>';try{const inf=await(await fetch(`/api/durak_panel/${kod}`)).json();let x=`<button class="bk" onclick="shYakin()">← Geri</button><div class="sec">🚏 Durak: ${kod}</div>`;Object.values(V).forEach(m=>map.removeLayer(m));V={};const activeBuses=[];if(inf.length){x+='<div style="display:flex;flex-direction:column;gap:2px">';x+='<div class="sec" style="font-size:.75rem;margin:4px 0">🚌 Geçen Hatlar</div><div class="lst" style="max-height:40vh;overflow-y:auto">';inf.forEach(h=>{x+=`<div class="it ${h.kat}" onclick="shL('${encodeURIComponent(h.hat)}')"><div><b>${h.hat}</b> - ${h.ad}</div>${h.gelen?(()=>{let vb='';if(h.gelen.verify){const v=h.gelen.verify;if(v.status==='OK')vb='<span style="color:#fff;background:var(--green);padding:1px 3px;border-radius:3px;font-size:0.55rem;margin-left:4px">✅ Doğrulandı</span>';else if(v.status==='WARN')vb=`<span style="color:#fff;background:#f59e0b;padding:1px 3px;border-radius:3px;font-size:0.55rem;margin-left:4px">⚠️ ${v.msg}</span>`;else if(v.status==='ERR')vb=`<span style="color:#fff;background:var(--red);padding:1px 3px;border-radius:3px;font-size:0.55rem;margin-left:4px">❌ ${v.msg}</span>`;else vb=`<span style="color:#fff;background:var(--accent);padding:1px 3px;border-radius:3px;font-size:0.55rem;margin-left:4px">ℹ️ ${v.msg}</span>`}if(h.gelen.lat&&h.gelen.lon){const m=L.marker([h.gelen.lat,h.gelen.lon],{icon:bI(K[h.kat].c,h.gelen.plaka)}).addTo(map).bindPopup(`<b>${h.hat}</b><br>${h.gelen.tahmini_dk} dk`);V['v'+h.gelen.plaka]=m;activeBuses.push([h.gelen.lat,h.gelen.lon])}return`<div class="live-badge">⏱️ ${h.gelen.tahmini_dk} dk (${h.gelen.durak_kaldi} durak)${vb}<br><span style="font-weight:400;font-size:0.6rem">Plaka: ${h.gelen.plaka} • Hız: ${h.gelen.hiz} km/s • ${h.gelen.doluluk} yolcu</span></div>`})():''}</div>`});x+='</div>';x+='<div class="sec" style="font-size:.75rem;margin:8px 0 4px">📍 Yaklaşan Araçlar</div><div class="lst">';const approaching=inf.filter(h=>h.gelen);if(approaching.length>0){approaching.forEach(h=>{const g=h.gelen;x+=`<div class="arac" onclick="map.setView([${g.lat},${g.lon}],16)" style="padding:8px 10px"><div style="display:flex;justify-content:space-between;align-items:center;width:100%"><div><div style="font-weight:700;font-size:.8rem;color:var(--text)">${h.hat}</div><div style="font-size:.65rem;color:var(--text2);margin-top:2px">🚌 ${g.plaka}</div></div><div style="text-align:right"><div style="font-weight:800;font-size:1rem;color:var(--green)">${g.tahmini_dk} dk</div><div style="font-size:.6rem;color:var(--text3)">${g.durak_kaldi} durak • ${g.hiz} km/s</div></div></div></div>`})}else{x+='<div class="no-data" style="font-size:.7rem">Yaklaşan araç bulunamadı</div>'}x+='</div></div>';if(activeBuses.length>0){const group=L.featureGroup(Object.values(V));map.fitBounds(group.getBounds().pad(0.2))}}else x+='<div class="no-data">Hat bilgisi yok</div>';
// Yakın mekanları getir
const durak=await(await fetch(`/api/durak_ara?q=${encodeURIComponent(kod)}`)).json();const d0=durak[0];if(d0&&d0.lat&&d0.lon){try{const pois=await(await fetch(`/api/yakin_mekanlar?lat=${d0.lat}&lon=${d0.lon}&radius=1`)).json();if(pois.length){x+=`<div class="sec" style="margin-top:12px">🏛️ Yakındaki Turistik Mekanlar</div>`;pois.forEach(p=>{x+=`<div class="drk" onclick="shMekanDetay(${p.id})" style="gap:10px;padding:10px"><img src="${p.img}" style="width:48px;height:48px;border-radius:8px;object-fit:cover;flex-shrink:0" onerror="this.style.display='none'"><div class="inf"><span class="ad">${p.title}</span><span class="fyt">${p.mesafe_m}m • ${p.cat} • ${p.hours}</span></div></div>`})}}catch(e){}}
document.getElementById('ct').innerHTML=x}catch(e){console.error('DurakDetay hata:',e)}}

async function shMekanDetay(id){try{const all=await(await fetch('/api/mekanlar')).json();const m=all.find(x=>x.id===id);if(!m)return;clr();map.setView([m.lat,m.lon],16);M['poi']=L.marker([m.lat,m.lon],{icon:L.divIcon({className:'',html:'<div style="background:#9333ea;color:#fff;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;border:2px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.3)">🏛</div>',iconSize:[32,32],iconAnchor:[16,32]})}).addTo(map);let x=`<button class="bk" onclick="shYakin()">← Geri</button>`;x+=`<div style="border-radius:12px;overflow:hidden;margin-bottom:12px"><img src="${m.img}" style="width:100%;height:180px;object-fit:cover" onerror="this.src='/static/images/placeholder.png'"></div>`;x+=`<div style="font-weight:700;font-size:1.1rem;margin-bottom:4px;color:var(--text)">${m.title}</div>`;x+=`<div style="font-size:.7rem;color:var(--text2);margin-bottom:8px"><span style="background:var(--accent-bg);padding:2px 8px;border-radius:6px;color:var(--accent);font-weight:600">${m.cat}</span></div>`;x+=`<div style="font-size:.8rem;line-height:1.6;color:var(--text);margin-bottom:12px">${m.desc}</div>`;x+=`<div class="ig"><div class="ic"><div class="v">🕐</div><div class="l">${m.hours}</div></div><div class="ic"><div class="v">${m.sections}</div><div class="l">Bölüm</div></div></div>`;if(m.audio&&m.audio.tr){x+=`<div class="sec">🔊 Sesli Anlatım</div><audio controls style="width:100%;margin:8px 0;border-radius:8px" preload="none"><source src="${m.audio.tr}" type="audio/mpeg">Tarayıcınız ses oynatmayı desteklemiyor.</audio>`}x+=`<a href="${m.url}" target="_blank" class="bk" style="display:block;text-align:center;text-decoration:none;margin-top:8px">🏛️ samsunkesfet.com'da Görüntüle</a>`;document.getElementById('ct').innerHTML=x}catch(e){console.error(e)}}
window.shMekanDetay=shMekanDetay;

// ===== TABS =====
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));t.classList.add('on');cur=t.dataset.t;clr();if(cur==='rota')shRotaUI();else if(cur==='hat')loadHats();else if(cur==='yakin')shYakin();else if(cur==='odak')shO();else shS()});

// ===== HAT LİSTESİ =====
function shH(){const bk={};H.forEach(h=>{const k=h.kat||'otobus';(bk[k]=bk[k]||[]).push(h)});let x=`<div class="src-wrap"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg><input class="src" placeholder="Hat ara..." oninput="flt(this.value)"></div><div class="kg">`;Object.entries(K).forEach(([k,v])=>{const cnt=k==='dil'?H.length:(bk[k]?bk[k].length:0);x+=`<div class="kb ${sK===k?'on':''}" onclick="selK('${k}')"><div class="i">${v.i}</div>${v.n}<span style="font-size:0.5rem;opacity:0.7">(${cnt})</span></div>`});x+=`</div><div class="lst" id="lst">`;(sK&&sK!=='dil'?bk[sK]||[]:H).forEach(h=>{x+=`<div class="it ${h.kat||'otobus'}" onclick="shL('${encodeURIComponent(h.code)}')">${h.name||h.code}</div>`});document.getElementById('ct').innerHTML=x+`</div>`}
window.selK=k=>{sK=sK===k?null:k;shH()};
window.flt=q=>{q=q.toLowerCase();const bk={};H.forEach(h=>{const k=h.kat||'otobus';(bk[k]=bk[k]||[]).push(h)});const f=(sK&&sK!=='dil'?bk[sK]||[]:H).filter(h=>(h.code+h.name).toLowerCase().includes(q));document.getElementById('lst').innerHTML=f.map(h=>`<div class="it ${h.kat||'otobus'}" onclick="shL('${encodeURIComponent(h.code)}')">${h.name||h.code}</div>`).join('')};

// ===== ARAÇ GÜNCELLEME =====
function saveSetting(k,v){localStorage.setItem(k,v?'1':'0')}
function getSetting(k,def){const v=localStorage.getItem(k);if(v===null)return def;return v==='1'}
function toggleSettings(){const p=document.getElementById('settingsPanel');if(p.style.display==='none'){p.style.display='block';loadSettingsUI();setTimeout(()=>document.addEventListener('click',closeSettingsOutside),10)}else closeSettings()}
function closeSettings(){document.getElementById('settingsPanel').style.display='none';document.removeEventListener('click',closeSettingsOutside)}
function closeSettingsOutside(e){const p=document.getElementById('settingsPanel');const b=document.getElementById('settingsBtn');if(!p.contains(e.target)&&e.target!==b){closeSettings()}}
function loadSettingsUI(){document.getElementById('chkHasilat').checked=getSetting('showHasilat',false);document.getElementById('chkLabels').checked=getSetting('showLabels',true);document.getElementById('chkRoute').checked=getSetting('showRoute',true);document.getElementById('chkAutoRefresh').checked=getSetting('autoRefresh',true);document.getElementById('chkAllStops').checked=getSetting('showAllStops',false)}
function resetSettings(){localStorage.removeItem('showHasilat');localStorage.removeItem('showLabels');localStorage.removeItem('showRoute');localStorage.removeItem('autoRefresh');localStorage.removeItem('showAllStops');localStorage.removeItem('theme');applyTheme(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');loadSettingsUI();toggleAllStops(false);showToast('Ayarlar varsayılana çevrildi')}
let allStopMarkers=[];
async function toggleAllStops(show){
    allStopMarkers.forEach(m=>map.removeLayer(m));
    allStopMarkers=[];
    if(!show) return;
    try{
        const stops=await(await fetch('/api/tum_duraklar')).json();
        const sIcon=L.divIcon({className:'',html:'<div style="width:8px;height:8px;background:#6366f1;border:2px solid #fff;border-radius:50%;box-shadow:0 1px 3px rgba(0,0,0,.4)"></div>',iconSize:[12,12],iconAnchor:[6,6]});
        stops.forEach(s=>{
            const m=L.marker([s.lat,s.lon],{icon:sIcon}).addTo(map)
                .bindPopup(`<b>${s.ad}</b><br><small>${s.kod?'Kod: '+s.kod:'ID: '+s.id}</small><br><button onclick="shDurakDetay('${s.id||s.kod}');if(window.innerWidth<=480)togglePnl(true)" style="margin-top:4px;padding:4px 8px;font-size:.7rem;cursor:pointer;border:1px solid #ccc;border-radius:4px">Detay Gör</button>`);
            allStopMarkers.push(m);
        });
        showToast(`${stops.length} durak haritada gösteriliyor`);
    }catch(e){console.error('Durak yükleme hatası:',e)}
}
async function upV(e,col){try{const aa=await(await fetch('/api/hat/arac/'+e)).json();Object.values(V).forEach(m=>map.removeLayer(m));V={};let html='';const showH=localStorage.getItem('showHasilat')==='1';document.querySelectorAll('.drk .vtg').forEach(el=>el.remove());if(Array.isArray(aa)&&aa.length>0){document.getElementById('acnt').innerText=aa.length;aa.forEach(a=>{V['v'+a.plaka]=L.marker([a.lat,a.lon],{icon:bI(col,a.plaka)}).addTo(map);const yak=a.yakin||'';const durumIcon=a.durum==='dikkat'?'⚠️':a.durum==='uyari'?'🔶':'🔹';html+=`<div class="arac" onclick="map.setView([${a.lat},${a.lon}],16)" style="flex-wrap:wrap"><div style="display:flex;justify-content:space-between;width:100%;align-items:center"><div><div class="pl">${durumIcon} ${a.plaka}</div><div class="inf" style="color:var(--text);font-weight:600;margin-top:2px">${yak?'📍 '+yak:''}</div></div><div style="text-align:right"><div style="font-weight:800;font-size:.9rem;color:var(--text)">${a.hiz} <small style="font-weight:400;font-size:0.6rem">km/s</small></div><div style="font-size:.65rem;color:var(--text2);margin-top:2px">${a.saat?'⏱ '+a.saat:''}</div></div></div><div style="display:flex;gap:6px;flex-wrap:wrap;width:100%;margin-top:10px;padding-top:10px;border-top:1px solid var(--card-border);font-size:.65rem;color:var(--text)"><span style="background:var(--bg3);padding:4px 8px;border-radius:12px;border:1px solid var(--card-border)">👥 <b>${a.yolcu}</b> biniş</span><span style="background:var(--bg3);padding:4px 8px;border-radius:12px;border:1px solid var(--card-border)">📊 Gün: <b>${a.gunluk_yolcu||0}</b></span><span style="background:var(--bg3);padding:4px 8px;border-radius:12px;border:1px solid var(--card-border)">🏎 Max: <b>${a.max_hiz||0}</b></span><span style="background:var(--bg3);padding:4px 8px;border-radius:12px;border:1px solid var(--card-border)">📏 <b>${a.mesafe_km||0}</b> km</span>${showH?`<span style="background:var(--bg3);padding:4px 8px;border-radius:12px;border:1px solid var(--card-border)">💰 <b>₺${(a.hasilat||0).toFixed(0)}</b></span>`:''}</div></div>`;if(yak){const rows=document.querySelectorAll('.drk');rows.forEach(r=>{if(r.innerText.includes(yak)){if(!r.querySelector('.vtg'))r.innerHTML+=`<span class="vtg" style="background:${col};color:#fff;padding:2px 6px;border-radius:4px;font-size:0.6rem;margin-left:6px">🚌 ${a.plaka}</span>`}})}});document.getElementById('vlist').innerHTML=html}else{document.getElementById('acnt').innerText='0';document.getElementById('vlist').innerHTML='<div style="text-align:center;padding:10px;color:var(--text3);font-size:0.7rem">Aktif araç yok</div>'}}catch(e){console.error(e)}}

// ===== OSRM ROUTE HELPER =====
async function drawRouteOSRM(coords,color){
    if(!coords||coords.length<2) return;
    try{
        // Max 25 waypoints for OSRM demo, sample if more
        let pts=coords;
        if(pts.length>25){
            const step=Math.ceil(pts.length/24);
            const sampled=[pts[0]];
            for(let i=step;i<pts.length-1;i+=step) sampled.push(pts[i]);
            sampled.push(pts[pts.length-1]);
            pts=sampled;
        }
        const wp=pts.map(c=>c[1]+','+c[0]).join(';');
        const res=await fetch(`https://router.project-osrm.org/route/v1/driving/${wp}?overview=full&geometries=geojson`);
        const data=await res.json();
        if(data.routes&&data.routes[0]){
            const geo=data.routes[0].geometry.coordinates.map(c=>[c[1],c[0]]);
            const pl=L.polyline(geo,{color:color,weight:4,opacity:0.7,dashArray:null}).addTo(map);
            M['routeLine']=pl;
        }
    }catch(e){console.log('OSRM route error:',e)}
}

// Stop marker with name label
const stopLbl=(n,num,c)=>{
    const isDark=document.documentElement.getAttribute('data-theme')==='dark';
    const bg=isDark?'rgba(15,23,42,0.85)':'rgba(255,255,255,0.9)';
    const tc=isDark?'#e2e8f0':'#1e293b';
    return L.divIcon({className:'',html:`<div style="position:relative"><div style="width:20px;height:20px;background:${c};border-radius:50%;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);color:#fff;font-size:9px;display:flex;align-items:center;justify-content:center;font-weight:700">${num}</div><div style="position:absolute;top:-8px;left:24px;background:${bg};color:${tc};padding:1px 6px;border-radius:4px;font-size:9px;white-space:nowrap;font-weight:600;box-shadow:0 1px 4px rgba(0,0,0,.2);pointer-events:none">${n}</div></div>`,iconSize:[20,20],iconAnchor:[10,10]});
};

function togglePnl(forceMinimize = false){
    const p = document.querySelector('.pnl');
    const svg = document.querySelector('#pnlToggle svg path');
    const toggle = document.getElementById('pnlToggle');
    if(forceMinimize || !p.classList.contains('minimized')){
        p.classList.add('minimized');
        if(svg) svg.setAttribute('d', 'M5 15l7-7 7 7');
    } else {
        p.classList.remove('minimized');
        if(svg) svg.setAttribute('d', 'M19 9l-7 7-7-7');
    }
    // Reposition toggle button at panel bottom
    requestAnimationFrame(()=>{
        const rect = p.getBoundingClientRect();
        if(toggle) toggle.style.top = rect.bottom + 'px';
    });
}
// Auto-position toggle on resize and load
function positionToggle(){
    const p = document.querySelector('.pnl');
    const toggle = document.getElementById('pnlToggle');
    if(p && toggle){
        const rect = p.getBoundingClientRect();
        toggle.style.top = rect.bottom + 'px';
    }
}
window.addEventListener('resize', positionToggle);
setInterval(positionToggle, 500);

// ===== HAT DETAY (shL) =====
async function shL(e,backToRoute=false){if(window.innerWidth<=480)togglePnl(true);clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';try{const[inf,dr,sf,ar,pr,fy]=await Promise.all([fetch('/api/hat/info/'+e),fetch('/api/hat/durak/'+e),fetch('/api/hat/sefer/'+e),fetch('/api/hat/arac/'+e),fetch('/api/hat/esles/'+e),fetch('/api/hat/fiyat/'+e)].map(p=>p.then(r=>r.json())));const nm=inf.name||decodeURIComponent(e),k=inf.kat||'otobus',ki=K[k]||K.otobus,g=inf.tip==='gidis',col=ki.c;const da=Array.isArray(dr)?dr:[],sa=Array.isArray(sf)?sf:[],aa=Array.isArray(ar)?ar:[];const tamF=(fy.tam_fiyat||20).toFixed(2),indF=(fy.indirimli_fiyat||14).toFixed(2);let x=backToRoute?`<button class="bk" onclick="shRotaUI();if(window.innerWidth<=480)togglePnl(false)">← Rotaya Dön</button>`:`<button class="bk" onclick="shH();if(window.innerWidth<=480)togglePnl(false)">← Hatlar</button>`;x+=`<div class="hdr" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px"><div style="font-weight:700;font-size:.9rem;display:flex;align-items:center"><div style="width:24px;height:24px;margin-right:8px;display:flex;pointer-events:none">${ki.i}</div> ${nm}</div>`;if(pr.code)x+=`<button class="pbtn" onclick="shL('${encodeURIComponent(pr.code)}',${backToRoute})">${g?'Dönüş ➝':'← Gidiş'}</button>`;x+=`</div><div class="ig"><div class="ic" onclick="document.getElementById('aktarmaModal').style.display='flex'" style="cursor:pointer;border-color:var(--accent)"><div class="v" style="font-size:1rem;margin-bottom:4px">ℹ️</div><div class="l"><b>Aktarma Kuralları</b><br><small>Tıkla ve Oku</small></div></div><div class="ic"><div class="v">${da.length}</div><div class="l">Durak</div></div><div class="ic"><div class="v" id="acnt">${aa.length}</div><div class="l">Araç</div></div></div>`;

    // === BİLGİLENDİRME KUTULARI ===
    if(nm.includes('SAMSUNUM-1')){
        x+=`<div style="background:var(--accent-bg);border:1px solid var(--accent);border-radius:10px;padding:12px;margin:10px 0;font-size:0.75rem;color:var(--text)">
            <h4 style="margin-bottom:8px;color:var(--orange)">⚠️ DEĞERLİ YOLCULARIMIZIN DİKKATİNE!</h4>
            <p>Hava koşullarına bağlı olarak sefer saatlerinde değişiklikler yaşanabilir.</p>
            <p style="margin-top:8px"><b>Sefer Süresi:</b> 1 saat 15 dakika</p>
            <p><b>Ücret:</b> Tam 250 TL / Öğrenci 200 TL</p>
            <p style="margin-top:8px">📞 İletişim: <b>0362 431 10 12</b></p>
        </div>`;
    }
    else if(nm.includes('SAMSUNUM-2')){
        x+=`<div style="background:rgba(220,38,38,0.1);border:1px solid var(--red);border-radius:10px;padding:12px;margin:10px 0;font-size:0.75rem;color:var(--text)">
            <h4 style="margin-bottom:8px">🛑 ÇALIŞMAMAKTADIR</h4>
            <p>DSİ Bölge Müdürlüğü çalışmalarından dolayı Samsunum-2 Gemisi çalışamamaktadır.</p>
            <p style="margin-top:8px">Anlayışınız için teşekkür ederiz.</p>
        </div>`;
    }
    else if(nm.includes('SAMSUNUM-3')){
        x+=`<div style="background:var(--accent-bg);border:1px solid var(--accent);border-radius:10px;padding:12px;margin:10px 0;font-size:0.75rem;color:var(--text)">
            <h4 style="margin-bottom:8px">ℹ️ Sefer Bilgisi</h4>
            <p>Sefer saatleri <b>doluluğa göre</b> belirlenir. Hava koşullarına bağlı aksamalar yaşanabilir.</p>
            <p style="margin-top:8px"><b>Sefer Süresi:</b> 1 saat 15 dk</p>
            <p><b>Ücret:</b> Tam 250 TL / Öğrenci 200 TL</p>
        </div>`;
    }
    else if(nm.includes('ALTINKAYA')||nm.includes('FERİBOT')){
         x+=`<div style="background:var(--bg2);border:1px solid var(--card-border);border-radius:10px;padding:12px;margin:10px 0;font-size:0.7rem;color:var(--text)">
            <h4 style="margin-bottom:8px">⛴️ Altınkaya 55 Feribot Tarifesi</h4>
            <p><b>Yolcu:</b> Tam 15 TL / Öğrenci 7 TL</p>
            <p><b>Araçlar:</b></p>
            <ul style="padding-left:15px;margin:5px 0"><li>Otomobil/Minibüs: 75 TL</li><li>Römorklu Traktör/Kamyonet: 90 TL</li><li>Kamyon (Boş): 290 TL / (Dolu): 580 TL</li><li>Otobüs: 290 TL (10m üstü: 410 TL)</li></ul>
            <p style="margin-top:5px;font-size:0.65rem">** Gece tarifesi (%50 zamlı) uygulanır.</p>
        </div>`;
    }
    else if(nm.includes('TELEFERİK')){
         x+=`<div style="background:rgba(236,72,153,0.08);border:1px solid var(--pink);border-radius:10px;padding:12px;margin:10px 0;font-size:0.75rem;color:var(--text)">
            <h4 style="margin-bottom:8px">🚡 Batıpark - Amisos Tepesi</h4>
            <div style="font-size:0.7rem;margin-bottom:8px;line-height:1.4">323 metre uzunluğundaki hat Batı Park ile Baruthane Tümülüsleri arasında hizmet verir.</div>
            <p><b>🕘 Çalışma:</b> 10:30 - 22:00</p>
            <p><b>Ücret:</b> Tam 50 TL / Öğrenci 30 TL</p>
            <p style="margin-top:8px">📞 Bilgi: <b>0362 431 10 12</b></p>
        </div>`;
    }
    else if(nm.includes('ECZANELER') && nm.includes('TEKKEKÖY') && nm.includes('GİDİŞ')){
        x+=`<div style="background:rgba(234,88,12,0.1);border:1px solid var(--orange);border-radius:10px;padding:12px;margin:10px 0;font-size:0.75rem;color:var(--text)">
            <h4 style="margin-bottom:8px">🚋 ECZANELER → TEKKEKÖY Gidiş</h4>
            <p>Tramvay hattı • Aynı hat durakları, farklı başlangıç noktası</p>
            <p style="margin-top:6px"><b>Ücret:</b> Tam 34 TL / Öğrenci 20 TL</p>
            <p>📞 <b>0362 431 10 12</b></p>
        </div>`;
    }
    else if(nm.includes('TEKKEKÖY') && nm.includes('ECZANELER') && nm.includes('DÖNÜŞ')){
        x+=`<div style="background:rgba(234,88,12,0.1);border:1px solid var(--orange);border-radius:10px;padding:12px;margin:10px 0;font-size:0.75rem;color:var(--text)">
            <h4 style="margin-bottom:8px">🚋 TEKKEKÖY → ECZANELER Dönüş</h4>
            <p>Tramvay hattı • Aynı hat durakları, farklı başlangıç noktası</p>
            <p style="margin-top:6px"><b>Ücret:</b> Tam 34 TL / Öğrenci 20 TL</p>
            <p>📞 <b>0362 431 10 12</b></p>
        </div>`;
    }
    else if(nm.includes('YURTLAR') && nm.includes('BELEDİYE')){
        x+=`<div style="background:rgba(234,88,12,0.1);border:1px solid var(--orange);border-radius:10px;padding:12px;margin:10px 0;font-size:0.75rem;color:var(--text)">
            <h4 style="margin-bottom:8px">🚋 YURTLAR → BELEDİYE EVLERİ</h4>
            <p>Tramvay hattı • Aynı hat durakları, farklı başlangıç noktası</p>
            <p style="margin-top:6px"><b>Ücret:</b> Tam 34 TL / Öğrenci 20 TL</p>
            <p>📞 <b>0362 431 10 12</b></p>
        </div>`;
    }
    else if(nm.includes('BELEDİYE') && nm.includes('YURTLAR') && nm.includes('DÖNÜŞ')){
        x+=`<div style="background:rgba(234,88,12,0.1);border:1px solid var(--orange);border-radius:10px;padding:12px;margin:10px 0;font-size:0.75rem;color:var(--text)">
            <h4 style="margin-bottom:8px">🚋 BELEDİYE EVLERİ → YURTLAR Dönüş</h4>
            <p>Tramvay hattı • Aynı hat durakları, farklı başlangıç noktası</p>
            <p style="margin-top:6px"><b>Ücret:</b> Tam 34 TL / Öğrenci 20 TL</p>
            <p>📞 <b>0362 431 10 12</b></p>
        </div>`;
    }
    else if(nm.includes('TRAMVAY')){
        x+=`<div style="background:var(--accent-bg);border:1px solid var(--accent);border-radius:10px;padding:8px;margin:10px 0;font-size:0.75rem;text-align:center;color:var(--text)">
             ℹ️ <b>Bilgi:</b> Güncel sefer saatleri için <a href="tel:03624311012" style="color:var(--accent)">0362 431 10 12</a> arayabilirsiniz.
        </div>
        <div style="margin:10px 0;border:1px solid var(--card-border);border-radius:10px;overflow:hidden">
            <div style="display:flex;background:var(--bg2);border-bottom:1px solid var(--card-border)">
                <div onclick="openTramTab('hi',this)" style="flex:1;padding:10px;text-align:center;cursor:pointer;font-weight:bold;background:var(--card);border-bottom:2px solid var(--accent)">Hafta İçi</div>
                <div onclick="openTramTab('cmt',this)" style="flex:1;padding:10px;text-align:center;cursor:pointer;border-bottom:2px solid transparent">Cumartesi</div>
                <div onclick="openTramTab('pzr',this)" style="flex:1;padding:10px;text-align:center;cursor:pointer;border-bottom:2px solid transparent">Pazar</div>
            </div>
            <div id="tramTabContent" style="padding:10px;background:var(--card);overflow-x:auto">
                <div id="tab_hi" style="display:block"><h5 style="margin:5px 0 10px;text-align:center">Hafta İçi Sefer Aralıkları</h5><table border="1" cellpadding="5" cellspacing="0" style="width:100%;font-size:0.65rem;border-collapse:collapse;text-align:center;color:var(--text)"><thead><tr style="background:var(--bg2)"><th colspan="2">Saat</th><th colspan="2">Sefer Sıklığı (Dk)</th></tr><tr><th>Başlangıç</th><th>Bitiş</th><th>Yurtlar -> Tekkeköy</th><th>Tekkeköy -> Yurtlar</th></tr></thead><tbody><tr><td>06:15</td><td>07:00</td><td>14</td><td>16</td></tr><tr><td>07:00</td><td>07:30</td><td>14</td><td>16</td></tr><tr><td>07:30</td><td>08:00</td><td>5</td><td>8</td></tr><tr><td>08:00</td><td>09:00</td><td>8</td><td>10</td></tr><tr><td>09:00</td><td>17:00</td><td>7</td><td>12-14</td></tr><tr><td>17:00</td><td>17:30</td><td>7</td><td>10</td></tr><tr><td>17:30</td><td>18:30</td><td>14</td><td>14</td></tr><tr><td>18:30</td><td>20:00</td><td>14</td><td>14</td></tr><tr><td>20:00</td><td>21:00</td><td>16</td><td>16</td></tr><tr><td>21:00</td><td>23:30</td><td>20</td><td>20</td></tr><tr><td>23:30</td><td>23:45</td><td>15</td><td>15</td></tr></tbody></table></div>
                <div id="tab_cmt" style="display:none"><h5 style="margin:5px 0 10px;text-align:center">Cumartesi Sefer Aralıkları</h5><table border="1" cellpadding="5" cellspacing="0" style="width:100%;font-size:0.65rem;border-collapse:collapse;text-align:center;color:var(--text)"><thead><tr style="background:var(--bg2)"><th colspan="2">Saat</th><th colspan="2">Sefer Sıklığı (Dk)</th></tr><tr><th>Başlangıç</th><th>Bitiş</th><th>Yurtlar -> Tekkeköy</th><th>Tekkeköy -> Yurtlar</th></tr></thead><tbody><tr><td>06:15</td><td>07:30</td><td>16</td><td>16</td></tr><tr><td>07:30</td><td>12:00</td><td>16</td><td>16</td></tr><tr><td>12:00</td><td>18:00</td><td>12</td><td>12</td></tr><tr><td>18:00</td><td>20:00</td><td>14</td><td>14</td></tr><tr><td>20:00</td><td>20:30</td><td>16</td><td>16</td></tr><tr><td>20:30</td><td>23:00</td><td>20</td><td>20</td></tr><tr><td>23:00</td><td>23:45</td><td>30</td><td>20</td></tr></tbody></table></div>
                <div id="tab_pzr" style="display:none"><h5 style="margin:5px 0 10px;text-align:center">Pazar Sefer Aralıkları</h5><table border="1" cellpadding="5" cellspacing="0" style="width:100%;font-size:0.65rem;border-collapse:collapse;text-align:center;color:var(--text)"><thead><tr style="background:var(--bg2)"><th colspan="2">Saat</th><th colspan="2">Sefer Sıklığı (Dk)</th></tr><tr><th>Başlangıç</th><th>Bitiş</th><th>Yurtlar -> Tekkeköy</th><th>Tekkeköy -> Yurtlar</th></tr></thead><tbody><tr><td>06:15</td><td>11:30</td><td>18</td><td>18</td></tr><tr><td>11:30</td><td>18:00</td><td>14</td><td>14</td></tr><tr><td>18:00</td><td>22:00</td><td>16</td><td>16</td></tr><tr><td>22:00</td><td>23:00</td><td>20</td><td>20</td></tr><tr><td>23:00</td><td>23:45</td><td>30</td><td>30</td></tr></tbody></table></div>
            </div>
        </div>`;
    }

    x+=`<div class="fiyat"><div class="t">Bilet</div><div class="pv">₺${tamF}</div><div class="s">İndirimli ₺${indF}${fy.aktarma1?' | Aktarma: '+fy.aktarma1:''}</div></div>`;x+=`<div class="araclar"><div class="t">🚌 Canlı Araçlar</div><div id="vlist">Yükleniyor...</div></div>`;if(sa.length){const hi=sa.filter(s=>s.gun==='hi').sort((a,b)=>(a.saat||'').localeCompare(b.saat||'')),hs=sa.filter(s=>s.gun==='hs').sort((a,b)=>(a.saat||'').localeCompare(b.saat||''));
    const hergun=sa.filter(s=>s.gun==='Her Gün').sort((a,b)=>(a.saat||'').localeCompare(b.saat||''));
    const haftasonu=sa.filter(s=>s.gun==='Hafta Sonu').sort((a,b)=>(a.saat||'').localeCompare(b.saat||''));
    if(hergun.length){x+=`<div class="saat"><div class="t">📅 Sefer Saatleri (Her Gün)</div><div class="saatlar">${hergun.map(s=>`<span>${s.saat}${s.yon?'<br><small>'+s.yon+'</small>':''}</span>`).join('')}</div></div>`}
    if(haftasonu.length){x+=`<div class="saat"><div class="t">📅 Sefer Saatleri (Hafta Sonu)</div><div class="saatlar">${haftasonu.map(s=>`<span>${s.saat}${s.yon?'<br><small>'+s.yon+'</small>':''}</span>`).join('')}</div></div>`}
    if(hi.length||hs.length){x+=`<div class="saat"><div class="t">📅 Saatler</div><div class="saattab"><div class="on" onclick="schT('hi',this)">Hİ (${hi.length})</div><div onclick="schT('hs',this)">HS (${hs.length})</div></div><div class="saatlar" id="scht">${hi.slice(0,40).map(s=>`<span>${s.saat}</span>`).join('')}${hi.length>40?`<span>+${hi.length-40}</span>`:''}</div></div>`;window._s={hi,hs}}}if(da.length){x+=`<div class="sec">📍 Duraklar (${da.length})</div>`;const co=[];const stopCol=col;const showLbl=getSetting('showLabels',true);da.forEach((d,i)=>{x+=`<div class="drk" onclick="map.setView([${d.lat},${d.lon}],17)"><span class="no" style="background:${stopCol}">${i+1}</span><span class="inf"><span class="ad">${d.ad}</span></span></div>`;if(d.lat&&d.lon){co.push([d.lat,d.lon]);M['d'+i]=L.marker([d.lat,d.lon],{icon:showLbl?stopLbl(d.ad,i+1,stopCol):dI(i+1,stopCol)}).addTo(map)}});if(co.length){map.fitBounds(co,{padding:[40,40]});if(getSetting('showRoute',true))drawRouteOSRM(co,col)}}else x+=`<div class="no-data">📍 Durak bilgisi yok</div>`;document.getElementById('ct').innerHTML=x;upV(e,col);if(getSetting('autoRefresh',true))liveT=setInterval(()=>upV(e,col),5000)}catch(e){console.error(e);document.getElementById('ct').innerHTML=`<button class="bk" onclick="shH()">← Hatlar</button><div class="no-data">❌ Hata</div>`}}
window.shL=shL;
window.schT=(t,b)=>{document.querySelectorAll('.saattab div').forEach(x=>x.classList.remove('on'));b.classList.add('on');const d=window._s?.[t]||[];document.getElementById('scht').innerHTML=d.slice(0,40).map(s=>`<span>${s.saat}</span>`).join('')+(d.length>40?`<span>+${d.length-40}</span>`:'')};
window.openTramTab=function(tabId,el){document.getElementById('tab_hi').style.display='none';document.getElementById('tab_cmt').style.display='none';document.getElementById('tab_pzr').style.display='none';document.getElementById('tab_'+tabId).style.display='block';let tabs=el.parentNode.children;for(let i=0;i<tabs.length;i++){tabs[i].style.borderBottom='2px solid transparent';tabs[i].style.fontWeight='normal';tabs[i].style.backgroundColor='transparent'}el.style.borderBottom='2px solid var(--accent)';el.style.fontWeight='bold';el.style.backgroundColor='var(--card)'};

// ===== ODAK =====
async function shO(){clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';document.getElementById('infoModal').style.display='flex';try{const d=await(await fetch('/api/odak')).json();if(!d||!d.length){document.getElementById('ct').innerHTML='<div class="no-data">🏔️ Veri yok</div>';return}let x=`<div style="text-align:center;padding:16px 0"><img src="/static/images/odak.png" style="height:80px;border-radius:12px;box-shadow:var(--shadow2)"></div><div class="tel">📞 Bilgi: <a href="tel:03624311012">0362 431 10 12</a></div><div style="background:var(--accent-bg);border:1px solid var(--accent);border-radius:10px;padding:8px;margin:8px 0;font-size:0.65rem;text-align:center;color:var(--text)">⚠️ <b>DİKKAT:</b> Fiyatlar değişiklik gösterebilir.</div><div class="lst">${d.map(o=>`<div class="it odak" onclick="shOD('${o.id}')">${o.kod} ${o.ad}</div>`).join('')}</div>`;document.getElementById('ct').innerHTML=x}catch(e){console.error(e)}}

async function shOD(id){clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';try{const[hl,dr]=await Promise.all([fetch('/api/odak').then(r=>r.json()),fetch('/api/odak/'+id+'/durak').then(r=>r.json())]);const h=(hl||[]).find(x=>x.id==id)||{},da=Array.isArray(dr)?dr:[],ilk=da[0]||{};const isGidis=h.ad&&h.ad.includes('Gidiş');const pair=(hl||[]).find(x=>x.kod===h.kod&&x.id!=id);let x=`<button class="bk" onclick="shO()">← Odak</button><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px"><div style="font-weight:700;font-size:1rem">🏔️ ${h.kod||''} ${h.ad||''}</div>${pair?`<button class="pbtn" onclick="shOD('${pair.id}')">${isGidis?'Dönüş ➡':'&#x2190; Gidiş'}</button>`:''}</div>`;x+=`<div class="ig"><div class="ic"><div class="v">${da.length}</div><div class="l">Durak</div></div><div class="ic"><div class="v">₺${ilk.fiyat||'?'}</div><div class="l">Tam</div></div><div class="ic"><div class="v" id="oacnt">0</div><div class="l">Araç</div></div></div>`;x+=`<div class="araclar"><div class="t">🏔️ Canlı Araçlar</div><div id="ovlist">Yükleniyor...</div></div>`;x+=`<div class="tel">📞 Bilgi: <a href="tel:03624311012">0362 431 10 12</a></div>`;if(da.length){x+=`<div class="sec">📍 Güzergah</div>`;const co=[];da.forEach((d,i)=>{x+=`<div class="drk" onclick="map.setView([${d.lat},${d.lon}],16)"><span class="no" style="background:var(--green)">${i+1}</span><span class="inf"><span class="ad">${d.ad}</span><span class="fyt">₺${d.fiyat||'?'} / ₺${d.fiyat_ogr||'?'}<br><small>(Sol: Tam, Sağ: İndirimli)</small></span></span></div>`;if(d.lat>0&&d.lon>0){co.push([d.lat,d.lon]);M['o'+i]=L.marker([d.lat,d.lon],{icon:dI(i+1,'#16a34a')}).addTo(map)}});if(co.length>1){const pl=L.polyline(co,{color:'#16a34a',weight:4,opacity:0.7,dashArray:'8,6'}).addTo(map);M['odak_route']=pl;map.fitBounds(pl.getBounds().pad(0.2))}else if(co.length)map.fitBounds(co,{padding:[40,40]})}document.getElementById('ct').innerHTML=x;upOdakV(id);liveT=setInterval(()=>upOdakV(id),5000)}catch(e){console.error(e)}}
window.shOD=shOD;
async function upOdakV(hatid){try{const r=await(await fetch('/api/proxy_odak_araclar?hatid='+hatid)).json();Object.values(V).forEach(m=>map.removeLayer(m));V={};const el=document.getElementById('ovlist'),cnt=document.getElementById('oacnt');if(!r||!r.vehicles||!r.vehicles.length){if(cnt)cnt.innerText='0';if(el)el.innerHTML='<div style="text-align:center;padding:10px;color:var(--text3);font-size:0.7rem">Aktif araç yok</div>';return}if(cnt)cnt.innerText=r.vehicles.length;let html='';r.vehicles.forEach(v=>{const lat=parseFloat((v.Enlem||v.lat||'0').toString().replace(',','.'));const lon=parseFloat((v.Boylam||v.lon||'0').toString().replace(',','.'));const plaka=(v.Plaka||v.plate||'').toString();const hiz=(v.Hizi||v.speed||'0').toString();if(lat>0&&lon>0){V['ov'+plaka]=L.marker([lat,lon],{icon:bI('#16a34a',plaka)}).addTo(map);html+=`<div class="arac" onclick="map.setView([${lat},${lon}],16)"><div><div class="pl">${plaka}</div></div><div style="text-align:right"><div style="font-weight:700">${hiz} km/s</div></div></div>`}});if(el)el.innerHTML=html||'<div style="text-align:center;padding:10px;color:var(--text3);font-size:0.7rem">Konum verisi yok</div>'}catch(e){}}

// ===== SAMAIR =====
async function shS(){clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';try{const d=await(await fetch('/api/samair')).json();if(!d||!d.length){document.getElementById('ct').innerHTML='<div class="no-data">✈️ Veri yok</div>';return}let x=`<div style="text-align:center;padding:16px 0"><img src="/static/images/samair.png" style="height:80px;border-radius:12px;box-shadow:var(--shadow2)"></div><div class="tel">📞 Bilgi: <a href="tel:03624311012">0362 431 10 12</a></div><div style="background:var(--accent-bg);border:1px solid var(--accent);border-radius:10px;padding:8px;margin:8px 0;font-size:0.65rem;text-align:center;color:var(--text)">⚠️ Test verileridir. Veriler her saat başı güncellenir.</div><div class="lst">${d.map(h=>`<div class="it" style="border-left-color:var(--red)" onclick="shSD(${h.id},'${h.kod}')">${h.ad}</div>`).join('')}</div>`;document.getElementById('ct').innerHTML=x}catch(e){console.error(e)}}

async function shSD(id,kod){clr();document.getElementById('ct').innerHTML='<div class="loading">⏳</div>';try{const[hl,dr,sf]=await Promise.all([fetch('/api/samair').then(r=>r.json()),fetch('/api/samair/'+id+'/durak').then(r=>r.json()),fetch('/api/samair/'+id+'/sefer').then(r=>r.json())]);const h=(hl||[]).find(x=>x.id==id)||{},da=Array.isArray(dr)?dr:[],seferler=sf.data||[],last_up=sf.last_update||'';let x=`<button class="bk" onclick="shS()">← Samair</button><div style="font-weight:700;margin-bottom:10px;font-size:1rem">✈️ ${h.ad||''}</div>`;x+=`<div class="ig"><div class="ic"><div class="v">${da.length}</div><div class="l">Durak</div></div><div class="ic"><div class="v" id="acnt">0</div><div class="l">Araç</div></div></div>`;x+=`<div class="araclar"><div class="t">✈️ Canlı Araçlar</div><div id="vlist">Yükleniyor...</div></div>`;x+=`<div class="tel">📞 Bilgi: <a href="tel:03624311012">0362 431 10 12</a></div>`;if(seferler.length){x+=`<div class="sec">✈️ Uçuş & Servis Saatleri</div>${last_up?`<div style="text-align:center;font-size:0.6rem;color:var(--text3);margin-bottom:5px">Son Güncelleme: ${last_up}</div>`:''}`;let cDay="";seferler.forEach(s=>{if(s.gun_format!==cDay){x+=`<div class="dhead">${s.gun_format}</div>`;cDay=s.gun_format}x+=`<div class="sfr"><div class="st">${s.saat} → ${s.varis}</div><div class="fr">${s.firma} - ${s.ucak_saat}</div></div>`})}else{x+=`<div class="no-data">✈️ Uçuş bilgisi bekleniyor...</div>`}if(da.length){x+=`<div class="sec">📍 Duraklar (${da.length})</div>`;const co=[];da.forEach((d,i)=>{x+=`<div class="drk" onclick="map.setView([${d.lat},${d.lon}],16)"><span class="no" style="background:var(--purple)">${i+1}</span><span class="inf"><span class="ad">${d.ad}</span><span class="fyt">₺${d.fiyat||'?'}</span></span></div>`;if(d.lat>0&&d.lon>0){co.push([d.lat,d.lon]);M['s'+i]=L.marker([d.lat,d.lon],{icon:dI(i+1,'#9333ea')}).addTo(map)}});if(co.length>1){const pl=L.polyline(co,{color:'#9333ea',weight:4,opacity:0.7,dashArray:'8,6'}).addTo(map);M['samair_route']=pl;map.fitBounds(pl.getBounds().pad(0.2))}else if(co.length)map.fitBounds(co,{padding:[40,40]})}document.getElementById('ct').innerHTML=x;upV(kod,'#9333ea');liveT=setInterval(()=>upV(kod,'#9333ea'),5000)}catch(e){console.error(e)}}
window.shSD=shSD;

function showDisclaimer(){if(!localStorage.getItem('disclaimerShown')){document.getElementById('infoModal').style.display='flex';localStorage.setItem('disclaimerShown','true')}}

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

    app = FastAPI(title="Samsun Ulaşım Sistemi")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    # Geolocation izni için Permissions-Policy header ekle
    from starlette.middleware.base import BaseHTTPMiddleware
    class PermissionsPolicyMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["Permissions-Policy"] = "geolocation=(self)"
            return response
    app.add_middleware(PermissionsPolicyMiddleware)

    if os.path.exists("static"): app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.on_event("startup")
    async def startup_event():
        asyncio.create_task(update_gtfs_feed())

    async def update_gtfs_feed():
        """GTFS-RT — On-Demand modunda sadece aktif hatları sorgular.
        Admin panelden ayarlanabilir: mode, interval, max_lines.
        Gece 23:00-09:00 arası API'ye istek atmaz.
        """
        http_client = col.http
        
        while True:
            cfg = _admin_config
            interval = cfg.get('gtfs_rt_interval', 60)
            
            # Kapalıysa bekle
            if not cfg.get('gtfs_rt_enabled', True):
                await asyncio.sleep(30)
                continue
            
            # Gece modu (23-09 TR)
            tr_hour = (datetime.utcnow().hour + 3) % 24
            if tr_hour >= 23 or tr_hour < 9:
                log.debug(f"🌙 Gece modu (saat {tr_hour:02d}:xx TR). GTFS-RT duraklatıldı.")
                await asyncio.sleep(300)
                continue
            
            try:
                mode = cfg.get('gtfs_rt_mode', 'ondemand')
                now = time.time()
                
                # Hangi hatları sorgulayacağımızı belirle
                if mode == 'ondemand':
                    # Sadece son 5dk içinde kullanıcı istekte bulunan hatlar
                    with _active_lines_lock:
                        # Süresi dolmuş hatları temizle
                        expired = [k for k, t in _active_lines.items() if now - t > _ACTIVE_TTL]
                        for k in expired:
                            del _active_lines[k]
                        target_codes = list(_active_lines.keys())
                    
                    if not target_codes:
                        log.debug("📡 GTFS-RT: Aktif hat yok, bekleniyor...")
                        await asyncio.sleep(interval)
                        continue
                else:
                    # All mode: DB'den çek, max_lines ile sınırla
                    max_l = cfg.get('gtfs_rt_max_lines', 10)
                    lines = db.get("SELECT code FROM hat WHERE kat NOT IN ('tramvay', 'odak', 'samair', 'tekne', 'teleferik')")
                    target_codes = [l['code'] for l in lines[:max_l]]
                
                # Feed oluştur
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.header.gtfs_realtime_version = "2.0"
                feed.header.timestamp = int(now)
                
                vehicle_count = 0
                seen_plates = set()
                
                for code in target_codes:
                    try:
                        data = await asyncio.to_thread(
                            http_client.asis, 'RealTimeData', lineCode=code
                        )
                        _api_stats['asis_calls'] += 1
                        
                        for d in data or []:
                            lat = parse_float(d.get('enlem'))
                            lon = parse_float(d.get('boylam'))
                            plaka = d.get('plaka', '?')
                            hiz = parse_float(d.get('hiz', 0))
                            
                            if not (40 < lat < 43 and 34 < lon < 38):
                                continue
                            if plaka in seen_plates:
                                continue
                            seen_plates.add(plaka)
                            
                            entity = feed.entity.add()
                            entity.id = plaka
                            entity.vehicle.trip.route_id = code
                            entity.vehicle.trip.trip_id = f"{code}_{plaka}_{int(now // 3600)}"
                            entity.vehicle.position.latitude = lat
                            entity.vehicle.position.longitude = lon
                            entity.vehicle.position.speed = hiz / 3.6
                            
                            try:
                                # 'yon' alanı 0-360 derece pusula yönüdür (0=Kuzey, 90=Doğu...)
                                # API'de 'aci' diye alan yok, doğrusu 'yon'
                                yon_val = parse_float(d.get('yon', 0))
                                if yon_val > 0:
                                    entity.vehicle.position.bearing = yon_val
                            except Exception:
                                pass
                            
                            entity.vehicle.timestamp = int(now)
                            entity.vehicle.vehicle.id = plaka
                            entity.vehicle.vehicle.label = plaka
                            
                            try:
                                kapasite_oran = parse_float(d.get('kapasite', 0))
                                if kapasite_oran > 0:
                                    if kapasite_oran < 20:
                                        entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.MANY_SEATS_AVAILABLE
                                    elif kapasite_oran < 50:
                                        entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.FEW_SEATS_AVAILABLE
                                    elif kapasite_oran < 80:
                                        entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.STANDING_ROOM_ONLY
                                    else:
                                        entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.FULL
                            except Exception:
                                pass
                            
                            vehicle_count += 1
                            
                    except Exception as e:
                        log.debug(f"GTFS-RT hat hatası ({code}): {e}")
                    
                    # Rate limit koruması: Her hat sorgusu arasında 100ms bekle
                    await asyncio.sleep(0.1)
                
                with _gtfs_feed_lock:
                    global gtfs_feed
                    gtfs_feed = feed
                log.info(f"GTFS-RT: {vehicle_count} araç / {len(target_codes)} hat ({mode})")
                
            except Exception as e:
                log.error(f"GTFS loop error: {e}")
            
            await asyncio.sleep(interval)

    @app.get("/", response_class=HTMLResponse)
    async def home(): return HTML

    @app.get("/api/yakin")
    async def api_yakin(lat: float, lon: float):
        return JSONResponse(col.yakindaki_duraklar(lat, lon))

    # ==========================================
    # TURİSTİK MEKANLAR (POI)
    # ==========================================
    MEKANLAR = [
        {"id":1,"title":"Kent Müzesi","desc":"Samsun'un tarihi ve kültürel mirasını sergileyen önemli bir müze.","cat":"Müzeler","img":"https://samsunkesfet.com/media/img/muze/muzekapak/kent-muzesi-kapak.jpg","lat":41.28929,"lon":36.33769,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/km/101.mp3"},"code":"km","url":"https://samsunkesfet.com/muze/km/1","sections":30},
        {"id":2,"title":"Onur Anıtı","desc":"Samsun'un bağımsızlık mücadelesinin simgesi anıt.","cat":"Anıtlar","img":"https://samsunkesfet.com/media/img/muze/muzekapak/onur-aniti.jpg","lat":41.29653,"lon":36.33262,"hours":"7/24 Açık","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/oa/onuraniti.mp3"},"code":"oa","url":"https://samsunkesfet.com/muze/oa/1","sections":1},
        {"id":3,"title":"Tütün İskelesi","desc":"Osmanlı dönemi tütün ticaretinin önemli merkezi.","cat":"Tarihi Mekanlar","img":"https://samsunkesfet.com/media/img/muze/muzekapak/tutun-iskelesi.jpg","lat":41.29025,"lon":36.33514,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/ti/tutun2.mp3"},"code":"ti","url":"https://samsunkesfet.com/muze/ti/1","sections":1},
        {"id":4,"title":"Alaçam Mübadele Müzesi","desc":"Türk-Yunan nüfus mübadelesini anlatan müze.","cat":"Müzeler","img":"https://samsunkesfet.com/media/img/muze/muzekapak/0.jpg","lat":41.29221,"lon":36.34080,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/ac/3.mp3"},"code":"ac","url":"https://samsunkesfet.com/muze/ac/1","sections":11},
        {"id":5,"title":"Amazon Köyü","desc":"Antik Amazon savaşçılarının izlerini taşıyan tarihi alan.","cat":"Tarihi Mekanlar","img":"https://samsunkesfet.com/media/img/muze/muzekapak/amazon-koyu.png","lat":41.29353,"lon":36.33917,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/az/1-amazon-g.mp3"},"code":"az","url":"https://samsunkesfet.com/muze/az/1","sections":11},
        {"id":6,"title":"Samsun Müzesi","desc":"Bölgenin en kapsamlı arkeoloji ve etnografya müzesi.","cat":"Müzeler","img":"https://samsunkesfet.com/media/img/muze/muzekapak/samsun-muzesi.jpg","lat":41.29145,"lon":36.33803,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/sm/sm.mp3"},"code":"sm","url":"https://samsunkesfet.com/muze/sm/1","sections":1},
        {"id":7,"title":"Sadi Tekkesi","desc":"Osmanlı dönemi dervişlerinin yaşadığı tarihi tekke.","cat":"Tarihi Mekanlar","img":"https://samsunkesfet.com/media/img/muze/muzekapak/sadi-tekkesi.jpg","lat":41.28887,"lon":36.33802,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/st/saditekkesi.mp3"},"code":"st","url":"https://samsunkesfet.com/muze/st/1","sections":1},
        {"id":8,"title":"İlkadım Anıtı","desc":"Atatürk'ün Samsun'a çıkışını simgeleyen anıt.","cat":"Anıtlar","img":"https://samsunkesfet.com/media/img/muze/muzekapak/ilkadim-aniti.jpg","lat":41.29048,"lon":36.33154,"hours":"7/24 Açık","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/ia/1.mp3"},"code":"ia","url":"https://samsunkesfet.com/muze/ia/1","sections":1},
        {"id":9,"title":"Gazi Müzesi","desc":"Atatürk'ün Samsun'da kaldığı tarihi konak-müze.","cat":"Müzeler","img":"https://samsunkesfet.com/media/img/muze/muzekapak/gazi-muzesi.jpg","lat":41.29027,"lon":36.33469,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/gz/gazimuzesi.mp3"},"code":"gz","url":"https://samsunkesfet.com/muze/gz/1","sections":1},
        {"id":10,"title":"Havza Atatürk Evi","desc":"Atatürk'ün Havza'da kaplıca tedavisi gördüğü ev.","cat":"Müzeler","img":"https://samsunkesfet.com/media/img/muze/muzekapak/havza-ataturk-evi.jpg","lat":41.29515,"lon":36.33554,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/hv/1.mp3"},"code":"hv","url":"https://samsunkesfet.com/muze/hv/1","sections":20},
        {"id":11,"title":"Bandırma Vapuru","desc":"Atatürk'ün Samsun'a çıktığı tarihi gemi-müze.","cat":"Müzeler","img":"https://samsunkesfet.com/media/img/muze/muzekapak/bandirma-gemisi.jpg","lat":41.29557,"lon":36.33787,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/bv/bandirma-1.mp3"},"code":"bv","url":"https://samsunkesfet.com/muze/bv/1","sections":31},
        {"id":12,"title":"Bafra Tütün Müzesi","desc":"Bafra'nın tütün üretim tarihini anlatan müze.","cat":"Müzeler","img":"https://samsunkesfet.com/media/img/muze/muzekapak/bafra.jpg","lat":41.29735,"lon":36.33717,"hours":"09:00 - 17:30","audio":{"tr":"https://samsunkesfet.com/media/sound/tr/bf/101.mp3"},"code":"bf","url":"https://samsunkesfet.com/muze/bf/1","sections":18},
    ]

    @app.get("/api/mekanlar")
    async def api_mekanlar():
        return JSONResponse(MEKANLAR)

    @app.get("/api/yakin_mekanlar")
    async def api_yakin_mekanlar(lat: float, lon: float, radius: float = 1.0):
        """Verilen koordinattan radius km içindeki mekanları döner"""
        import math
        results = []
        for m in MEKANLAR:
            dlat = math.radians(m['lat'] - lat)
            dlon = math.radians(m['lon'] - lon)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(m['lat'])) * math.sin(dlon/2)**2
            dist_km = 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            if dist_km <= radius:
                results.append({**m, "mesafe_m": round(dist_km * 1000)})
        results.sort(key=lambda x: x['mesafe_m'])
        return JSONResponse(results)

    # ==========================================
    # FUZZY SEARCH HELPERS
    # ==========================================
    def normalize_tr(text):
        """Türkçe karakter normalizasyonu + lowercase — fuzzy arama için"""
        if not text: return ""
        t = text.lower()
        replacements = {'ı':'i','ğ':'g','ü':'u','ş':'s','ö':'o','ç':'c','İ':'i','Ğ':'g','Ü':'u','Ş':'s','Ö':'o','Ç':'c','â':'a','î':'i','û':'u'}
        for old, new in replacements.items():
            t = t.replace(old, new)
        return t

    def fuzzy_match(query, target, threshold=0.6):
        """Basit benzerlik skoru (0-1 arası). Substring + karakter örtüşme."""
        nq = normalize_tr(query)
        nt = normalize_tr(target)
        if nq in nt: return 1.0
        if nt in nq: return 0.9
        # Karakter örtüşme oranı
        common = sum(1 for c in nq if c in nt)
        score = common / max(len(nq), 1)
        # Ardışık karakter bonus
        max_seq = 0; seq = 0; ti = 0
        for c in nq:
            found = nt.find(c, ti)
            if found >= 0:
                seq += 1; ti = found + 1
                max_seq = max(max_seq, seq)
            else:
                seq = 0
        seq_bonus = max_seq / max(len(nq), 1) * 0.3
        return min(score + seq_bonus, 1.0)

    @app.get("/api/durak_ara")
    async def api_durak_ara(q: str):
        if not q or len(q) < 2: return JSONResponse([])
        q_like = f"%{q.lower()}%"
        # Önce tam eşleşme dene
        res = col.db.get("SELECT id, kod, ad, lat, lon FROM durak WHERE lower(ad) LIKE ? OR kod LIKE ? OR id LIKE ? LIMIT 20", (q_like, q_like, q_like))
        # Eğer sonuç yoksa fuzzy arama yap
        if not res:
            all_stops = col.db.get("SELECT id, kod, ad, lat, lon FROM durak WHERE ad IS NOT NULL")
            scored = []
            for s in all_stops:
                score = fuzzy_match(q, s['ad'])
                if score >= 0.5:
                    scored.append((score, s))
            scored.sort(key=lambda x: -x[0])
            res = [s for _, s in scored[:20]]
        # Tram corrections
        if hasattr(col.db, 'tram_corrections'):
            for d in res:
                for csv_name, coords in col.db.tram_corrections.items():
                    cv_low = csv_name.lower().replace(' i̇stasyonu', '').replace(' istasyonu', '')
                    ad_low = d['ad'].lower()
                    if cv_low in ad_low or ad_low in cv_low:
                        d['lat'] = coords[0]
                        d['lon'] = coords[1]
                        break
        return JSONResponse(res)

    @app.get("/api/durak_panel/{kod}")
    async def api_durak_panel(kod: str):
        return JSONResponse(col.durak_bilgi(kod))

    @app.get("/api/tum_duraklar")
    async def api_tum_duraklar():
        """Haritada tüm durakları göstermek için"""
        res = col.db.get("SELECT id, kod, ad, lat, lon FROM durak WHERE lat IS NOT NULL AND lon IS NOT NULL")
        return JSONResponse(res)

    # ==========================================
    # YBS PROXY ENDPOINTS (MOBILE APP İÇİN)
    # ==========================================
    
    YBS_TOKEN_CACHE = {"token": None, "expiry": 0}
    
    async def get_ybs_token(http_client):
        now = time.time()
        if YBS_TOKEN_CACHE["token"] and now < YBS_TOKEN_CACHE["expiry"]:
            return YBS_TOKEN_CACHE["token"]
            
        try:
            # YBS API: GET ?method=getGuestToken (OpenAPI spec'e uygun)
            resp = await asyncio.to_thread(
                http_client.get,
                "https://ybs.samsun.bel.tr/service/?method=getGuestToken",
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            )
            data = resp.json()
            if data and data.get("token"):
                YBS_TOKEN_CACHE["token"] = data["token"]
                YBS_TOKEN_CACHE["expiry"] = now + 180 # 3 dakika
                return data["token"]
        except Exception as e:
            log.error(f"YBS Proxy Token Hatası: {e}")
        return None

    @app.get("/api/proxy_odak")
    async def proxy_odak():
        """Mobil uygulama için Odak noktalarını proxy yapar (WAF Aşar)"""
        http_client = col.http
        token = await get_ybs_token(http_client.session)
        if not token: return JSONResponse([])
        
        try:
            resp = await asyncio.to_thread(
                http_client.session.get,
                f"https://ybs.samsun.bel.tr/service/?method=odakSamsun_Crud&submethod=HatlarAllList&token={token}",
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://odak.samsun.bel.tr/"},
                timeout=10
            )
            content_type = resp.headers.get('content-type', '')
            if 'text/html' in content_type or resp.status_code != 200:
                log.warning(f"Odak Proxy: HTML/WAF yanıtı (status={resp.status_code})")
                return JSONResponse([])
            try:
                data = resp.json()
            except (ValueError, TypeError):
                log.warning("Odak Proxy: JSON parse hatası (muhtemelen WAF)")
                return JSONResponse([])
            raw = []
            if data.get('status') == 'SUCCESS' and data.get('data'):
                raw = data['data']
            elif data.get('root'):
                raw = data['root']
            # Mobil uyumlu alan adlarına normalize et (kodu→kod, adi→ad)
            normalized = []
            for item in (raw if isinstance(raw, list) else []):
                normalized.append({
                    'id': item.get('id', item.get('kodu', '')),
                    'kod': item.get('kod', item.get('kodu', '')),
                    'ad': item.get('ad', item.get('adi', '')),
                    'gunler': item.get('gunler', ''),
                })
            return JSONResponse(normalized)
        except Exception as e:
            log.error(f"YBS Proxy Odak Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy_samair_saatler")
    async def proxy_samair_saatler(hatid: int):
        """Mobil uygulama için SamAir saatlerini proxy yapar"""
        http_client = col.http
        token = await get_ybs_token(http_client.session)
        if not token: return JSONResponse([])
        
        try:
            resp = await asyncio.to_thread(
                http_client.session.get,
                f"https://ybs.samsun.bel.tr/service/?method=samair_ucaksefersaatleri_public&submethod=HatlarList&hatid={hatid}&token={token}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            content_type = resp.headers.get('content-type', '')
            if 'text/html' in content_type or resp.status_code != 200:
                log.warning(f"SamAir Saatler: HTML/WAF yanıtı (status={resp.status_code})")
                return JSONResponse([])
            try:
                data = resp.json()
            except (ValueError, TypeError):
                log.warning("SamAir Saatler: JSON parse hatası (muhtemelen WAF)")
                return JSONResponse([])
            raw = data.get('data', data.get('root', []))
            if not isinstance(raw, list):
                raw = []
            # Mobil uyumlu alan adlarına normalize et
            normalized = []
            for item in raw:
                normalized.append({
                    'saat': item.get('saat', ''),
                    'varis': item.get('varis_saati', item.get('varis', '')),
                    'firma': item.get('ucak_firmasi', item.get('firma', '')),
                    'ucak_saat': item.get('ucak_saatleri', item.get('ucak_saat', '')),
                    'tarih': item.get('tarih', ''),
                    'gun_format': item.get('formatted_date', item.get('gun_format', '')),
                })
            return JSONResponse(normalized)
        except Exception as e:
            log.error(f"YBS Proxy SamAir Saatler Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy_samair_araclar")
    async def proxy_samair_araclar():
        """Mobil uygulama için SamAir araç konumlarını proxy yapar"""
        http_client = col.http
        token = await get_ybs_token(http_client.session)
        if not token: return JSONResponse([])
        
        try:
            resp = await asyncio.to_thread(
                http_client.session.get,
                f"https://ybs.samsun.bel.tr/service/?method=samair_duraklar_public&submethod=araclar&token={token}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            # WAF/Cloudflare HTML yanıtı kontrolü
            content_type = resp.headers.get('content-type', '')
            if 'text/html' in content_type or resp.status_code != 200:
                log.warning(f"SamAir Araclar: HTML/WAF yanıtı (status={resp.status_code})")
                return JSONResponse([])
            try:
                data = resp.json()
            except (ValueError, TypeError):
                log.warning("SamAir Araclar: JSON parse hatası (muhtemelen WAF)")
                return JSONResponse([])
            raw = data.get('data', [])
            if not isinstance(raw, list):
                raw = []
            # Mobil uyumlu alan adlarına normalize et (Enlem→lat, Boylam→lon vb.)
            normalized = []
            for item in raw:
                lat_val = item.get('Enlem', item.get('enlem', item.get('lat', 0)))
                lon_val = item.get('Boylam', item.get('boylam', item.get('lon', 0)))
                try:
                    lat_f = float(str(lat_val).replace(',', '.'))
                    lon_f = float(str(lon_val).replace(',', '.'))
                except (ValueError, TypeError):
                    lat_f, lon_f = 0.0, 0.0
                normalized.append({
                    'lat': lat_f,
                    'lon': lon_f,
                    'plate': str(item.get('Plaka', item.get('plaka', item.get('plate', '')))),
                    'speed': str(item.get('Hizi', item.get('hiz', item.get('speed', '0')))),
                    'lineCode': str(item.get('HatKodu', item.get('hatKodu', item.get('lineCode', 'SAMAIR')))),
                })
            return JSONResponse(normalized)
        except Exception as e:
            log.error(f"YBS Proxy SamAir Araclar Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy_odak_araclar")
    async def proxy_odak_araclar(hatid: int):
        """Odak turistik hat canlı araç konumları"""
        http_client = col.http
        token = await get_ybs_token(http_client.session)
        if not token:
            return JSONResponse({"active": True, "vehicles": [], "error": "Token alınamadı"})
        
        try:
            resp = await asyncio.to_thread(
                http_client.session.get,
                f"https://ybs.samsun.bel.tr/service/?method=odakSamsun_Crud&submethod=AraclarList&hatid={hatid}&token={token}",
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://odak.samsun.bel.tr/"},
                timeout=8
            )
            data = resp.json()
            vehicles = data.get('data', data.get('root', []))
            if isinstance(vehicles, list):
                return JSONResponse({"active": True, "vehicles": vehicles})
            return JSONResponse({"active": True, "vehicles": []})
        except Exception as e:
            log.error(f"YBS Proxy Odak Araclar Hatası: {e}")
            return JSONResponse({"active": True, "vehicles": [], "error": str(e)})

    @app.get("/api/proxy/smart_stations")
    async def proxy_smart_stations(stationId: str):
        """Mobil uygulama için SmartStations proxy (Durağa yaklaşan araçlar)"""
        try:
            data = await asyncio.wait_for(
                asyncio.to_thread(col.http.asis, 'SmartStations', stationId=int(stationId)),
                timeout=8
            )
            _api_stats['asis_calls'] += 1
            return JSONResponse(data or [])
        except Exception as e:
            log.error(f"Proxy SmartStations Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy/lines")
    async def proxy_lines():
        """Mobil uygulama için Lines proxy (Alfabetik sıralı ve Vapur etiketli)."""
        try:
            data = await asyncio.wait_for(
                asyncio.to_thread(col.http.asis, 'Lines'),
                timeout=10
            )
            _api_stats['asis_calls'] += 1
            if isinstance(data, dict):
                data = data.get('data', data.get('result', []))
            
            lines_list = data or []
            # 'tekne' kategorisi varsa Vapur yap ve isme göre sırala
            for line in lines_list:
                # Custom category check fallback on asis data
                c = str(line.get('lineCode', '')).strip()
                n = str(line.get('lineName', '')).strip()
                kategori = col.kat(c, n)
                line['kat'] = 'Vapur' if kategori == 'tekne' else kategori.capitalize()
            
            # Hat Adına göre alfabetik sırala
            lines_list.sort(key=lambda x: str(x.get('lineName', '')).lower())
            return JSONResponse(lines_list)
        except Exception as e:
            log.error(f"Proxy Lines Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy/orjlines")
    async def proxy_orjlines():
        """Mobil uygulama için OrjLines proxy."""
        try:
            # OpenAPI şemasına göre OrjLines ekstra bir top-level nesne ve totalRow içeriyor olabilir
            # Ancak Http.asis fonksiyonu data arrayini çeviriyor
            data = await asyncio.wait_for(
                asyncio.to_thread(col.http.asis, 'OrjLines'),
                timeout=10
            )
            _api_stats['asis_calls'] += 1
            if isinstance(data, dict):
                data = data.get('data', data.get('result', []))
            return JSONResponse(data or [])
        except Exception as e:
            log.error(f"Proxy OrjLines Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy/realtime")
    async def proxy_realtime(lineCode: str):
        """Mobil uygulama için RealTimeData proxy (Hat canlı araç)"""
        # On-Demand: Bu hattı aktif olarak işaretle
        with _active_lines_lock:
            _active_lines[lineCode] = time.time()
        try:
            data = await asyncio.wait_for(
                asyncio.to_thread(col.http.asis, 'RealTimeData', lineCode=lineCode),
                timeout=8
            )
            _api_stats['asis_calls'] += 1
            return JSONResponse(data or [])
        except Exception as e:
            log.error(f"Proxy RealTimeData Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy/stops_stations")
    async def proxy_stops_stations(lineCode: str):
        """Mobil uygulama için StopsStations proxy (Hat durakları)
        
        lineCode verilirse o hattın durak sırası döner.
        asis() zaten data listesini döndürür — ekstra dict check gerekmez.
        """
        try:
            data = await asyncio.wait_for(
                asyncio.to_thread(col.http.asis, 'StopsStations', lineCode=lineCode),
                timeout=10
            )
            _api_stats['asis_calls'] += 1
            # asis() zaten data listesini döndürür; dict kontrolü gereksiz ama güvenlik için tutuyoruz
            if isinstance(data, dict):
                data = data.get('data', data.get('result', []))
            return JSONResponse(data or [])
        except Exception as e:
            log.error(f"Proxy StopsStations Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy/line_directions")
    async def proxy_line_directions(lineCode: str):
        """Mobil uygulama için LineDirections proxy (Hat yönleri)
        
        KRİTİK: ASIS API'de lineCode filtresi sunucu tarafında çalışmıyor.
        Her çağrıda tüm sistem verisi (~8557 kayıt) döner.
        Bu proxy istemci tarafında lineCode alanına göre filtreler.
        """
        try:
            data = await asyncio.wait_for(
                asyncio.to_thread(col.http.asis, 'LineDirections', lineCode=lineCode),
                timeout=15  # 8557 kayıt için timeout artırıldı
            )
            _api_stats['asis_calls'] += 1
            if isinstance(data, dict):
                data = data.get('data', data.get('result', []))
            if isinstance(data, list) and lineCode:
                # Sunucu tarafı filtresi çalışmıyor — istemci tarafında filtrele
                data = [d for d in data if d.get('lineCode') == lineCode]
            return JSONResponse(data or [])
        except Exception as e:
            log.error(f"Proxy LineDirections Hatası: {e}")
            return JSONResponse([])

    @app.get("/api/proxy/schedules")
    async def proxy_schedules(lineCode: str, scheduleDate: str = None):
        """Mobil uygulama için Schedules proxy (Hat saatleri / tarife)
        
        NOT: scheduleDate parametresi API'de zorunlu ama etkisizdir —
        her tarih için aynı aktif çizelge döner. Yine de gönderilmesi gerekir.
        Format: YYYY-MM-DD (T00:00:00 suffix gereksiz, her ikisi kabul edilir)
        """
        if not scheduleDate:
            scheduleDate = datetime.now().strftime("%Y-%m-%d")
        try:
            # scheduleDate'deki T00:00:00 suffix'ini temizle (API ikisini de kabul eder ama sade tutalım)
            clean_date = scheduleDate.split('T')[0] if 'T' in scheduleDate else scheduleDate
            data = await asyncio.wait_for(
                asyncio.to_thread(col.http.asis, 'Schedules', lineCode=lineCode, scheduleDate=clean_date),
                timeout=10
            )
            _api_stats['asis_calls'] += 1
            if isinstance(data, dict):
                data = data.get('data', data.get('result', []))
            # yon alanını okunabilir forma çevir: "G" → "Gidiş", "D" → "Dönüş"
            if isinstance(data, list):
                yon_map = {'G': 'Gidiş', 'D': 'Dönüş'}
                for item in data:
                    if isinstance(item, dict) and 'yon' in item:
                        item['yon'] = yon_map.get(item['yon'], item['yon'])
            return JSONResponse(data or [])
        except Exception as e:
            log.error(f"Proxy Schedules Hatası: {e}")
            return JSONResponse([])

    @app.get("/api")
    async def api_root():
        """API kök endpoint — sağlık ve mevcut endpoint listesi"""
        return JSONResponse({
            "status": "ok",
            "version": "v26",
            "uptime_seconds": int(time.time() - _START_TIME),
            "endpoints": {
                "proxy": [
                    "/api/proxy/lines",
                    "/api/proxy/orjlines",
                    "/api/proxy/smart_stations?stationId=",
                    "/api/proxy/realtime?lineCode=",
                    "/api/proxy/stops_stations?lineCode=",
                    "/api/proxy/line_directions?lineCode=",
                    "/api/proxy/schedules?lineCode=&scheduleDate=",
                ],
                "hat": [
                    "/api/hat",
                    "/api/hat/arac/{code}",
                    "/api/hat/durak/{code}",
                    "/api/hat/sefer/{code}",
                    "/api/hat/fiyat/{code}",
                    "/api/hat/info/{code}",
                ],
                "diger": [
                    "/api/health",
                    "/api/yakin?lat=&lon=",
                    "/api/rota",
                    "/api/odak",
                    "/api/samair",
                ],
            }
        })

    # ==========================================

    @app.get("/api/rota")
    async def api_rota(start: str = None, lat1: float = None, lon1: float = None, 
                       end: str = None, lat2: float = None, lon2: float = None):
        """
        Rotayı hesaplar.
        İstenirse koordinat (lat1, lon1 vs) verilir, istenirse yer ismi (start=Atakum, end=Meydan) verilir.
        Yer ismi verilirse OSM Nominatim ile koordinata çevrilir. (Samsun bounds restriction ile)
        """
        async def geocode(query: str):
            if not query: return None, None
            # Samsun'a yönelik arama — query'ye "Samsun" ekle (zaten yoksa)
            q = query.strip()
            q_search = q if 'samsun' in q.lower() else f"{q}, Samsun"
            
            # 1. Nominatim (birincil)
            try:
                url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q_search)}&format=json&limit=3&viewbox=35.5,41.5,36.8,41.1&bounded=0&countrycodes=tr"
                headers = {"User-Agent": "SamsunTransitApp/2.0 (contact@samsun-transit.com)"}
                resp = await asyncio.wait_for(
                    asyncio.to_thread(requests.get, url, headers=headers, timeout=5),
                    timeout=6.0
                )
                if resp.ok:
                    data = resp.json()
                    if data and len(data) > 0:
                        # Samsun sınırları içinde olan ilk sonucu tercih et
                        for d in data:
                            lat, lon = float(d['lat']), float(d['lon'])
                            if 41.0 <= lat <= 41.6 and 35.5 <= lon <= 37.0:
                                log.info(f"Geocode OK (Nominatim): '{q}' -> {lat},{lon} ({d.get('display_name','')[:50]})")
                                return lat, lon
                        # Samsun dışı sonuç varsa yine al
                        lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                        log.info(f"Geocode (Nominatim, dış): '{q}' -> {lat},{lon}")
                        return lat, lon
            except Exception as e:
                log.debug(f"Nominatim hata: {e}")
            
            # 2. Photon API (fallback — Nominatim verisi kullanır ama farklı sunucu)
            try:
                url2 = f"https://photon.komoot.io/api/?q={urllib.parse.quote(q_search)}&limit=3&lat=41.29&lon=36.33&lang=tr"
                resp2 = await asyncio.wait_for(
                    asyncio.to_thread(requests.get, url2, timeout=5),
                    timeout=6.0
                )
                if resp2.ok:
                    pdata = resp2.json()
                    features = pdata.get('features', [])
                    if features:
                        coords = features[0]['geometry']['coordinates']
                        lat, lon = coords[1], coords[0]
                        log.info(f"Geocode OK (Photon): '{q}' -> {lat},{lon}")
                        return lat, lon
            except Exception as e:
                log.debug(f"Photon hata: {e}")
            
            log.warning(f"Geocode BAŞARISIZ: '{q}'")
            return None, None

        # Resolve Start
        if start and (lat1 is None or lon1 is None):
            lat1, lon1 = await geocode(start)
        
        # Resolve End
        if end and (lat2 is None or lon2 is None):
            lat2, lon2 = await geocode(end)
            
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return JSONResponse({"error": "Konum bulunamadı. Lütfen daha açık bir adres girin."}, status_code=400)
            
        return JSONResponse(col.yol_tarifi(lat1, lon1, lat2, lon2))

    @app.get("/api/hava")
    async def get_hava():
        """MGM'den Samsun Atakum güncel hava durumunu çeker"""
        try:
            url = "https://servis.mgm.gov.tr/web/sondurumlar?merkezid=95501" # 95501 = Samsun Atakum
            headers = {
                "Origin": "https://www.mgm.gov.tr",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            if data and len(data) > 0:
                return JSONResponse({
                    "sicaklik": data[0].get("sicaklik"),
                    "hadise": data[0].get("hadiseKodu"),
                    "nem": data[0].get("nem"),
                    "zaman": data[0].get("veriZamani")
                })
            return JSONResponse({"error": "Veri bulunamadı"})
        except Exception as e:
            log.error(f"Hava durumu hatası: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # --- Health Check ---
    @app.get("/api/health")
    async def health_check():
        """Sistem durum kontrolü"""
        with _gtfs_feed_lock:
            vehicle_count = len(gtfs_feed.entity)
        
        proxy_status = "active" if col.http.s.proxies else "disabled"
        
        return JSONResponse({
            "status": "ok",
            "uptime_seconds": int(time.time() - _START_TIME),
            "proxy": proxy_status,
            "db": {
                "hat": db.cnt('hat'),
                "durak": db.cnt('durak'),
                "fiyat": db.cnt('fiyat'),
                "odak": db.cnt('odak'),
                "samair": db.cnt('samair'),
            },
            "last_update": db.get_meta('son_guncelleme'),
            "gtfs_rt_vehicles": vehicle_count,
        })

    @app.get("/api/app_version")
    async def app_version():
        """Mobil uygulama güncel sürüm bilgisi (repo gizli olduğu için proxy)"""
        return JSONResponse({
            "latest_version": "2.5.0",
            "min_version": "2.0.0",
            "release_notes": "• SamAir canlı araç takibi düzeltildi\n• Odak Samsun canlı sorgu aktif\n• Fiyatlar güncellendi\n• Yakın durak harita modu eklendi\n• Uygulama içi güncelleme kontrolü",
            "download_url": "https://samsun-gtfs-rt.onrender.com/api/app_version",
            "force_update": False,
        })

    @app.get("/api/debug/proxy")
    async def debug_proxy():
        """Proxy bağlantı testi — ASIS ve YBS erişilebilir mi?"""
        results = {}
        http = col.http
        
        # Proxy durumu
        results["proxy_configured"] = bool(http.s.proxies)
        results["proxy_env"] = {
            "PROXY_HOST": os.environ.get("PROXY_HOST", "NOT SET"),
            "PROXY_PORT": os.environ.get("PROXY_PORT", "NOT SET"),
            "PROXY_USER": "***" if os.environ.get("PROXY_USER") else "NOT SET",
        }
        
        # IP testi
        try:
            r = await asyncio.to_thread(http.s.get, "https://api.ipify.org", timeout=5)
            results["proxy_ip"] = r.text
        except Exception as e:
            results["proxy_ip"] = f"ERROR: {e}"
        
        # ASIS testi
        try:
            r = await asyncio.to_thread(http.s.get, f"{ASIS}/Lines", timeout=10)
            data = r.json()
            lines = data.get('data', data) if isinstance(data, dict) else data
            results["asis"] = {"status": r.status_code, "hat_count": len(lines) if isinstance(lines, list) else "?"}
        except Exception as e:
            results["asis"] = {"error": str(e)}
        
        # YBS token testi
        try:
            tok = http.ybs_token()
            results["ybs_token"] = tok[:6] + "..." if tok else "FAILED"
        except Exception as e:
            results["ybs_token"] = f"ERROR: {e}"
        
        return JSONResponse(results)

    # ==========================================
    # 🔐 ADMIN KONTROL PANELİ (ADMIN_KEY ile korumalı)
    # ==========================================
    ADMIN_KEY = os.environ.get('ADMIN_KEY', '')
    
    def _check_admin(key: str):
        """Admin key doğrulama"""
        if not ADMIN_KEY:
            return False  # ADMIN_KEY set edilmemişse admin paneli kapalı
        return key == ADMIN_KEY
    
    def _save_config():
        """Config'i SQLite'a kaydet"""
        for k, v in _admin_config.items():
            db.ex("INSERT OR REPLACE INTO app_config(key, value) VALUES(?, ?)", (k, str(v)))
    
    def _load_config():
        """Config'i SQLite'dan yükle"""
        try:
            rows = db.get("SELECT key, value FROM app_config")
            for row in rows:
                k, v = row['key'], row['value']
                if k in _admin_config:
                    if isinstance(_admin_config[k], bool):
                        _admin_config[k] = v.lower() in ('true', '1', 'yes')
                    elif isinstance(_admin_config[k], int):
                        _admin_config[k] = int(v)
                    else:
                        _admin_config[k] = v
            log.info(f"⚙️ Admin config yüklendi: mode={_admin_config['gtfs_rt_mode']}, interval={_admin_config['gtfs_rt_interval']}s")
        except Exception:
            pass  # İlk başlatmada tablo boş olabilir
    
    _load_config()
    
    @app.get("/api/admin/config")
    async def admin_get_config(key: str = ''):
        if not _check_admin(key):
            return JSONResponse({"error": "Yetkisiz"}, status_code=403)
        return JSONResponse(_admin_config)
    
    @app.post("/api/admin/config")
    async def admin_set_config(key: str = '', gtfs_rt_enabled: bool = None, gtfs_rt_interval: int = None,
                                gtfs_rt_mode: str = None, gtfs_rt_max_lines: int = None, samair_interval: int = None):
        if not _check_admin(key):
            return JSONResponse({"error": "Yetkisiz"}, status_code=403)
        
        if gtfs_rt_enabled is not None: _admin_config['gtfs_rt_enabled'] = gtfs_rt_enabled
        if gtfs_rt_interval is not None: _admin_config['gtfs_rt_interval'] = max(10, gtfs_rt_interval)
        if gtfs_rt_mode in ('ondemand', 'all'): _admin_config['gtfs_rt_mode'] = gtfs_rt_mode
        if gtfs_rt_max_lines is not None: _admin_config['gtfs_rt_max_lines'] = max(1, min(50, gtfs_rt_max_lines))
        if samair_interval is not None: _admin_config['samair_interval'] = max(600, samair_interval)
        
        _save_config()
        log.info(f"⚙️ Admin config güncellendi: {_admin_config}")
        return JSONResponse({"ok": True, "config": _admin_config})
    
    @app.get("/api/admin/stats")
    async def admin_stats(key: str = ''):
        if not _check_admin(key):
            return JSONResponse({"error": "Yetkisiz"}, status_code=403)
        
        with _active_lines_lock:
            now = time.time()
            active = {k: int(now - t) for k, t in _active_lines.items() if now - t < _ACTIVE_TTL}
        
        with _gtfs_feed_lock:
            vehicle_count = len(gtfs_feed.entity)
        
        uptime = int(time.time() - _START_TIME)
        stats_age = int(time.time() - _api_stats['last_reset'])
        
        return JSONResponse({
            "uptime_seconds": uptime,
            "config": _admin_config,
            "active_lines": active,
            "active_line_count": len(active),
            "gtfs_rt_vehicles": vehicle_count,
            "api_stats": {
                "asis_calls": _api_stats['asis_calls'],
                "ybs_calls": _api_stats['ybs_calls'],
                "period_seconds": stats_age,
                "asis_per_minute": round(_api_stats['asis_calls'] / max(1, stats_age / 60), 1),
            },
            "proxy_active": bool(col.http.s.proxies),
            "tr_hour": (datetime.utcnow().hour + 3) % 24,
        })
    
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_panel(key: str = ''):
        if not _check_admin(key):
            return HTMLResponse("<h1>403 - Yetkisiz</h1><p>URL'e ?key=ADMIN_KEY ekleyin</p>", status_code=403)
        
        return HTMLResponse(f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🔐 Samsun Ulaşım Sistemi Admin</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:20px;max-width:700px;margin:0 auto}}
h1{{color:#4fc3f7;margin-bottom:20px;font-size:1.5em}}
.card{{background:#1a1a2e;border:1px solid #333;border-radius:12px;padding:20px;margin-bottom:15px}}
.card h2{{color:#64ffda;font-size:1.1em;margin-bottom:12px}}
label{{display:block;margin:8px 0 4px;color:#aaa;font-size:0.9em}}
input,select{{width:100%;padding:8px 12px;background:#0d1117;border:1px solid #444;border-radius:6px;color:#e0e0e0;font-size:0.95em}}
.toggle{{display:flex;align-items:center;gap:10px;margin:8px 0}}
.toggle input[type=checkbox]{{width:20px;height:20px;accent-color:#4fc3f7}}
button{{background:#4fc3f7;color:#000;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;font-weight:bold;font-size:1em;margin-top:12px;width:100%}}
button:hover{{background:#29b6f6}}
.stat{{display:inline-block;background:#0d1117;padding:6px 12px;border-radius:6px;margin:3px;font-size:0.85em}}
.stat b{{color:#4fc3f7}}
#status{{margin-top:10px;padding:10px;border-radius:6px;display:none}}
.ok{{background:#1b5e20;display:block!important}}
.err{{background:#b71c1c;display:block!important}}
#lines{{margin-top:8px;font-size:0.85em;color:#aaa}}
</style></head>
<body>
<h1>🔐 Samsun Ulaşım Sistemi Admin Panel</h1>

<div class="card">
<h2>📡 GTFS-RT Ayarları</h2>
<div class="toggle">
<input type="checkbox" id="enabled" {"checked" if _admin_config["gtfs_rt_enabled"] else ""}>
<label for="enabled" style="display:inline;color:#e0e0e0">GTFS-RT Aktif</label>
</div>
<label>Mod</label>
<select id="mode">
<option value="ondemand" {"selected" if _admin_config["gtfs_rt_mode"]=="ondemand" else ""}>On-Demand (Sadece bakılan hatlar)</option>
<option value="all" {"selected" if _admin_config["gtfs_rt_mode"]=="all" else ""}>All (Tüm hatlar, max_lines ile sınırlı)</option>
</select>
<label>Güncelleme Aralığı (saniye)</label>
<input type="number" id="interval" value="{_admin_config["gtfs_rt_interval"]}" min="10" max="300">
<label>Max Hat Sayısı (All modunda)</label>
<input type="number" id="maxlines" value="{_admin_config["gtfs_rt_max_lines"]}" min="1" max="50">
</div>

<div class="card">
<h2>✈️ SamAir Ayarları</h2>
<label>Güncelleme Aralığı (saniye)</label>
<input type="number" id="samair" value="{_admin_config["samair_interval"]}" min="600" max="86400">
</div>

<button onclick="save()">💾 Kaydet</button>
<div id="status"></div>

<div class="card" style="margin-top:15px">
<h2>📊 Canlı Durum</h2>
<div id="stats">Yükleniyor...</div>
<div id="lines"></div>
</div>

<script>
const K='{key}';
const API=window.location.origin;
async function save(){{
  const s=document.getElementById('status');
  try{{
    const r=await fetch(API+'/api/admin/config?key='+K,{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},
      body:'gtfs_rt_enabled='+document.getElementById('enabled').checked+'&gtfs_rt_interval='+document.getElementById('interval').value+'&gtfs_rt_mode='+document.getElementById('mode').value+'&gtfs_rt_max_lines='+document.getElementById('maxlines').value+'&samair_interval='+document.getElementById('samair').value}});
    const d=await r.json();
    s.className=d.ok?'ok':'err'; s.textContent=d.ok?'✅ Kaydedildi!':'❌ Hata';
  }}catch(e){{s.className='err';s.textContent='❌ '+e}}
  setTimeout(()=>s.style.display='none',3000);
}}
async function loadStats(){{
  try{{
    const r=await fetch(API+'/api/admin/stats?key='+K);
    const d=await r.json();
    const h=document.getElementById('stats');
    h.innerHTML=`
      <span class="stat">⏱ Uptime: <b>${{Math.floor(d.uptime_seconds/60)}}dk</b></span>
      <span class="stat">🚌 Araç: <b>${{d.gtfs_rt_vehicles}}</b></span>
      <span class="stat">📡 Aktif Hat: <b>${{d.active_line_count}}</b></span>
      <span class="stat">📊 ASIS: <b>${{d.api_stats.asis_per_minute}}/dk</b></span>
      <span class="stat">🌐 Proxy: <b>${{d.proxy_active?'✅':'❌'}}</b></span>
      <span class="stat">🕐 TR Saat: <b>${{d.tr_hour}}:xx</b></span>`;
    const al=Object.entries(d.active_lines);
    document.getElementById('lines').innerHTML=al.length?
      '🔴 Aktif Hatlar: '+al.map(([k,v])=>`<span class="stat">${{k}} <b>${{v}}sn önce</b></span>`).join(''):'💤 Kimse araç takip etmiyor';
  }}catch(e){{}}
}}
loadStats(); setInterval(loadStats, 10000);
</script>
</body></html>''')

    # --- Standart API Endpointleri ---
    @app.get("/gtfs-rt/vehicle-positions")
    async def get_vehicle_positions():
        with _gtfs_feed_lock:
            # Header kontrolü ve yaması
            if not gtfs_feed.HasField('header'):
                gtfs_feed.header.gtfs_realtime_version = "2.0"
                gtfs_feed.header.timestamp = int(time.time())
            else:
                # Zaman damgasını güncelle
                gtfs_feed.header.timestamp = int(time.time())
                
            data = gtfs_feed.SerializeToString()
        return Response(content=data, media_type="application/x-protobuf")

    @app.get("/api/hat")
    async def get_hatlar():
        return JSONResponse(db.get("SELECT * FROM hat ORDER BY kat, name COLLATE NOCASE ASC"))
    
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
        
        # Fallback: DB'deki en yaygın fiyatı kullan (sıfır değilse)
        if not res:
            res = {"tam_fiyat": 20.0, "indirimli_fiyat": 14.0, "ogrenci_fiyat": 14.0, "aktarma1": "Ücretsiz"}
        else:
            # SQL row dict'e çevrildiyse doğrudan müdahale edebilmek için dict(res) kullan
            res = dict(res)

        # Öğrenci fiyatı için öncelikli gösterim (Yoksa indirimli fiyat kullanılır)
        gosterilecek_indirimli = res.get("ogrenci_fiyat") or res.get("indirimli_fiyat") or 14.0

        return JSONResponse({
            "tam_fiyat": res.get("tam_fiyat", 20.0),
            "indirimli_fiyat": gosterilecek_indirimli,
            "aktarma1": res.get("aktarma1", "Ücretsiz"),
            "extra_info": [
                "1 Saat İçi Aktarma: Ücretsiz | 1 Saat Sonrası: 8,00 TL",
                "Öğrenci Abonman: 50 Biniş 500 TL | Sınırsız 550 TL",
                "Sivil Abonman: 50 Biniş 1000 TL | Sınırsız 1100 TL",
                "Tam Samkart: 110 TL | Kayıp Kart: 150 TL"
            ]
        })
    
    @app.get("/api/hat/arac/{code:path}")
    async def api_arac(code: str):
        c = urllib.parse.unquote(code).strip()
        
        # On-Demand: Bu hattı aktif olarak işaretle (GTFS-RT sadece aktif hatları sorgular)
        with _active_lines_lock:
            _active_lines[c] = time.time()
        
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
            try:
                araclar = await asyncio.wait_for(asyncio.to_thread(col.canli, samair_hat), timeout=4.0)
            except Exception:
                araclar = []
            duraklar = db.get("SELECT * FROM samair_durak WHERE hat IN (SELECT id FROM samair WHERE kod LIKE ?) ORDER BY sira", (f'%{c}%',))
        else:
            # Normal hat
            try:
                araclar = await asyncio.wait_for(asyncio.to_thread(col.canli, c), timeout=4.0)
            except Exception:
                araclar = []
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
        if count == 0:
            try:
                await asyncio.wait_for(asyncio.to_thread(col.samair_seferler_guncelle, True), timeout=5.0)
            except Exception as e:
                log.error(f"Samair sefer guncelleme timeout/error: {e}")
        today = datetime.now().strftime("%Y-%m-%d")
        rows = db.get("SELECT * FROM samair_sefer WHERE hat=? AND tarih >= ? ORDER BY tarih, saat", (id, today))
        return JSONResponse({"data": rows, "last_update": db.get_meta('samair_last_update_str')})

    # ============================================================
    # YENİ: GTFS İYİLEŞTİRME API ENDPOINT'LERİ
    # ============================================================
    
    @app.get("/api/hat/{code}/yonler")
    async def api_hat_yonler(code: str):
        """Bir hattın gidiş/dönüş yönlerini getir (LineDirections API)"""
        c = urllib.parse.unquote(code).strip()
        yonler = db.get("SELECT yon_id, yon_adi FROM hat_yon WHERE hat=?", (c,))
        
        if not yonler:
            # Fallback: API'den direkt çek
            try:
                yonler_api = col.http.asis('LineDirections', lineCode=c)
                if yonler_api:
                    return JSONResponse([{
                        'yon_id': str(y.get('directionId', '')),
                        'yon_adi': fix_turkish(y.get('directionName', ''))
                    } for y in yonler_api])
            except:
                pass
        
        return JSONResponse(yonler or [])
    
    @app.get("/api/debug/endpoints")
    async def api_debug_endpoints():
        """Kullanılabilir ASIS endpoint'lerini göster"""
        return JSONResponse({
            "asis_endpoints": [
                {"name": "Lines", "params": [], "used": True},
                {"name": "OrjLines", "params": [], "used": True},
                {"name": "StopsStations", "params": ["lineCode?", "stopId?"], "used": True},
                {"name": "SmartStations", "params": ["stationId"], "used": True},
                {"name": "LineDirections", "params": ["lineCode"], "used": True},
                {"name": "RealTimeData", "params": ["lineCode"], "used": True},
                {"name": "Schedules", "params": ["lineCode", "scheduleDate"], "used": True}
            ],
            "base_url": ASIS,
            "gtfs_validator": "https://gtfs-validator.mobilitydata.org/"
        })
    
    @app.get("/gtfs/static.zip")
    async def gtfs_static_export():
        """GTFS Static feed'i ZIP olarak indir — DB'deki GTFS sütunlarını kullanır"""
        import zipfile
        import io
        from bs4 import BeautifulSoup
        
        # Agency bilgisi
        phone, email = "+905051955000", "info@samulas.com.tr"
        try:
            r_ag = requests.get("https://samulas.com.tr/iletisim/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            if r_ag.ok:
                soup = BeautifulSoup(r_ag.content, 'html.parser')
                for a in soup.find_all('a', href=True):
                    if a['href'].startswith('mailto:'): email = a['href'].replace('mailto:', '').strip()
                    elif a['href'].startswith('tel:'): phone = a['href'].replace('tel:', '').strip()
        except: pass
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. agency.txt
            agency_txt = "agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone,agency_email\n"
            agency_txt += f"samulas,Samulaş A.Ş.,https://samulas.com.tr,Europe/Istanbul,tr,{phone},{email}\n"
            zf.writestr("agency.txt", agency_txt)
            
            # 2. feed_info.txt (GTFS validator fix)
            feed_info_txt = "feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version,feed_contact_email,feed_contact_url\n"
            feed_info_txt += f"Samulaş A.Ş.,https://samulas.com.tr,tr,20240101,20261231,2.5,{email},https://samulas.com.tr/iletisim\n"
            zf.writestr("feed_info.txt", feed_info_txt)
            
            # 3. routes.txt — DB'deki GTFS sütunlarını kullan
            routes_txt = "route_id,agency_id,route_short_name,route_long_name,route_type,route_color,route_text_color\n"
            hatlar = db.get("SELECT code, gtfs_route_id, gtfs_route_short_name, gtfs_route_long_name, gtfs_route_type, gtfs_route_color FROM hat")
            route_id_map = {}
            for h in hatlar:
                rid = h['gtfs_route_id'] or sanitize_id(h['code'])
                route_id_map[h['code']] = rid
                r_short = h['gtfs_route_short_name'] or h['code'][:12]
                r_long = h['gtfs_route_long_name'] or h['code']
                r_type = h['gtfs_route_type'] or '3'
                r_color = h['gtfs_route_color'] or '1877F2'
                routes_txt += f"{rid},samulas,{r_short},{r_long},{r_type},{r_color},FFFFFF\n"
            zf.writestr("routes.txt", routes_txt)
            
            # 4. calendar.txt — dinamik tarih
            bugun = date.today()
            cal_start = bugun.strftime('%Y%m%d')
            cal_end = bugun.replace(year=bugun.year + 2).strftime('%Y%m%d')
            calendar_txt = "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
            calendar_txt += f"1,1,1,1,1,1,0,0,{cal_start},{cal_end}\n"
            calendar_txt += f"2,0,0,0,0,0,1,0,{cal_start},{cal_end}\n"
            calendar_txt += f"3,0,0,0,0,0,0,1,{cal_start},{cal_end}\n"
            calendar_txt += f"4,1,1,1,1,1,1,1,{cal_start},{cal_end}\n"
            zf.writestr("calendar.txt", calendar_txt)
            
            # 5. trips.txt & stop_times.txt — GTFS sütunlarını kullan + filtreler
            trips_lines = ["route_id,service_id,trip_id,trip_headsign,direction_id"]
            stop_times_lines = ["trip_id,arrival_time,departure_time,stop_id,stop_sequence"]
            
            # Durak koordinat cache
            durak_dict = {}
            for d in db.get("SELECT id, gtfs_stop_id, lat, lon FROM durak WHERE lat IS NOT NULL"):
                durak_dict[d['id']] = (d['lat'], d['lon'], d['gtfs_stop_id'] or sanitize_id(d['id']))
            
            # N+1 sorgu cache — tüm hat_durak'ları tek sorguda al
            from collections import defaultdict
            hat_durak_cache = defaultdict(list)
            for row in db.get("SELECT hat, durak_id, sira FROM hat_durak ORDER BY hat, sira ASC"):
                hat_durak_cache[row['hat']].append(row)
            
            used_stop_ids = set()
            skipped = 0
            
            seferler = db.get("SELECT id, hat, saat, yon, gun, gtfs_trip_id, gtfs_route_id, gtfs_service_id FROM sefer")
            for s in seferler:
                route_id_orig = s['hat']
                route_id = s['gtfs_route_id'] or route_id_map.get(route_id_orig, sanitize_id(route_id_orig))
                trip_id = s['gtfs_trip_id'] or sanitize_id(f"T_{s['id']}")
                headsign = title_case_tr(str(s['yon']).replace(',', ' '))
                service_id = s['gtfs_service_id'] or gun_to_service(s['gun'])
                yon_ascii = str(s['yon']).upper().translate(_ASCII_MAP)
                direction_id = "0" if "GIDIS" in yon_ascii or s['yon'] == 'G' else "1"
                
                route_duraklar = hat_durak_cache.get(route_id_orig, [])
                
                # Unusable trip filtresi
                if len(route_duraklar) <= 1:
                    skipped += 1
                    continue
                
                trips_lines.append(f"{route_id},{service_id},{trip_id},{headsign},{direction_id}")
                
                try:
                    h_val, m_val = map(int, s['saat'].split(':')[:2])
                    current_minutes = h_val * 60 + m_val
                except (ValueError, AttributeError, TypeError):
                    current_minutes = 360
                
                prev_lat, prev_lon = None, None
                for idx, rd in enumerate(route_duraklar):
                    sira = int(rd['sira'])
                    stop_id_orig = rd['durak_id']
                    dd = durak_dict.get(stop_id_orig)
                    stop_id = dd[2] if dd else sanitize_id(stop_id_orig)
                    
                    used_stop_ids.add(stop_id_orig)
                    
                    added_mins = 0
                    if idx > 0 and dd:
                        lat, lon = dd[0], dd[1]
                        if lat and lon and prev_lat and prev_lon:
                            dist = haversine(prev_lat, prev_lon, lat, lon)
                            added_mins = ((dist / 6.1) + 35) / 60.0
                        else:
                            added_mins = 1.5
                    
                    current_minutes += added_mins
                    total_sec = int(round(current_minutes * 60))
                    arr_h = total_sec // 3600
                    arr_m = (total_sec % 3600) // 60
                    arr_s = total_sec % 60
                    time_str = f"{arr_h:02d}:{arr_m:02d}:{arr_s:02d}"
                    
                    stop_times_lines.append(f"{trip_id},{time_str},{time_str},{stop_id},{sira}")
                    
                    if dd: prev_lat, prev_lon = dd[0], dd[1]
            
            zf.writestr("trips.txt", "\n".join(trips_lines) + "\n")
            zf.writestr("stop_times.txt", "\n".join(stop_times_lines) + "\n")
            
            # 6. stops.txt — sadece kullanılan duraklar (stop_without_stop_time fix)
            stops_txt = "stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type\n"
            duraklar = db.get("SELECT id, kod, gtfs_stop_id, gtfs_stop_name, lat, lon FROM durak WHERE lat IS NOT NULL")
            for d in duraklar:
                if d['id'] not in used_stop_ids:
                    continue
                sid = d['gtfs_stop_id'] or sanitize_id(d['id'])
                sname = d['gtfs_stop_name'] or d['id']
                stops_txt += f"{sid},{d['kod'] or ''},{sname},{d['lat']},{d['lon']},0\n"
            zf.writestr("stops.txt", stops_txt)
        
        zip_buffer.seek(0)
        return Response(zip_buffer.getvalue(), media_type="application/zip", headers={'Content-Disposition': 'attachment; filename="samsun_gtfs.zip"'})
    
    @app.get("/gtfs-rt/vehicle-positions.json")
    async def gtfs_rt_debug():
        """GTFS-RT feed'i JSON formatında göster (debug)"""
        from google.protobuf.json_format import MessageToDict
        return JSONResponse(MessageToDict(gtfs_feed))
    
    @app.get("/gtfs/validate")
    async def gtfs_validation_info():
        """GTFS Validator bilgisi"""
        return JSONResponse({
            "validator_url": "https://gtfs-validator.mobilitydata.org/",
            "gtfs_spec": "https://gtfs.org/schedule/reference/",
            "gtfs_rt_spec": "https://gtfs.org/realtime/reference/",
            "feed_endpoints": {
                "gtfs_static": "/gtfs/static.zip",
                "gtfs_rt": "/gtfs-rt/vehicle-positions",
                "gtfs_rt_json": "/gtfs-rt/vehicle-positions.json"
            },
            "improvements": {
                "realistic_stop_times": "✅ Enabled",
                "shapes": "✅ Enabled",
                "trip_id": "✅ Enabled",
                "bearing": "✅ Enabled",
                "occupancy": "✅ Enabled"
            }
        })

    return app

# ==========================================
# GLOBAL ASGI INITIALIZATION (SAMSUN TRANSIT)
# ==========================================
# Bu bölüm Render/Vercel gibi ASGI sunucularının 'app' objesini bulabilmesi içindir.

t_start = time.time()
try:
    leaflet_indir()
except Exception as e:
    log.warning(f"Leaflet indirme hatası (cloud ortamında olabilir): {e}")

# Servisleri başlat
db = Database()
db.connect()
col = Collector(db, Http())

# Veritabanını ilk açılışta güncelle (Background Thread içerisinde çalıştır, yoksa Render port dinlemeyi engeller!)
def initial_data_loader():
    try:
        log.info("🚀 Arka plan veri önbellekleme (veri_cek) başlatılıyor...")
        col.veri_cek()
        col.samair_seferler_guncelle()
        log.info("✅ Arka plan veri önbellekleme tamamlandı.")
    except Exception as e:
        log.error(f"Başlangıç veri çekme hatası: {e}")

loader_thread = threading.Thread(target=initial_data_loader, daemon=True)
loader_thread.start()

# FastAPI uygulamasını oluştur
app = create_app(db, col)

# Arka plan Samair güncelleyici fonksiyonu
def start_samair_updater():
    def samair_periodic_update():
        consecutive_errors = 0
        while True:
            interval = _admin_config.get('samair_interval', 7200)
            time.sleep(interval)
            # Gece kontrolü (23-09 arası güncelleme yapma)
            tr_hour = (datetime.utcnow().hour + 3) % 24
            if tr_hour >= 23 or tr_hour < 9:
                continue
            try:
                log.info(f"✈️ Samair seferleri güncelleniyor ({interval//3600}h aralıkla)...")
                col.samair_seferler_guncelle(force=True)
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                log.error(f"Samair güncelleme hatası: {e}")
                if consecutive_errors >= 3:
                    log.warning("⚠️ Samair güncelleme başarısız, sonraki döngüye atlanıyor")
                    consecutive_errors = 0

    update_thread = threading.Thread(target=samair_periodic_update, daemon=True)
    update_thread.start()
    log.info(f"✓ Samair otomatik güncelleme thread'i aktif (her {int(os.environ.get('SAMAIR_INTERVAL', '7200'))//3600} saat)")

# Render.com Free Tier Uyku Önleyici — 50sn uyku sınırına karşı 40sn ping
def start_keep_alive_ping():
    def pinger():
        import requests as _req
        import random
        targets = [
            "https://www.google.com",
            "https://1.1.1.1",
            "https://api.github.com/zen"
        ]
        while True:
            time.sleep(40) # Render 50 saniyede uyur, biz 40'ta uyandırıyoruz
            try:
                # 1. Kendi API'mizi pingleyelim
                url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")
                _req.get(f"{url}/api/health", timeout=5)
                
                # 2. Rastgele dış bir siteye istek atarak ağ aktivitesi yaratalım
                ext = random.choice(targets)
                _req.get(ext, timeout=5)
                
                tr_hour = (datetime.utcnow().hour + 3) % 24
                if tr_hour >= 23 or tr_hour < 9:
                    log.debug("💤 Gece modu: Sadece keep-alive (40s) ping gönderildi")
                else:
                    log.debug("💓 Keep-Alive (40s) ağ aktivitesi yaratıldı")
            except Exception:
                pass

    ping_thread = threading.Thread(target=pinger, daemon=True)
    ping_thread.start()
    log.info("✓ Keep-Alive pinger aktif (Her 40 saniyede bir ağ aktivitesi)")

# Eğer app oluşturulduysa (örneğin Render 'uvicorn samsun:app' dediğinde) updater'ı başlat.
if app:
    start_samair_updater()
    start_keep_alive_ping()

def main():
    import sys
    import signal
    import atexit
    
    # Windows terminal encoding fix
    if sys.platform == 'win32':
        try: sys.stdout.reconfigure(encoding='utf-8')
        except Exception: pass
    
    print("=" * 55)
    print("  SAMSUN TRANSIT - SUPER APP v25 (MASTER)")
    print("=" * 55)

    # Graceful shutdown (sadece lokal CLI için)
    def _shutdown(signum=None, frame=None):
        log.info("\n🚶 Sistem kapatılıyor...")
        try:
            if db.conn:
                db.conn.close()
                log.info("  ✅ Veritabanı bağlantısı kapatıldı")
        except Exception: pass
        log.info("  👋 Güle güle!")
    
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    atexit.register(_shutdown)

    startup_secs = time.time() - t_start
    log.info("=" * 50)
    log.info(f"  🚀 Sistem hazır: {startup_secs:.1f}sn")
    log.info(f"  📊 Hat: {db.cnt('hat')} | Durak: {db.cnt('durak')} | Fiyat: {db.cnt('fiyat')}")
    log.info(f"  🌐 Web: http://localhost:8000")
    log.info(f"  ❤️ Health: http://localhost:8000/api/health")
    log.info(f"  PID: {os.getpid()}")
    log.info("=" * 50)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

if __name__ == "__main__":
    main()
