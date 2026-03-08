"""
Turknet Infrastructure Query - Hybrid Playwright + API 
=======================================================
Strategy:
1. Use Scrapling to get cookies + token (bot detection bypass)
2. Use API for address chain (no captcha needed)
3. Use Playwright for the final sales/offer by intercepting the request
"""

import asyncio
import json
import logging
import base64
import uuid
import aiohttp
from scrapling.fetchers import AsyncDynamicSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
SG_BASE = "https://sales-gateway.turk.net"


def decode_jwt_payload(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except:
        return {}


async def query_turknet(bbk: str, bina_kodu: str, il_kod: int, ilce_kod: int, mah_kod: int):
    """
    Query Turknet infrastructure using hybrid approach:
    - API for address data (no captcha)
    - Playwright for sales/offer (intercept the actual browser request)
    """
    url = "https://www.turk.net/internet-hiz-altyapi-sorgulama"
    
    # ===== PHASE 1: Scrapling for cookies =====
    valid_cookies = {}
    async with AsyncDynamicSession(headless=True) as session:
        log.info("[Turknet] Scrapling ile sayfa yükleniyor...")
        page_resp = await session.fetch(url, timeout=30000)
        await asyncio.sleep(2)
        for c in page_resp.cookies:
            valid_cookies[c['name']] = c['value']
        log.info(f"[Turknet] Cookies: {list(valid_cookies.keys())}")
    
    token_cookie = valid_cookies.get("token", "")
    jwt_payload = decode_jwt_payload(token_cookie)
    sale_key = jwt_payload.get("SaleKey", "")
    log.info(f"[Turknet] SaleKey: {sale_key}")
    
    # ===== PHASE 2: API for address chain + token =====
    jar = aiohttp.CookieJar(unsafe=True)
    for name, value in valid_cookies.items():
        jar.update_cookies({name: value})
    
    timeout = aiohttp.ClientTimeout(total=20)
    base_h = {
        "User-Agent": CHROME_UA,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.turk.net",
        "Referer": "https://www.turk.net/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }
    
    result = {}
    
    async with aiohttp.ClientSession(cookie_jar=jar, timeout=timeout) as client:
        # Get Bearer token
        r = await client.post(
            "https://www.turk.net/api/auth/fetch-access-token",
            headers={**base_h, "Content-Type": "application/json", "Sec-Fetch-Site": "same-origin"}
        )
        t_data = json.loads(await r.text())
        access_token = t_data.get("accessToken", "")
        log.info(f"[Turknet] AccessToken alındı")
        
        auth_h = {**base_h, "Authorization": f"Bearer {access_token}"}
        
        # Address chain
        r = await client.get(f"{SG_BASE}/api/address/independent-sections/{bina_kodu}", headers=auth_h)
        sections = json.loads(await r.text())
        if sections.get("isSuccess"):
            for s in sections["data"]:
                if str(s["code"]) == str(bbk):
                    log.info(f"[Turknet] ✓ BBK bulundu: {s['name']} (code={s['code']})")
                    result["bbk_name"] = s["name"]
                    break
    
    # ===== PHASE 3: Playwright for sales/offer with request interception =====
    from playwright.async_api import async_playwright
    
    offer_result = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        context = await browser.new_context(user_agent=CHROME_UA, viewport={'width': 1920, 'height': 1080})
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        # Intercept the offer response
        captured_offer = {"response": None, "request_headers": None}
        
        async def handle_response(response):
            if "sales/offer" in response.url:
                try:
                    body = await response.text()
                    captured_offer["response"] = body
                    captured_offer["status"] = response.status
                    log.info(f"[Turknet] 🎯 Offer response intercepted: {response.status}")
                except:
                    pass
        
        async def handle_request(route, request):
            if "sales/offer" in request.url:
                captured_offer["request_headers"] = dict(request.headers)
                log.info(f"[Turknet] 🎯 Offer request intercepted!")
                log.info(f"  Captcha header: {request.headers.get('captcha', 'N/A')}")
                log.info(f"  X-Sale-Key: {request.headers.get('x-sale-key', 'N/A')}")
                
                # Modify the request body to use OUR bbk/address
                body = json.loads(request.post_data)
                body["value"] = str(bbk)
                body["buildingId"] = int(bina_kodu)
                body["cityId"] = il_kod
                body["countyId"] = ilce_kod
                body["neighborhoodId"] = mah_kod
                
                await route.continue_(post_data=json.dumps(body))
            else:
                await route.continue_()
        
        # Set up route interception
        await page.route("**/api/sales/offer", handle_request)
        page.on("response", handle_response)
        
        log.info("[Turknet] Playwright ile sayfa açılıyor...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except:
            pass
        
        await asyncio.sleep(3)
        
        # Now fill the form via Playwright
        # Step 1: Click "Adres girin" / input field 
        log.info("[Turknet] Form dolduruluyor...")
        
        try:
            # Click the address input area
            addr_input = page.locator('input[placeholder*="İl"]').first
            if not await addr_input.is_visible():
                addr_input = page.locator('[class*="select"]').first
            
            # Try clicking the İl selector
            il_selectors = page.locator('div[class*="addressFormItem"]').first
            await il_selectors.click()
            await asyncio.sleep(1)
            
            # Type and select Samsun
            await page.keyboard.type("Samsun")
            await asyncio.sleep(1)
            
            # Click SAMSUN option
            samsun_option = page.locator('text=SAMSUN').first
            if await samsun_option.is_visible():
                await samsun_option.click()
                log.info("[Turknet] ✓ Samsun seçildi")
            await asyncio.sleep(1)
            
            # İlçe - type and select Atakum
            await page.keyboard.type("Atakum")
            await asyncio.sleep(1)
            atakum_option = page.locator('text=ATAKUM').first
            if await atakum_option.is_visible():
                await atakum_option.click()
                log.info("[Turknet] ✓ Atakum seçildi")
            await asyncio.sleep(1)
            
            # Mahalle - this will trigger bucak selection first, then mahalle
            # Type the first few letters of the mahalle  
            await page.keyboard.type("Atakent")
            await asyncio.sleep(1)
            mah_option = page.locator('text=ATAKENT').first
            if await mah_option.is_visible():
                await mah_option.click()
                log.info("[Turknet] ✓ Atakent seçildi")
            await asyncio.sleep(1)
            
            # Cadde - select first available
            cadde_options = page.locator('[class*="option"]')
            first_cadde = cadde_options.first
            if await first_cadde.is_visible():
                cadde_text = await first_cadde.text_content()
                await first_cadde.click()
                log.info(f"[Turknet] ✓ Cadde seçildi: {cadde_text}")
            await asyncio.sleep(1)
            
            # Bina - select first available
            bina_options = page.locator('[class*="option"]')
            first_bina = bina_options.first
            if await first_bina.is_visible():
                bina_text = await first_bina.text_content()
                await first_bina.click()
                log.info(f"[Turknet] ✓ Bina seçildi: {bina_text}")
            await asyncio.sleep(1)
            
            # Daire - select first available (this should trigger the offer)
            daire_options = page.locator('[class*="option"]')
            first_daire = daire_options.first
            if await first_daire.is_visible():
                daire_text = await first_daire.text_content()
                await first_daire.click()
                log.info(f"[Turknet] ✓ Daire seçildi: {daire_text}")
            
            # Wait for the offer to complete
            log.info("[Turknet] Sorgu sonucu bekleniyor...")
            await asyncio.sleep(8)
            
        except Exception as e:
            log.warning(f"[Turknet] Form doldurma hatası: {e}")
            log.info("[Turknet] Alternatif yöntem: JS ile doğrudan sorgu yapılıyor...")
            
            # Alternative: Execute JS directly to make the offer call
            # Use the intercepted captcha mechanism
            try:
                js_result = await page.evaluate(f'''() => {{
                    return new Promise(async (resolve) => {{
                        try {{
                            // Get cookies
                            const cookies = document.cookie;
                            
                            // First get token
                            const tokenRes = await fetch('/api/auth/fetch-access-token', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                            }});
                            const tokenData = await tokenRes.json();
                            
                            // Get captcha from grecaptcha if available
                            let captchaVal = '{str(uuid.uuid4())}';
                            
                            // Now make the offer request  
                            const offerRes = await fetch('https://sales-gateway.turk.net/api/sales/offer', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json, text/plain, */*',
                                    'Authorization': 'Bearer ' + tokenData.accessToken,
                                    'Captcha': captchaVal,
                                    'X-Sale-Key': '{sale_key}',
                                    'Origin': 'https://www.turk.net',
                                    'Referer': 'https://www.turk.net/',
                                }},
                                body: JSON.stringify({{
                                    isInfrastructureInquiry: true,
                                    key: "BBK",
                                    buildingId: {int(bina_kodu)},
                                    value: "{bbk}",
                                    inquirySource: 2,
                                    cityId: {il_kod},
                                    channel: 2,
                                    operator: "",
                                    countyId: {ilce_kod},
                                    neighborhoodId: {mah_kod}
                                }})
                            }});
                            const offerData = await offerRes.json();
                            resolve(JSON.stringify({{status: offerRes.status, data: offerData}}));
                        }} catch(e) {{
                            resolve(JSON.stringify({{error: e.message}}));
                        }}
                    }});
                }}''')
                log.info(f"[Turknet] JS offer result: {js_result[:500]}")
                try:
                    offer_result = json.loads(js_result)
                except:
                    pass
            except Exception as e2:
                log.warning(f"[Turknet] JS offer failed: {e2}")
        
        # Check captured offer from interception
        if captured_offer["response"]:
            log.info(f"[Turknet] Intercepted offer response: {captured_offer['response'][:500]}")
            try:
                offer_result = json.loads(captured_offer["response"])
            except:
                pass
        
        if captured_offer["request_headers"]:
            log.info(f"[Turknet] Request headers captured - Captcha was: {captured_offer['request_headers'].get('captcha', 'NONE')}")
        
        await browser.close()
    
    if offer_result:
        log.info(f"[Turknet] OFFER RESULT: {json.dumps(offer_result, indent=2, ensure_ascii=False)[:1000]}")
    
    return offer_result or result


if __name__ == "__main__":
    asyncio.run(query_turknet("50937297", "28547025", 55, 2072, 61794))
