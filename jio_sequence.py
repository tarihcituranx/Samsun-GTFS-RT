import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_jio_with_sequence(target_bbk: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        print("1. Loading JIO and solving Cloudflare (if any)...")
        await page.goto("https://www.jio.com.tr/internet-altyapi-hiz-sorgulama", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        print("2. Getting XSRF token from page...")
        cookies = await context.cookies()
        import urllib.parse
        xsrf = next((urllib.parse.unquote(c['value']) for c in cookies if c['name'] == 'XSRF-TOKEN'), None)
        print(f"XSRF exists: {bool(xsrf)}")
        
        print("3. Executing API call sequence in browser context...")
        
        # We will use the exact data the user gave us for Besiktas as a test case
        # because the backend session requires real matching IDs.
        script = """async (v) => {
            const h = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-XSRF-TOKEN': v.xsrf
            };
            
            // 1. Cities
            let res = await fetch('/api/v1/ttservice/cities', {method: 'POST', headers: h, body: "{}"});
            console.log("cities:", res.status);
            
            // 2. Towns (Istanbul = 34)
            res = await fetch('/api/v1/ttservice/towns', {method: 'POST', headers: h, body: JSON.stringify({city_id: 34})});
            console.log("towns:", res.status);
            
            // 3. Neighbors (Besiktas = 1183)
            res = await fetch('/api/v1/ttservice/neighbors', {method: 'POST', headers: h, body: JSON.stringify({town_id: "1183"})});
            console.log("neighbors:", res.status);
            
            // 4. Streets (Bebek = 40232)
            res = await fetch('/api/v1/ttservice/streets', {method: 'POST', headers: h, body: JSON.stringify({neighboor_id: "40232"})});
            console.log("streets:", res.status);
            
            // 5. Buildings (Aziz Ogan = 743926)
            res = await fetch('/api/v1/ttservice/buildings', {method: 'POST', headers: h, body: JSON.stringify({street_id: "743926"})});
            console.log("buildings:", res.status);
            
            // 6. Homes (Akasya Ap = 18023369)
            res = await fetch('/api/v1/ttservice/homes', {method: 'POST', headers: h, body: JSON.stringify({building_id: "18023369"})});
            console.log("homes:", res.status);
            
            // 7. Final VAE Query
            const final_body = {
                "selectedCity": {"code": 34, "value": "İSTANBUL"},
                "selectedTown": {"code": "1183", "value": "BEŞİKTAŞ"},
                "selectedNeighbor": {"code": "40232", "value": "BEBEK MAHALLESİ", "post_code": "34342"},
                "selectedStreet": {"code": "743926", "value": "AZİZ OGAN SOKAGI"},
                "selectedBuilding": {"code": "18023369", "value": "NO :13AKASYA APARTMANI"},
                "selectedHome": {"code": "15814309", "value": "Ic Kapi(Daire) No :3"}
            };
            res = await fetch('/api/v1/ttservice/tt_vae_query', {method: 'POST', headers: h, body: JSON.stringify(final_body)});
            return {status: res.status, text: await res.text()};
        }"""
        
        result = await page.evaluate(script, {'xsrf': xsrf})
        print(f"\nFINAL RESULT: {result['status']}")
        print(result['text'][:500])
        
        await browser.close()
        
if __name__ == "__main__":
    asyncio.run(scrape_jio_with_sequence("15814309"))
