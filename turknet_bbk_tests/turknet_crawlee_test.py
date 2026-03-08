import asyncio
import json
import base64
import uuid
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from crawlee.crawlers import HTTPCrawler, HTTPCrawlingContext
from httpx import AsyncClient

async def main():
    print("--- Starting Turknet Crawlee + HTTPX Test ---")
    
    # 1. We will use Crawlee's Playwright crawler just to visit the page and get cookies
    # Crawlee automatically handles stealth techniques and browser management
    valid_cookies = {}
    
    crawler = PlaywrightCrawler(
        headless=True,
        browser_type="chromium",
    )
    
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        print(f"Visited: {context.request.url}")
        await context.page.wait_for_timeout(3000)
        cookies = await context.page.context.cookies()
        for c in cookies:
            valid_cookies[c['name']] = c['value']
            
    await crawler.run(["https://www.turk.net/internet-hiz-altyapi-sorgulama"])
    print(f"Got {len(valid_cookies)} cookies from Crawlee Playwright.")
    
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
    
    # 2. Setup HTTPX client with the exact headers from PowerShell
    cookie_str = "; ".join([f"{k}={v}" for k, v in valid_cookies.items()])
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.turk.net",
        "Referer": "https://www.turk.net/",
        "Cookie": cookie_str
    }
    
    async with AsyncClient(http2=True) as client:
        print("\n[1] Fetching access token...")
        r1 = await client.post("https://www.turk.net/api/auth/fetch-access-token", headers={**headers, "Content-Type": "application/json"})
        print(f"Auth Status: {r1.status_code}")
        try:
            auth_data = r1.json()
            access_token = auth_data.get("accessToken", "")
            print(f"AccessToken found: {bool(access_token)}")
        except Exception as e:
            print(f"Failed to get token: {r1.text}")
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
            **headers,
            "Authorization": f"Bearer {access_token}",
            "Captcha": str(uuid.uuid4()),
            "X-Sale-Key": sale_key,
            "Content-Type": "application/json"
        }
        
        r2 = await client.post("https://sales-gateway.turk.net/api/sales/offer", headers=offer_h, json=offer_body)
        print(f"Offer Status: {r2.status_code}")
        print(r2.text)

if __name__ == "__main__":
    asyncio.run(main())
