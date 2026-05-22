import requests
import concurrent.futures

def test_single_proxy(p_str):
    p_str = p_str.strip()
    if not p_str:
        return None, False, 0, ""
    
    # Format: host:port@user:pass
    if '@' in p_str:
        hp, up = p_str.split('@', 1)
        proxy_url = f"http://{up}@{hp}"
    else:
        proxy_url = f"http://{p_str}"
        
    proxies = {"http": proxy_url, "https": proxy_url}
    
    # Test HTTPBin for IP check
    try:
        r = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
        if r.status_code == 200:
            ip = r.json().get("origin", "")
            return p_str, True, r.elapsed.total_seconds(), ip
    except Exception as e:
        return p_str, False, 0, str(e)
    return p_str, False, 0, "Non-200 status code"

def main():
    print("Reading proxies from proxy_https_auth.csv...")
    try:
        with open("proxy_https_auth.csv", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Loaded {len(lines)} proxies. Testing the first 10 concurrently...")
    
    to_test = lines[:10]
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_single_proxy, p): p for p in to_test}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            
    print("\nResults:")
    print("=" * 80)
    for p_str, ok, duration, info in results:
        if ok:
            print(f"SUCCESS: {p_str.split('@')[0]} | Time: {duration:.2f}s | IP: {info}")
        else:
            # truncate error message if long
            err_msg = info[:60] + "..." if len(info) > 60 else info
            print(f"FAILED: {p_str.split('@')[0]} | Error: {err_msg}")
    print("=" * 80)

if __name__ == "__main__":
    main()
