#!/usr/bin/env python3
"""
Turknet — headed browser ile formu doldur, Google Places autocomplete'i çalıştır
BBK numarası ile de sorgulamayı dene
"""
import asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    from playwright.async_api import async_playwright
    proxy_config = {"server": "http://dc1.livaproxy.com:38186", "username": "[GIZLI_KULLANICI]", "password": "[GIZLI_SIFRE]"}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, 
            proxy=proxy_config,
            slow_mo=200,  # Her aksiyonu yavaşlat
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
            viewport={"width": 1920, "height": 1080}, locale="tr-TR",
        )
        page = await context.new_page()
        
        # Fetch intercept
        await page.add_init_script("""
            window.__offer_reqs = [];
            const _f = window.fetch;
            window.fetch = async function(...a) {
                const [u, o] = a;
                if (u && u.toString().includes('sales/offer')) {
                    const h = {};
                    if (o?.headers) {
                        if (o.headers instanceof Headers) o.headers.forEach((v,k)=>h[k]=v);
                        else Object.entries(o.headers).forEach(([k,v])=>h[k]=v);
                    }
                    window.__offer_reqs.push({url:u.toString(), headers:h, body:o?.body});
                }
                return _f.apply(this, a);
            };
        """)
        
        # Network intercept
        async def on_req(req):
            if '/api/sales/offer' in req.url:
                print(f"\n{'='*50}")
                print(f"[OFFER REQ] {req.method}")
                for k in ['captcha', 'x-sale-key', 'authorization']:
                    v = req.headers.get(k, '')
                    if v: print(f"  {k}: {v[:100]}")
                try:
                    if req.post_data: print(f"  body: {req.post_data[:400]}")
                except: pass
        async def on_resp(resp):
            if '/api/sales/offer' in resp.url:
                try:
                    b = await resp.json()
                    print(f"  → {resp.status}: {json.dumps(b, ensure_ascii=False)[:500]}")
                except: pass
        page.on("request", on_req)
        page.on("response", on_resp)
        
        print("=== 1. Sayfa ===")
        await page.goto("https://www.turk.net/internet-hiz-altyapi-sorgulama", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        print(f"Title: {await page.title()}")
        
        # Input'u bul ve tıkla
        print("\n=== 2. Adres yazılıyor ===")
        addr_input = page.locator('input[placeholder="Adres girin"]')
        await addr_input.scroll_into_view_if_needed()
        await addr_input.click()
        await page.wait_for_timeout(500)
        
        # Yavaşça yaz
        await addr_input.type("Cobat", delay=200)
        await page.wait_for_timeout(3000)
        
        # Google Places suggestions'ı kontrol et
        await page.screenshot(path='turknet_places1.png')
        
        # Google Places pac-container (standart class)
        pac_items = await page.evaluate("""() => {
            const containers = document.querySelectorAll('.pac-container, .pac-item, [class*="pac-"]');
            return Array.from(containers).map(el => ({
                cls: el.className, text: el.textContent.trim().substring(0, 100),
                visible: el.getBoundingClientRect().height > 0,
                childCount: el.children.length,
            }));
        }""")
        print(f"PAC items: {len(pac_items)}")
        for p_item in pac_items:
            print(f"  {p_item}")
        
        # Temizle ve farklı metin dene
        await addr_input.clear()
        await page.wait_for_timeout(500)
        await addr_input.type("Samsun", delay=200)
        await page.wait_for_timeout(3000)
        
        # Suggestions
        await page.screenshot(path='turknet_places2.png')
        pac_items2 = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.pac-container .pac-item, [class*="pac-item"]'))
                .map(el => ({text: el.textContent.trim().substring(0, 100), visible: el.getBoundingClientRect().height > 0}));
        }""")
        print(f"\nPAC items after 'Samsun': {len(pac_items2)}")
        for p_item in pac_items2:
            print(f"  {p_item}")
        
        # Google Places yoksa, form'un kendi autocomplete'i mi var?
        all_after = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('*'))
                .filter(el => {
                    const r = el.getBoundingClientRect();
                    return r.height > 0 && r.top > 400 && r.top < 600 && r.height < 100 && el.textContent.trim().length > 3;
                })
                .slice(0, 15)
                .map(el => ({tag: el.tagName, text: el.textContent.trim().substring(0, 80), y: Math.round(el.getBoundingClientRect().y)}));
        }""")
        print(f"\nElements near input (y 400-600):")
        for a in all_after:
            print(f"  [{a.get('tag')}] y={a.get('y')} {a.get('text')}")
        
        # 30 saniye bekle — ekranı gözlemle
        print("\n30 saniye bekleniyor...")
        await page.wait_for_timeout(30000)
        
        # Final intercept check
        intercepted = await page.evaluate("() => window.__offer_reqs")
        if intercepted:
            print(f"\n🎯 INTERCEPTED ({len(intercepted)}):")
            for r in intercepted:
                print(json.dumps(r, ensure_ascii=False, indent=2))
        
        await browser.close()

asyncio.run(main())
