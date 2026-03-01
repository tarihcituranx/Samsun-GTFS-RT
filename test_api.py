import requests
import json
import urllib3

urllib3.disable_warnings()

url = 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis'

# Test 1: Empty param
print("Testing empty param...")
try:
    r = requests.post(url, data={'methodName': 'RealTimeData', 'paramJson': '{}'}, verify=False)
    print("Status:", r.status_code)
    print("Response:", r.text[:200])
except Exception as e: print(e)

# Test 2: Multiple lines
print("\nTesting multiple lines (12/17,24/A)...")
try:
    p = json.dumps({"lineCode": "12/17,24/A"})
    r = requests.post(url, data={'methodName': 'RealTimeData', 'paramJson': p}, verify=False)
    print("Status:", r.status_code)
    print("Response:", r.text[:200])
except Exception as e: print(e)
