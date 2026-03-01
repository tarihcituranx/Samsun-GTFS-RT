
import requests

def check_qrdurak():
    url = "https://mobil.samsun.bel.tr/QRDurak.php?stopId=5328"
    print(f"Testing {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        }
        r = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {r.status_code}")
        print(f"Content Preview: {r.text[:200]}")
    except Exception as e:
        print(f"Error accessing QRDurak: {e}")

def check_asis_with_headers():
    url = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/Lines"
    print(f"\nTesting ASIS with Headers: {url}")
    try:
        # Mimic the mobile app or a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://mobil.samsun.bel.tr/',
            'Origin': 'https://mobil.samsun.bel.tr',
            'X-Requested-With': 'XMLHttpRequest'
        }
        r = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {r.status_code}")
        if r.ok:
            try:
                data = r.json()
                print(f"Data: {data}")
            except:
                print(f"Text: {r.text[:200]}")
    except Exception as e:
        print(f"Error accessing ASIS: {e}")


def check_ybs():
    print("\nTesting YBS API...")
    try:
        # 1. Get Token
        r = requests.get("https://ybs.samsun.bel.tr/service/?method=getGuestToken", timeout=10)
        print(f"YBS Token Status: {r.status_code}")
        if r.ok:
            data = r.json()
            token = data.get('token')
            print(f"Token Acquired: {'Yes' if token else 'No'}")
            
            if token:
                # 2. Try to fetch lines with token
                p = {'method': 'getBusLines', 'token': token}
                r2 = requests.get("https://ybs.samsun.bel.tr/service/", params=p, timeout=10)
                print(f"YBS Lines Status: {r2.status_code}")
                if r2.ok:
                    res = r2.json()
                    print(f"YBS Response Type: {type(res)}")
                    
                    if isinstance(res, list):
                        print(f"YBS Line Count: {len(res)}")
                        if len(res) > 0:
                            print(f"Sample Item: {res[0]}")
                    elif isinstance(res, dict):
                        print(f"YBS Status: {res.get('status')}")
                        print(f"YBS Data: {res.get('data')}")
        else:
            print(f"YBS Token Error: {r.text[:100]}")
    except Exception as e:
        print(f"YBS Error: {e}")

def check_asis_stops():
    url = "https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/StopsStations"
    print(f"\nTesting ASIS StopsStations: {url}")
    try:
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            print(f"ASIS Stops Data: {data}")
        else:
            print(f"ASIS Stops Status: {r.status_code}")
    except Exception as e:
        print(f"ASIS Stops Error: {e}")

def check_samair_ybs():
    print("\nTesting Samair YBS (Flights)...")
    try:
        r = requests.get("https://ybs.samsun.bel.tr/service/?method=getGuestToken", timeout=10)
        if not r.ok: return
        token = r.json().get('token')
        
        # Test Flight Schedules
        # Hat ID 3 seems to be H1 (from code: H1 -> 3)
        p = {
            'method': 'samair_ucaksefersaatleri_public',
            'submethod': 'HatlarList',
            'hatid': 3,
            'token': token
        }
        r2 = requests.get("https://ybs.samsun.bel.tr/service/", params=p, timeout=10)
        print(f"Samair Schedule Status: {r2.status_code}")
        if r2.ok:
            try:
                data = r2.json()
                # YBS calls might return direct list or dict
                print(f"Samair Data Type: {type(data)}")
                if isinstance(data, list):
                    print(f"Flight Count: {len(data)}")
                    if data: print(f"Sample Flight: {data[0]}")
                elif isinstance(data, dict):
                     print(f"Samair Response: {data}")
            except Exception as e:
                print(f"Samair Json Error: {e}")
                print(f"Raw: {r2.text[:100]}")
    except Exception as e:
        print(f"Samair Error: {e}")

if __name__ == "__main__":
    import sys
    with open("check_log.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        check_qrdurak()
        check_asis_with_headers()
        check_asis_stops()
        check_ybs()
        check_samair_ybs()
