import asyncio
import json
import base64
import uuid
import aiohttp
from scrapling.fetchers import AsyncDynamicSession

async def main():
    print("--- Starting Turknet Raw Cookie Test ---")
    
    valid_cookies = {}
    async with AsyncDynamicSession(headless=True) as s:
        page_resp = await s.fetch("https://www.turk.net/internet-hiz-altyapi-sorgulama", timeout=15000)
        await asyncio.sleep(2)
        for c in page_resp.cookies:
            valid_cookies[c['name']] = c['value']
            
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
    
    # Build Cookie Header string
    cookie_str = "; ".join([f"{k}={v}" for k, v in valid_cookies.items()])
    
    base_h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.turk.net",
        "Referer": "https://www.turk.net/",
        "Cookie": cookie_str
    }
    
    async with aiohttp.ClientSession() as c:
        print("\n[1] Fetching access token...")
        r1 = await c.post("https://www.turk.net/api/auth/fetch-access-token", headers={**base_h, "Content-Type": "application/json"})
        print(f"Auth Status: {r1.status}")
        try:
            auth_data = json.loads(await r1.text())
            access_token = auth_data.get("accessToken", "")
            print(f"AccessToken found: {bool(access_token)}")
        except Exception as e:
            print(f"Failed to get token: {await r1.text()}")
            return
            
        print("\n[2] Making sales/offer query...")
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
            **base_h,
            "Authorization": f"Bearer {access_token}",
            "Captcha": str(uuid.uuid4()),
            "X-Sale-Key": sale_key,
            "Content-Type": "application/json"
        }
        
        r2 = await c.post("https://sales-gateway.turk.net/api/sales/offer", headers=offer_h, json=offer_body)
        print(f"Offer Status: {r2.status}")
        print(await r2.text())

if __name__ == "__main__":
    asyncio.run(main())
