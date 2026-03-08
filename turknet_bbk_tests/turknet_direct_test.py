import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
    "Origin": "https://www.turk.net",
    "Referer": "https://www.turk.net/",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
}

SG = "https://sales-gateway.turk.net"

# Test 1: Cities (address resolution)
print("=== Test 1: cities ===")
try:
    r = requests.get(f"{SG}/api/address/cities", headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    data = r.json()
    samsun = [c for c in data.get("data", []) if "SAMSUN" in c.get("name", "")]
    print(f"isSuccess: {data.get('isSuccess')}, Samsun: {samsun}")
except Exception as e:
    print(f"HATA: {e}")

# Test 2: Counties/55
print("\n=== Test 2: counties/55 ===")
try:
    r = requests.get(f"{SG}/api/address/counties/55", headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    data = r.json()
    atakum = [c for c in data.get("data", []) if "ATAKUM" in c.get("name", "")]
    print(f"isSuccess: {data.get('isSuccess')}, Atakum: {atakum}")
except Exception as e:
    print(f"HATA: {e}")

# Test 3: www.turk.net auth token
print("\n=== Test 3: www.turk.net auth ===")
try:
    r = requests.post("https://www.turk.net/api/auth/fetch-access-token",
        headers={**headers, "Content-Type": "application/json", "sec-fetch-site": "same-origin"},
        json={}, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:200]}")
except Exception as e:
    print(f"HATA: {e}")

# Test 4: sales/offer without auth (baseline)
print("\n=== Test 4: sales/offer (no auth) ===")
try:
    body = {
        "isInfrastructureInquiry": True,
        "key": "BBK",
        "buildingId": 28547025,
        "value": "50937297",
        "inquirySource": 2,
        "cityId": 55,
        "channel": 2,
        "operator": "",
        "countyId": 2072,
        "neighborhoodId": 61794
    }
    r = requests.post(f"{SG}/api/sales/offer",
        headers={**headers, "Content-Type": "application/json",
                 "X-Sale-Key": "10b6c95b-f53e-4179-b46a-fa0ddd97dcf4",
                 "Captcha": "6e7e52fd-d6bb-4fbf-ac66-50ad8348d89f"},
        json=body, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"HATA: {e}")

# Test 5: sales/offer WITH hardcoded bearer token
print("\n=== Test 5: sales/offer (with hardcoded bearer) ===")
try:
    # Try fetching token first
    token_ok = False
    access_token = ""
    try:
        rt = requests.post("https://www.turk.net/api/auth/fetch-access-token",
            headers={**headers, "Content-Type": "application/json", "sec-fetch-site": "same-origin"},
            json={}, timeout=10)
        if rt.status_code == 200:
            access_token = rt.json().get("accessToken", "")
            token_ok = True
            print(f"Token fetched: {access_token[:30]}...")
    except:
        pass
    
    if not token_ok:
        print("Token fetch failed, trying offer without Authorization...")
    
    offer_headers = {
        **headers,
        "Content-Type": "application/json",
        "X-Sale-Key": "10b6c95b-f53e-4179-b46a-fa0ddd97dcf4",
        "Captcha": "6e7e52fd-d6bb-4fbf-ac66-50ad8348d89f",
    }
    if access_token:
        offer_headers["Authorization"] = f"Bearer {access_token}"
    
    r = requests.post(f"{SG}/api/sales/offer",
        headers=offer_headers, json=body, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"HATA: {e}")
