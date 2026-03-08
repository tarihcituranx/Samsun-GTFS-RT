#!/usr/bin/env python3
"""
Avrupa proxy üzerinden API geo-restriction testi.
Her API'ye Avrupa IP'den istek atar ve hangi API'lerin
Türk IP GEREKTİRDİĞİNİ tespit eder.
"""
import requests
import sys
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Avrupa proxy — HTTPS IP (port 8444)
PROXIES_RAW = [
    "net-146-19-39-16.mcccx.com:8444@mix101IRZKPYZ:1kkMLTYi",
    "net-185-61-218-148.mcccx.com:8444@mix101IRZKPYZ:1kkMLTYi",
    "net-147-78-183-91.mcccx.com:8444@mix101IRZKPYZ:1kkMLTYi",
    "net-157-22-100-162.mcccx.com:8444@mix101IRZKPYZ:1kkMLTYi",
    "net-193-233-88-84.mcccx.com:8444@mix101IRZKPYZ:1kkMLTYi",
]

def parse_proxy(raw):
    """host:port@user:pass → https://user:pass@host:port"""
    host_port, user_pass = raw.split("@")
    return f"https://{user_pass}@{host_port}"

EU_PROXY = parse_proxy(PROXIES_RAW[0])
EU_PROXY_DICT = {"http": EU_PROXY, "https": EU_PROXY}

# Test edilecek API'ler — her biri TURKISH_IP_DOMAINS listesinden
# Basit bir GET isteği yapar ve HTTP status + response boyutuna bakar
TEST_URLS = {
    "alaznet.com.tr":           "https://alaznet.com.tr",
    "turksatkablo.net":         "https://turksatkablo.net",
    "dsmart.com.tr":            "https://www.dsmart.com.tr",
    "milleni.com.tr":           "https://www.milleni.com.tr",
    "issaraclari.com":          "https://issaraclari.com",
    "mgm.gov.tr":               "https://servis.mgm.gov.tr/web/",
    "diyanet.gov.tr":           "https://kuran.diyanet.gov.tr",
    "karakutu.com.tr":          "https://www.karakutu.com.tr",
    "turk.net":                 "https://turk.net",
    "superonline.com":          "https://www.superonline.net",
    "vodafone.com.tr":          "https://www.vodafone.com.tr",
    "turkcell.com.tr":          "https://www.turkcell.com.tr",
    "vivanet.tr":               "https://vivanet.tr",
    "teknofix.com.tr":          "https://www.teknofix.com.tr",
    "diyanetnamazvakti.com.tr": "https://www.diyanetnamazvakti.com.tr",
    "emushaf.net":              "https://ezanvakti.emushaf.net/sehirler/2",
    "imsakiyem.com":            "https://imsakiyem.com",
    "afad.gov.tr":              "https://deprem.afad.gov.tr",
    "millisaraylar.gov.tr":     "https://www.millisaraylar.gov.tr",
    "sbb.gov.tr":               "https://www.sbb.gov.tr",
}

TIMEOUT = 15

