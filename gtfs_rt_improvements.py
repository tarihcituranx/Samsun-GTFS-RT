# GTFS-RT İyileştirmeleri - Mevcut samsun.py'ye eklenecek değişiklikler

"""
GTFS Realtime Feed Geliştirmeleri
==================================

Mevcut kodunuzdaki update_gtfs_feed() fonksiyonunu aşağıdaki versiyonla değiştirin:
"""

async def update_gtfs_feed():
    """
    GTFS-RT vehicle positions feed'ini 15 saniyede bir güncelle
    
    Özellikler:
    - Tüm aktif hatları tarar (tramvay/tekne/teleferik hariç)
    - Araç konumları, hız, yön, doluluk bilgileri
    - GTFS-RT 2.0 standardına uygun
    - Duplicate plaka kontrolü
    - Error handling ve logging
    """
    http_client = Http()  # Mevcut çalışan Http sınıfı
    
    while True:
        try:
            # 1. Tüm hat kodlarını çek (sadece canlı veri olanlar)
            lines = db.get("""
                SELECT code, name, kat 
                FROM hat 
                WHERE kat NOT IN ('tramvay', 'odak', 'samair', 'tekne', 'teleferik')
                ORDER BY kat, code
            """)
            
            # 2. Feed oluştur
            feed = gtfs_realtime_pb2.FeedMessage()
            
            # Header bilgileri
            feed.header.gtfs_realtime_version = "2.0"
            feed.header.timestamp = int(time.time())
            feed.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
            
            vehicle_count = 0
            error_count = 0
            seen_entities = set()  # Duplicate entity ID kontrolü
            
            # 3. Her hat için araç verisi çek
            for line in lines:
                try:
                    # API çağrısı (async thread'de)
                    data = await asyncio.to_thread(
                        http_client.asis, 
                        'RealTimeData', 
                        lineCode=line['code']
                    )
                    
                    if not data:
                        continue
                    
                    for d in data:
                        try:
                            # Veri parse
                            lat = parse_float(d.get('enlem', 0))
                            lon = parse_float(d.get('boylam', 0))
                            plaka = str(d.get('plaka', '')).strip()
                            hiz = float(d.get('hiz', 0))
                            yon = float(d.get('yon', 0))  # bearing (0-360)
                            yolcu = int(d.get('seferYolcu', 0))
                            
                            # Validasyon
                            if not (40.0 < lat < 43.0 and 34.0 < lon < 38.0):
                                continue  # Samsun koordinat sınırları dışında
                            
                            if not plaka or plaka == '?' or len(plaka) < 2:
                                continue  # Geçersiz plaka
                            
                            # Benzersiz entity ID (format: HATCODE_PLAKA)
                            entity_id = f"{line['code']}_{plaka}".replace(' ', '_')
                            
                            if entity_id in seen_entities:
                                continue  # Duplicate, skip
                            
                            seen_entities.add(entity_id)
                            
                            # GTFS-RT Entity oluştur
                            entity = feed.entity.add()
                            entity.id = entity_id
                            
                            # Trip bilgileri
                            entity.vehicle.trip.route_id = line['code']
                            entity.vehicle.trip.trip_id = f"trip_{line['code']}_{int(time.time())}"
                            
                            # Pozisyon bilgileri
                            entity.vehicle.position.latitude = lat
                            entity.vehicle.position.longitude = lon
                            entity.vehicle.position.speed = hiz / 3.6  # km/h -> m/s
                            entity.vehicle.position.bearing = yon
                            
                            # Zaman damgası
                            entity.vehicle.timestamp = int(time.time())
                            
                            # Araç bilgileri
                            entity.vehicle.vehicle.id = plaka
                            entity.vehicle.vehicle.label = f"{plaka} ({line['code']})"
                            
                            # Doluluk durumu (GTFS-RT extension)
                            if yolcu > 0:
                                if yolcu < 20:
                                    entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.MANY_SEATS_AVAILABLE
                                elif yolcu < 40:
                                    entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.FEW_SEATS_AVAILABLE
                                else:
                                    entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.STANDING_ROOM_ONLY
                            
                            vehicle_count += 1
                            
                        except (ValueError, TypeError, KeyError) as e:
                            error_count += 1
                            continue
                            
                except Exception as e:
                    log.warning(f"Hat {line.get('code', '?')} veri çekme hatası: {str(e)[:50]}")
                    error_count += 1
                    continue
            
            # 4. Global feed'i güncelle (thread-safe)
            global gtfs_feed
            gtfs_feed = feed
            
            # Loglama
            log.info(
                f"🚌 GTFS-RT Güncellendi: "
                f"{vehicle_count} araç, "
                f"{len(lines)} hat tarandı, "
                f"{error_count} hata"
            )
            
        except Exception as e:
            log.error(f"GTFS güncelleme döngüsü hatası: {e}")
        
        # 15 saniye bekle
        await asyncio.sleep(15)


"""
Ek Endpoint'ler
===============

Aşağıdaki endpoint'leri de ekleyebilirsiniz:
"""

# 1. GTFS-RT Vehicle Positions (Protobuf)
@app.get("/gtfs-rt/vehicle-positions")
async def get_vehicle_positions():
    """
    GTFS Realtime Vehicle Positions feed
    Content-Type: application/x-protobuf
    """
    return Response(
        content=gtfs_feed.SerializeToString(), 
        media_type="application/x-protobuf",
        headers={
            "Content-Disposition": "inline; filename=vehicle-positions.pb"
        }
    )


# 2. JSON formatında (debug/test için)
@app.get("/gtfs-rt/vehicle-positions.json")
async def get_vehicle_positions_json():
    """
    GTFS-RT feed'i JSON formatında döndürür (debug için)
    """
    from google.protobuf import json_format
    
    try:
        json_data = json_format.MessageToDict(gtfs_feed)
        return JSONResponse(json_data)
    except Exception as e:
        return JSONResponse(
            {"error": str(e)}, 
            status_code=500
        )


