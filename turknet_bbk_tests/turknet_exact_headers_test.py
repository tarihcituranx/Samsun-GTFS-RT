import asyncio
import json
import base64
import uuid
from httpx import AsyncClient
import curl_cffi.requests

async def main():
    print("--- Starting Turknet Custom HTTPX/CFFI Impersonator Test ---")
    
    # We saw curl_cffi natively drop connection, meaning TLS fingerpint might be getting caught 
    # OR we just need to send the EXACT headers the user posted.
    # The user posted PowerShell Invoke-WebRequest which uses basic .NET HTTP client 
    # but provides extensive headers like Edge 145.
    
    headers_get_token = {
        "authority": "www.turk.net",
        "method": "POST",
        "path": "/api/auth/fetch-access-token",
        "scheme": "https",
        "accept": "*/*",
        "accept-language": "tr,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "origin": "https://www.turk.net",
        "referer": "https://www.turk.net/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Microsoft Edge\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
    }
    
    headers_post_offer = {
        "authority": "sales-gateway.turk.net",
        "method": "POST",
        "path": "/api/sales/offer",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-language": "tr,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "origin": "https://www.turk.net",
        "referer": "https://www.turk.net/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Microsoft Edge\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
    }

    # Use the exact cookies from the user's snippet
    cookie_str = "token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJTYWxlS2V5IjoiMTBiNmM5NWItZjUzZS00MTc5LWI0NmEtZmEwZGRkOTdkY2Y0In0.6xLpLDB70JIMI61IIIou0_gXay_sJtec8f43SZL_KJo; mat_tel=9fb6a1cf-39e7-4563-8c62-a1018c89413d; _ga=GA1.1.964290344.1770928760; FPID=FPID2.2.262o3r86OYBqbVB8cdjROx%2FwjN2XUmjkP7N0ItZlD4s%3D.1770928760; _fbp=fb.1.1770928759892.1050414461; _gcl_au=1.1.1953538937.1770928761; FPAU=1.1.1953538937.1770928761; _tt_enable_cookie=1; _ttp=01KH9S8TMYFPZS5TPRT568H4AK_.tt.1; _ym_uid=1770928762546741488; _ym_d=1770928762; _hjSessionUser_6526413=eyJpZCI6ImZhZjc0OWUyLTljNjctNTdiMC1hNTRkLTlmMzAxZGQ5MWEzOSIsImNyZWF0ZWQiOjE3NzA5Mjg3NTk2ODksImV4aXN0aW5nIjp0cnVlfQ==; _gtmeec=eyJjdCI6Ijc1MWM1OWZlMWZhNzM0ZTYxYmVjN2MxNDIxNzFiZmNiY2E5N2ZmODIyMzE3MWI0YmQ2M2Q4MTY1YTY3YTRkNzQifQ%3D%3D; c_fiber_request_seen=true; c_fiber_return_count=1; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22unknown%22%2C%22expiryDate%22%3A%222027-02-12T21%3A11%3A30.511Z%22%7D; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22FuQhMKktITF6MT14u6m3%22%2C%22expiryDate%22%3A%222027-02-12T21%3A11%3A30.511Z%22%7D; _uetmsclkid=_uet2dd160c8d12f1a9a93220946eb5c24f7; mat_ep=https%3A//www.turk.net/internet-hiz-altyapi-sorgulama%3Futm_source%3Dbing%26utm_medium%3Dcpc%26utm_campaign%3Dsearch_brand_longtail_others%26utm_id%3D485982883%26utm_content%3Dturknet_altyapi_mixed_longtail_others%26utm_term%3Dt%25C3%25BCrknet+altyap%25C4%25B1+sorgulama%26utm_matchtype%3De%26msclkid%3D2dd160c8d12f1a9a93220946eb5c24f7%2Chttps%3A//www.turk.net/; cto_bundle=ZuBhaV83ZmpZSk5FQkJ5T21RTDdlQmJMYSUyQldPaVY4V0s1UW83RzAwTk1IZjFrZWljRVlqTGtsa1AzeUlyODR5RmY0MyUyRktsRXE4eWhSQkklMkJ4ckdzJTJCV3M0RmF2cFk1cTd0ZWQ3MU1RYnZqVURMYnpDNEhibkJZTzhzR1BvSlN1RkVYJTJCOG9sVXpFRlAzRjdRUk5IVUVaMHlIZE1RJTNEJTNE; ttcsid=1770928761505::et_XRW19gdVTFpJDpuI0.1.1770930691306.0::1.1927120.1929512::1927096.9.109.23::0.0.0; ttcsid_CBPM83BC77UFL42EFOL0=1770928761504::G3Vw3YV6CdN1aO7dYfVY.1.1770930691306.1; _uetvid=e7d278e0085211f1a1e437c0f665258c|1pi2bfj|1770931054116|6|1|bat.bing.com/p/conversions/c/n; _ga_75KDPS7844=GS2.1.s1770932719`$o2`$g0`$t1770932719`$j60`$l0`$h82146633; _ga_19EDNSW9TP=GS2.1.s1771686995`$o2`$g0`$t1771686995`$j60`$l0`$h0; envType=316e44e5-322f-4bee-8e4e-2e82488c75e2"
    
    headers_get_token["Cookie"] = cookie_str
    
    async with curl_cffi.requests.AsyncSession(impersonate="chrome120") as client:
        print("\n[1] Fetching access token...")
        try:
            r1 = await client.post("https://www.turk.net/api/auth/fetch-access-token", headers=headers_get_token, json={})
            print(f"Auth Status: {r1.status_code}")
            auth_data = r1.json()
            access_token = auth_data.get("accessToken", "")
            print(f"AccessToken found: {bool(access_token)}")
        except Exception as e:
            print(f"Failed to get token: {e}")
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
        
        headers_post_offer["Cookie"] = cookie_str
        headers_post_offer["Authorization"] = f"Bearer {access_token}"
        headers_post_offer["Captcha"] = "6e7e52fd-d6bb-4fbf-ac66-50ad8348d89f" # From user trace
        headers_post_offer["X-Sale-Key"] = "10b6c95b-f53e-4179-b46a-fa0ddd97dcf4" # From user trace
        
        r2 = await client.post("https://sales-gateway.turk.net/api/sales/offer", headers=headers_post_offer, json=offer_body)
        print(f"Offer Status: {r2.status_code}")
        print(r2.text)

if __name__ == "__main__":
    asyncio.run(main())
