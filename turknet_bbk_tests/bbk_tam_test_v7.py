#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=============================================================================
  BBK ALTYAPI TAM TEST SİSTEMİ v7 — LOSSLESS FINAL REPORT
=============================================================================

  AMAÇ
  ────────────────────────────────────────────────────────────────────────────
  - Kaynak tarafında filtreleme yapma
  - Downstream tarafında filtreleme yapma
  - Final parser'larda teknoloji / servis tahmini uydurma
  - Sadece açık alanları taşı
  - Ham response'ları da sakla
  - Final tabloda dürüst göster:
      Q= query_success
      M= match_success
      S= service_available (yalnızca açık alan varsa)
      T= technology (yalnızca açık alan varsa)

  KAYNAKLAR
  ────────────────────────────────────────────────────────────────────────────
  - ISS
  - Alaznet Sorgu
  - Alaznet AdresCek
  - Vivanet
  - JIO

  DOWNSTREAM
  ────────────────────────────────────────────────────────────────────────────
  - D-Smart
  - Milenicom
  - Türksat Livewire
  - Teknofix Secondary
=============================================================================
"""

import requests
import json
import re
import time
import random
import string
import urllib.parse
import urllib3
import logging
import os
import html as html_module
import ast
from datetime import datetime
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── ÇIKTI DİZİNİ ───────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(_SCRIPT_DIR, "bbk_ciktilar")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── LOGGING ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("BBK_TEST")

# ─── CONFIG ─────────────────────────────────────────────────────────────────
BBK_LIST  = ["50937281", "37735014", "12525039"]
# ONLY TEST THE FIRST BBK FOR TURKNET
BBK_LIST = ["50937281"]
ATTEMPTS  = 1
RATE_DELAY = 1.8
BBK_DELAY  = 3.0
HTTP_TIMEOUT_SHORT  = 12
HTTP_TIMEOUT_MEDIUM = 22
HTTP_TIMEOUT_LONG   = 40

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/144.0.0.0 Safari/537.36"
)

# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def _sleep(s: float = RATE_DELAY):
    time.sleep(s + random.uniform(0.2, 0.45))

def _score(data: Any) -> int:
    try:
        return len(json.dumps(data, ensure_ascii=False, default=str)) if data else -1
    except Exception:
        return -1

def _norm_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _safe_json_text(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)

def compact_text(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)[:2000]
    except Exception:
        return str(obj)[:2000]

def find_first_key(obj, keys_upper):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).upper() in keys_upper:
                return v
            found = find_first_key(v, keys_upper)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first_key(item, keys_upper)
            if found is not None:
                return found
    return None

def find_all_number_keys(obj, keys_upper):
    vals = []

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                ku = str(k).upper()
                if ku in keys_upper and isinstance(v, (int, float)):
                    vals.append(v)
                walk(v)
        elif isinstance(x, list):
            for item in x:
                walk(item)

    walk(obj)
    return vals

# ═══════════════════════════════════════════════════════════════════════════
#  NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════
def _dn(t: str) -> str:
    if not t:
        return ""
    t = str(t).upper()
    for s, d in [
        ("İ", "I"), ("İ", "I"), ("Ğ", "G"), ("Ü", "U"),
        ("Ş", "S"), ("Ö", "O"), ("Ç", "C")
    ]:
        t = t.replace(s, d)
    t = re.sub(
        r'\b(MAH|MAH\.|MAHALLESI|MAHALLESİ|SK|SOK|SOKAK|SOKAGI|SOKAĞI|CAD|CADDE|CADDESI|CADDESİ|BLV|BULVARI?)\.?\b',
        '',
        t
    )
    t = re.sub(r'[^A-Z0-9 ]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def clean_mahalle_name(v: str) -> str:
    v = _dn(v)
    v = v.replace("MAH", "").replace("MAHALLESI", "").strip()
    return re.sub(r"\s+", " ", v).strip()

def _normalize_building_no(v: str) -> str:
    v = _dn(v)
    v = v.replace("NO", "").strip()
    return v

# ═══════════════════════════════════════════════════════════════════════════
#  ADRES PARSER
# ═══════════════════════════════════════════════════════════════════════════
_SOKAK_PAT = re.compile(
    r'([\wÇĞİÖŞÜçğışöşü][\w\sÇĞİÖŞÜçğıöşü\.\-]+'
    r'(?:SOKAK|SOKAĞI|SOKAGI|SOK\.?|CADDE(?:Sİ)?|CAD\.?'
    r'|BULVAR(?:I)?|BLV\.?|KÜME\s+EVLERİ|CSBM|YOLU|SK\.?))',
    re.IGNORECASE | re.UNICODE
)

def parse_adres_text(adres: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not adres:
        return result

    adres = _norm_spaces(adres)

    if "/" in adres:
        left, right = adres.rsplit("/", 1)
        result["IL"] = _norm_spaces(right)
        left = _norm_spaces(left)

        tail_match = re.search(r'(?:DAİRE|DAIRE)\s*[:/]\s*\S+\s+(.+)$', left, re.IGNORECASE)
        if tail_match:
            result["ILCE"] = _norm_spaces(tail_match.group(1))
            adres = _norm_spaces(left[:tail_match.start()])
        else:
            tail_no = re.search(r'NO\s*[:/]\s*\S+\s+(.+)$', left, re.IGNORECASE)
            if tail_no:
                result["ILCE"] = _norm_spaces(tail_no.group(1))
                adres = _norm_spaces(left[:tail_no.start()])
            else:
                m_ilce = re.search(r'(.+?)\s+([A-ZÇĞİÖŞÜa-zçğıöşü\.\-]+)$', left)
                if m_ilce:
                    adres = _norm_spaces(m_ilce.group(1))
                    result["ILCE"] = _norm_spaces(m_ilce.group(2))
                else:
                    adres = left

    m = re.search(r'D[AİI]RE\s*[:/]\s*(\S+)', adres, re.IGNORECASE)
    if m and m.group(1) not in ("-", ""):
        result["DAIRE"] = _norm_spaces(m.group(1))
        adres = _norm_spaces(adres[:m.start()])

    m = re.search(r'NO\s*[:/]\s*([A-Z0-9\/\- ]+)', adres, re.IGNORECASE)
    if m:
        result["BINA"] = _norm_spaces(m.group(1).rstrip(","))
        adres = _norm_spaces(adres[:m.start()])

    m = _SOKAK_PAT.search(adres)
    if m:
        result["SOKAK"] = _norm_spaces(m.group(1))
        adres = _norm_spaces(adres[:m.start()])

    adres = _norm_spaces(adres.strip(","))
    if adres:
        result["MAHALLE"] = adres

    return {k: v for k, v in result.items() if v}

def extract_address_from_alaz(data: Dict) -> Dict[str, str]:
    try:
        aa = data.get("aciklama", {}).get("AcikAdres", {})
        ak = data.get("aciklama", {}).get("AdresKodu", {})
        out = {
            "IL": aa.get("IlAdi") or ak.get("IlAdi"),
            "ILCE": aa.get("IlceAdi") or ak.get("IlceAdi"),
            "MAHALLE": aa.get("MahalleAdi") or ak.get("MahalleAdi"),
            "SOKAK": aa.get("CSBMAdi") or aa.get("SokakAdi") or aa.get("CaddeAdi") or ak.get("CsbmAdi"),
            "BINA": aa.get("DisKapiNo") or ak.get("DisKapiNo") or ak.get("BinaNo"),
            "DAIRE": aa.get("IcKapiNo") or ak.get("IcKapiNo") or ak.get("DaireNo"),
            "BINA_KODU": ak.get("BinaKodu"),
            "IL_KODU": ak.get("IlKodu"),
            "ILCE_KODU": ak.get("IlceKodu"),
            "MAHALLE_KODU": ak.get("MahalleKodu"),
            "CSBM_KODU": ak.get("CsbmKodu"),
        }
        return {k: v for k, v in out.items() if v not in (None, "", "-", "0")}
    except Exception:
        return {}

def _parse_iss_address_field(raw_addr: Any) -> Dict[str, str]:
    if not raw_addr:
        return {}

    if isinstance(raw_addr, dict):
        out = {
            "IL": raw_addr.get("province"),
            "ILCE": raw_addr.get("district"),
            "MAHALLE": raw_addr.get("neighborhood"),
            "SOKAK": raw_addr.get("street"),
            "BINA": raw_addr.get("building_no"),
            "DAIRE": raw_addr.get("apartment_no"),
            "SITE": raw_addr.get("site_name"),
            "BLOK": raw_addr.get("block_name"),
            "_FULL_ADDRESS_": raw_addr.get("full_address"),
        }
        cleaned = {}
        for k, v in out.items():
            if v not in (None, "", [], {}):
                cleaned[k] = _norm_spaces(str(v))
        return cleaned

    if isinstance(raw_addr, str):
        txt = raw_addr.strip()
        if txt.startswith("{") and txt.endswith("}"):
            try:
                obj = ast.literal_eval(txt)
                if isinstance(obj, dict):
                    return _parse_iss_address_field(obj)
            except Exception:
                pass
        return parse_adres_text(txt)

    return {}

def extract_address_from_iss(data: Dict) -> Dict[str, str]:
    result_raw = data.get("result", data)
    address_raw = result_raw.get("address", "") or data.get("address", "")
    addr = _parse_iss_address_field(address_raw)
    if addr:
        log.info(f"    [ISS] result.address parse → {addr}")
    return {k: v for k, v in addr.items() if v}

def extract_address_from_adres_cek(data: Dict, bbk: str) -> Dict[str, str]:
    out = {}
    try:
        if data.get("Adres"):
            out.update(parse_adres_text(data["Adres"]))
        if data.get("BBK"):
            out["BBK"] = str(data["BBK"])
        elif bbk:
            out["BBK"] = str(bbk)
        return {k: v for k, v in out.items() if v}
    except Exception:
        return {}

def resolve_address(bbk: str, iss: Dict, alaz: Dict, adres_cek: Dict, jio: Optional[Dict] = None) -> Dict[str, str]:
    if alaz and "_error_" not in alaz:
        addr = extract_address_from_alaz(alaz)
        if all(addr.get(k) for k in ["IL", "ILCE", "MAHALLE"]):
            log.info("  [Adres] ★ Kaynak: Alaznet AcikAdres")
            return addr

    if iss and "_error_" not in iss:
        addr = extract_address_from_iss(iss)
        if all(addr.get(k) for k in ["IL", "ILCE"]):
            log.info("  [Adres] ★ Kaynak: ISS result.address")
            return addr

    if adres_cek and "_error_" not in adres_cek:
        addr = extract_address_from_adres_cek(adres_cek, bbk)
        if addr.get("IL"):
            log.info("  [Adres] ★ Kaynak: Alaznet AdresCek metin")
            return addr

    log.warning("  [Adres] Hiçbir güvenli kaynaktan tam adres çıkarılamadı!")
    return {}

# ═══════════════════════════════════════════════════════════════════════════
#  QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def query_iss(bbk: str) -> Dict:
    url = f"https://issaraclari.com/api/api.php?action=port-info&bbk={bbk}"
    try:
        resp = requests.get(url, headers={
            "authority": "issaraclari.com",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "referer": "https://issaraclari.com/altyapi-sorgulama",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": CHROME_UA,
        }, timeout=HTTP_TIMEOUT_MEDIUM)
        log.info(f"  [ISS] HTTP {resp.status_code}")
        if resp.status_code != 200:
            return {"_error_": f"HTTP {resp.status_code}", "_source_": "ISS"}
        data = resp.json()
        data["_source_"] = "ISS Araçları"
        return data
    except Exception as e:
        return {"_error_": str(e), "_source_": "ISS"}

def query_alaznet_sorgu(bbk: str) -> Dict:
    url = "https://alaznet.com.tr/service/altyapi/sorgu.php"
    headers = {
        "User-Agent": CHROME_UA,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Referer": "https://alaznet.com.tr/service/altyapi/sayfa.php",
        "Origin": "https://alaznet.com.tr",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cookie": "PHPSESSID=altyapi_sorgu_session",
    }
    try:
        resp = requests.get(url, params={"daire_id": bbk}, headers=headers, timeout=HTTP_TIMEOUT_MEDIUM)
        log.info(f"  [Alaznet-Sorgu] HTTP {resp.status_code}")
        if resp.status_code != 200:
            return {"_error_": f"HTTP {resp.status_code}", "_source_": "Alaznet"}
        data = resp.json()
        data["_source_"] = "Alaznet Sorgu"
        return data
    except Exception as e:
        return {"_error_": str(e), "_source_": "Alaznet"}

def query_alaznet_adres_cek(bbk: str) -> Dict:
    url = "https://alaznet.com.tr/service/altyapi/adres_cek.php"
    try:
        resp = requests.get(url, params={"home": bbk}, headers={
            "User-Agent": CHROME_UA,
            "Accept": "application/json, */*",
            "Referer": "https://alaznet.com.tr/service/altyapi/sayfa.php",
            "X-Requested-With": "XMLHttpRequest",
        }, timeout=HTTP_TIMEOUT_SHORT)
        log.info(f"  [Alaznet-AdresCek] HTTP {resp.status_code}")
        if resp.status_code != 200:
            return {"_error_": f"HTTP {resp.status_code}", "_source_": "Alaznet AdresCek"}
        data = resp.json(strict=False) if resp.content else {}
        data["_source_"] = "Alaznet AdresCek"
        return data
    except Exception as e:
        return {"_error_": str(e), "_source_": "Alaznet AdresCek"}

def query_vivanet(bbk: str) -> Dict:
    url = "https://vivanet.tr/altyap.php"
    try:
        resp = requests.post(url, data={"tt_altyapi": bbk}, headers={
            "User-Agent": CHROME_UA,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://vivanet.tr/altyapi-sorgula/",
        }, timeout=HTTP_TIMEOUT_MEDIUM)
        log.info(f"  [Vivanet] HTTP {resp.status_code}")
        text = resp.text.strip()
        result = {"_raw_": text, "_source_": "Vivanet TT"}
        if "--" in text:
            parts = text.split("--")
            if len(parts) >= 3:
                result["tip"]  = parts[0].strip()
                result["hiz"]  = parts[1].strip()
                result["port"] = "1" if "VAR" in parts[2].upper() else "0"
        return result
    except Exception as e:
        return {"_error_": str(e), "_source_": "Vivanet TT"}

def query_jio(bbk: str) -> Dict:
    import asyncio
    import urllib.parse
    import aiohttp
    from scrapling.fetchers import AsyncDynamicSession

    async def _do_jio():
        base_url = "https://www.jio.com.tr"
        api_url = f"{base_url}/api/v1/ttservice/tt_vae_query"
        body = {
            "selectedCity": {"code": 55, "value": "SAMSUN"},
            "selectedTown": {"code": "2072", "value": "ATAKUM"},
            "selectedNeighbor": {"code": "61794", "value": "MERKEZ", "post_code": "00000"},
            "selectedStreet": {"code": "894797", "value": "MERKEZ"},
            "selectedBuilding": {"code": "28547025", "value": "MERKEZ"},
            "selectedHome": {"code": str(bbk), "value": f"BBK {bbk}"}
        }
        try:
            valid_cookies = {}
            xsrf = ""
            async with AsyncDynamicSession(headless=True) as s:
                page_obj = await s.fetch('https://www.jio.com.tr/internet-altyapi-hiz-sorgulama', timeout=25000)
                for c in page_obj.cookies:
                    valid_cookies[c['name']] = c['value']
                    if c['name'] == 'XSRF-TOKEN':
                        xsrf = urllib.parse.unquote(c['value'])
            
            if not xsrf or not valid_cookies:
                return {"_error_": "XSRF alınamadı", "_source_": "JIO"}

            headers = {
                "User-Agent": CHROME_UA,
                "Accept": "application/json; charset=utf-8",
                "Origin": base_url,
                "Referer": f"{base_url}/internet-altyapi-hiz-sorgulama",
                "X-Xsrf-Token": xsrf,
                "Content-Type": "application/json"
            }
            
            jar = aiohttp.CookieJar(unsafe=True)
            for name, value in valid_cookies.items():
                jar.update_cookies({name: value})
                
            timeout = aiohttp.ClientTimeout(total=15)
            log.info(f"  [JIO] Bypass OK, TT POST atılıyor... (BBK: {bbk})")
            async with aiohttp.ClientSession(cookie_jar=jar, timeout=timeout) as session:
                async with session.post(api_url, json=body, headers=headers, ssl=False) as resp:
                    if resp.status != 200:
                        return {"_error_": f"HTTP {resp.status} - {await resp.text()}", "_source_": "JIO"}
                    data = await resp.json()
                    data["_source_"] = "JIO"
                    return data
        except Exception as e:
            return {"_error_": str(e), "_source_": "JIO"}

    try:
        data = asyncio.run(_do_jio())
        return data
    except Exception as e:
        return {"_error_": str(e), "_source_": "JIO"}
    except Exception as e:
        return {"_error_": str(e), "_source_": "JIO"}

def query_turknet(bbk: str, addr_dict: Dict = None) -> Dict:
    """Turknet altyapı sorgusu — Hibrit Bypass + Proxy + sales-gateway API.
    Fallback zinciri: UC → Selenium → Scrapling → Crawlee
    Adres sözlüğündeki IL/ILCE/MAHALLE isimlerinden Turknet API ile ID'leri bulur.
    infrastructureType: 4=ADSL, 5=VDSL, 6=GigaFiber, 11=Fiber
    """
    import base64
    import uuid

    SG = "https://sales-gateway.turk.net"
    INFRA_MAP = {4: "ADSL", 5: "VDSL", 6: "GigaFiber", 11: "Fiber"}
    TARGET_URL = "https://www.turk.net/internet-hiz-altyapi-sorgulama"
    
    # Proxy config
    _ph = os.environ.get("PROXY_HOST", "")
    _pp = os.environ.get("PROXY_PORT", "")
    _pu = os.environ.get("PROXY_USER", "")
    _pw = os.environ.get("PROXY_PASS", "")
    proxy_url = None
    if _ph and _pp:
        proxy_url = f"http://{_pu}:{_pw}@{_ph}:{_pp}" if _pu else f"http://{_ph}:{_pp}"
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    
    # ── TOKEN ALMA: Fallback zinciri ──
    def _get_token_uc():
        try:
            import undetected_chromedriver as uc
            opts = uc.ChromeOptions()
            opts.add_argument("--headless=new"); opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage"); opts.add_argument("--disable-gpu")
            if _ph and _pp:
                opts.add_argument(f"--proxy-server={_ph}:{_pp}")
            driver = uc.Chrome(options=opts, version_main=None)
            try:
                driver.get(TARGET_URL); time.sleep(6)
                cookies = {c['name']:c['value'] for c in driver.get_cookies()}
                at = ""
                try:
                    at = driver.execute_script("const r=await fetch('/api/auth/fetch-access-token',{method:'POST',headers:{'Content-Type':'application/json'}});const d=await r.json();return d.accessToken||''")
                except: pass
                if cookies.get('token') or at: return cookies, at
            finally:
                try: driver.quit()
                except: pass
        except Exception as e:
            log.warning(f"  [Turknet/UC] {e}")
        return None, None
    
    def _get_token_selenium():
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            opts = Options()
            opts.add_argument("--headless=new"); opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            if _ph and _pp:
                opts.add_argument(f"--proxy-server={_ph}:{_pp}")
            driver = webdriver.Chrome(options=opts)
            try:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                    {"source":"Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"})
                driver.get(TARGET_URL); time.sleep(6)
                cookies = {c['name']:c['value'] for c in driver.get_cookies()}
                at = ""
                try:
                    at = driver.execute_script("const r=await fetch('/api/auth/fetch-access-token',{method:'POST',headers:{'Content-Type':'application/json'}});const d=await r.json();return d.accessToken||''")
                except: pass
                if cookies.get('token') or at: return cookies, at
            finally:
                try: driver.quit()
                except: pass
        except Exception as e:
            log.warning(f"  [Turknet/Selenium] {e}")
        return None, None
    
    def _get_token_scrapling():
        import asyncio as _aio
        async def _inner():
            from scrapling.fetchers import AsyncDynamicSession
            kw = {"headless": True}
            if proxy_url:
                kw["proxy"] = {"server": f"http://{_ph}:{_pp}"}
                if _pu: kw["proxy"]["username"] = _pu; kw["proxy"]["password"] = _pw
            async with AsyncDynamicSession(**kw) as s:
                resp = await s.fetch(TARGET_URL, timeout=15000)
                await _aio.sleep(3)
                return {c['name']:c['value'] for c in resp.cookies}
        try:
            cookies = _aio.run(_inner())
            if cookies.get('token'): return cookies, ""
        except Exception as e:
            log.warning(f"  [Turknet/Scrapling] {e}")
        return None, None
    
    def _get_token_crawlee():
        import asyncio as _aio
        async def _inner():
            try:
                from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
            except ImportError:
                from crawlee.crawlers import PlaywrightCrawler
                from crawlee.crawlers._playwright import PlaywrightCrawlingContext
            rc = {}
            pc = None
            if proxy_url:
                from crawlee import ProxyConfiguration
                pc = ProxyConfiguration(proxy_urls=[proxy_url])
            crawler = PlaywrightCrawler(headless=True, browser_type="chromium",
                                        max_request_retries=1, proxy_configuration=pc)
            @crawler.router.default_handler
            async def h(ctx: PlaywrightCrawlingContext):
                nonlocal rc
                await ctx.page.wait_for_timeout(5000)
                for c in await ctx.page.context.cookies():
                    rc[c['name']] = c['value']
            await crawler.run([TARGET_URL])
            return rc
        try:
            cookies = _aio.run(_inner())
            if cookies.get('token'): return cookies, ""
        except Exception as e:
            log.warning(f"  [Turknet/Crawlee] {e}")
        return None, None
    
    # Fallback zinciri
    cookies, access_token = None, ""
    for name, fn in [("UC", _get_token_uc), ("Selenium", _get_token_selenium),
                     ("Scrapling", _get_token_scrapling), ("Crawlee", _get_token_crawlee)]:
        log.info(f"  [Turknet] Token yöntemi: {name}...")
        cookies, access_token = fn()
        if cookies:
            log.info(f"  [Turknet] ✓ {name} ile token alındı")
            break
    
    if not cookies:
        return {"_error_": "Hiçbir yöntemle token alınamadı", "_source_": "Turknet"}
    
    # access_token yoksa requests ile dene
    if not access_token and cookies.get('token'):
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        try:
            r = requests.post("https://www.turk.net/api/auth/fetch-access-token",
                headers={"User-Agent":"Mozilla/5.0","Cookie":cookie_str,
                         "Content-Type":"application/json","Origin":"https://www.turk.net",
                         "Referer":"https://www.turk.net/"}, json={}, timeout=10, proxies=proxies)
            if r.status_code == 200:
                access_token = r.json().get("accessToken", "")
        except: pass
    
    # SaleKey
    sale_key = ""
    tok = cookies.get("token", "")
    if tok:
        try:
            parts = tok.split(".")
            payload_b64 = parts[1] + "==" * (4 - len(parts[1]) % 4)
            jwt_pl = json.loads(base64.urlsafe_b64decode(payload_b64))
            sale_key = jwt_pl.get("SaleKey", "")
        except: pass
    
    # ── API ÇAĞRILARI: requests + proxy ──
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    base_h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.turk.net", "Referer": "https://www.turk.net/",
        "sec-fetch-mode": "cors", "sec-fetch-site": "same-site",
        "Cookie": cookie_str,
    }
    if access_token:
        base_h["Authorization"] = f"Bearer {access_token}"
    
    result = {"_source_": "Turknet", "sale_key": sale_key}
    
    # Adres çözümleme
    il_adi = (addr_dict or {}).get("IL", "").strip().upper()
    ilce_adi = (addr_dict or {}).get("ILCE", "").strip().upper()
    mahalle_adi = (addr_dict or {}).get("MAHALLE", "").strip().upper()
    city_id = county_id = neighborhood_id = 0
    
    if il_adi:
        try:
            r = requests.get(f"{SG}/api/address/cities", headers=base_h, timeout=10, proxies=proxies)
            if r.status_code == 200:
                for c in r.json().get("data", []):
                    if c.get("name","").strip().upper() == il_adi:
                        city_id = c["code"]; log.info(f"  [Turknet] İl: {il_adi} → {city_id}"); break
        except Exception as e:
            log.warning(f"  [Turknet] İl API: {e}")
    if not city_id: city_id = 55
    
    if ilce_adi and city_id:
        try:
            r = requests.get(f"{SG}/api/address/counties/{city_id}", headers=base_h, timeout=10, proxies=proxies)
            if r.status_code == 200:
                for c in r.json().get("data", []):
                    cn = c.get("name","").strip().upper()
                    if cn == ilce_adi or ilce_adi in cn:
                        county_id = c["code"]; log.info(f"  [Turknet] İlçe: {ilce_adi} → {county_id}"); break
        except Exception as e:
            log.warning(f"  [Turknet] İlçe API: {e}")
    
    tid = vid = 0
    if county_id:
        try:
            r = requests.get(f"{SG}/api/address/townships/{county_id}", headers=base_h, timeout=10, proxies=proxies)
            if r.status_code == 200:
                d = r.json().get("data",[])
                if d: tid = d[0]["code"]; log.info(f"  [Turknet] Township: {d[0].get('name','')} → {tid}")
        except: pass
    if tid:
        try:
            r = requests.get(f"{SG}/api/address/villages/{tid}", headers=base_h, timeout=10, proxies=proxies)
            if r.status_code == 200:
                d = r.json().get("data",[])
                if d: vid = d[0]["code"]; log.info(f"  [Turknet] Village: {d[0].get('name','')} → {vid}")
        except: pass
    if mahalle_adi and vid:
        try:
            r = requests.get(f"{SG}/api/address/districts/{vid}", headers=base_h, timeout=10, proxies=proxies)
            if r.status_code == 200:
                mc = re.sub(r'\s+',' ',mahalle_adi).replace("MAH.","").replace("MAH","").strip()
                for d in r.json().get("data",[]):
                    dn = re.sub(r'\s+',' ',d.get("name","")).strip().upper()
                    if mc == dn or mc in dn or dn in mc:
                        neighborhood_id = d["code"]; log.info(f"  [Turknet] Mahalle: {mc} → {neighborhood_id}"); break
        except: pass
    
    result["resolved_city_id"] = city_id
    result["resolved_county_id"] = county_id
    result["resolved_neighborhood_id"] = neighborhood_id
    
    # Sales/Offer
    building_id = 0
    try:
        if addr_dict and addr_dict.get("BINA_KODU"):
            building_id = int(addr_dict.get("BINA_KODU"))
    except: pass
    
    body = {
        "isInfrastructureInquiry": True, "key": "BBK", "buildingId": building_id,
        "value": str(bbk), "inquirySource": 2, "cityId": city_id, "channel": 2,
        "operator": "", "countyId": county_id, "neighborhoodId": neighborhood_id,
    }
    offer_h = {**base_h, "Content-Type": "application/json",
               "Captcha": str(uuid.uuid4()), "X-Sale-Key": sale_key}
    
    log.info(f"  [Turknet] POST sales/offer | BBK={bbk} city={city_id} county={county_id} neigh={neighborhood_id} bldg={building_id}")
    try:
        r = requests.post(f"{SG}/api/sales/offer", headers=offer_h, json=body, timeout=15, proxies=proxies)
        result["offer_status"] = r.status_code
        if r.status_code == 200:
            offer_data = r.json()
            result["offer_isSuccess"] = offer_data.get("isSuccess")
            if offer_data.get("isSuccess") and offer_data.get("data"):
                info = offer_data["data"].get("offerInfo", {})
                infra_type = info.get("infrastructureType", 0)
                result["tip"] = INFRA_MAP.get(infra_type, f"Tip-{infra_type}")
                result["hiz"] = str(info.get("downloadSpeed", 0))
                result["upload"] = str(info.get("uploadSpeed", 0))
                result["price"] = info.get("finalPrice")
                result["kampanya"] = info.get("campaignDescription", "")
                log.info(f"  [Turknet] ✓ Sonuç: {result['tip']} {result['hiz']} Mbps")
            else:
                result["offer_message"] = offer_data.get("message", "")
                log.warning(f"  [Turknet] Offer boş: {offer_data.get('message')}")
        else:
            log.warning(f"  [Turknet] Offer HTTP {r.status_code}")
    except Exception as e:
        log.warning(f"  [Turknet] Offer hata: {e}")
    

    return result



# ═══════════════════════════════════════════════════════════════════════════
#  D-SMART
# ═══════════════════════════════════════════════════════════════════════════
DSMART_URL = "https://www.dsmart.com.tr/api/v1/public/search/internet"
DSMART_HDR = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr,en;q=0.9",
    "Referer": "https://www.dsmart.com.tr/internet-altyapi-sorgulama",
    "Origin": "https://www.dsmart.com.tr",
    "User-Agent": CHROME_UA,
}

def _dfind(items, target):
    if not items or not target:
        return None
    nt = _dn(target)

    for item in items:
        cand = _dn(item.get("text", "") or item.get("ad", ""))
        if cand == nt:
            return item

    for item in items:
        cand = _dn(item.get("text", "") or item.get("ad", ""))
        if nt and (nt in cand or cand in nt):
            return item

    tw = set(nt.split())
    best, bs = None, 0
    for item in items:
        iw = set(_dn(item.get("text", "") or item.get("ad", "")).split())
        s = len(tw & iw) / max(len(tw), len(iw)) if tw and iw else 0
        if s > bs and s >= 0.5:
            best, bs = item, s
    return best

def _dfind_mahalle(items, target):
    if not items or not target:
        return None
    nt = clean_mahalle_name(target)

    for item in items:
        cand = clean_mahalle_name(item.get("text", "") or item.get("ad", ""))
        if cand == nt:
            return item

    for item in items:
        cand = clean_mahalle_name(item.get("text", "") or item.get("ad", ""))
        if nt and (nt in cand or cand in nt):
            return item

    return None

def _dget(session, type_name, value):
    try:
        r = session.get(DSMART_URL, params={"type": type_name, "value": value}, timeout=HTTP_TIMEOUT_MEDIUM)
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception as e:
        log.error(f"    [D-Smart] GET {type_name} hata: {e}")
    return None

def _dsmart_find_building(binalar: List[Dict], bina_no: str) -> Optional[Dict]:
    if not binalar or not bina_no:
        return None

    nb = _normalize_building_no(bina_no)

    for b in binalar:
        txt = _normalize_building_no(str(b.get("text", "")))
        if txt == nb or txt.startswith(nb + " "):
            return b

    for b in binalar:
        raw = _normalize_building_no(str(b.get("text", "")))
        nums = re.findall(r'[A-Z0-9/]+', raw)
        if nums and nums[0] == nb:
            return b

    return None

def query_dsmart(bbk: str, addr: Dict) -> Dict:
    session = requests.Session()
    session.headers.update(DSMART_HDR)
    src = {"_source_": "D-Smart/Superonline", "_bbk_": bbk, "_addr_": addr}

    il = addr.get("IL", "")
    ilce = addr.get("ILCE", "")
    mah = addr.get("MAHALLE", "")
    sok = addr.get("SOKAK", "")
    bina_no = addr.get("BINA", "")

    try:
        log.info("    [D-Smart] İl sorgusu...")
        iller = _dget(session, "Il", 0)
        if not iller:
            return {**src, "_error_": "İl listesi alınamadı"}

        il_item = _dfind(iller, il)
        if not il_item:
            return {**src, "_error_": f"İl bulunamadı: {il}"}
        il_kod = il_item.get("kod") or il_item.get("value")
        log.info(f"    [D-Smart] İl: {il_item.get('text')} (kod={il_kod})")
        _sleep(0.5)

        ilceler = _dget(session, "Ilce", il_kod)
        if not ilceler:
            return {**src, "_error_": "İlçe listesi alınamadı"}
        ilce_item = _dfind(ilceler, ilce)
        if not ilce_item:
            return {**src, "_error_": f"İlçe bulunamadı: {ilce}"}
        ilce_kod = ilce_item.get("kod") or ilce_item.get("value")
        log.info(f"    [D-Smart] İlçe: {ilce_item.get('text')} (kod={ilce_kod})")
        _sleep(0.5)

        bucaklar = _dget(session, "Bucak", ilce_kod)
        if not bucaklar:
            return {**src, "_error_": "Bucak alınamadı"}
        bucak_kod = bucaklar[0].get("kod") or bucaklar[0].get("value")
        _sleep(0.4)

        koyler = _dget(session, "Koy", bucak_kod)
        if not koyler:
            return {**src, "_error_": "Köy alınamadı"}
        koy_kod = koyler[0].get("kod") or koyler[0].get("value")
        _sleep(0.4)

        mahalleler = _dget(session, "Mahalle", koy_kod)
        if not mahalleler:
            return {**src, "_error_": "Mahalle listesi alınamadı"}

        mah_item = _dfind_mahalle(mahalleler, mah) or _dfind(mahalleler, mah)
        if not mah_item:
            sample = [str(x.get("text", "")) for x in mahalleler[:10]]
            return {**src, "_error_": f"Mahalle bulunamadı: {mah}", "_sample_mahalleler_": sample}
        mah_kod = mah_item.get("kod") or mah_item.get("value")
        log.info(f"    [D-Smart] Mahalle: {mah_item.get('text')} (kod={mah_kod})")
        _sleep(0.5)

        sokaklar = _dget(session, "CaddeSokak", mah_kod)
        if not sokaklar:
            return {**src, "_error_": "Sokak listesi alınamadı"}
        sok_item = _dfind(sokaklar, sok)
        if not sok_item:
            return {**src, "_error_": f"Sokak bulunamadı: {sok}"}
        sok_kod = sok_item.get("kod") or sok_item.get("value")
        log.info(f"    [D-Smart] Sokak: {sok_item.get('text')} (kod={sok_kod})")
        _sleep(0.5)

        binalar = _dget(session, "Bina", sok_kod)
        if not binalar:
            return {**src, "_error_": "Bina listesi alınamadı"}

        bina_item = _dsmart_find_building(binalar, bina_no)
        if not bina_item:
            sample = [str(x.get("text", "")) for x in binalar[:5]]
            return {**src, "_error_": f"Bina eşleşmedi: {bina_no}", "_sample_buildings_": sample}

        bina_kod = bina_item.get("kod") or bina_item.get("value")
        log.info(f"    [D-Smart] Bina: {bina_item.get('text')} (kod={bina_kod})")
        _sleep(0.5)

        daireler = _dget(session, "Daire", bina_kod)
        if not daireler:
            return {**src, "_error_": "Daire listesi alınamadı"}

        daire_item = None
        for d in daireler:
            raw = str(d.get("value", ""))
            cand = raw.split("||")[0] if "||" in raw else raw
            if cand == str(bbk):
                daire_item = d
                break

        if not daire_item:
            return {
                **src,
                "_error_": f"Daire/BBK eşleşmedi: istenen={bbk}",
                "_sample_flats_": [str(x.get('value', ''))[:60] for x in daireler[:5]],
                "_bina_kod_": bina_kod
            }

        daire_val = str(daire_item.get("value", ""))
        dsmart_bbk = daire_val.split("||")[0] if "||" in daire_val else daire_val
        log.info(f"    [D-Smart] Daire BBK: istenen={bbk} seçilen={dsmart_bbk}")
        _sleep(0.5)

        log.info(f"    [D-Smart] Final POST | BBK={dsmart_bbk} | BCode={bina_kod}")
        resp = session.post(
            DSMART_URL,
            files={"BBK": (None, dsmart_bbk), "BuildingCode": (None, str(bina_kod))},
            timeout=HTTP_TIMEOUT_LONG
        )
        log.info(f"    [D-Smart] POST HTTP {resp.status_code}")
        if resp.status_code != 200:
            return {**src, "_error_": f"POST HTTP {resp.status_code}", "_raw_": resp.text[:300]}
        try:
            return {**src, **resp.json(), "_dsmart_bbk_": dsmart_bbk, "_bina_kod_": bina_kod}
        except Exception:
            return {**src, "_raw_": resp.text[:800], "_dsmart_bbk_": dsmart_bbk, "_bina_kod_": bina_kod}

    except Exception as e:
        log.error(f"  [D-Smart] Hata: {e}")
        return {**src, "_error_": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
#  MILENICOM
# ═══════════════════════════════════════════════════════════════════════════
MILLENI_ALTS = [
    "https://www.milleni.com.tr",
    "https://milleni.com.tr",
]

def query_milenicom(bina_kodu: str, daire_no: str, bbk: str = "") -> Dict:
    src = {"_source_": "Milenicom/Milleni", "_bina_kodu_": bina_kodu, "_daire_no_": daire_no}

    base = None
    for alt in MILLENI_ALTS:
        try:
            r = requests.get(alt, timeout=8, headers={"User-Agent": CHROME_UA}, allow_redirects=True)
            if r.status_code < 500:
                base = alt
                log.info(f"    [Milenicom] Bağlantı OK: {alt}")
                break
        except Exception as e:
            log.warning(f"    [Milenicom] {alt}: {e}")

    if not base:
        return {**src, "_error_": "Tüm Milenicom URL'leri ulaşılamaz"}

    session = requests.Session()
    session.headers.update({"User-Agent": CHROME_UA})

    try:
        token = None
        token_url = None
        for path in ["/internet-altyapi-sorgulama", "/altyapi-sorgulama"]:
            try:
                r = session.get(f"{base}{path}", timeout=HTTP_TIMEOUT_MEDIUM, headers={"Accept": "text/html,*/*"})
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    inp = soup.find("input", {"name": "__RequestVerificationToken"})
                    if inp:
                        token = inp.get("value", "")
                    token_url = f"{base}{path}"
                    break
            except Exception:
                continue

        log.info(f"    [Milenicom] Token: {'alındı' if token else 'YOK'} | URL={token_url}")
        _sleep(0.8)

        hdrs = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": token_url or f"{base}/internet-altyapi-sorgulama",
        }
        data2 = {"buildingId": bina_kodu}
        if token:
            data2["__RequestVerificationToken"] = token

        apts = None
        for ep in ["/GetIndependentParts", "/api/GetIndependentParts"]:
            try:
                r = session.post(f"{base}{ep}", data=data2, headers=hdrs, timeout=HTTP_TIMEOUT_MEDIUM)
                if r.status_code == 200:
                    apts = r.json()
                    log.info(f"    [Milenicom] {len(apts) if apts else 0} daire | endpoint={ep}")
                    break
                log.warning(f"    [Milenicom] {ep} HTTP {r.status_code}")
            except Exception as e:
                log.warning(f"    [Milenicom] {ep}: {e}")

        if not apts:
            return {**src, "_error_": "Daire listesi alınamadı"}

        log.info(f"    [Milenicom] İlk 5 daire: {[{'N': a.get('Name'), 'Id': (a.get('IdString') or '')[:15]} for a in apts[:5]]}")

        bbk_apt = None
        matched = None
        for apt in apts:
            name = _norm_spaces(str(apt.get("Name", "")))
            if name in {str(daire_no), f"D: {daire_no}", f"D:{daire_no}", f"DAİRE: {daire_no}", f"DAIRE: {daire_no}"}:
                bbk_apt = apt.get("IdString")
                matched = apt
                log.info(f"    [Milenicom] Daire eşleşti: Name='{name}'")
                break

        if not bbk_apt and str(daire_no).isdigit():
            for apt in apts:
                nums = re.findall(r'\d+', str(apt.get("Name", "")))
                if nums and int(nums[-1]) == int(daire_no):
                    bbk_apt = apt.get("IdString")
                    matched = apt
                    log.info(f"    [Milenicom] Sayısal eşleşme: Name='{apt.get('Name')}'")
                    break

        if not bbk_apt:
            return {
                **src,
                "_error_": f"Daire eşleşmedi: {daire_no}",
                "_sample_flats_": [str(a.get("Name", "")) for a in apts[:10]],
                "_daire_sayisi_": len(apts)
            }

        _sleep(0.8)

        rtoken = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(172))
        data3 = {"buildingId": bina_kodu, "bbk": bbk_apt, "token": rtoken}
        if token:
            data3["__RequestVerificationToken"] = token

        resp3 = None
        for ep in [token_url, f"{base}/internet-altyapi-sorgulama"]:
            if not ep:
                continue
            try:
                r = session.post(ep, data=data3, headers=hdrs, timeout=HTTP_TIMEOUT_LONG)
                if r.status_code == 200:
                    resp3 = r
                    break
                log.warning(f"    [Milenicom] Final {ep} HTTP {r.status_code}")
            except Exception as e:
                log.warning(f"    [Milenicom] Final {ep}: {e}")

        log.info(f"    [Milenicom] Final HTTP {resp3.status_code if resp3 else 'N/A'}")
        if not resp3:
            return {**src, "_error_": "Final POST başarısız"}

        try:
            final = resp3.json()
            return {**src, **final, "_bbk_secilen_": bbk_apt, "_matched_apt_": matched, "_daire_sayisi_": len(apts)}
        except Exception:
            return {**src, "_raw_response_": resp3.text[:1500], "_bbk_secilen_": bbk_apt, "_matched_apt_": matched, "_daire_sayisi_": len(apts)}

    except Exception as e:
        log.error(f"  [Milenicom] Hata: {e}")
        return {**src, "_error_": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
#  TÜRKSAT + TEKNOFIX
# ═══════════════════════════════════════════════════════════════════════════
TS_BASE   = "https://www.turksatkablo.net"
TS_PAGE   = f"{TS_BASE}/altyapi-sorgulama"
TS_UPDATE = f"{TS_BASE}/livewire/update"
TS_HDR    = {"User-Agent": CHROME_UA}
TS_LW_HDR = {
    "Content-Type": "application/json",
    "X-Livewire": "true",
    "Origin": TS_BASE,
    "Referer": TS_PAGE,
}

def _ts_normalize(t: str) -> str:
    t = (t or "").upper().strip()
    for s, d in [("İ","I"),("İ","I"),("Ğ","G"),("Ü","U"),("Ş","S"),("Ö","O"),("Ç","C")]:
        t = t.replace(s, d)
    for suffix in [
        " MAH.(MERKEZ)", " MAH.", " MAH", " MAHALLESI", " MAHALLESİ",
        " CAD.", " CAD", " CADDESI", " CADDESİ", " CADDE",
        " SOK.", " SOK", " SOKAK", " SOKAGI", " SOKAĞI",
        " SK.", " SK", "(MERKEZ)", " BULVARI", " BULV.", " BULVAR",
        " KUME EVLERI", " KÜME EVLERİ", " CSBM", " YOLU"
    ]:
        t = t.replace(suffix, "")
    t = re.sub(r'[^A-Z0-9 ]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def _ts_collect(structure, key_check):
    results = []
    if isinstance(structure, dict):
        if key_check(structure):
            results.append(structure)
    elif isinstance(structure, list):
        for item in structure:
            results.extend(_ts_collect(item, key_check))
    return results

def _ts_find(data_list, search_text: str) -> Optional[Dict]:
    if not data_list or not search_text:
        return None
    items = _ts_collect(data_list, lambda x: 'ad' in x and ('kod' in x or 't_id' in x))
    sn = _ts_normalize(search_text)

    for c in items:
        if _ts_normalize(c.get('ad', '')) == sn:
            return c
    for c in items:
        cn = _ts_normalize(c.get('ad', ''))
        if sn and (sn in cn or cn in sn):
            return c
    return None

def _ts_find_building(data_list, bina_no: str) -> Optional[Dict]:
    if not data_list:
        return None
    items = _ts_collect(data_list, lambda x: 'diskapino' in x or 'bina_adi' in x)
    num = _norm_spaces(bina_no)

    for c in items:
        if _norm_spaces(c.get('diskapino', '')) == num:
            return c

    matches = [
        c for c in items
        if _norm_spaces(c.get('diskapino', '')).startswith(num + ' ')
        or _norm_spaces(c.get('diskapino', '')) == num
    ]
    if matches:
        good = [m for m in matches if m.get('hizmet_var') and m.get('sebeke')]
        return good[0] if good else matches[0]

    for c in items:
        if num and num in _norm_spaces(c.get('bina_adi', '')):
            return c

    return None

def _ts_get_initial(session: requests.Session) -> Optional[Dict]:
    try:
        resp = session.get(TS_PAGE, headers=TS_HDR, timeout=15, verify=False)
        if resp.status_code != 200:
            log.warning(f"    [Türksat] Sayfa HTTP {resp.status_code}")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        inp = soup.find("input", {"name": "_token"})
        if not inp:
            log.warning("    [Türksat] _token input bulunamadı")
            return None
        token = inp.get("value", "")

        for div in soup.find_all("div", {"wire:snapshot": True}):
            try:
                raw = html_module.unescape(div.get("wire:snapshot", ""))
                snap = json.loads(raw)
                if snap.get("memo", {}).get("name") == "infrastructure-query":
                    comp_id = div.get("wire:id", "")
                    log.info(f"    [Türksat] Livewire component bulundu: {comp_id}")
                    return {"token": token, "snapshot": snap, "component_id": comp_id}
            except Exception:
                continue

        log.warning("    [Türksat] infrastructure-query component bulunamadı")
        return None
    except Exception as e:
        log.error(f"    [Türksat] Initial state hatası: {e}")
        return None

def _ts_update(session, token: str, snapshot: Dict, updates: Dict) -> Optional[Dict]:
    headers = {**TS_HDR, **TS_LW_HDR, "X-Csrf-Token": token}
    payload = {
        "_token": token,
        "components": [{"snapshot": json.dumps(snapshot), "updates": updates, "calls": []}]
    }
    try:
        resp = session.post(TS_UPDATE, json=payload, headers=headers, timeout=15, verify=False)
        if resp.status_code != 200:
            log.warning(f"    [Türksat] update HTTP {resp.status_code}")
            return None
        comp = resp.json()["components"][0]
        return json.loads(comp["snapshot"])
    except Exception as e:
        log.error(f"    [Türksat] update hatası: {e}")
        return None

def _ts_call(session, token: str, snapshot: Dict, method: str) -> Optional[Dict]:
    headers = {**TS_HDR, **TS_LW_HDR, "X-Csrf-Token": token}
    payload = {
        "_token": token,
        "components": [{"snapshot": json.dumps(snapshot), "updates": {}, "calls": [{"path": "", "method": method, "params": []}]}]
    }
    try:
        resp = session.post(TS_UPDATE, json=payload, headers=headers, timeout=20, verify=False)
        if resp.status_code != 200:
            log.warning(f"    [Türksat] call '{method}' HTTP {resp.status_code}")
            return None
        comp = resp.json()["components"][0]
        return json.loads(comp["snapshot"])
    except Exception as e:
        log.error(f"    [Türksat] call '{method}' hatası: {e}")
        return None

def query_teknofix(bina_id: str, daire_id: str = None) -> Dict:
    url = "https://api.teknofix.com.tr/api/turksat/infrastructure-query/check-service-address"
    payload = {"building_id": int(bina_id)}
    if daire_id:
        try:
            payload["apartment_number"] = int(daire_id)
        except Exception:
            pass
    try:
        resp = requests.post(url, json=payload, headers={
            "Accept": "*/*",
            "Accept-Language": "tr,en;q=0.9",
            "Origin": "https://teknofix.com.tr",
            "Referer": "https://teknofix.com.tr/",
            "Content-Type": "application/json",
            "User-Agent": CHROME_UA,
        }, timeout=10)
        log.info(f"    [Teknofix] HTTP {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            data["_source_"] = "Teknofix"
            return data
        return {"_error_": f"HTTP {resp.status_code}", "_source_": "Teknofix"}
    except Exception as e:
        return {"_error_": str(e), "_source_": "Teknofix"}

def query_turksat(addr: Dict) -> Dict:
    src = {"_source_": "Türksat Kablonet", "_addr_": addr}
    session = requests.Session()

    try:
        log.info("    [Türksat] Sayfa yükleniyor...")
        state = _ts_get_initial(session)
        if not state:
            return {**src, "_error_": "Sayfa yüklenemedi (turksatkablo.net)"}

        token = state["token"]
        snap  = state["snapshot"]
        data  = snap.get("data", {})

        il_name   = addr.get("IL", "")
        ilce_name = addr.get("ILCE", "")
        mah_name  = addr.get("MAHALLE", "")
        sok_name  = addr.get("SOKAK", "")
        bina_no   = addr.get("BINA", "")
        daire_no  = addr.get("DAIRE", "")

        il_item = _ts_find(data.get("provinceData"), il_name)
        if not il_item:
            return {**src, "_error_": f"İl bulunamadı: {il_name}"}
        il_kod = il_item["kod"]
        log.info(f"    [Türksat] İl: {il_item['ad']} (kod={il_kod})")
        _sleep(0.4)

        snap = _ts_update(session, token, snap, {"districtQuery": str(il_kod)})
        if not snap:
            return {**src, "_error_": "İlçe güncellemesi başarısız"}
        _sleep(0.3)

        ilce_item = _ts_find(snap["data"].get("districtData"), ilce_name)
        if not ilce_item:
            return {**src, "_error_": f"İlçe bulunamadı: {ilce_name}"}
        ilce_id = ilce_item.get("t_id") or ilce_item.get("kod")
        log.info(f"    [Türksat] İlçe: {ilce_item['ad']} (t_id={ilce_id})")
        _sleep(0.3)

        snap = _ts_update(session, token, snap, {"districtQuery": str(il_kod), "neighborhoodQuery": str(ilce_id)})
        if not snap:
            return {**src, "_error_": "Mahalle güncellemesi başarısız"}
        _sleep(0.3)

        mah_item = _ts_find(snap["data"].get("neighborhoodData"), mah_name)
        if not mah_item:
            return {**src, "_error_": f"Mahalle bulunamadı: {mah_name}"}
        mah_id = mah_item.get("t_id") or mah_item.get("kod")
        log.info(f"    [Türksat] Mahalle: {mah_item['ad']} (t_id={mah_id})")
        _sleep(0.3)

        snap = _ts_update(session, token, snap, {
            "districtQuery": str(il_kod),
            "neighborhoodQuery": str(ilce_id),
            "streetQuery": str(mah_id)
        })
        if not snap:
            return {**src, "_error_": "Sokak güncellemesi başarısız"}
        _sleep(0.3)

        sok_item = _ts_find(snap["data"].get("streetData"), sok_name)
        if not sok_item:
            return {**src, "_error_": f"Sokak bulunamadı: {sok_name}"}
        sok_id = sok_item.get("t_id") or sok_item.get("kod")
        log.info(f"    [Türksat] Sokak: {sok_item['ad']} (t_id={sok_id})")
        _sleep(0.3)

        snap = _ts_update(session, token, snap, {
            "districtQuery": str(il_kod),
            "neighborhoodQuery": str(ilce_id),
            "streetQuery": str(mah_id),
            "buildingQuery": str(sok_id)
        })
        if not snap:
            return {**src, "_error_": "Bina güncellemesi başarısız"}
        _sleep(0.3)

        bina_item = _ts_find_building(snap["data"].get("buildingData"), bina_no)
        if not bina_item:
            sample = [
                {"diskapino": x.get("diskapino"), "bina_adi": x.get("bina_adi"), "hizmet_var": x.get("hizmet_var"), "sebeke": x.get("sebeke")}
                for x in _ts_collect(snap["data"].get("buildingData"), lambda y: 'diskapino' in y or 'bina_adi' in y)[:5]
            ]
            return {**src, "_error_": f"Bina bulunamadı: {bina_no}", "_sample_buildings_": sample}

        bina_t_id = bina_item.get("t_id")
        bina_kod  = bina_item.get("kod")
        log.info(f"    [Türksat] Bina: {bina_item.get('diskapino')} - {bina_item.get('bina_adi')} (t_id={bina_t_id}, hizmet={bina_item.get('hizmet_var')}, sebeke={bina_item.get('sebeke')})")

        apt_val = f"{bina_t_id}|{bina_kod}"
        snap = _ts_update(session, token, snap, {
            "districtQuery": str(il_kod),
            "neighborhoodQuery": str(ilce_id),
            "streetQuery": str(mah_id),
            "buildingQuery": str(sok_id),
            "apartmentQuery": apt_val
        })
        if not snap:
            return {**src, "_error_": "Daire güncellemesi başarısız"}
        _sleep(0.3)

        daire_item = None
        daire_t_id = None
        if daire_no:
            apt_data = snap["data"].get("apartmentData")
            daire_item = _ts_find(apt_data, str(daire_no)) if apt_data else None
            if daire_item:
                daire_t_id = daire_item.get("t_id")
                snap = _ts_update(session, token, snap, {
                    "districtQuery": str(il_kod),
                    "neighborhoodQuery": str(ilce_id),
                    "streetQuery": str(mah_id),
                    "buildingQuery": str(sok_id),
                    "apartmentQuery": apt_val,
                    "apartmentNumber": str(daire_t_id)
                })
                log.info(f"    [Türksat] Daire: {daire_item.get('ad')} (t_id={daire_t_id})")
        _sleep(0.3)

        log.info("    [Türksat] checkService() çağrılıyor...")
        final_snap = _ts_call(session, token, snap, "checkService")

        sebeke_turu_map = {1: 'HFC/Kablo', 2: 'DSL', 3: 'FTTB', 4: 'FTTH', 5: 'Fiber (FTTH)'}
        st = bina_item.get("sebeke_turu")
        result = {
            **src,
            "_bina_item_": bina_item,
            "_daire_item_": daire_item,
            "_bina_t_id_": bina_t_id,
            "_daire_t_id_": daire_t_id,
            "hizmet_var": bina_item.get("hizmet_var", False),
            "sebeke": bina_item.get("sebeke", False),
            "sebeke_turu": st,
            "sebeke_turu_text": sebeke_turu_map.get(st, str(st) if st else ""),
            "devre_no": bina_item.get("devre_no"),
            "cmts_adi": bina_item.get("cmts_adi"),
        }

        if final_snap:
            result["_final_snapshot_data_"] = final_snap.get("data", {})
            result["status"] = "Var" if (bina_item.get("hizmet_var") or bina_item.get("sebeke")) else "Yok"

        if bina_t_id:
            log.info("    [Teknofix] İkincil doğrulama...")
            tf = query_teknofix(str(bina_t_id), str(daire_t_id) if daire_t_id else None)
            result["_teknofix_"] = tf

        return result

    except Exception as e:
        log.error(f"  [Türksat] Hata: {e}")
        return {**src, "_error_": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
#  PARSERS — LOSSLESS / NO GUESS
# ═══════════════════════════════════════════════════════════════════════════
def parse_dsmart_result(data: Dict) -> Dict:
    out = {
        "provider": "dsmart",
        "query_success": False,
        "match_success": False,
        "service_available": None,
        "technology": "",
        "max_download_mbps": None,
        "max_upload_mbps": None,
        "port_status": "",
        "bbk": data.get("_dsmart_bbk_", ""),
        "building_code": data.get("_bina_kod_", ""),
        "message": "",
        "error": "",
        "tt_info": {},
        "sol_info": {},
        "raw_keys": list(data.keys()) if isinstance(data, dict) else [],
        "raw_excerpt": compact_text(data),
    }

    if not isinstance(data, dict):
        out["error"] = "Geçersiz response tipi"
        return out

    if data.get("_error_") or data.get("error"):
        out["error"] = data.get("_error_") or data.get("error")
        return out

    out["query_success"] = True
    out["match_success"] = bool(data.get("_dsmart_bbk_") and data.get("_bina_kod_"))

    # D-Smart meta.message
    meta = data.get("meta", {})
    out["message"] = str(meta.get("message", "")) if isinstance(meta, dict) else ""

    # D-Smart data: list of {maxSpeed, tech, portAvailable, description, provider}
    items = data.get("data", [])
    if isinstance(items, list) and items:
        out["service_available"] = True
        techs = []
        max_dl = 0

        for item in items:
            if not isinstance(item, dict):
                continue
            provider = str(item.get("provider", "")).upper()
            tech = item.get("tech", "")
            max_speed_raw = item.get("maxSpeed", "0")
            port_avail = item.get("portAvailable", False)

            # Parse speed: "1000 Mbps" -> 1000
            speed_num = 0
            if isinstance(max_speed_raw, (int, float)):
                speed_num = int(max_speed_raw)
            elif isinstance(max_speed_raw, str):
                m = re.search(r'(\d+)', max_speed_raw)
                if m:
                    speed_num = int(m.group(1))

            if provider == "TT":
                out["tt_info"] = {"tech": tech, "speed": speed_num, "port": port_avail}
            elif provider == "SOL":
                out["sol_info"] = {"tech": tech, "speed": speed_num, "port": port_avail}

            if tech:
                techs.append(tech)
            if speed_num > max_dl:
                max_dl = speed_num
            if port_avail:
                out["port_status"] = "VAR"

        if techs:
            out["technology"] = "/".join(dict.fromkeys(techs))  # deduplicate
        if max_dl > 0:
            out["max_download_mbps"] = max_dl
    elif isinstance(items, list) and not items:
        out["service_available"] = False

    return out

def parse_milenicom_result(data: Dict) -> Dict:
    out = {
        "provider": "milenicom",
        "query_success": False,
        "match_success": False,
        "service_available": None,
        "technology": "",
        "max_download_mbps": None,
        "max_upload_mbps": None,
        "max_download_sol_mbps": None,
        "port_status": "",
        "bbk": data.get("_bbk_secilen_", ""),
        "building_code": data.get("_bina_kodu_", ""),
        "matched_apartment": "",
        "apartment_count": data.get("_daire_sayisi_", None),
        "has_tt_fiber": None,
        "sol_available": None,
        "tt_available": None,
        "tt_service_types": "",
        "inf_key": "",
        "message": "",
        "error": "",
        "raw_keys": list(data.keys()) if isinstance(data, dict) else [],
        "raw_excerpt": compact_text(data),
    }

    if not isinstance(data, dict):
        out["error"] = "Geçersiz response tipi"
        return out

    if data.get("_error_") or data.get("error"):
        out["error"] = data.get("_error_") or data.get("error")
        return out

    out["query_success"] = True

    matched = data.get("_matched_apt_", {})
    if isinstance(matched, dict):
        out["matched_apartment"] = matched.get("Name", "")
        out["match_success"] = bool(out["matched_apartment"])

    out["message"] = str(data.get("message", "") or "")

    # Milenicom doğrudan alan haritalama
    out["service_available"] = data.get("hasInfrastructure")
    out["has_tt_fiber"] = data.get("hasTTFiber")
    out["sol_available"] = data.get("solAvailable")
    out["tt_available"] = data.get("ttAvailable")
    out["tt_service_types"] = str(data.get("ttServiceTypes", ""))
    out["inf_key"] = str(data.get("infKey", ""))

    # maxSpeed = TT max hız, maxSpeedSol = Superonline max hız
    ms = data.get("maxSpeed")
    if isinstance(ms, (int, float)) and ms > 0:
        out["max_download_mbps"] = int(ms)
    ms_sol = data.get("maxSpeedSol")
    if isinstance(ms_sol, (int, float)) and ms_sol > 0:
        out["max_download_sol_mbps"] = int(ms_sol)

    # Teknoloji belirleme: ttServiceTypes ve infKey'den
    svc = out["tt_service_types"].upper()
    if "FIBER" in svc or out["has_tt_fiber"]:
        out["technology"] = "Fiber"
    elif "V1" in svc or "V2" in svc:
        out["technology"] = "VDSL"
    elif "A1" in svc or "A2" in svc:
        out["technology"] = "ADSL"
    elif out["inf_key"] == "tt":
        out["technology"] = "TT"
    elif out["inf_key"] == "sol":
        out["technology"] = "SOL"

    # googleEvent içinden ek bilgi
    ge = data.get("googleEvent", {})
    if isinstance(ge, dict):
        label = ge.get("eventLabel", "")
        if label and not out["technology"]:
            out["technology"] = label

    return out

def parse_turknet_result(data: Dict) -> Dict:
    out = {
        "provider": "turknet",
        "query_success": False,
        "match_success": False,
        "service_available": None,
        "technology": "",
        "max_download_mbps": None,
        "max_upload_mbps": None,
        "port_status": "",
        "bbk": "",
        "kampanya": "",
        "price": None,
        "message": "",
        "error": "",
        "raw_keys": list(data.keys()) if isinstance(data, dict) else [],
        "raw_excerpt": compact_text(data),
    }

    if not isinstance(data, dict):
        out["error"] = "Geçersiz response tipi"
        return out

    if data.get("_error_") or data.get("error"):
        out["error"] = data.get("_error_") or data.get("error")
        return out

    out["query_success"] = True
    
    # Turknet offer data processing
    if "tip" in data:
        out["match_success"] = True
        out["technology"] = str(data.get("tip", ""))
        try:
            out["max_download_mbps"] = int(float(data.get("hiz", 0)))
        except (ValueError, TypeError):
            pass
            
        try:
            out["max_upload_mbps"] = int(float(data.get("upload", 0)))
        except (ValueError, TypeError):
            pass
            
        out["price"] = data.get("price")
        out["kampanya"] = data.get("kampanya", "")
        
        # If there's speed, service is available
        out["service_available"] = out["max_download_mbps"] is not None and out["max_download_mbps"] > 0

    return out

def parse_turksat_result(data: Dict) -> Dict:
    out = {
        "provider": "turksat_livewire",
        "query_success": False,
        "match_success": False,
        "service_available": None,
        "technology": "",
        "max_download_mbps": None,
        "max_upload_mbps": None,
        "port_status": "",
        "bbk": "",
        "building_code": data.get("_bina_t_id_", ""),
        "devre_no": "",
        "cmts_adi": "",
        "sebeke_raw": None,
        "message": "",
        "error": "",
        "raw_keys": list(data.keys()) if isinstance(data, dict) else [],
        "raw_excerpt": compact_text(data),
    }

    if not isinstance(data, dict):
        out["error"] = "Geçersiz response tipi"
        return out

    if data.get("_error_"):
        out["error"] = data["_error_"]
        return out

    out["query_success"] = True
    out["match_success"] = bool(data.get("_bina_t_id_"))

    # Doğrudan alan haritalama
    hizmet = data.get("hizmet_var")
    sebeke = data.get("sebeke")
    out["service_available"] = bool(hizmet or sebeke)
    out["sebeke_raw"] = sebeke
    out["devre_no"] = str(data.get("devre_no", "") or "")
    out["cmts_adi"] = str(data.get("cmts_adi", "") or "")

    if data.get("sebeke_turu_text"):
        out["technology"] = str(data["sebeke_turu_text"])
    elif data.get("sebeke_turu"):
        sebeke_turu_map = {1: 'HFC/Kablo', 2: 'DSL', 3: 'FTTB', 4: 'FTTH', 5: 'Fiber (FTTH)'}
        out["technology"] = sebeke_turu_map.get(data["sebeke_turu"], str(data["sebeke_turu"]))

    out["message"] = str(data.get("status", "") or "")

    # Final snapshot'tan ek veri
    fsd = data.get("_final_snapshot_data_", {})
    if isinstance(fsd, dict):
        # checkService sonucu — result_message olabilir
        rm = fsd.get("resultMessage") or fsd.get("result_message") or fsd.get("message")
        if rm and isinstance(rm, str):
            out["message"] = rm

    return out

def parse_teknofix_result(data: Dict) -> Dict:
    out = {
        "provider": "teknofix_secondary",
        "query_success": False,
        "match_success": False,
        "service_available": None,
        "technology": "",
        "max_download_mbps": None,
        "max_upload_mbps": None,
        "port_status": "",
        "bbk": "",
        "building_code": "",
        "message": "",
        "error": "",
        "raw_keys": list(data.keys()) if isinstance(data, dict) else [],
        "raw_excerpt": compact_text(data),
    }

    if not isinstance(data, dict):
        out["error"] = "Geçersiz response tipi"
        return out

    if data.get("_error_"):
        out["error"] = data["_error_"]
        return out

    out["query_success"] = True
    out["match_success"] = data.get("status") == "success"

    # Teknofix doğrudan alanlar
    msg = str(data.get("message", "") or "")
    out["message"] = msg

    # message içinden hizmet varlığı ve teknoloji çıkar
    msg_lower = msg.lower()
    if "sunulmaktadır" in msg_lower or "hizmeti" in msg_lower:
        out["service_available"] = True
    elif "sunulmamaktadır" in msg_lower or "bulunmamaktadır" in msg_lower:
        out["service_available"] = False

    # Teknoloji belirleme — message içinden
    if "fiber" in msg_lower:
        out["technology"] = "Fiber"
    elif "hfc" in msg_lower or "kablo" in msg_lower or "kablonet" in msg_lower:
        out["technology"] = "HFC/Kablo"
    elif "dsl" in msg_lower:
        out["technology"] = "DSL"

    # Hız bilgisi — "100 Mbps" gibi
    speed_match = re.search(r'(\d+)\s*Mbps', msg)
    if speed_match:
        out["max_download_mbps"] = int(speed_match.group(1))

    # data alanı varsa (nadir — genelde null)
    extra = data.get("data")
    if isinstance(extra, dict):
        if extra.get("technology"):
            out["technology"] = str(extra["technology"])
        if extra.get("maxSpeed"):
            try:
                out["max_download_mbps"] = int(extra["maxSpeed"])
            except (ValueError, TypeError):
                pass

    return out

# ═══════════════════════════════════════════════════════════════════════════
#  FINAL DECISION
# ═══════════════════════════════════════════════════════════════════════════
def build_final_decision(report: Dict) -> Dict:
    addr = report.get("address_resolved", {})
    parsed = report.get("downstream_parsed", {})
    
    confidence = 0
    if addr.get("IL"): confidence += 10
    if addr.get("ILCE"): confidence += 10
    if addr.get("MAHALLE"): confidence += 10
    if addr.get("SOKAK"): confidence += 10
    if addr.get("BINA"): confidence += 10
    if addr.get("DAIRE"): confidence += 10
    if addr.get("BINA_KODU"): confidence += 10

    for name in ["dsmart", "milenicom", "turksat_livewire", "teknofix_secondary"]:
        p = parsed.get(name, {})
        if p.get("query_success"):
            confidence += 5
        if p.get("match_success"):
            confidence += 5

    confidence = min(confidence, 100)

    return {
        "bbk": report.get("bbk"),
        "confidence_score": confidence,
        "best_address_source": report.get("best_source", ""),
        "providers": parsed,
    }

# ═══════════════════════════════════════════════════════════════════════════
#  RUN
# ═══════════════════════════════════════════════════════════════════════════
def run_bbk_test(bbk: str, attempt: int) -> Dict:
    log.info(f"\n{'='*65}")
    log.info(f"  BBK={bbk} | Deneme #{attempt}")
    log.info(f"{'='*65}")

    report = {
        "bbk": bbk,
        "attempt": attempt,
        "ts": datetime.now().isoformat(),
        "bbk_queries": {},
        "address_resolved": {},
        "best_source": "",
        "downstream": {},
        "downstream_parsed": {},
        "final_decision": {}
    }

    log.info(f"\n── PHASE 1: BBK Altyapı Sorguları ─────────────────")
    log.info("[1/6] ISS Araçları...")
    iss = query_iss(bbk)
    report["bbk_queries"]["iss_araclari"] = iss
    _sleep()

    log.info("[2/6] Alaznet Sorgu...")
    alaz = query_alaznet_sorgu(bbk)
    report["bbk_queries"]["alaznet_sorgu"] = alaz
    _sleep()

    log.info("[3/6] Alaznet AdresCek...")
    adres_cek = query_alaznet_adres_cek(bbk)
    report["bbk_queries"]["alaznet_adres_cek"] = adres_cek
    _sleep()

    log.info("[4/6] Vivanet TT...")
    viva = query_vivanet(bbk)
    report["bbk_queries"]["vivanet_tt"] = viva
    _sleep()

    log.info("[5/6] JIO...")
    jio = query_jio(bbk)
    report["bbk_queries"]["jio"] = jio
    _sleep()



    log.info(f"\n── PHASE 2: Kaynak Analizi ─────────────────────────")
    best_name = max(
        report["bbk_queries"],
        key=lambda k: _score(report["bbk_queries"][k]) if "_error_" not in report["bbk_queries"][k] else -1,
        default=""
    )
    report["best_source"] = best_name

    for src_name, data in sorted(report["bbk_queries"].items(), key=lambda x: _score(x[1]), reverse=True):
        flag = "✓" if "_error_" not in data else "✗"
        log.info(f"  {flag} {src_name:<28} {_score(data):>6} byte")

    if "_error_" not in iss:
        rb = iss.get("result", iss)
        log.info(f"\n  [ISS] result.address = '{rb.get('address', '')}'")
        log.info(f"  [ISS] result üst anahtarlar: {list(rb.keys()) if isinstance(rb, dict) else '-'}")
        for tech in ("fiber", "vdsl", "adsl"):
            tb = rb.get(tech, {}) if isinstance(rb, dict) else {}
            inner = tb.get("data", {}) if isinstance(tb, dict) else {}
            if isinstance(inner, dict) and inner:
                log.info(
                    f"  [ISS] {tech}.data önemli: "
                    f"SNTRLMDA={inner.get('SNTRLMDA', '-')} "
                    f"SNTRLAD={inner.get('SNTRLAD', '-')} "
                    f"DSLMXSPD={inner.get('DSLMXSPD', '-')}"
                )

    if "_error_" not in jio:
        jr = jio.get("result", {})
        if isinstance(jr, dict):
            jd = jr.get("data", {})
            log.info(f"\n  [JIO] result.data anahtarları: {list(jd.keys()) if isinstance(jd, dict) else '-'}")

    log.info(f"\n── PHASE 3: Adres Çözümü ───────────────────────────")
    addr = resolve_address(bbk, iss, alaz, adres_cek, jio)
    report["address_resolved"] = addr
    log.info(f"  Adres: {addr}")

    if not addr.get("IL"):
        log.error("  Adres yok! Downstream atlanıyor.")
        report["downstream"]["_error_"] = "Adres çözülemedi"
        report["final_decision"] = build_final_decision(report)
        return report

    bina_kodu = addr.get("BINA_KODU", "")
    daire_no  = addr.get("DAIRE", "1")

    log.info(f"\n── PHASE 4: Downstream Sorgular ────────────────────")

    log.info("[1/3] D-Smart / Superonline...")
    report["downstream"]["dsmart"] = query_dsmart(bbk, addr)
    _sleep(1.2)

    log.info("[2/3] Milenicom (milleni.com.tr)...")
    if bina_kodu:
        report["downstream"]["milenicom"] = query_milenicom(str(bina_kodu), str(daire_no), bbk)
    else:
        report["downstream"]["milenicom"] = {
            "_source_": "Milenicom",
            "_error_": "BinaKodu yok (Alaznet AdresKodu.BinaKodu gerekli)",
        }
        log.warning("  [Milenicom] BinaKodu yok!")
    _sleep(1.2)

    log.info("[3/4] Türksat (turksatkablo.net / Livewire)...")
    report["downstream"]["turksat"] = query_turksat(addr)
    _sleep(1.0)
    
    log.info("[4/4] Turknet...")
    report["downstream"]["turknet"] = query_turknet(bbk, addr)
    _sleep()

    tt_raw = report["downstream"].get("turksat", {})
    teknofix_raw = tt_raw.get("_teknofix_", {}) if isinstance(tt_raw, dict) else {}

    report["downstream_parsed"] = {
        "dsmart": parse_dsmart_result(report["downstream"].get("dsmart", {})),
        "milenicom": parse_milenicom_result(report["downstream"].get("milenicom", {})),
        "turksat_livewire": parse_turksat_result(tt_raw),
        "teknofix_secondary": parse_teknofix_result(teknofix_raw),
        "turknet": parse_turknet_result(report["downstream"].get("turknet", {})),
    }

    report["final_decision"] = build_final_decision(report)
    return report

# ═══════════════════════════════════════════════════════════════════════════
#  REPORTS
# ═══════════════════════════════════════════════════════════════════════════
def print_summary(all_results: List[Dict]):
    print("\n" + "═"*100)
    print("  TAM ÖZET RAPOR")
    print("═"*100)

    for r in all_results:
        addr = r.get("address_resolved", {})
        print(f"\n┌─ BBK={r['bbk']}  Deneme=#{r['attempt']}  {r['ts'][:19]}")
        print(f"│  Adres: {addr.get('IL','-')}/{addr.get('ILCE','-')}/{str(addr.get('MAHALLE','-'))[:24]}  Bina:{addr.get('BINA','-')}  D:{addr.get('DAIRE','-')}  BinaKodu:{addr.get('BINA_KODU','-')}")
        print(f"│  BBK Sorguları:")
        for k, v in r.get("bbk_queries", {}).items():
            err = v.get("_error_", "")
            flag = "✓" if not err else "✗"
            best = " ◄ EN İYİ" if k == r.get("best_source") else ""
            print(f"│    {flag} {k:<28} {_score(v):>6} byte{best}")

        print(f"│  Downstream:")
        for k, v in r.get("downstream", {}).items():
            if k == "_error_":
                print(f"│    ✗ {v}")
                continue
            err = v.get("_error_", "") or v.get("error", "")
            flag = "✓" if not err else "✗"
            extra = ""
            if err:
                extra = f"  → {str(err)[:70]}"
            elif k == "dsmart":
                extra = f"  → bbk={v.get('_dsmart_bbk_', '-')} binaKod={v.get('_bina_kod_', '-')}"
            elif k == "milenicom":
                extra = f"  → daireSayisi={v.get('_daire_sayisi_', '-')} secilen={str(v.get('_matched_apt_', {}))[:35]}"
            elif k == "turksat":
                extra = f"  → hizmet={v.get('hizmet_var', '-')} sebeke={v.get('sebeke', '-')} tip={v.get('sebeke_turu_text', '-')}"
            print(f"│    {flag} {k:<28}{_score(v):>6} byte{extra}")
        print(f"└{'─'*95}")

def _provider_cell(p: Dict) -> str:
    if not p:
        return "-"
    if p.get("error"):
        return f"HATA:{str(p['error'])[:14]}"

    parts = []
    if p.get("query_success") is not None:
        parts.append("Q=1" if p.get("query_success") else "Q=0")
    if p.get("match_success") is not None:
        parts.append("M=1" if p.get("match_success") else "M=0")

    if p.get("service_available") is True:
        parts.append("S=VAR")
    elif p.get("service_available") is False:
        parts.append("S=YOK")

    if p.get("technology"):
        parts.append(f"T={p['technology']}")

    return " | ".join(parts) if parts else "RAW"

def print_final_matrix(all_results: List[Dict]):
    print("\n" + "═"*180)
    print("  NİHAİ SERVİS MATRİSİ")
    print("═"*180)
    print(f"{'BBK':<10} {'İL/İLÇE':<24} {'D-Smart':<28} {'Milenicom':<28} {'TT Livewire':<28} {'Teknofix':<24} {'Turknet':<28} {'Conf':<6}")
    print("-"*180)

    for r in all_results:
        bbk = r["bbk"]
        addr = r.get("address_resolved", {})
        loc = f"{addr.get('IL','-')}/{addr.get('ILCE','-')}"[:24]

        dp = r.get("downstream_parsed", {}).get("dsmart", {})
        mp = r.get("downstream_parsed", {}).get("milenicom", {})
        tp = r.get("downstream_parsed", {}).get("turksat_livewire", {})
        tf = r.get("downstream_parsed", {}).get("teknofix_secondary", {})
        tn = r.get("downstream_parsed", {}).get("turknet", {})
        fd = r.get("final_decision", {})

        print(
            f"{bbk:<10} {loc:<24} {_provider_cell(dp):<28} {_provider_cell(mp):<28} "
            f"{_provider_cell(tp):<28} {_provider_cell(tf):<24} {_provider_cell(tn):<28} {fd.get('confidence_score', 0):<6}"
        )

def print_development_report(all_results: List[Dict]):
    print("\n" + "═"*140)
    print("  BOT GELİŞTİRME RAPORU")
    print("═"*140)

    for r in all_results:
        bbk = r["bbk"]
        addr = r.get("address_resolved", {})
        parsed = r.get("downstream_parsed", {})
        fd = r.get("final_decision", {})

        dsmart = parsed.get("dsmart", {})
        mil = parsed.get("milenicom", {})
        tt = parsed.get("turksat_livewire", {})
        tf = parsed.get("teknofix_secondary", {})
        tn = parsed.get("turknet", {})

        print(f"\n[{bbk}]")
        print(f"  Adres Kaynağı : {r.get('best_source')}")
        print(f"  Adres         : {addr.get('IL','-')} / {addr.get('ILCE','-')} / {addr.get('MAHALLE','-')} / {addr.get('SOKAK','-')} / No:{addr.get('BINA','-')} / D:{addr.get('DAIRE','-')}")
        print(f"  BinaKodu      : {addr.get('BINA_KODU','-')}")
        print(f"  Confidence    : {fd.get('confidence_score', 0)}")

        print("  Sağlayıcı Özeti:")
        print(f"    - D-Smart   : {dsmart.get('technology','-')} ({dsmart.get('max_download_mbps','-')} Mbps) | Match: {dsmart.get('match_success')} | Avail: {dsmart.get('service_available')}")
        print(f"    - Milenicom : {mil.get('technology','-')} ({mil.get('max_download_mbps','-')} Mbps) | Match: {mil.get('match_success')} | Avail: {mil.get('service_available')}")
        print(f"    - TT Kablo  : {tt.get('technology','-')} | Match: {tt.get('match_success')} | Avail: {tt.get('service_available')}")
        print(f"    - Teknofix  : {tf.get('technology','-')} ({tf.get('max_download_mbps','-')} Mbps) | Match: {tf.get('match_success')} | Avail: {tf.get('service_available')}")
        print(f"    - Turknet   : {tn.get('technology','-')} ({tn.get('max_download_mbps','-')} Mbps) | Match: {tn.get('match_success')} | Avail: {tn.get('service_available')}")

        print("  Geliştirme Notu:")
        if dsmart.get("error"):
            print("    * D-Smart zinciri hata veriyor; mahalle/sokak/bina normalizasyonunu geliştir.")
        if mil.get("query_success") and not mil.get("technology") and mil.get("service_available") is not True:
            print("    * Milenicom final payload içinde açık servis/teknoloji alanları ayrıca haritalanmalı.")
        if tt.get("query_success") and not tt.get("technology"):
            print("    * Türksat final snapshot daha ayrıntılı parse edilebilir.")
        if tf.get("query_success") and tf.get("service_available") is None and not tf.get("technology"):
            print("    * Teknofix response alanları daha net haritalanmalı.")
        if dsmart.get("query_success") and mil.get("query_success") and tt.get("query_success"):
            print("    * Bu BBK provider coverage karşılaştırması için iyi bir test kaydı.")

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║      BBK ALTYAPI TAM TEST SİSTEMİ v8 — LOSSLESS FINAL REPORT          ║
║  BBK : {', '.join(BBK_LIST):<52}║
║  Test: {ATTEMPTS}x | Sistemler: ISS/Alaz/Viva/JIO/Turknet/DSmart/Milleni/TT ║
╚══════════════════════════════════════════════════════════════════════════╝
""")

    all_results = []

    for i, bbk in enumerate(BBK_LIST):
        if i > 0:
            log.info(f"\n⏳ BBK değişimi ({BBK_DELAY}s)...")
            time.sleep(BBK_DELAY)

        for attempt in range(1, ATTEMPTS + 1):
            result = run_bbk_test(bbk, attempt)
            all_results.append(result)

            fname = os.path.join(OUTPUT_DIR, f"bbk_{bbk}_attempt{attempt}.json")
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            log.info(f"\n  💾 {fname}")

    full = os.path.join(OUTPUT_DIR, "bbk_full_report.json")
    with open(full, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)

    print_summary(all_results)
    print_final_matrix(all_results)
    print_development_report(all_results)

    print("\n" + "═"*100)
    print("  KAYNAK BÜYÜKLÜK KARŞILAŞTIRMASI")
    print("═"*100)

    scores: Dict[str, List[int]] = {}
    for r in all_results:
        for k, v in r.get("bbk_queries", {}).items():
            scores.setdefault(k, []).append(_score(v) if "_error_" not in v else 0)

    for k, vs in sorted(scores.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True):
        avg = sum(vs) / len(vs)
        print(f"  {k:<30} ort={avg:>7.0f}  max={max(vs):>7}")

    print(f"\n✅ Tamamlandı → {OUTPUT_DIR}")

if __name__ == "__main__":
    main()