
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scan_paths():
    base_urls = [
        "https://api.samsun.bel.tr/OHSSoapToJson/",
        "https://api.samsun.bel.tr/OHSSoapToJson/api/",
        "https://api.samsun.bel.tr/",
    ]
    
    paths = [
        "",
        "swagger",
        "swagger/index.html",
        "swagger/ui/index",
        "swagger-ui.html",
        "docs",
        "help",
        "api-docs",
        "v2",
        "api/Asis",
        "GetServiceErrors", # Common endpoint
        "service",
        "wsdl",
        "OHSSoapToJson.asmx", # SOAP check
        "?wsdl", # SOAP check
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print("Scanning for potential API endpoints...")
    
    found_any = False
    
    for base in base_urls:
        print(f"\n--- Scanning Base: {base} ---")
        for p in paths:
            url = base + p
            # Avoid double slashes logic if needed, but simple concat is fine for test
            if base.endswith("/") and p.startswith("/"):
                url = base + p[1:]
            
            try:
                r = requests.get(url, headers=headers, timeout=5, verify=False)
                # Filter out 404s and 500s usually
                if r.status_code not in [404]:
                    print(f"[{r.status_code}] {url}  (Len: {len(r.content)})")
                    if r.status_code == 200:
                        found_any = True
                        if len(r.content) < 500:
                            print(f"   -> Content Preview: {r.text[:200]}")
            except Exception as e:
                pass
                
    if not found_any:
        print("\nNo interesting accessible endpoints found.")

if __name__ == "__main__":
    scan_paths()
