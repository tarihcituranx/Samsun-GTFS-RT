import asyncio
import json
import base64
import uuid
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

PROXY_URL = "http://tarihcituranx:AdIowZ8L@dc1.livaproxy.com:38186"
TARGET_URL = "https://www.turk.net/internet-hiz-altyapi-sorgulama"

async def get_cookies_scrapling():
    from scrapling.fetchers import AsyncDynamicSession
    print("\n[Scrapling] Başlıyor...")
    # Increase timeout significantly for slow proxy + Cloudflare wait
    kw = {"headless": True, "proxy": {"server": PROXY_URL}}
    
    cookies = {}
    try:
        async with AsyncDynamicSession(**kw) as s:
            print("[Scrapling] Sayfaya gidiliyor...")
            resp = await s.fetch(TARGET_URL, timeout=45000)
            print(f"[Scrapling] Yanıt alındı: {resp.status}")
            
            # Cloudflare'in tamamen geçmesi ve token'in set edilmesi için bekle
            await asyncio.sleep(5)
            
            for c in resp.cookies:
                cookies[c['name']] = c['value']
                
            print(f"[Scrapling] Çekilen cookie'ler: {list(cookies.keys())}")
            if "token" in cookies:
                print(f"[Scrapling] ✓ Token cookie bulundu: {cookies['token'][:30]}...")
            else:
                print("[Scrapling] ❌ Token cookie BULUNAMADI")
                # Fallback: JS execute ile dogrudan accessToken fetch
    except Exception as e:
        print(f"[Scrapling] Hata: {e}")
        
    return cookies


async def main():
    print("=== TURKNET BYPASS TEST ===")
    
    cookies = await get_cookies_scrapling()
    if not cookies or "token" not in cookies:
        print("Geçerli token cookie alınamadı, çıkılıyor.")
        return

    token_cookie = cookies["token"]
    
    # 1. SaleKey çıkar
    sale_key = ""
    try:
        parts = token_cookie.split(".")
        payload_b64 = parts[1] + "==" * (4 - len(parts[1]) % 4)
        jwt_pl = json.loads(base64.urlsafe_b64decode(payload_b64))
        sale_key = jwt_pl.get("SaleKey", "")
        print(f"SaleKey Çıkarıldı: {sale_key}")
    except Exception as e:
        print(f"SaleKey Çıkarma Hatası: {e}")
        return

    # 2. AccessToken iste
    proxies = {"http": PROXY_URL, "https": PROXY_URL}
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.turk.net",
        "Referer": "https://www.turk.net/",
        "Cookie": cookie_str
    }
    
    print("\n[Auth] fetch-access-token çağrılıyor...")
    try:
        r = requests.post("https://www.turk.net/api/auth/fetch-access-token", 
                          headers=headers, json={}, proxies=proxies, timeout=15)
        if r.status_code == 200:
            at_data = r.json()
            access_token = at_data.get("accessToken", "")
            print(f"[Auth] ✓ AccessToken alındı: {len(access_token)} chars")
        else:
            print(f"[Auth] Hata: {r.status_code} - {r.text[:200]}")
            return
    except Exception as e:
        print(f"[Auth] Exception: {e}")
        return

    # 3. Offer iste
    print("\n[Offer] sales/offer çağrılıyor...")
    offer_headers = {
        **headers,
        "Authorization": f"Bearer {access_token}",
        "Captcha": str(uuid.uuid4()),
        "X-Sale-Key": sale_key,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
    }
    
    # Cookie header güncelleniyor (accessToken eklendi)
    cookies["accessToken"] = access_token
    offer_headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    
    # Adres değerleri (Samsun Atakum Çobanlı 50937281)
    body = {
        "isInfrastructureInquiry": True,
        "key": "BBK",
        "buildingId": 28547025,
        "value": "50937281",
        "inquirySource": 2,
        "cityId": 55,
        "channel": 2,
        "operator": "",
        "countyId": 2072,
        "neighborhoodId": 61794
    }
    
    try:
        # Note the endpoint: sales-gateway.turk.net
        r2 = requests.post("https://sales-gateway.turk.net/api/sales/offer", 
                           headers=offer_headers, json=body, proxies=proxies, timeout=20)
        
        print(f"Status: {r2.status_code}")
        print(f"Body: {r2.text[:500]}")
        
        if r2.status_code == 200:
            data = r2.json()
            if data.get("isSuccess"):
                info = data.get("data", {}).get("offerInfo", {})
                print("\n🎉 OFFER BAŞARILI!")
                print(f"Hız: {info.get('downloadSpeed')} Mbps")
                print(f"Fiyat: {info.get('finalPrice')} TL")
    except Exception as e:
        print(f"[Offer] Exception: {e}")


if __name__ == "__main__":
    asyncio.run(main())