def check_direct(name, url):
    """Proxy OLMADAN direkt istek"""
    try:
        r = requests.get(url, timeout=TIMEOUT, verify=False, allow_redirects=True,
                        headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code, len(r.content)
    except requests.ConnectionError as e:
        return "CONN_ERR", str(e)[:80]
    except requests.Timeout:
        return "TIMEOUT", ""
    except Exception as e:
        return "ERROR", str(e)[:80]

def check_eu_proxy(name, url):
    """Avrupa proxy üzerinden istek (Render'ı simüle eder)"""
    try:
        r = requests.get(url, timeout=TIMEOUT, verify=False, allow_redirects=True,
                        proxies=EU_PROXY_DICT,
                        headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code, len(r.content)
    except requests.ConnectionError as e:
        return "CONN_ERR", str(e)[:80]
    except requests.Timeout:
        return "TIMEOUT", ""
    except Exception as e:
        return "ERROR", str(e)[:80]


def main():
    print("=" * 70)
    print("  API Geo-Restriction Testi — Avrupa IP vs Türk IP")
    print("=" * 70)

    # Önce proxy çalışıyor mu test et
    print(f"\n  Proxy: {EU_PROXY[:50]}...")
    try:
        r = requests.get("https://httpbin.org/ip", proxies=EU_PROXY_DICT, timeout=10, verify=False)
        ip = r.json().get("origin", "?")
        print(f"  Proxy IP: {ip}")
    except Exception as e:
        print(f"  ⚠ Proxy bağlanılamıyor: {e}")
        # İkinci proxy'yi dene
        eu2 = parse_proxy(PROXIES_RAW[1])
        eu2_dict = {"http": eu2, "https": eu2}
        try:
            r = requests.get("https://httpbin.org/ip", proxies=eu2_dict, timeout=10, verify=False)
            ip = r.json().get("origin", "?")
            print(f"  Proxy 2 IP: {ip}")
            EU_PROXY_DICT.update(eu2_dict)
        except Exception as e2:
            print(f"  ⚠ Proxy 2 de başarısız: {e2}")
            print("  Proxy'siz devam ediliyor...")

    # Kendi IP'mizi kontrol et
    try:
        r = requests.get("https://httpbin.org/ip", timeout=10, verify=False)
        ip = r.json().get("origin", "?")
        print(f"  Direkt IP:  {ip}")
    except:
        pass

    print(f"\n{'─' * 70}")
    print(f"  {'Domain':<30} {'Direkt (TR)':<15} {'EU Proxy':<15} {'Karar'}")
    print(f"{'─' * 70}")

    results = {}

    for domain, url in TEST_URLS.items():
        # Direkt (Türk IP — bizim makine)
        d_status, d_size = check_direct(domain, url)

        # Avrupa proxy üzerinden
        eu_status, eu_size = check_eu_proxy(domain, url)

        # Karar ver
        d_ok = isinstance(d_status, int) and 200 <= d_status < 400
        eu_ok = isinstance(eu_status, int) and 200 <= eu_status < 400

        if eu_ok:
            verdict = "✔ Proxy GEREKSIZ"
        elif d_ok and not eu_ok:
            verdict = "✘ Proxy GEREKLI"
        elif not d_ok and not eu_ok:
            verdict = "? Her ikisi de hata"
        else:
            verdict = "? Belirsiz"

        results[domain] = verdict

        d_str = f"{d_status}" if isinstance(d_status, int) else d_status
        eu_str = f"{eu_status}" if isinstance(eu_status, int) else eu_status

        print(f"  {domain:<30} {d_str:<15} {eu_str:<15} {verdict}")
        time.sleep(0.3)

    # Özet
    print(f"\n{'═' * 70}")
    print("  ÖZET")
    print(f"{'═' * 70}")

    needed = [d for d, v in results.items() if "GEREKLI" in v]
    not_needed = [d for d, v in results.items() if "GEREKSIZ" in v]
    unclear = [d for d, v in results.items() if "?" in v]

    print(f"\n  Proxy GEREKLİ ({len(needed)}):")
    for d in needed:
        print(f"    ✘ {d}")

    print(f"\n  Proxy GEREKSİZ ({len(not_needed)}):")
    for d in not_needed:
        print(f"    ✔ {d}")

    if unclear:
        print(f"\n  Belirsiz ({len(unclear)}):")
        for d in unclear:
            print(f"    ? {d}")

    # Yeni TURKISH_IP_DOMAINS önerisi
    if needed:
        print(f"\n  📋 Önerilen TURKISH_IP_DOMAINS:")
        print("  TURKISH_IP_DOMAINS = [")
        for d in needed:
            print(f'      "{d}",')
        print("  ]")


if __name__ == "__main__":
    main()
