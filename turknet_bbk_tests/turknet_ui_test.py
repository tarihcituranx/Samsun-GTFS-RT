import asyncio, json
from playwright.async_api import async_playwright

async def test_ui():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        c = await b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
        await c.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = await c.new_page()
        
        intercepted = {}
        async def on_resp(resp):
            if 'sales/offer' in resp.url and resp.request.method == 'POST':
                try: 
                    intercepted['body'] = await resp.text()
                    intercepted['status'] = resp.status
                except: 
                    pass
        page.on('response', on_resp)
        
        async def req_route(route, request):
            if 'sales/offer' in request.url:
               try:
                   body = json.loads(request.post_data)
                   print(f'Original POST: {body}')
                   body['value'] = '50937281'
                   body['buildingId'] = 28547025
                   body['cityId'] = 55
                   body['countyId'] = 2072
                   body['neighborhoodId'] = 61794
                   await route.continue_(post_data=json.dumps(body))
               except:
                   await route.continue_()
            else: await route.continue_()
            
        await page.route('**/api/sales/offer', req_route)

        print('Loading page...')
        await page.goto('https://www.turk.net/internet-hiz-altyapi-sorgulama', wait_until='networkidle')
        await asyncio.sleep(2)
        
        print('Filling form...')
        
        # Turknet's form is completely driven by inputs where you type and select
        # The first input is actually 'İl'
        await page.locator('input[type="text"]').first.click()
        await page.keyboard.type('Samsun')
        await asyncio.sleep(1)
        # Select first visible option from the dropdown
        await page.locator('.select__option').first.click()
        await asyncio.sleep(1)

        # Ilce
        await page.keyboard.type('Atakum')
        await asyncio.sleep(1)
        await page.locator('.select__option').first.click()
        await asyncio.sleep(1)
        
        # Mahalle
        await page.keyboard.type('Atakent')
        await asyncio.sleep(1)
        await page.locator('.select__option').first.click()
        await asyncio.sleep(1)
        
        # Cadde
        await page.locator('.select__option').first.click()
        await asyncio.sleep(1)
        
        # Bina
        await page.locator('.select__option').first.click()
        await asyncio.sleep(1)
        
        # Daire -- clicking this usually submits the form immediately!
        await page.locator('.select__option').first.click()
        await asyncio.sleep(5)
        
        # Or maybe there is a button?
        btn = page.locator('button.btn-primary', has_text='Sorgula')
        if await btn.is_visible():
            await btn.click()
            await asyncio.sleep(3)
        
        print(f'RESULT: {intercepted}')
        await b.close()

if __name__ == '__main__':
    asyncio.run(test_ui())
