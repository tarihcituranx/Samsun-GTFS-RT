import requests, json, uuid, sys, base64
sys.stdout.reconfigure(encoding='utf-8')

def encode_sale_key(uuid_str):
    # JWT structure for token cookie just in case
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b'=').decode('ascii')
    payload = base64.urlsafe_b64encode(json.dumps({"SaleKey": uuid_str}).encode('utf-8')).rstrip(b'=').decode('ascii')
    return f"{header}.{payload}.fake"

def main():
    print("=== TURKNET LOCAL IP TEST (NO PROXY) ===")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.turk.net",
        "Referer": "https://www.turk.net/",
        "Sec-Fetch-Site": "same-origin",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Microsoft Edge\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    
    # 1. Get Token
    print("1. Fetching access token...")
    try:
        r = requests.post("https://www.turk.net/api/auth/fetch-access-token", headers=headers, json={}, timeout=10)
        at = r.json().get('accessToken', '')
        print(f"Token: OK ({len(at)} chars)")
    except Exception as e:
        print(f"Token error (Cloudflare blocked local IP?): {e}")
        try:
            print(r.text[:200])
        except: pass
        return

    # 2. Offer test
    print("\n2. Calling offer API...")
    # Known working dummy variables
    sale_key = "10b6c95b-f53e-4179-b46a-fa0ddd97dcf4"
    fake_token_cookie = encode_sale_key(sale_key)
    
    offer_headers = {
        **headers,
        "Sec-Fetch-Site": "same-site",
        "Authorization": f"Bearer {at}",
        "Captcha": str(uuid.uuid4()),
        "X-Sale-Key": sale_key,
        "Cookie": f"token={fake_token_cookie}; accessToken={at}"
    }
    
    body = {
        "isInfrastructureInquiry": True,
        "key": "BBK",
        "buildingId": 28547025,
        "value": "50937281",
        "inquirySource": 2,
        "cityId": 55,
        "channel": 2,
        "operator": "",
        "countyId": 2072,
        "neighborhoodId": 61794
    }
    
    r2 = requests.post("https://sales-gateway.turk.net/api/sales/offer", headers=offer_headers, json=body, timeout=15)
    print(f"Offer Status: {r2.status_code}")
    print(f"Offer Body: {r2.text[:500]}")

if __name__ == "__main__":
    main()
