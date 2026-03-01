import requests
import time

URL = "http://localhost:8000/"

def check():
    try:
        print(f"Fetching {URL}...")
        r = requests.get(URL)
        if r.status_code != 200:
            print(f"Failed: {r.status_code}")
            return

        html = r.text
        if "DEĞERLİ YOLCULARIMIZIN DİKKATİNE" in html:
            print("✅ PASS: New Info Box text found in HTML.")
        else:
            print("❌ FAIL: New Info Box text NOT found in HTML!")
            print("Server might be serving old cached version or code not updated.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    time.sleep(5)
    check()
