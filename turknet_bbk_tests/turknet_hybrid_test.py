#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turknet HİBRİT BYPASS — Tüm Silahlar + Proxy
==============================================
Proxy: PROXY_HOST/PORT/USER/PASS env vars (Render'da Türk proxy)
Fallback Zinciri:
  1. undetected-chromedriver + proxy
  2. Selenium stealth + proxy
  3. Scrapling + proxy  
  4. Crawlee PlaywrightCrawler + proxy
  
Sonra: requests + proxy ile sales-gateway.turk.net API
"""
import json
import time
import base64
import uuid
import re
import sys
import os
import requests
import asyncio
import logging

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("turknet_hybrid")

SG = "https://sales-gateway.turk.net"
INFRA_MAP = {4: "ADSL", 5: "VDSL", 6: "GigaFiber", 11: "Fiber"}
TARGET = "https://www.turk.net/internet-hiz-altyapi-sorgulama"

# ═══════════════════════════════════════════════════════════════════════════
#  PROXY CONFIG (Render env vars)
# ═══════════════════════════════════════════════════════════════════════════
PROXY_HOST = os.getenv("PROXY_HOST", "")
PROXY_PORT = os.getenv("PROXY_PORT", "")
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")

def get_proxy_url():
    if PROXY_HOST and PROXY_PORT:
        if PROXY_USER and PROXY_PASS:
            return f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        return f"http://{PROXY_HOST}:{PROXY_PORT}"
    return None

PROXY_URL = get_proxy_url()
log.info(f"Proxy: {'AYARLI → ' + PROXY_HOST + ':' + PROXY_PORT if PROXY_URL else 'YOK (lokal test)'}")

# ═══════════════════════════════════════════════════════════════════════════
#  YÖNTEM 1: undetected-chromedriver + proxy
# ═══════════════════════════════════════════════════════════════════════════
def get_token_uc():
    log.info("🔫 [1/4] undetected-chromedriver deneniyor...")
    try:
        import undetected_chromedriver as uc
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        if PROXY_URL:
            # UC proxy: --proxy-server format
            proxy_arg = f"{PROXY_HOST}:{PROXY_PORT}"
            options.add_argument(f"--proxy-server={proxy_arg}")
            log.info(f"  [UC] Proxy: {proxy_arg}")
        
        driver = uc.Chrome(options=options, version_main=None)
        try:
            # Proxy auth varsa extension ile
            if PROXY_URL and PROXY_USER:
                # Chrome proxy auth için manifest.json + background.js gerekli
                # Basit yaklaşım: URL'e git ve auth popup'ı ele al
                pass
            
            driver.get(TARGET)
            time.sleep(6)
            log.info(f"  [UC] Title: {driver.title}")
            
            cookies = {}
            for c in driver.get_cookies():
                cookies[c['name']] = c['value']
            log.info(f"  [UC] {len(cookies)} cookie")
            
            if not cookies.get('token'):
                time.sleep(5)
                for c in driver.get_cookies():
                    cookies[c['name']] = c['value']
            
            access_token = ""
            try:
                access_token = driver.execute_script("""
                    const r = await fetch('/api/auth/fetch-access-token', {method:'POST',headers:{'Content-Type':'application/json'}});
                    const d = await r.json(); return d.accessToken||'';
                """)
            except: pass
            
            if cookies.get('token') or access_token:
                log.info(f"  [UC] ✅ Token:{'VAR' if cookies.get('token') else 'YOK'} Access:{'VAR' if access_token else 'YOK'}")
                return cookies, access_token
        finally:
            try: driver.quit()
            except: pass
    except Exception as e:
        log.warning(f"  [UC] ❌ {e}")
    return None, None


# ═══════════════════════════════════════════════════════════════════════════
#  YÖNTEM 2: Selenium stealth + proxy
# ═══════════════════════════════════════════════════════════════════════════
def get_token_selenium():
    log.info("🔫 [2/4] Selenium stealth deneniyor...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        if PROXY_URL:
            options.add_argument(f"--proxy-server={PROXY_HOST}:{PROXY_PORT}")
            log.info(f"  [Selenium] Proxy: {PROXY_HOST}:{PROXY_PORT}")
        
        driver = webdriver.Chrome(options=options)
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            })
            driver.get(TARGET)
            time.sleep(6)
            log.info(f"  [Selenium] Title: {driver.title}")
            
            cookies = {}
            for c in driver.get_cookies():
                cookies[c['name']] = c['value']
            
            access_token = ""
            try:
                access_token = driver.execute_script("""
                    const r = await fetch('/api/auth/fetch-access-token', {method:'POST',headers:{'Content-Type':'application/json'}});
                    const d = await r.json(); return d.accessToken||'';
                """)
            except: pass
            
            if cookies.get('token') or access_token:
                log.info(f"  [Selenium] ✅ Token:{'VAR' if cookies.get('token') else 'YOK'} Access:{'VAR' if access_token else 'YOK'}")
                return cookies, access_token
        finally:
            try: driver.quit()
            except: pass
    except Exception as e:
        log.warning(f"  [Selenium] ❌ {e}")
    return None, None


# ═══════════════════════════════════════════════════════════════════════════
#  YÖNTEM 3: scrapling + proxy
# ═══════════════════════════════════════════════════════════════════════════
def get_token_scrapling():
    log.info("🔫 [3/4] Scrapling deneniyor...")
    async def _inner():
        from scrapling.fetchers import AsyncDynamicSession
        kwargs = {"headless": True}
        if PROXY_URL:
            kwargs["proxy"] = {"server": f"http://{PROXY_HOST}:{PROXY_PORT}"}
            if PROXY_USER:
                kwargs["proxy"]["username"] = PROXY_USER
                kwargs["proxy"]["password"] = PROXY_PASS
            log.info(f"  [Scrapling] Proxy: {PROXY_HOST}:{PROXY_PORT}")
        
        async with AsyncDynamicSession(**kwargs) as s:
            page_resp = await s.fetch(TARGET, timeout=15000)
            await asyncio.sleep(3)
            cookies = {}
            for c in page_resp.cookies:
                cookies[c['name']] = c['value']
            log.info(f"  [Scrapling] {len(cookies)} cookie")
            return cookies
    
    try:
        cookies = asyncio.run(_inner())
        if cookies.get('token'):
            log.info("  [Scrapling] ✅ Token VAR")
            return cookies, ""
    except Exception as e:
        log.warning(f"  [Scrapling] ❌ {e}")
    return None, None


# ═══════════════════════════════════════════════════════════════════════════
#  YÖNTEM 4: crawlee + proxy
# ═══════════════════════════════════════════════════════════════════════════
def get_token_crawlee():
    log.info("🔫 [4/4] Crawlee deneniyor...")
    async def _inner():
        try:
            from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
        except ImportError:
            from crawlee.crawlers import PlaywrightCrawler
            from crawlee.crawlers._playwright import PlaywrightCrawlingContext
        
        result_cookies = {}
        
        # Crawlee proxy config
        proxy_config = None
        if PROXY_URL:
            from crawlee import ProxyConfiguration
            proxy_config = ProxyConfiguration(
                proxy_urls=[PROXY_URL]
            )
            log.info(f"  [Crawlee] Proxy: {PROXY_HOST}:{PROXY_PORT}")
        
        crawler = PlaywrightCrawler(
            headless=True,
            browser_type="chromium",
            max_request_retries=1,
            proxy_configuration=proxy_config,
        )
        
        @crawler.router.default_handler
        async def handler(context: PlaywrightCrawlingContext):
            nonlocal result_cookies
            await context.page.wait_for_timeout(5000)
            for c in await context.page.context.cookies():
                result_cookies[c['name']] = c['value']
        
        await crawler.run([TARGET])
        return result_cookies
    
    try:
        cookies = asyncio.run(_inner())
        if cookies.get('token'):
            log.info(f"  [Crawlee] ✅ Token VAR")
            return cookies, ""
    except Exception as e:
        log.warning(f"  [Crawlee] ❌ {e}")
    return None, None


# ═══════════════════════════════════════════════════════════════════════════
#  ANA FALLBACK ZİNCİRİ
# ═══════════════════════════════════════════════════════════════════════════
def get_turknet_auth():
    methods = [
        ("undetected-chromedriver", get_token_uc),
        ("Selenium stealth", get_token_selenium),
        ("Scrapling", get_token_scrapling),
        ("Crawlee", get_token_crawlee),
    ]
    
    for name, func in methods:
        log.info(f"\n{'─'*50}")
        cookies, access_token = func()
        if cookies:
            log.info(f"🏆 {name} BAŞARILI!")
            
            # access_token yoksa requests ile dene
            if not access_token and cookies.get('token'):
                cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                try:
                    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
                    r = requests.post("https://www.turk.net/api/auth/fetch-access-token",
                        headers={"User-Agent":"Mozilla/5.0","Cookie":cookie_str,"Content-Type":"application/json",
                                 "Origin":"https://www.turk.net","Referer":"https://www.turk.net/"},
                        json={}, timeout=10, proxies=proxies)
                    if r.status_code == 200:
                        access_token = r.json().get("accessToken", "")
                except: pass
            
            return cookies, access_token
    
    log.error("💀 TÜM YÖNTEMLER BAŞARISIZ!")
    return {}, ""


# ═══════════════════════════════════════════════════════════════════════════
#  SALES-GATEWAY API (requests + proxy)
# ═══════════════════════════════════════════════════════════════════════════
def query_offer(cookie_dict, access_token, bbk, addr_dict):
    sale_key = ""
    token_str = cookie_dict.get("token", "")
    if token_str:
        try:
            parts = token_str.split(".")
            payload_b64 = parts[1] + "==" * (4 - len(parts[1]) % 4)
            jwt_pl = json.loads(base64.urlsafe_b64decode(payload_b64))
            sale_key = jwt_pl.get("SaleKey", "")
        except: pass
    
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.turk.net",
        "Referer": "https://www.turk.net/",
        "sec-ch-ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Cookie": cookie_str,
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    il = addr_dict.get("IL","").strip().upper()
    ilce = addr_dict.get("ILCE","").strip().upper()
    mah = addr_dict.get("MAHALLE","").strip().upper()
    city_id = county_id = neighborhood_id = 0
    
    # Cities
    try:
        r = requests.get(f"{SG}/api/address/cities", headers=headers, timeout=10, proxies=proxies)
        log.info(f"  Cities: {r.status_code}")
        if r.status_code == 200:
            for c in r.json().get("data",[]):
                if c.get("name","").strip().upper() == il:
                    city_id = c["code"]; break
    except Exception as e:
        log.warning(f"  Cities: {e}")
    if not city_id: city_id = 55
    
    # Counties
    if ilce:
        try:
            r = requests.get(f"{SG}/api/address/counties/{city_id}", headers=headers, timeout=10, proxies=proxies)
            if r.status_code == 200:
                for c in r.json().get("data",[]):
                    cn = c.get("name","").strip().upper()
                    if cn == ilce or ilce in cn:
                        county_id = c["code"]; break
        except: pass
    
    # Township → Village → District
    tid = vid = 0
    if county_id:
        try:
            r = requests.get(f"{SG}/api/address/townships/{county_id}", headers=headers, timeout=10, proxies=proxies)
            if r.status_code == 200:
                d = r.json().get("data",[])
                if d: tid = d[0]["code"]
        except: pass
    if tid:
        try:
            r = requests.get(f"{SG}/api/address/villages/{tid}", headers=headers, timeout=10, proxies=proxies)
            if r.status_code == 200:
                d = r.json().get("data",[])
                if d: vid = d[0]["code"]
        except: pass
    if mah and vid:
        try:
            r = requests.get(f"{SG}/api/address/districts/{vid}", headers=headers, timeout=10, proxies=proxies)
            if r.status_code == 200:
                mc = re.sub(r'\s+',' ',mah).replace("MAH.","").replace("MAH","").strip()
                for d in r.json().get("data",[]):
                    dn = re.sub(r'\s+',' ',d.get("name","")).strip().upper()
                    if mc == dn or mc in dn or dn in mc:
                        neighborhood_id = d["code"]; break
        except: pass
    
    log.info(f"  Adres: city={city_id} county={county_id} neigh={neighborhood_id}")
    
    building_id = int(addr_dict.get("BINA_KODU",0) or 0)
    body = {
        "isInfrastructureInquiry": True, "key": "BBK", "buildingId": building_id,
        "value": str(bbk), "inquirySource": 2, "cityId": city_id, "channel": 2,
        "operator": "", "countyId": county_id, "neighborhoodId": neighborhood_id,
    }
    offer_h = {**headers, "Content-Type":"application/json",
               "Captcha": str(uuid.uuid4()), "X-Sale-Key": sale_key}
    
    log.info(f"  POST offer BBK={bbk} bldg={building_id}")
    try:
        r = requests.post(f"{SG}/api/sales/offer", headers=offer_h, json=body, timeout=15, proxies=proxies)
        log.info(f"  Offer: HTTP {r.status_code}")
        log.info(f"  Body: {r.text[:500]}")
        if r.status_code == 200:
            od = r.json()
            if od.get("isSuccess") and od.get("data"):
                info = od["data"].get("offerInfo",{})
                it = info.get("infrastructureType",0)
                log.info(f"  ✅ {INFRA_MAP.get(it,f'Tip-{it}')} | {info.get('downloadSpeed',0)} Mbps")
                return True, od
    except Exception as e:
        log.warning(f"  Offer: {e}")
    return False, {}


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 TURKNET HİBRİT BYPASS — TÜM SİLAHLAR + PROXY")
    print("=" * 60)
    
    cookies, access_token = get_turknet_auth()
    addr = {"IL":"SAMSUN","ILCE":"ATAKUM","MAHALLE":"ÇOBANLI MAH.","BINA_KODU":28547025}
    success, data = query_offer(cookies, access_token, "50937281", addr)
    
    print("\n" + "=" * 60)
    if success:
        print("  🎉 TURKNET BAŞARILI!")
    else:
        print("  ❌ Başarısız")
    print("=" * 60)
