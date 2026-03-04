# GTFS Realtime Implementasyonu - Samsun Transit

Bu dokümantasyon, Samsun Transit projesine GTFS Realtime (GTFS-RT) desteğinin nasıl eklendiğini ve kullanıldığını açıklar.

## 📋 İçindekiler

1. [GTFS-RT Nedir?](#gtfs-rt-nedir)
2. [Kurulum](#kurulum)
3. [Implementasyon Detayları](#implementasyon-detayları)
4. [Kullanım](#kullanım)
5. [Test](#test)
6. [Transit Uygulamalarıyla Entegrasyon](#transit-uygulamalarıyla-entegrasyon)
7. [Sorun Giderme](#sorun-giderme)

## 🚌 GTFS-RT Nedir?

GTFS Realtime (General Transit Feed Specification - Realtime), toplu taşıma sistemlerinin canlı konumlarını, varış tahminlerini ve servis uyarılarını paylaşmak için kullanılan açık veri standardıdır.

### Temel Özellikler:
- **Protocol Buffers** formatında veri aktarımı (kompakt ve hızlı)
- Standart format (tüm transit uygulamaları destekler)
- Üç feed tipi:
  - **Vehicle Positions** (Araç konumları) ✅ Implementasyon yapıldı
  - **Trip Updates** (Sefer güncellemeleri)
  - **Service Alerts** (Servis uyarıları)

## 🔧 Kurulum

### Gereksinimler

```bash
# Python bağımlılıkları
pip install gtfs-realtime-bindings
pip install protobuf>=3.19.0

# Zaten yüklü olanlar (samsun.py'de)
pip install fastapi uvicorn requests
```

### 1. Mevcut Koda Entegrasyon

`samsun.py` dosyanızda zaten GTFS-RT implementasyonu var, ancak iyileştirmeler için `gtfs_rt_improvements.py` dosyasındaki `update_gtfs_feed()` fonksiyonunu kullanın:

```python
# samsun.py içinde (satır 1980 civarı)
# Mevcut update_gtfs_feed() fonksiyonunu aşağıdaki ile değiştirin:

async def update_gtfs_feed():
    """GTFS-RT vehicle positions feed'ini 15 saniyede bir güncelle"""
    http_client = Http()
    
    while True:
        try:
            # Tüm hat kodlarını çek
            lines = db.get("""
                SELECT code, name, kat 
                FROM hat 
                WHERE kat NOT IN ('tramvay', 'odak', 'samair', 'tekne', 'teleferik')
            """)
            
            # Feed oluştur
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.header.gtfs_realtime_version = "2.0"
            feed.header.timestamp = int(time.time())
            feed.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
            
            vehicle_count = 0
            seen_entities = set()
            
            # Her hat için veri çek
            for line in lines:
                try:
                    data = await asyncio.to_thread(
                        http_client.asis, 
                        'RealTimeData', 
                        lineCode=line['code']
                    )
                    
                    for d in data or []:
                        # Parse ve validasyon
                        lat = parse_float(d.get('enlem', 0))
                        lon = parse_float(d.get('boylam', 0))
                        plaka = str(d.get('plaka', '')).strip()
                        hiz = float(d.get('hiz', 0))
                        yon = float(d.get('yon', 0))
                        yolcu = int(d.get('seferYolcu', 0))
                        
                        # Validasyon
                        if not (40 < lat < 43 and 34 < lon < 38):
                            continue
                        if not plaka or plaka == '?':
                            continue
                        
                        # Unique ID
                        entity_id = f"{line['code']}_{plaka}".replace(' ', '_')
                        if entity_id in seen_entities:
                            continue
                        seen_entities.add(entity_id)
                        
                        # GTFS-RT Entity
                        entity = feed.entity.add()
                        entity.id = entity_id
                        entity.vehicle.trip.route_id = line['code']
                        entity.vehicle.trip.trip_id = f"trip_{line['code']}_{int(time.time())}"
                        entity.vehicle.position.latitude = lat
                        entity.vehicle.position.longitude = lon
                        entity.vehicle.position.speed = hiz / 3.6
                        entity.vehicle.position.bearing = yon
                        entity.vehicle.timestamp = int(time.time())
                        entity.vehicle.vehicle.id = plaka
                        entity.vehicle.vehicle.label = f"{plaka} ({line['code']})"
                        
                        # Doluluk durumu
                        if yolcu > 0:
                            if yolcu < 20:
                                entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.MANY_SEATS_AVAILABLE
                            elif yolcu < 40:
                                entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.FEW_SEATS_AVAILABLE
                            else:
                                entity.vehicle.occupancy_status = gtfs_realtime_pb2.VehiclePosition.STANDING_ROOM_ONLY
                        
                        vehicle_count += 1
                        
                except Exception as e:
                    log.warning(f"Hat {line['code']} hata: {e}")
                    continue
            
            # Global feed'i güncelle
            global gtfs_feed
            gtfs_feed = feed
            
            log.info(f"🚌 GTFS-RT: {vehicle_count} araç güncellendi ({len(lines)} hat)")
            
        except Exception as e:
            log.error(f"GTFS loop error: {e}")
        
        await asyncio.sleep(15)
```

### 2. Endpoint'leri Kontrol Edin

`samsun.py`'de bu endpoint zaten var:

```python
@app.get("/gtfs-rt/vehicle-positions")
async def get_vehicle_positions():
    return Response(
        content=gtfs_feed.SerializeToString(), 
        media_type="application/x-protobuf"
    )
```

Ek olarak şu endpoint'leri de ekleyebilirsiniz:

```python
# JSON formatı (debug için)
@app.get("/gtfs-rt/vehicle-positions.json")
async def get_vehicle_positions_json():
    from google.protobuf import json_format
    return JSONResponse(json_format.MessageToDict(gtfs_feed))

# İstatistikler
@app.get("/gtfs-rt/stats")
async def get_gtfs_stats():
    return JSONResponse({
        "vehicle_count": len(gtfs_feed.entity),
        "timestamp": gtfs_feed.header.timestamp,
        "entities": [
            {
                "id": e.id,
                "route": e.vehicle.trip.route_id,
                "position": {
                    "lat": e.vehicle.position.latitude,
                    "lon": e.vehicle.position.longitude
                }
            }
            for e in gtfs_feed.entity[:20]
        ]
    })
```

## 📡 Kullanım

### Sunucuyu Başlatma

```bash
python samsun.py
```

Sunucu başladıktan sonra:
- Web arayüz: http://localhost:8000
- GTFS-RT feed: http://localhost:8000/gtfs-rt/vehicle-positions

### Feed'e Erişim

#### 1. Protobuf Formatı (Standart)

```bash
# Komut satırından
curl http://localhost:8000/gtfs-rt/vehicle-positions --output positions.pb

# Python ile
import requests
from google.transit import gtfs_realtime_pb2

response = requests.get('http://localhost:8000/gtfs-rt/vehicle-positions')
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

for entity in feed.entity:
    vehicle = entity.vehicle
    print(f"Araç: {vehicle.vehicle.label}")
    print(f"Konum: {vehicle.position.latitude}, {vehicle.position.longitude}")
    print(f"Hız: {vehicle.position.speed * 3.6:.1f} km/h")
```

#### 2. JSON Formatı (Debug)

```bash
curl http://localhost:8000/gtfs-rt/vehicle-positions.json | jq .
```

#### 3. İstatistikler

```bash
curl http://localhost:8000/gtfs-rt/stats | jq .
```

## 🧪 Test

### Test Script'i Kullanma

```bash
# İnteraktif menü
python gtfs_rt_test.py

# Direkt testler
python gtfs_rt_test.py test        # Protobuf test
python gtfs_rt_test.py json        # JSON test
python gtfs_rt_test.py stats       # İstatistik test
python gtfs_rt_test.py validate    # Validasyon
python gtfs_rt_test.py monitor 120 # 120 saniye izleme
python gtfs_rt_test.py export      # GeoJSON export
python gtfs_rt_test.py all         # Tüm testler
```

### Manuel Test

```bash
# 1. Sunucu çalışıyor mu?
curl -I http://localhost:8000/gtfs-rt/vehicle-positions

# 2. Feed boş mu?
curl http://localhost:8000/gtfs-rt/stats | jq '.vehicle_count'

# 3. Koordinatlar doğru mu?
curl http://localhost:8000/gtfs-rt/stats | jq '.entities[0].position'
```

## 🔌 Transit Uygulamalarıyla Entegrasyon

### 1. OneBusAway

```yaml
# onebusaway-config.xml
<gtfs-realtime>
  <vehicle-positions>
    <url>http://your-server:8000/gtfs-rt/vehicle-positions</url>
    <refreshInterval>15</refreshInterval>
  </vehicle-positions>
</gtfs-realtime>
```

### 2. OpenTripPlanner

```json
// router-config.json
{
  "updaters": [
    {
      "type": "vehicle-positions",
      "url": "http://your-server:8000/gtfs-rt/vehicle-positions",
      "feedId": "SAMULAS",
      "frequency": 15
    }
  ]
}
```

### 3. Transitime

```properties
# transitime.properties
transitime.avl.url=http://your-server:8000/gtfs-rt/vehicle-positions
transitime.avl.feedType=GTFS_RT
transitime.avl.pollingRate=15
```

### 4. Google Transit Partner Dashboard

1. https://partnerdashboard.google.com/ adresine gidin
2. "Realtime Feed" ekleyin
3. URL: `http://your-server:8000/gtfs-rt/vehicle-positions`
4. Format: GTFS-Realtime
5. Doğrulama yapın

## 📊 Veri Yapısı

### GTFS-RT Entity Örneği

```json
{
  "id": "E2_34ABC123",
  "vehicle": {
    "trip": {
      "route_id": "E2",
      "trip_id": "trip_E2_1707394800"
    },
    "position": {
      "latitude": 41.2925,
      "longitude": 36.3315,
      "speed": 8.33,      // m/s (30 km/h)
      "bearing": 180.0    // derece
    },
    "timestamp": 1707394800,
    "vehicle": {
      "id": "34ABC123",
      "label": "34ABC123 (E2)"
    },
    "occupancy_status": "FEW_SEATS_AVAILABLE"
  }
}
```

### Doluluk Durumu Kodları

| Kod | Enum | Türkçe | Yolcu Sayısı |
|-----|------|--------|--------------|
| 0 | EMPTY | Boş | 0 |
| 1 | MANY_SEATS_AVAILABLE | Çok yer var | < 20 |
| 2 | FEW_SEATS_AVAILABLE | Az yer var | 20-40 |
| 3 | STANDING_ROOM_ONLY | Ayakta | > 40 |
| 4 | CRUSHED_STANDING_ROOM_ONLY | Sadece ayakta | > 60 |
| 5 | FULL | Dolu | > 80 |
| 6 | NOT_ACCEPTING_PASSENGERS | Yolcu almıyor | - |

## 🔍 Sorun Giderme

### Problem: Feed boş gelir

```bash
# İstatistikleri kontrol et
curl http://localhost:8000/gtfs-rt/stats

# Log'ları kontrol et (samsun.py çıktısı)
# "GTFS-RT: 0 araç güncellendi" mesajı varsa:
```

**Çözüm 1:** ASIS API'den veri gelmiyor olabilir
```python
# Test: Manuel olarak bir hat çek
from samsun import Http
http = Http()
data = http.asis('RealTimeData', lineCode='E2')
print(len(data))  # 0 ise API sorunlu
```

**Çözüm 2:** Koordinat filtresi çok dar
```python
# samsun.py'de şu satırı değiştirin:
if not (40 < lat < 43 and 34 < lon < 38):
# Şuna:
if not (39 < lat < 44 and 33 < lon < 39):
```

### Problem: Yavaş güncelleme

**Belirtiler:** 15 saniyede güncellenmesi gereken feed çok geç güncellenir

**Çözüm:** Paralel isteklere geçin
```python
# gtfs_rt_improvements.py'deki fetch_line_data_parallel() kullanın
results = await fetch_line_data_parallel(lines, max_workers=20)
```

### Problem: Duplicate entity ID

**Belirtiler:** Aynı araç birden fazla kez görünür

**Çözüm:** `seen_entities` kontrolü zaten var, ama hat kodu da eklenmeli
```python
entity_id = f"{line['code']}_{plaka}".replace(' ', '_')
```

### Problem: Transit uygulaması feed'i kabul etmiyor

**Kontrol 1:** Validasyon
```bash
python gtfs_rt_test.py validate
```

**Kontrol 2:** GTFS Static feed gerekli
Bazı uygulamalar GTFS-RT ile birlikte GTFS Static (routes.txt, stops.txt) ister.

```python
# gtfs_rt_improvements.py'deki create_gtfs_static() kullanın
```

## 📚 Ek Kaynaklar

- **GTFS-RT Spesifikasyonu:** https://gtfs.org/realtime/
- **Protocol Buffers:** https://developers.google.com/protocol-buffers
- **GTFS-RT Validator:** https://github.com/MobilityData/gtfs-realtime-validator
- **GTFS-RT Bindings:** https://github.com/MobilityData/gtfs-realtime-bindings

## 🤝 Katkı

Bu implementasyon Samsun Transit projesine özel olarak geliştirilmiştir. Geliştirmeler için:

1. Öneri/sorun bildirmek için GitHub Issues kullanın
2. Pull request gönderin
3. Dokümantasyonu güncelleyin

## 📝 Lisans

Proje lisansı ile aynıdır.

---

**Not:** Bu implementasyon gerçek zamanlı veri sağlar ancak transit yönlendirme için GTFS Static feed de gereklidir. Tam entegrasyon için her iki feed'i de sağlamanız önerilir.
