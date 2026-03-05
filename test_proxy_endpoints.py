import requests
import time
import json
import sys

# Endpoints to test
ASIS_BASE = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
PROXY_BASE = "https://samsun-gtfs-rt.onrender.com/api/proxy"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

TEST_CASES = [
    {"name": "Lines", "path": "/Lines", "params": {}},
    {"name": "RealTimeData", "path": "/RealTimeData", "params": {"lineCode": "E3"}},
    {"name": "SmartStations", "path": "/SmartStations", "params": {"stationId": "5055"}}, # Örnek durak
    {"name": "LineDirections", "path": "/LineDirections", "params": {"lineCode": "E3"}},
    {"name": "StopsStations", "path": "/StopsStations", "params": {"lineCode": "E3"}}
]

report = []

def compare_data(name, direct_res, proxy_res):
    if direct_res.status_code != 200:
        return f"❌ {name} (Direct) başarısız: HTTP {direct_res.status_code}"
    if proxy_res.status_code != 200:
        return f"❌ {name} (Proxy) başarısız: HTTP {proxy_res.status_code}"

    try:
        d_json = direct_res.json()
        p_json = proxy_res.json()
    except Exception as e:
        return f"❌ {name} JSON parse hatası: {e}"

    # ASIS direct usually wraps in 'data' key or returns list directly
    d_data = d_json.get('data', d_json) if isinstance(d_json, dict) else d_json
    p_data = p_json.get('data', p_json) if isinstance(p_json, dict) else p_json

    if type(d_data) != type(p_data):
        return f"⚠️ {name} Veri Tipi Uyumu Hatalı: Direct={type(d_data)}, Proxy={type(p_data)}"

    if isinstance(d_data, list):
        d_len = len(d_data)
        p_len = len(p_data)
        count_msg = f"✅ Öğe Sayısı Uyumu (Direct: {d_len}, Proxy: {p_len})" if d_len == p_len else f"⚠️ Öğe Sayısı Farklı (Direct: {d_len}, Proxy: {p_len})"
        
        # Check first item keys
        if d_len > 0 and p_len > 0 and isinstance(d_data[0], dict) and isinstance(p_data[0], dict):
            d_keys = set(d_data[0].keys())
            p_keys = set(p_data[0].keys())
            if d_keys == p_keys:
                key_msg = "✅ Alanlar (Keys) Birebir Uyuşuyor"
            else:
                missing = d_keys - p_keys
                extra = p_keys - d_keys
                key_msg = f"⚠️ Alan (Key) Farklılıkları var.\nProxy'de eksik: {missing}\nProxy'de fazla: {extra}"
        else:
            key_msg = "✅ Alan analizi uygulanamaz."
            
        return f"{name} Testi:\n- {count_msg}\n- {key_msg}"
        
    return f"✅ {name} Testi Başarılı (Farklı tipte veri geldi, ancak hata alınmadı)"

for tc in TEST_CASES:
    name = tc['name']
    path = tc['path']
    params = tc['params']
    
    print(f"Testing {name}...")
    
    start_t = time.time()
    try:
        res_direct = requests.get(ASIS_BASE + path, params=params, headers=HEADERS, timeout=15)
        d_time = time.time() - start_t
    except Exception as e:
        report.append(f"❌ {name} Direct bağlantı hatası: {e}")
        continue
        
    start_t = time.time()
    try:
        res_proxy = requests.get(PROXY_BASE + path, params=params, headers=HEADERS, timeout=15)
        p_time = time.time() - start_t
    except Exception as e:
        report.append(f"❌ {name} Proxy bağlantı hatası: {e}")
        continue
        
    res_msg = compare_data(name, res_direct, res_proxy)
    time_msg = f"- Yanıt Süresi: Direct={d_time:.2f}sn, Proxy={p_time:.2f}sn"
    report.append(f"{res_msg}\n{time_msg}\n-------------------")

with open("api_test_report.md", "w", encoding="utf-8") as f:
    f.write("# API Proxy vs Direct Endpoints Test Raporu\n\n")
    f.write("\n\n".join(report))

print("Test tamamlandı. api_test_report.md oluşturuldu.")
