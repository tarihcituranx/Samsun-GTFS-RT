
import requests
import time

def check_asis():
    print("Testing ASIS API...")
    try:
        r = requests.get("https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/Lines", timeout=10)
        print(f"ASIS Status: {r.status_code}")
        if r.ok:
            data = r.json()
            print(f"ASIS Data Length: {len(data) if data else 0}")
            print(f"ASIS Data Content: {data}")
            return True
        else:
            print(f"ASIS Error: {r.text[:100]}")
            return False
    except Exception as e:
        print(f"ASIS Exception: {e}")
        return False

def check_samulas():
    print("\nTesting Samulaş Web...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get("https://samulas.com.tr/otobusler", headers=headers, timeout=10)
        print(f"Samulaş Status: {r.status_code}")
        if r.ok:
            print("Samulaş Accessible")
            return True
        else:
            print(f"Samulaş Error: {r.text[:100]}")
            return False
    except Exception as e:
        print(f"Samulaş Exception: {e}")
        return False

if __name__ == "__main__":
    asis = check_asis()
    sam = check_samulas()
    

    if asis and sam:
        print("\nNO BAN DETECTED. All systems verified.")
    else:
        print("\nPOTENTIAL BAN OR CONNECTION ISSUE DETECTED.")
