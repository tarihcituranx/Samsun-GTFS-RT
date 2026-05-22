import requests
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://samsun-gtfs-rt.onrender.com"

endpoints = [
    ("/", None),
    ("/api", None),
    ("/api/tum_duraklar", None),
    ("/api/hat", None),
    ("/api/odak", None),
    ("/api/samair", None),
    ("/api/proxy/lines", None),
    ("/api/proxy/stops_stations", None),
    ("/api/proxy/smart_stations", None),
    ("/api/proxy_odak", None),
    ("/api/proxy_samair_saatler", None),
    ("/api/proxy_samair_araclar", None),
    ("/api/proxy_odak_araclar", None),
]

print("=" * 80)
print(f"Testing Render App: {BASE_URL}")
print("=" * 80)

for ep, params in endpoints:
    url = f"{BASE_URL}{ep}"
    print(f"Requesting: {url} ...", end="", flush=True)
    start_time = time.time()
    try:
        r = requests.get(url, params=params, timeout=15)
        duration = time.time() - start_time
        print(f" DONE in {duration:.2f}s | Status: {r.status_code} | Size: {len(r.content)} bytes")
    except Exception as e:
        duration = time.time() - start_time
        print(f" FAILED after {duration:.2f}s | Error: {e}")
    # Rate limit friendly sleep
    time.sleep(1.0)

print("=" * 80)
print("Test completed.")
print("=" * 80)
