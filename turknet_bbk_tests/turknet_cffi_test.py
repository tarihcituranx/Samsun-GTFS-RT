import asyncio
import json
import base64
import uuid
from curl_cffi.requests import AsyncSession

async def main():
    print("--- Starting Turknet curl_cffi Test ---")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Origin": "https://www.turk.net",
        "Referer": "https://www.turk.net/",
    }
    
    async with AsyncSession(impersonate="chrome120") as s:
        print("[1] Fetching homepage to get cookies...")
        r0 = await s.get("https://www.turk.net/internet-hiz-altyapi-sorgulama")
        print(f"Status: {r0.status_code}")
        
        # Check cookies
        cookies = s.cookies.get_dict(".turk.net")
        if not cookies:
            cookies = s.cookies.get_dict("www.turk.net")
            
        token_cookie = cookies.get("token", "")
        print(f"Token cookie found: {bool(token_cookie)}")
        
        # Extract SaleKey
        sale_key = ""
        if token_cookie:
            try:
                parts = token_cookie.split(".")
                payload_b64 = parts[1] + "==" * (4 - len(parts[1]) % 4)
                jwt_pl = json.loads(base64.urlsafe_b64decode(payload_b64))
                sale_key = jwt_pl.get("SaleKey", "")
            except:
                pass
        print(f"SaleKey: {sale_key}")
        
        print("\n[2] Fetching access token...")
        # Note: fetch-access-token is on same-origin for www.turk.net
        auth_h = {**headers, "Sec-Fetch-Site": "same-origin"}
        r1 = await s.post("https://www.turk.net/api/auth/fetch-access-token", headers=auth_h)
        print(f"Auth Status: {r1.status_code}")
        auth_data = r1.json()
        access_token = auth_data.get("accessToken", "")
        print(f"AccessToken found: {bool(access_token)}")
        
        print("\n[3] Making sales/offer query...")
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
            **headers,
            "Authorization": f"Bearer {access_token}",
            "Captcha": str(uuid.uuid4()),
            "X-Sale-Key": sale_key
        }
        
        r2 = await s.post("https://sales-gateway.turk.net/api/sales/offer", headers=offer_h, json=offer_body)
        print(f"Offer Status: {r2.status_code}")
        print(r2.text)

if __name__ == "__main__":
    asyncio.run(main())
