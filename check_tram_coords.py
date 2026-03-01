import requests
import time

URL = "http://localhost:8000/api/hat/durak/SAMULAŞ%20-%20TRAMVAY"

def check():
    try:
        print(f"Fetching {URL}...")
        r = requests.get(URL)
        if r.status_code != 200:
            print(f"Failed: {r.status_code}")
            return

        duraklar = r.json()
        print(f"Total stops: {len(duraklar)}")
        
        found = False
        for d in duraklar:
            if "Örnek Sanayi" in d['ad']:
                found = True
                print(f"Found: {d['ad']} -> Lat: {d['lat']}, Lon: {d['lon']}")
                # Expected from CSV: 41.241601, 36.407934
                # Allow small error margin
                if abs(d['lat'] - 41.241601) < 0.0001 and abs(d['lon'] - 36.407934) < 0.0001:
                    print("✅ PASS: Coordinates match CSV!")
                else:
                    print("❌ FAIL: Coordinates do NOT match CSV!")
                    print(f"   Expected: 41.241601, 36.407934")
                    
        if not found:
            print("❌ FAIL: Örnek Sanayi stop not found in list!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    time.sleep(5) # Wait for server
    check()
