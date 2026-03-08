#!/usr/bin/env python3
"""BBK 66348264 — Alaznet, Vivanet, ISS test (TR vs EU)"""
import asyncio, aiohttp, json, time, sys

EU_PROXY = "https://mix101IRZKPYZ:1kkMLTYi@net-146-19-39-16.mcccx.com:8444"
BBK = "66348264"

async def fetch(name, url, method, headers, proxy=None, **kw):
    label = "EU Proxy" if proxy else "Direkt (TR)"
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            t0 = time.time()
            if method == "POST":
                ctx = s.post(url, headers=headers, proxy=proxy, ssl=False, **kw)
            else:
                ctx = s.get(url, headers=headers, proxy=proxy, ssl=False, **kw)
            async with ctx as r:
                elapsed = time.time() - t0
                text = await r.text()
                if r.status == 200:
                    # Try JSON
                    try:
                        data = json.loads(text)
                        tip = data.get("tip", "?")
                        hiz = data.get("hiz", "?")
                        port = data.get("port", "?")
                        src = data.get("_source", "")
                        det = data.get("detay", {})
                        santral = ""
                        if isinstance(det, dict):
                            santral = det.get("SantralAdi", "")
                        print(f"  OK  [{label}] {name} -> {r.status} ({elapsed:.1f}s) | {tip} {hiz}Mbps Port:{port} {santral} {src}")
                    except json.JSONDecodeError:
                        # Vivanet TIP--HIZ--PORT format
                        if "--" in text:
                            parts = text.split("--")
                            print(f"  OK  [{label}] {name} -> {r.status} ({elapsed:.1f}s) | {parts[0].strip()} {parts[1].strip()}Mbps Port:{parts[2].strip()}")
                        else:
                            print(f"  OK  [{label}] {name} -> {r.status} ({elapsed:.1f}s) | {text[:100]}")
                    return True
                else:
                    print(f"  XX  [{label}] {name} -> {r.status} ({elapsed:.1f}s) | {text[:80]}")
                    return False
    except Exception as e:
        print(f"  XX  [{label}] {name} -> HATA: {e}")
        return False

async def main():
    print("=" * 65)
    print(f"  BBK Altyapi Testi — BBK: {BBK}")
    print("=" * 65)

    # IP check
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://httpbin.org/ip", ssl=False) as r:
                data = await r.json()
                origin = data.get("origin", "?")
                print(f"  Direkt IP: {origin}")
    except: pass
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://httpbin.org/ip", proxy=EU_PROXY, ssl=False) as r:
                data = await r.json()
                origin = data.get("origin", "?")
                print(f"  EU Proxy:  {origin}")
    except Exception as e:
        print(f"  EU Proxy hatasi: {e}")

    alaz_h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*", "Accept-Language": "tr,en;q=0.9",
        "Referer": "https://alaznet.com.tr/service/altyapi/sayfa.php"
    }
    viva_h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://vivanet.tr/altyapi-sorgula/"
    }
    iss_h = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "referer": "https://issaraclari.com/altyapi-sorgulama",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    results = {}

    print("\n  --- ALAZNET (sorgu.php?daire_id) ---")
    results["alaz_tr"] = await fetch("Alaznet", f"https://alaznet.com.tr/service/altyapi/sorgu.php?daire_id={BBK}", "GET", alaz_h)
    results["alaz_eu"] = await fetch("Alaznet", f"https://alaznet.com.tr/service/altyapi/sorgu.php?daire_id={BBK}", "GET", alaz_h, proxy=EU_PROXY)

    print("\n  --- VIVANET (POST tt_altyapi) ---")
    results["viva_tr"] = await fetch("Vivanet", "https://vivanet.tr/altyap.php", "POST", viva_h, data={"tt_altyapi": BBK})
    results["viva_eu"] = await fetch("Vivanet", "https://vivanet.tr/altyap.php", "POST", viva_h, proxy=EU_PROXY, data={"tt_altyapi": BBK})

    print("\n  --- ISS ARACLARI (port-info&bbk) ---")
    results["iss_tr"] = await fetch("ISS", f"https://issaraclari.com/api/api.php?action=port-info&bbk={BBK}", "GET", iss_h)
    results["iss_eu"] = await fetch("ISS", f"https://issaraclari.com/api/api.php?action=port-info&bbk={BBK}", "GET", iss_h, proxy=EU_PROXY)

    print("\n" + "=" * 65)
    print("  OZET")
    print("=" * 65)
    header = f"  {'API':<15} {'Turk IP':<8} {'Avrupa':<8} Proxy?"
    print(header)
    print("  " + "-" * 40)
    for api, tk, ek in [("Alaznet", "alaz_tr", "alaz_eu"), ("Vivanet", "viva_tr", "viva_eu"), ("ISS Araclari", "iss_tr", "iss_eu")]:
        t = "OK" if results.get(tk) else "FAIL"
        e = "OK" if results.get(ek) else "FAIL"
        p = "GEREKSIZ" if results.get(ek) else ("GEREKLI" if results.get(tk) else "?")
        print(f"  {api:<15} {t:<8} {e:<8} {p}")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
