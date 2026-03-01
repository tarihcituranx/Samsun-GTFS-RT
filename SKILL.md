---
name: Samsun Transit Flutter App - IDX Geliştirme Kılavuzu
description: Bu skill, Samsun Transit Flutter uygulamasını Google Project IDX ortamında nasıl derleyip çalıştıracağını ve test edeceğini açıklar. Uygulamanın mimarisini, bağımlılıklarını ve doğru test yöntemini tanımlar.
---

# Samsun Transit - Project IDX Geliştirme Kılavuzu

## Proje Yapısı

```
test/ (Kök Repo - tarihcituranx/Samsun-GTFS-RT)
├── .idx/
│   └── dev.nix              ← IDX Workspace Yapılandırması (BURADAN BAŞLA)
├── samsun_mobil/
│   └── samsun_mobil_app/    ← Flutter Android Uygulaması (ANA KLASÖR)
│       ├── lib/
│       │   ├── main.dart                    ← Uygulama giriş noktası
│       │   ├── helpers/database_helper.dart ← SQLite Şeması
│       │   ├── services/
│       │   │   ├── synchronization_service.dart ← API Veri Toplama (samsun.py portu)
│       │   │   ├── api_service.dart             ← Canlı Araç API Çağrıları
│       │   │   └── db_service.dart              ← Offline Rota Motoru
│       │   └── screens/
│       │       └── home_screen.dart  ← 3 Sekmeli Ana UI
│       ├── assets/
│       │   └── samsun_mobil.db  ← Gömülü SQLite DB (statik veri)
│       └── pubspec.yaml
└── samsun.py  ← Orijinal Python backend (referans amaçlı, ARTIK KULLANILMIYOR)
```

## Mimari Özeti

Bu uygulama **%100 Serverless (Sunucusuz)** tasarlanmıştır:

1. **Veri Katmanı:** `DatabaseHelper` → SQLite şemasını tanımlar (`hat`, `durak`, `hat_durak`, `sefer`, `fiyat`, `samair`, `odak` tabloları)
2. **Veri Toplama:** `SynchronizationService.runFullSynchronization()` → İlk açılışta ASIS ve YBS API'lerini çağırır, tüm verileri yerel SQLite'a yazar
3. **Offline Rota:** `DBService.calculateRouteLocally()` → SQL INTERSECT + Haversine ile Python'a ihtiyaç duymadan rota hesaplar
4. **Canlı Araç:** `ApiService.getDuragaYaklasanAraclar()` → ASIS SmartStations API'sini doğrudan çağırır
5. **UI:** `HomeScreen` → 3 sekme: Harita, Yakın Duraklar, Nasıl Giderim

## IDX'te Uygulamayı Çalıştırma Adımları

### 1. Workspace'i Yapılandır
IDX'te `.idx/dev.nix` dosyası zaten yapılandırılmıştır. IDX açılırken sağ alt köşede mavi bir **"Rebuild Environment"** butonu çıkarsa tıkla.

### 2. Bağımlılıkları Yükle (Otomatik)
Workspace açıldığında `flutter pub get` otomatik çalışır. Eğer çalışmazsa terminale yaz:
```bash
cd samsun_mobil/samsun_mobil_app && flutter pub get
```

### 3. Android Emülatörü Başlat
IDX'in sağ panelinde **"Preview"** (Önizleme) butonuna tıkla → **"Android"** seç. Birkaç dakika içinde sağ tarafta sanal bir Android telefon ekranı açılacak.

### 4. Uygulamayı Derleme (APK)
Terminale yaz:
```bash
cd samsun_mobil/samsun_mobil_app && flutter build apk --release
```
APK dosyası şu yolda oluşacak:
`samsun_mobil/samsun_mobil_app/build/app/outputs/flutter-apk/app-release.apk`

## ⚠️ KRİTİK: Test Yöntemi

**`flutter test` KULLANMA!** Bu uygulama `sqflite` (Native SQLite) kullanır.
Headless test ortamında `libsqlite3.so` kütüphanesi bulunamadığı için testler hata verir.
Bu bir **kod hatası DEĞİL**, test ortamının sınırıdır.

**Doğru test yöntemi:** IDX'in sağ panelindeki **Android Emülatörü** üzerinden görsel test yap.

## Önemli API Endpoints

| Servis | URL |
|--------|-----|
| ASIS Lines | `https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/Lines` |
| ASIS Stops | `https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/StopsStations` |
| ASIS Canlı | `https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/RealTimeData?lineCode=XX` |
| ASIS Akıllı Durak | `https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/SmartStations?stationId=XX` |
| ASIS Seferler | `https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/Schedules?lineCode=XX&scheduleDate=YYYY-MM-DD` |
| YBS Odak Hatlar | `https://ybs.samsun.bel.tr/service/odak_otobus_public/HatlarList` |
| YBS Samair | `https://ybs.samsun.bel.tr/service/samair_ucaksefersaatleri_public/LokasyonlarList` |

## Sık Karşılaşılan Hatalar

| Hata | Çözüm |
|------|-------|
| `libsqlite3.so not found` | `flutter test` kullanma, IDX Emülatörü ile test et |
| `android-sdk not found` | `.idx/dev.nix` dosyasındaki yapılandırmayı kontrol et, "Rebuild" butona bas |
| `Assets not found: samsun_mobil.db` | `pubspec.yaml`'daki `assets:` bölümünü kontrol et |
| `package samsun_transit not found` | `pubspec.yaml`'daki `name:` alanının `samsun_transit` olduğundan emin ol |
| `path not found` | `samsun_mobil/samsun_mobil_app` klasöründe olduğundan emin ol |
