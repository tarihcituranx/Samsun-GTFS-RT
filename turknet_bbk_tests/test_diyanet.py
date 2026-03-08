#!/usr/bin/env python3
"""Diyanet Kuran API — Türk IP vs Avrupa IP testi"""
import asyncio, aiohttp, json, time, sys

EU_PROXY = "https://mix101IRZKPYZ:1kkMLTYi@net-146-19-39-16.mcccx.com:8444"
BASE = "https://t061.diyanet.gov.tr/apigateway/acikkaynakkuran"
TOKEN = "652|UiPQA5VHo8S1xDydOb8jzX74p7OWCXxvlJBnubJSfc0a89f1"

ENDPOINTS = [
    ("Tum Sureler",    "/api/v1/chapters",      {"language": "tr"}),
    ("Fatiha Ayetler", "/api/v1/chapters/1",     {}),
    ("Sayfa 1",        "/api/v1/verses/page/1",  {}),
    ("Cuz 1",          "/api/v1/juz/1",          {}),
    ("Font Listesi",   "/api/v1/fonts",          {}),
]

async def test_ep(name, path, params, proxy=None):
    label = "EU Proxy" if proxy else "Direkt (TR)"
    url = BASE + path
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            t0 = time.time()
            async with s.get(url, params=params, headers=headers, proxy=proxy, ssl=False) as r:
                elapsed = time.time() - t0
                text = await r.text()
                if r.status == 200:
                    try:
                        data = json.loads(text)
                        items = len(data) if isinstance(data, list) else len(data.get("data", []))
                    except:
                        items = "?"
                    print(f"  OK  [{label}] {name} -> {r.status} ({elapsed:.1f}s) | {items} items")
                    return True
                else:
                    snippet = text[:80].replace("\n", " ")
                    print(f"  XX  [{label}] {name} -> {r.status} ({elapsed:.1f}s) | {snippet}")
                    return False
    except Exception as e:
        print(f"  XX  [{label}] {name} -> HATA: {e}")
        return False

async def main():
    print("=" * 65)
    print("  Diyanet Kuran API Testi — Turk IP vs Avrupa IP")
    print("=" * 65)

    # IP check
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://httpbin.org/ip", ssl=False) as r:
                d = await r.json()
                print(f"  Direkt IP: {d['origin']}")
    except: pass
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://httpbin.org/ip", proxy=EU_PROXY, ssl=False) as r:
                d = await r.json()
                print(f"  EU Proxy:  {d['origin']}")
    except Exception as e:
        print(f"  EU Proxy bağlantı hatası: {e}")

    print()
    results = {}
    for name, path, params in ENDPOINTS:
        print(f"  --- {name} ({path}) ---")
        tr = await test_ep(name, path, params, proxy=None)
        eu = await test_ep(name, path, params, proxy=EU_PROXY)
        results[name] = {"tr": tr, "eu": eu}
        print()

    print("=" * 65)
    print("  OZET")
    print("=" * 65)
    print(f"  {'Endpoint':<20} {'Turk IP':<12} {'Avrupa IP':<12} Proxy?")
    print(f"  {'-' * 55}")
    for name, r in results.items():
        tr_s = "OK" if r["tr"] else "FAIL"
        eu_s = "OK" if r["eu"] else "FAIL"
        if r["eu"]:
            p = "GEREKSIZ"
        elif r["tr"]:
            p = "GEREKLI"
        else:
            p = "Belirsiz"
        print(f"  {name:<20} {tr_s:<12} {eu_s:<12} {p}")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
