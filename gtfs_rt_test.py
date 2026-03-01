#!/usr/bin/env python3
"""
GTFS Realtime Test ve Kullanım Script'i
========================================

Bu script Samsun Transit GTFS-RT feed'ini test eder ve görselleştirir.

Kullanım:
    python gtfs_rt_test.py
"""

import requests
import time
from datetime import datetime
from google.transit import gtfs_realtime_pb2

# GTFS-RT Feed URL'si
FEED_URL = "http://localhost:8000/gtfs-rt/vehicle-positions"
JSON_URL = "http://localhost:8000/gtfs-rt/vehicle-positions.json"
STATS_URL = "http://localhost:8000/gtfs-rt/stats"


def test_protobuf_feed():
    """Protobuf formatındaki feed'i test et"""
    print("🚌 GTFS Realtime Feed Test")
    print("=" * 60)
    
    try:
        # Feed'i indir
        response = requests.get(FEED_URL, timeout=10)
        response.raise_for_status()
        
        # Parse et
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        # Header bilgileri
        print(f"\n📋 Feed Bilgileri:")
        print(f"  Versiyon: {feed.header.gtfs_realtime_version}")
        print(f"  Zaman: {datetime.fromtimestamp(feed.header.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Araç Sayısı: {len(feed.entity)}")
        
        # İlk 10 aracı göster
        print(f"\n🚍 Araçlar (İlk 10):")
        print("-" * 60)
        
        for i, entity in enumerate(feed.entity[:10], 1):
            v = entity.vehicle
            print(f"\n{i}. Araç:")
            print(f"   ID: {entity.id}")
            print(f"   Hat: {v.trip.route_id}")
            print(f"   Plaka: {v.vehicle.label}")
            print(f"   Konum: {v.position.latitude:.6f}, {v.position.longitude:.6f}")
            print(f"   Hız: {v.position.speed * 3.6:.1f} km/h")
            print(f"   Yön: {v.position.bearing:.0f}°")
            
            if v.HasField('occupancy_status'):
                doluluk = {
                    0: "Bilinmiyor",
                    1: "Boş",
                    2: "Çok yer var",
                    3: "Az yer var",
                    4: "Ayakta",
                    5: "Sadece ayakta",
                    6: "Dolu",
                    7: "Yolcu almıyor"
                }.get(v.occupancy_status, "Bilinmiyor")
                print(f"   Doluluk: {doluluk}")
        
        print("\n" + "=" * 60)
        print(f"✅ Test başarılı! Toplam {len(feed.entity)} araç bulundu.\n")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Bağlantı hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Parse hatası: {e}")
        return False


def test_json_feed():
    """JSON formatındaki feed'i test et (debug)"""
    print("\n📊 JSON Feed Test")
    print("=" * 60)
    
    try:
        response = requests.get(JSON_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        header = data.get('header', {})
        entities = data.get('entity', [])
        
        print(f"\nHeader:")
        print(f"  Versiyon: {header.get('gtfsRealtimeVersion', 'N/A')}")
        print(f"  Timestamp: {header.get('timestamp', 'N/A')}")
        
        print(f"\nToplam Araç: {len(entities)}")
        
        if entities:
            print("\nÖrnek Entity (İlk):")
            print(entities[0])
        
        print("\n✅ JSON test başarılı!\n")
        return True
        
    except Exception as e:
        print(f"❌ JSON test hatası: {e}\n")
        return False


def test_stats():
    """İstatistik endpoint'ini test et"""
    print("\n📈 İstatistik Test")
    print("=" * 60)
    
    try:
        response = requests.get(STATS_URL, timeout=10)
        response.raise_for_status()
        stats = response.json()
        
        print(f"\nFeed Versiyonu: {stats.get('feed_version')}")
        print(f"Son Güncelleme: {stats.get('last_update')}")
        print(f"Araç Sayısı: {stats.get('vehicle_count')}")
        
        print("\nAraçlar:")
        for entity in stats.get('entities', [])[:5]:
            print(f"  • {entity['vehicle']} ({entity['route']})")
            print(f"    Konum: {entity['position']['lat']:.6f}, {entity['position']['lon']:.6f}")
            print(f"    Hız: {entity['position']['speed_ms'] * 3.6:.1f} km/h")
        
        print("\n✅ İstatistik test başarılı!\n")
        return True
        
    except Exception as e:
        print(f"❌ İstatistik test hatası: {e}\n")
        return False


def monitor_feed(duration_seconds=60, interval=15):
    """
    Feed'i belirli süre boyunca izle
    
    Args:
        duration_seconds: İzleme süresi (saniye)
        interval: Güncelleme aralığı (saniye)
    """
    print(f"\n🔍 Feed İzleme Modu ({duration_seconds} saniye)")
    print("=" * 60)
    
    start_time = time.time()
    iteration = 0
    
    while time.time() - start_time < duration_seconds:
        iteration += 1
        print(f"\n⏱️  İterasyon {iteration} - {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            response = requests.get(FEED_URL, timeout=5)
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            # Hat bazlı istatistik
            routes = {}
            for entity in feed.entity:
                route = entity.vehicle.trip.route_id
                routes[route] = routes.get(route, 0) + 1
            
            print(f"  Toplam Araç: {len(feed.entity)}")
            print(f"  Aktif Hatlar: {len(routes)}")
            
            # En çok aracı olan hatlar
            top_routes = sorted(routes.items(), key=lambda x: x[1], reverse=True)[:5]
            print("\n  En Aktif Hatlar:")
            for route, count in top_routes:
                print(f"    {route}: {count} araç")
            
        except Exception as e:
            print(f"  ❌ Hata: {e}")
        
        time.sleep(interval)
    
    print("\n✅ İzleme tamamlandı!\n")


def export_to_geojson():
    """
    Araç konumlarını GeoJSON formatına çevir
    """
    print("\n🗺️  GeoJSON Export")
    print("=" * 60)
    
    try:
        response = requests.get(FEED_URL, timeout=10)
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for entity in feed.entity:
            v = entity.vehicle
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [v.position.longitude, v.position.latitude]
                },
                "properties": {
                    "id": entity.id,
                    "route": v.trip.route_id,
                    "vehicle": v.vehicle.label,
                    "speed_kmh": round(v.position.speed * 3.6, 1),
                    "bearing": v.position.bearing,
                    "timestamp": v.timestamp
                }
            }
            
            geojson["features"].append(feature)
        
        # Dosyaya yaz
        import json
        filename = f"vehicles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ GeoJSON export tamamlandı: {filename}")
        print(f"   Toplam {len(geojson['features'])} araç\n")
        
        return filename
        
    except Exception as e:
        print(f"❌ Export hatası: {e}\n")
        return None


