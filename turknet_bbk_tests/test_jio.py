#!/usr/bin/env python3
"""JIO.com.tr API — Session + XSRF ile doğru test (TR vs EU)"""
import asyncio, aiohttp, json, time, sys, re

EU_PROXY = "https://mix101IRZKPYZ:1kkMLTYi@net-146-19-39-16.mcccx.com:8444"

BASE = "https://www.jio.com.tr"
API = BASE + "/api/v1"

# Samsun/Atakum test adresi
QUERY_CHAIN = [
    ("cities",     None),
    ("towns",      {"city_id": 55}),                        # SAMSUN
    ("neighbors",  {"town_id": "2072"}),                    # ATAKUM
    ("streets",    {"neighboor_id": "61794"}),               # ÇOBANLI MAH
    ("buildings",  {"street_id": "894797"}),                 # AYDINLIK CAD
    ("homes",      {"building_id": "28547025"}),             # NO:117
    ("tt_vae_query", {
        "selectedCity": {"code": 55, "value": "SAMSUN"},
        "selectedTown": {"code": "2072", "value": "ATAKUM"},
        "selectedNeighbor": {"code": "61794", "value": "ÇOBANLI  MAHALLESİ", "post_code": "55270"},
        "selectedStreet": {"code": "894797", "value": "AYDINLIK CADDESI"},
        "selectedBuilding": {"code": "28547025", "value": "NO :117 AAKORUPARK A1"},
        "selectedHome": {"code": "50937269", "value": "Ic Kapi(Daire) No :28"}
    }),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
    "Accept": "application/json; charset=utf-8",
    "Accept-Language": "tr,en;q=0.9",
    "Origin": BASE,
    "Referer": BASE + "/internet-altyapi-hiz-sorgulama",
    "Sec-Ch-Ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


async def get_session(proxy=None):
    """JIO sayfasını ziyaret edip session cookie + XSRF token al"""
    label = "EU" if proxy else "TR"
    try:
        jar = aiohttp.CookieJar(unsafe=True)
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(cookie_jar=jar, timeout=timeout) as session:
            # Sayfayı ziyaret et
            async with session.get(
                BASE + "/internet-altyapi-hiz-sorgulama",
                headers={"User-Agent": HEADERS["User-Agent"]},
                proxy=proxy, ssl=False
            ) as resp:
                if resp.status != 200:
                    print(f"  XX [{label}] Session sayfa -> {resp.status}")
                    return None, None

            # Cookie'leri topla
            cookies = {c.key: c.value for c in jar}
            xsrf = cookies.get("XSRF-TOKEN", "")

            if xsrf:
                # URL decode
                from urllib.parse import unquote
                xsrf = unquote(xsrf)
                print(f"  OK [{label}] Session alındı (XSRF: {xsrf[:30]}...)")
            else:
                print(f"  XX [{label}] XSRF-TOKEN cookie bulunamadı")
                print(f"       Cookies: {list(cookies.keys())}")

            return jar, xsrf
    except Exception as e:
        print(f"  XX [{label}] Session hatası: {e}")
        return None, None


async def test_chain(proxy=None):
    """Tüm address chain'i test et"""
    label = "EU" if proxy else "TR"

    jar, xsrf = await get_session(proxy)
    if not jar or not xsrf:
        return False

    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(cookie_jar=jar, timeout=timeout) as session:
            for name, body in QUERY_CHAIN:
                url = f"{API}/ttservice/{name}"
                h = dict(HEADERS)
                h["X-Xsrf-Token"] = xsrf

                t0 = time.time()
                if body is None:
                    # Empty POST (cities gibi)
                    async with session.post(url, headers=h, proxy=proxy, ssl=False) as resp:
                        elapsed = time.time() - t0
                        text = await resp.text()
                else:
                    h["Content-Type"] = "application/json"
                    async with session.post(url, json=body, headers=h, proxy=proxy, ssl=False) as resp:
                        elapsed = time.time() - t0
                        text = await resp.text()

                if resp.status == 200:
                    try:
                        data = json.loads(text)
                        if isinstance(data, list):
                            detail = f"{len(data)} items"
                        elif isinstance(data, dict):
                            # tt_vae_query sonucu
                            if "tip" in data or "hiz" in data:
                                tip = data.get("tip", "?")
                                hiz = data.get("hiz", "?")
                                port = data.get("port", "?")
                                adres = data.get("full_adres", "")[:50]
                                detail = f"{tip} {hiz}Mbps Port:{port} | {adres}"
                            elif "data" in data:
                                d = data["data"]
                                detail = f"{len(d)} items" if isinstance(d, list) else str(d)[:60]
                            else:
                                detail = str(data)[:80]
                        else:
                            detail = text[:60]
                    except:
                        detail = text[:60]
                    print(f"  OK [{label}] {name:<16} {resp.status} ({elapsed:.1f}s) | {detail}")
                else:
                    snippet = text[:60].replace("\n", " ")
                    print(f"  XX [{label}] {name:<16} {resp.status} ({elapsed:.1f}s) | {snippet}")

                    # XSRF yenilendi mi kontrol et
                    cookies = {c.key: c.value for c in jar}
                    new_xsrf = cookies.get("XSRF-TOKEN", "")
                    if new_xsrf:
                        from urllib.parse import unquote
                        xsrf = unquote(new_xsrf)

                    if name == "cities":
                        print(f"       cities bile çalışmadı, chain durduruluyor.")
                        return False

            return True

    except Exception as e:
        print(f"  XX [{label}] Chain hatası: {e}")
        return False


async def main():
    print("=" * 70)
    print("  JIO.com.tr TT Service API — Session + XSRF Testi")
    print("=" * 70)

    # IP check
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://httpbin.org/ip", ssl=False) as r:
                d = await r.json()
                print(f"  TR IP: {d.get('origin','?')}")
    except: pass
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://httpbin.org/ip", proxy=EU_PROXY, ssl=False) as r:
                d = await r.json()
                print(f"  EU IP: {d.get('origin','?')}")
    except: pass

    print(f"\n  --- Türk IP (Direkt) ---")
    tr_ok = await test_chain(proxy=None)

    print(f"\n  --- Avrupa IP (Proxy) ---")
    eu_ok = await test_chain(proxy=EU_PROXY)

    print("\n" + "=" * 70)
    print("  SONUÇ")
    print("=" * 70)
    tr_s = "OK" if tr_ok else "FAIL"
    eu_s = "OK" if eu_ok else "FAIL"
    proxy_s = "GEREKSIZ" if eu_ok else ("GEREKLI" if tr_ok else "?")
    print(f"  JIO tt_vae_query:  TR={tr_s}  EU={eu_s}  Proxy: {proxy_s}")
    print()


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
