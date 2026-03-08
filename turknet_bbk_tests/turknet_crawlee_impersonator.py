import asyncio
import json
import base64
import uuid

from crawlee.http_clients import CurlImpersonateHttpClient
from crawlee.sessions import SessionPool

async def main():
    print("--- Starting Turknet Crawlee HTTP Impersonator Test ---")
    
    # We use crawlee's HTTP client with chrome impersonation to bypass Cloudflare
    client = CurlImpersonateHttpClient(impersonate="chrome120")
    
    # 1. Fetch homepage to get cookies and SaleKey
    r1 = await client.send_request(url="https://www.turk.net/internet-hiz-altyapi-sorgulama")
    print(f"Homepage Status: {r1.status_code}")
    
    # Collect cookies
    valid_cookies = {}
    for name, morsel in client.cookie_jar.items():
        valid_cookies[name] = morsel.value
        
    print(f"Got {len(valid_cookies)} cookies.")
    
    # Extract SaleKey
    sale_key = ""
    token_str = valid_cookies.get("token", "")
    if token_str:
        try:
            parts = token_str.split(".")
            payload_b64 = parts[1] + "==" * (4 - len(parts[1]) % 4)
            jwt_pl = json.loads(base64.urlsafe_b64decode(payload_b64))
            sale_key = jwt_pl.get("SaleKey", "")
        except: pass
        
    print(f"SaleKey: {sale_key}")
    
    # 2. Get Access Token
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.turk.net",
        "Referer": "https://www.turk.net/",
    }
    
    r2 = await client.send_request(
        method="POST", 
        url="https://www.turk.net/api/auth/fetch-access-token", 
        headers={**base_headers, "Content-Type": "application/json"}
    )
    
    print(f"Auth Status: {r2.status_code}")
    try:
        auth_data = json.loads(r2.read().decode())
        access_token = auth_data.get("accessToken", "")
        print(f"AccessToken found: {bool(access_token)}")
    except Exception as e:
        print(f"Failed to get token: {e}")
        return
        
    # 3. Make offer call
    offer_body = {
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
    
    offer_h = {
        **base_headers,
        "Authorization": f"Bearer {access_token}",
        "Captcha": str(uuid.uuid4()),
        "X-Sale-Key": sale_key,
        "Content-Type": "application/json"
    }
    
    r3 = await client.send_request(
        method="POST", 
        url="https://sales-gateway.turk.net/api/sales/offer", 
        headers=offer_h, 
        json=offer_body
    )
    
    print(f"Offer Status: {r3.status_code}")
    print(r3.read().decode())
    
if __name__ == "__main__":
    asyncio.run(main())
