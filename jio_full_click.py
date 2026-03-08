import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_jio_full_flow():
    async with async_playwright() as p:
        # User requested: "bizm scrapling ile sorgu at insan oldumuza inandır :)"
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        result_payload = None
        async def intercept_response(response):
            nonlocal result_payload
            if "tt_vae_query" in response.url and response.request.method == "POST":
                try:
                    text = await response.text()
                    print(f"\n[API] tt_vae_query response ({response.status}):\n{text[:200]}\n")
                    result_payload = text
                except Exception as e:
                    print(f"Error reading response: {e}")
                    
        page.on("response", intercept_response)
        
        print("1. Loading page...")
        await page.goto("https://www.jio.com.tr/internet-altyapi-hiz-sorgulama")
        await page.wait_for_timeout(2000)
        
        print("2. Selecting City (SAMSUN)...")
        await page.locator(".vs__search").nth(0).click()
        await page.wait_for_timeout(500)
        await page.locator(".vs__search").nth(0).fill("SAMSUN")
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1000)
        
        print("3. Selecting District (ATAKUM)...")
        await page.locator(".vs__search").nth(1).click()
        await page.wait_for_timeout(500)
        await page.locator(".vs__search").nth(1).fill("ATAKUM")
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1000)
        
        print("4. Selecting Mahalle (MERKEZ MAHALLESİ)...")
        await page.locator(".vs__search").nth(2).click()
        await page.wait_for_timeout(500)
        await page.locator(".vs__search").nth(2).fill("MERKEZ")
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1000)
        
        print("Waiting for final API response (max 10s)...")
        for _ in range(10):
            if result_payload:
                break
            await page.wait_for_timeout(1000)
            
        await browser.close()
        
if __name__ == "__main__":
    asyncio.run(scrape_jio_full_flow())
