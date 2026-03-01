import requests
import json
import urllib3
import datetime

urllib3.disable_warnings()

ASIS_URL = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis"
HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://samair.samsun.bel.tr/'
}

LINE_CODE = "SAMULAŞ - TRAMVAY"

def test_endpoint(ep, data):
    print(f"--- Testing {ep} ---")
    try:
        r = requests.post(f"{ASIS_URL}/{ep}", json=data, headers=HEADERS, verify=False, timeout=10)
        if r.ok:
            res = r.json()
            if isinstance(res, dict) and 'result' in res:
                items = res['result']
            else:
                items = res
            
            print(f"Status: {r.status_code}")
            print(f"Item Count: {len(items) if items else 0}")
            if items:
                print("Sample Item:", json.dumps(items[0], indent=2, ensure_ascii=False)[:500])
            else:
                print("Response is empty.")
        else:
            print(f"Failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error: {e}")
    print("\n")

def main():
    print(f"Testing for Line: {LINE_CODE}\n")
    
    # 1. Stops
    test_endpoint("StopsStations", {"lineCode": LINE_CODE})
    
    # 2. Schedules (Today)
    today = datetime.date.today().strftime("%Y-%m-%d")
    test_endpoint("Schedules", {"lineCode": LINE_CODE, "scheduleDate": today})
    
    # 3. Real Time Data
    test_endpoint("RealTimeData", {"lineCode": LINE_CODE})
    
    # 4. Active Vehicles (Alternative)
    test_endpoint("GetActiveVehicles", {"lineCode": LINE_CODE})

if __name__ == "__main__":
    main()