# 3. Feed istatistikleri
@app.get("/gtfs-rt/stats")
async def get_gtfs_stats():
    """
    GTFS-RT feed istatistikleri
    """
    return JSONResponse({
        "feed_version": gtfs_feed.header.gtfs_realtime_version,
        "timestamp": gtfs_feed.header.timestamp,
        "vehicle_count": len(gtfs_feed.entity),
        "last_update": datetime.fromtimestamp(gtfs_feed.header.timestamp).isoformat(),
        "entities": [
            {
                "id": e.id,
                "route": e.vehicle.trip.route_id,
                "position": {
                    "lat": e.vehicle.position.latitude,
                    "lon": e.vehicle.position.longitude,
                    "speed_ms": e.vehicle.position.speed,
                    "bearing": e.vehicle.position.bearing
                },
                "vehicle": e.vehicle.vehicle.label
            }
            for e in gtfs_feed.entity[:50]  # İlk 50 araç
        ]
    })


"""
Test ve Kullanım
================

1. Sunucu başlatıldıktan sonra:

   # Protobuf formatında (standart GTFS-RT)
   curl http://localhost:8000/gtfs-rt/vehicle-positions --output positions.pb
   
   # JSON formatında (görsel kontrol)
   curl http://localhost:8000/gtfs-rt/vehicle-positions.json
   
   # İstatistikler
   curl http://localhost:8000/gtfs-rt/stats


2. GTFS-RT okuyucu ile test:
   
   pip install gtfs-realtime-bindings
   
   import requests
   from google.transit import gtfs_realtime_pb2
   
   response = requests.get('http://localhost:8000/gtfs-rt/vehicle-positions')
   feed = gtfs_realtime_pb2.FeedMessage()
   feed.ParseFromString(response.content)
   
   for entity in feed.entity:
       print(f"Araç: {entity.vehicle.vehicle.label}")
       print(f"Konum: {entity.vehicle.position.latitude}, {entity.vehicle.position.longitude}")
       print(f"Hız: {entity.vehicle.position.speed * 3.6:.1f} km/h")
       print("---")


3. Transit uygulamalarında kullanım:
   
   - OneBusAway
   - Transitime
   - Google Transit Partner Dashboard
   - OpenTripPlanner
   
   Bu uygulamalara feed URL'sini ekleyin:
   http://your-server:8000/gtfs-rt/vehicle-positions
"""


"""
Performans İyileştirmeleri
===========================

Eğer çok fazla hat varsa ve performans sorunu yaşanıyorsa:

1. Paralel istekler:
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

async def fetch_line_data_parallel(lines, max_workers=10):
    """Birden fazla hattı paralel olarak çek"""
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                http_client.asis,
                'RealTimeData',
                lineCode=line['code']
            )
            for line in lines
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
    return results


"""
2. Caching (eğer update süresi 15 saniyeden uzunsa):
"""

from functools import lru_cache
import hashlib

@lru_cache(maxsize=200)
def get_cached_line_data(line_code, cache_key):
    """Hat verisini cache'le (cache_key = timestamp // 15)"""
    return http_client.asis('RealTimeData', lineCode=line_code)

# Kullanım:
cache_key = int(time.time()) // 15  # Her 15 saniyede bir cache sıfırlanır
data = get_cached_line_data(line['code'], cache_key)


"""
GTFS Static Feed Oluşturma (Opsiyonel)
========================================

GTFS-RT ile birlikte GTFS Static feed de oluşturabilirsiniz:
"""

def create_gtfs_static():
    """
    GTFS Static feed dosyaları oluştur (agency.txt, routes.txt, stops.txt, vs.)
    """
    import csv
    import zipfile
    from datetime import date
    
    # 1. agency.txt
    with open('agency.txt', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang'])
        writer.writerow(['SAMULAS', 'Samulaş', 'https://samulas.com.tr', 'Europe/Istanbul', 'tr'])
    
    # 2. routes.txt
    hatlar = db.get("SELECT code, name, kat FROM hat")
    with open('routes.txt', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type'])
        
        for h in hatlar:
            # route_type: 3 = Bus, 0 = Tram, 1 = Subway/Metro, 6 = Cable Car
            route_type = 0 if h['kat'] == 'tramvay' else 6 if h['kat'] == 'teleferik' else 3
            writer.writerow([h['code'], 'SAMULAS', h['code'], h['name'], route_type])
    
    # 3. stops.txt
    duraklar = db.get("SELECT id, ad, lat, lon FROM durak")
    with open('stops.txt', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['stop_id', 'stop_name', 'stop_lat', 'stop_lon'])
        
        for d in duraklar:
            writer.writerow([d['id'], d['ad'], d['lat'], d['lon']])
    
    # 4. trips.txt & stop_times.txt (basitleştirilmiş)
    # ... (tam implementasyon için daha fazla kod gerekir)
    
    # 5. Zip'le
    with zipfile.ZipFile('gtfs_static.zip', 'w') as zipf:
        zipf.write('agency.txt')
        zipf.write('routes.txt')
        zipf.write('stops.txt')
        # ... diğer dosyalar
    
    log.info("GTFS Static feed oluşturuldu: gtfs_static.zip")


# Endpoint ekle
@app.get("/gtfs-static")
async def download_gtfs_static():
    """GTFS Static feed'i indir"""
    if not os.path.exists('gtfs_static.zip'):
        create_gtfs_static()
    
    return FileResponse(
        'gtfs_static.zip',
        media_type='application/zip',
        filename='samsun_gtfs_static.zip'
    )
