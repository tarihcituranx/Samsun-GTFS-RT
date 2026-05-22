import requests
import time

BASE_URL = "https://samsun-gtfs-rt.onrender.com"

def run_tests():
    print("=" * 80)
    print("STARTING DYNAMIC INTEGRATION TESTS FOR RENDER API")
    print("=" * 80)

    # 1. Get lines
    print("1. Fetching all lines from /api/proxy/lines...")
    try:
        r = requests.get(f"{BASE_URL}/api/proxy/lines", timeout=15)
        if r.status_code == 200:
            lines = r.json()
            print(f"   Success! Loaded {len(lines)} lines.")
            if lines:
                # Find a line code
                sample_line = lines[0]
                line_code = sample_line.get("lineCode") or sample_line.get("HatKodu")
                line_name = sample_line.get("lineName") or sample_line.get("HatAdi")
                print(f"   Selected sample line: {line_code} ({line_name})")
                
                # 2. Test stops_stations with this lineCode
                print(f"2. Fetching stops for line: {line_code}...")
                r_stops = requests.get(f"{BASE_URL}/api/proxy/stops_stations", params={"lineCode": line_code}, timeout=15)
                print(f"   Status: {r_stops.status_code} | Size: {len(r_stops.content)} bytes")
                if r_stops.status_code == 200:
                    stops = r_stops.json()
                    print(f"   Found {len(stops)} stops.")
                    if stops:
                        sample_stop = stops[0]
                        stop_id = sample_stop.get("stopId") or sample_stop.get("stationId") or sample_stop.get("kod") or sample_stop.get("id")
                        stop_name = sample_stop.get("stopName") or sample_stop.get("ad")
                        print(f"   Selected sample stop: {stop_id} ({stop_name})")
                        
                        # 3. Test smart_stations with this stop_id
                        if stop_id:
                            print(f"3. Fetching smart station data for stop ID: {stop_id}...")
                            r_smart = requests.get(f"{BASE_URL}/api/proxy/smart_stations", params={"stationId": stop_id}, timeout=15)
                            print(f"   Status: {r_smart.status_code} | Size: {len(r_smart.content)} bytes")
                            try:
                                print(f"   JSON: {r_smart.json()[:2]} ...")
                            except:
                                print(f"   Raw text: {r_smart.text[:200]}")
        else:
            print(f"   Failed to load lines. Status: {r.status_code}")
    except Exception as e:
        print(f"   Error testing lines/stops/smart: {e}")

    time.sleep(1.0)

    # 4. Get Odak
    print("\n4. Fetching Odak lines from /api/odak...")
    try:
        r = requests.get(f"{BASE_URL}/api/odak", timeout=15)
        if r.status_code == 200:
            odaks = r.json()
            print(f"   Success! Loaded {len(odaks)} Odak lines.")
            if odaks:
                sample_odak = odaks[0]
                odak_id = sample_odak.get("id")
                odak_name = sample_odak.get("ad")
                print(f"   Selected sample Odak line ID: {odak_id} ({odak_name})")
                
                # 5. Test proxy_odak_araclar with this hatid
                print(f"5. Fetching vehicles for Odak line ID: {odak_id}...")
                r_vehicles = requests.get(f"{BASE_URL}/api/proxy_odak_araclar", params={"hatid": odak_id}, timeout=15)
                print(f"   Status: {r_vehicles.status_code} | Size: {len(r_vehicles.content)} bytes")
                try:
                    print(f"   JSON: {r_vehicles.json()}")
                except:
                    print(f"   Raw text: {r_vehicles.text[:200]}")
        else:
            print(f"   Failed to load Odak lines. Status: {r.status_code}")
    except Exception as e:
        print(f"   Error testing Odak: {e}")

    time.sleep(1.0)

    # 6. Get SamAir
    print("\n6. Fetching SamAir lines from /api/samair...")
    try:
        r = requests.get(f"{BASE_URL}/api/samair", timeout=15)
        if r.status_code == 200:
            samairs = r.json()
            print(f"   Success! Loaded {len(samairs)} SamAir lines.")
            if samairs:
                sample_samair = samairs[0]
                samair_id = sample_samair.get("id")
                samair_name = sample_samair.get("ad")
                print(f"   Selected sample SamAir line ID: {samair_id} ({samair_name})")
                
                # 7. Test proxy_samair_saatler with this hatid
                print(f"7. Fetching schedules for SamAir line ID: {samair_id}...")
                r_schedules = requests.get(f"{BASE_URL}/api/proxy_samair_saatler", params={"hatid": samair_id}, timeout=15)
                print(f"   Status: {r_schedules.status_code} | Size: {len(r_schedules.content)} bytes")
                try:
                    print(f"   JSON count: {len(r_schedules.json())}")
                except:
                    print(f"   Raw text: {r_schedules.text[:200]}")
        else:
            print(f"   Failed to load SamAir lines. Status: {r.status_code}")
    except Exception as e:
        print(f"   Error testing SamAir: {e}")

    print("=" * 80)
    print("DYNAMIC INTEGRATION TESTS COMPLETED.")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
