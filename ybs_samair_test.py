#!/usr/bin/env python3
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

YBS = "https://ybs.samsun.bel.tr/service/"

# Token al
r = requests.post(YBS, data={'method': 'getGuestToken'}, verify=False, timeout=10)
token = r.json().get('token')
print(f'Token: {token[:20]}...')

# Her hat ID için sefer sayısını test et
for hatid in range(1, 11):
    try:
        params = {
            'method': 'samair_ucaksefersaatleri_public',
            'submethod': 'HatlarList', 
            'hatid': hatid,
            'token': token
        }
        r = requests.get(YBS, params=params, verify=False, timeout=10)
        data = r.json()
        seferler = data.get('data') or data.get('root') or []
        print(f'Hat {hatid}: {len(seferler)} sefer')
        if seferler and len(seferler) > 0:
            print(f'  Örnek: {seferler[0]}')
    except Exception as e:
        print(f'Hat {hatid}: HATA - {e}')
