import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_jio_for_bbk(bbk_code: str):
    print(f"Starting JIO Scraper for BBK: {bbk_code}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Intercept API response
        result_data = {}
        async def handle_response(response):
            if "tt_vae_query" in response.url and response.request.method == "POST":
                try:
                    text = await response.text()
                    print(f"Intercepted tt_vae_query: {response.status} => {text[:100]}")
                    result_data["raw"] = text
                    result_data["status"] = response.status
                except Exception as e:
                    print(f"Error reading response: {e}")
                    
        page.on("response", handle_response)
        
        print("Navigating to JIO...")
        await page.goto("https://www.jio.com.tr/internet-altyapi-hiz-sorgulama", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # Unfortunately, the JIO UI doesn't have a "Search by BBK" input box on the frontend!
        # It ONLY has the dropdowns (City > District > etc).
        # We CANNOT type "BBK" directly without knowing the City/District first.
        # BUT we CAN inject JS to call their API directly if we bypass the validation!
        
        # Wait, if JIO UI doesn't have a BBK search box, how did it work previously?
        # The original code just POSTed to tt_vae_query with a fake Samsun address + selectedHome=BBK.
        
        await browser.close()
        return result_data

if __name__ == "__main__":
    asyncio.run(scrape_jio_for_bbk("37735014"))
