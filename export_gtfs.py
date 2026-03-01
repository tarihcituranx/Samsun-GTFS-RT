import sqlite3
import csv
import os
import math
from datetime import datetime, timedelta

# Yapılandırma
DB_PATH = 'samsun_v25.db'
GTFS_DIR = 'gtfs_data'
AGENCY_NAME = 'Samsun Büyükşehir Belediyesi'
AGENCY_URL = 'https://samulas.com.tr'
AGENCY_TIMEZONE = 'Europe/Istanbul'

if not os.path.exists(GTFS_DIR):
    os.makedirs(GTFS_DIR)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("1. Agency...")
with open(f'{GTFS_DIR}/agency.txt', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang', 'agency_phone'])
    w.writerow(['SAMULAS', AGENCY_NAME, AGENCY_URL, AGENCY_TIMEZONE, 'tr', '0362 431 10 12'])

print("2. Stops...")
with open(f'{GTFS_DIR}/stops.txt', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'location_type'])
    cur.execute("SELECT * FROM durak")
    for row in cur:
        w.writerow([row['id'], row['ad'], row['lat'], row['lon'], 0])

print("3. Routes...")
with open(f'{GTFS_DIR}/routes.txt', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type'])
    cur.execute("SELECT * FROM hat")
    for row in cur:
        r_type = 0 if row['kat'] == 'tramvay' else 3
        # Use code as short_name, name as long_name. Clean up name.
        long_name = row['name'].replace(row['code'], '').strip(' -')
        if not long_name: long_name = row['name']
        w.writerow([row['code'], 'SAMULAS', row['code'], long_name, r_type])

print("4. Calendar...")
with open(f'{GTFS_DIR}/calendar.txt', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date'])
    # Hafta İçi
    w.writerow(['weekday', 1, 1, 1, 1, 1, 0, 0, '20240101', '20251231'])
    # Cumartesi
    w.writerow(['saturday', 0, 0, 0, 0, 0, 1, 0, '20240101', '20251231'])
    # Pazar
    w.writerow(['sunday', 0, 0, 0, 0, 0, 0, 1, '20240101', '20251231'])

print("5. Trips & Stop Times...")
# Cache stops for each route
route_stops = {}
cur.execute("SELECT hat, durak_id, sira, lat, lon FROM hat_durak ORDER BY hat, sira")
for r in cur:
    if r['hat'] not in route_stops: route_stops[r['hat']] = []
    route_stops[r['hat']].append(r)

with open(f'{GTFS_DIR}/trips.txt', 'w', newline='', encoding='utf-8') as f_trips, \
     open(f'{GTFS_DIR}/stop_times.txt', 'w', newline='', encoding='utf-8') as f_st:
    
    w_trips = csv.writer(f_trips)
    w_trips.writerow(['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id'])
    
    w_st = csv.writer(f_st)
    w_st.writerow(['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'])
    
    cur.execute("SELECT * FROM sefer")
    trip_count = 0
    for row in cur:
        line = row['hat']
        if line not in route_stops: continue # No stops for this line?
        
        stops = route_stops[line]
        if not stops: continue
        
        # MAPPING
        day_map = {'hi': 'weekday', 'cs': 'saturday', 'p': 'sunday'}
        service_id = day_map.get(row['gun'], 'weekday')
        direction_id = 0 if row['yon'] == 'G' else 1
        
        # If Yon=Donus (1), maybe reverse stops?
        # WARNING based on analysis: Hat_durak likely has only 1 sequence.
        # If D, we might need to reverse it. But IDs change usually.
        # For this MVP, we assume Linear or Loop.
        # Reversing list of stops for 'D' direction as a heuristic
        current_stops = list(stops)
        if row['yon'] != 'G': # Not Gidis (Usually 'D')
             current_stops.reverse()
             # Note: Stop IDs might be wrong for return direction if they are different physical stops.
             # But for GTFS visual routing line, it might be okay.
        
        trip_id = f"{line}_{service_id}_{row['saat']}_{row['yon']}"
        w_trips.writerow([line, service_id, trip_id, line, direction_id])
        
        # TIMES
        start_time_str = row['saat']
        try:
            h, m = map(int, start_time_str.split(':'))
        except: continue
        
        current_time_seconds = h * 3600 + m * 60
        
        # Speed: Bus 25km/h (~7 m/s), Tram 30km/h (~8.3 m/s)
        speed = 8.3 if 'TRAMVAY' in line else 7.0
        
        for i, stop in enumerate(current_stops):
            # Calculate time from previous stop
            dist = 0
            if i > 0:
                prev = current_stops[i-1]
                dist = haversine(prev['lat'], prev['lon'], stop['lat'], stop['lon'])
            
            seconds_to_add = int(dist / speed)
            current_time_seconds += seconds_to_add
            
            # Format HH:MM:SS
            th = current_time_seconds // 3600
            tm = (current_time_seconds % 3600) // 60
            ts = current_time_seconds % 60
            # Handle > 24 hours (GTFS allows 25:00:00)
            time_str = f"{th:02d}:{tm:02d}:{ts:02d}"
            
            w_st.writerow([trip_id, time_str, time_str, stop['durak_id'], i+1])
        
        trip_count += 1

print(f"Done. Generated {trip_count} trips.")
conn.close()
