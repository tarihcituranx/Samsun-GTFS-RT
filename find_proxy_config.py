import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('samsun.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'proxy_https_auth.csv' in line or 'self.proxies_pool' in line or 'self.s.proxies' in line or 'PROXY_HOST' in line:
            print(f"{i}: {line.strip()}")