def validate_feed():
    """
    GTFS-RT feed'i doğrula (validasyon kuralları)
    """
    print("\n✓ Feed Validasyon")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    try:
        response = requests.get(FEED_URL, timeout=10)
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        # 1. Header kontrolü
        if not feed.header.gtfs_realtime_version:
            errors.append("Header'da GTFS-RT versiyonu eksik")
        
        if not feed.header.timestamp:
            errors.append("Header'da timestamp eksik")
        
        # 2. Entity kontrolleri
        for entity in feed.entity:
            if not entity.id:
                errors.append(f"Entity ID eksik")
            
            if entity.HasField('vehicle'):
                v = entity.vehicle
                
                # Trip kontrolü
                if not v.trip.route_id:
                    warnings.append(f"Entity {entity.id}: route_id eksik")
                
                # Pozisyon kontrolü
                if not v.position.latitude or not v.position.longitude:
                    errors.append(f"Entity {entity.id}: Konum bilgisi eksik")
                
                # Koordinat aralığı
                if not (40 < v.position.latitude < 43):
                    warnings.append(f"Entity {entity.id}: Latitude Samsun dışında ({v.position.latitude})")
                
                if not (34 < v.position.longitude < 38):
                    warnings.append(f"Entity {entity.id}: Longitude Samsun dışında ({v.position.longitude})")
                
                # Hız kontrolü
                if v.position.speed < 0:
                    errors.append(f"Entity {entity.id}: Negatif hız")
                
                if v.position.speed > 50:  # 50 m/s = 180 km/h
                    warnings.append(f"Entity {entity.id}: Çok yüksek hız ({v.position.speed * 3.6:.0f} km/h)")
        
        # Sonuçlar
        print(f"\n📊 Validasyon Sonuçları:")
        print(f"  Toplam Entity: {len(feed.entity)}")
        print(f"  Hatalar: {len(errors)}")
        print(f"  Uyarılar: {len(warnings)}")
        
        if errors:
            print("\n❌ HATALAR:")
            for error in errors[:10]:  # İlk 10 hata
                print(f"  • {error}")
        
        if warnings:
            print("\n⚠️  UYARILAR:")
            for warning in warnings[:10]:  # İlk 10 uyarı
                print(f"  • {warning}")
        
        if not errors and not warnings:
            print("\n✅ Feed geçerli! Hata veya uyarı yok.\n")
        
    except Exception as e:
        print(f"❌ Validasyon hatası: {e}\n")


def interactive_menu():
    """İnteraktif menü"""
    while True:
        print("\n" + "=" * 60)
        print("🚌 GTFS Realtime Test Menüsü")
        print("=" * 60)
        print("\n1. Protobuf Feed Test")
        print("2. JSON Feed Test")
        print("3. İstatistik Test")
        print("4. Feed İzleme (60 saniye)")
        print("5. GeoJSON Export")
        print("6. Feed Validasyon")
        print("7. Tüm Testleri Çalıştır")
        print("0. Çıkış")
        
        choice = input("\nSeçiminiz: ").strip()
        
        if choice == '1':
            test_protobuf_feed()
        elif choice == '2':
            test_json_feed()
        elif choice == '3':
            test_stats()
        elif choice == '4':
            monitor_feed()
        elif choice == '5':
            export_to_geojson()
        elif choice == '6':
            validate_feed()
        elif choice == '7':
            test_protobuf_feed()
            test_json_feed()
            test_stats()
            validate_feed()
        elif choice == '0':
            print("\n👋 Görüşmek üzere!\n")
            break
        else:
            print("\n❌ Geçersiz seçim!")


if __name__ == "__main__":
    import sys
    
    # Komut satırı argümanı kontrolü
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'test':
            test_protobuf_feed()
        elif cmd == 'json':
            test_json_feed()
        elif cmd == 'stats':
            test_stats()
        elif cmd == 'monitor':
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            monitor_feed(duration_seconds=duration)
        elif cmd == 'export':
            export_to_geojson()
        elif cmd == 'validate':
            validate_feed()
        elif cmd == 'all':
            test_protobuf_feed()
            test_json_feed()
            test_stats()
            validate_feed()
        else:
            print(f"Bilinmeyen komut: {cmd}")
            print("\nKullanım:")
            print("  python gtfs_rt_test.py [test|json|stats|monitor|export|validate|all]")
    else:
        # İnteraktif mod
        interactive_menu()
