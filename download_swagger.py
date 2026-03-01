
import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://api.samsun.bel.tr/OHSSoapToJson/v1/swagger.json"
print(f"Downloading {url}...")

try:
    r = requests.get(url, verify=False, timeout=10)
    print(f"Status: {r.status_code}")
    if r.ok:
        with open("swagger_download.json", "w", encoding="utf-8") as f:
            json.dump(r.json(), f, indent=2, ensure_ascii=False)
        print("Saved to swagger_download.json")
        print(f"Content Preview: {str(r.json())[:500]}")
    else:
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")
