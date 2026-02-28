# 🚌 Samsun GTFS & GTFS-RT

Samsun Büyükşehir Belediyesi toplu taşıma verileri — **GTFS Static** ve **GTFS Realtime** formatında.

> ⚠️ Bu proje Samsun Büyükşehir Belediyesi veya Samulaş A.Ş. ile resmi bağlantılı değildir. Veriler açık kaynaklardan sağlanmaktadır.

---

## 📊 Veri Kapsamı

| Metrik | Sayı |
|---|---|
| 🚌 Hatlar (Routes) | 108 |
| 📍 Duraklar (Stops) | 1530 |
| 🕐 Seferler (Trips) | 3773 |
| ✈️ Havalimanı Servisleri | 4 (H1-H4) |
| 🎯 Turistik Hatlar (Odak) | 11 |
| 🚠 Teleferik | 1 |
| 🛥️ Tekne/Feribot | 3 |

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────┐
│                   VERİ KAYNAKLARI                    │
├──────────┬──────────────┬──────────┬────────────────┤
│ ASİS API │ YBS API      │ Samulaş  │ Samulaş Web    │
│ (Hat/    │ (Samair/     │ V1 API   │ (Fiyat         │
│ Durak/   │ Odak/        │ (Short   │ Scraping)      │
│ Sefer)   │ Token)       │ Names)   │                │
└────┬─────┴──────┬───────┴────┬─────┴────────┬───────┘
     │            │            │              │
     ▼            ▼            ▼              ▼
┌─────────────────────────────────────────────────────┐
│              samsun.py (Master Pipeline)             │
│                                                     │
│  • fix_turkish() — Encoding düzeltme                │
│  • sanitize_id() — Türkçe→ASCII ID                  │
│  • title_case_tr() — GTFS Mixed Case                │
│  • extract_short_name() — ≤12 char                  │
│  • clean_long_name() — Prefix temizleme             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           SQLite DB (samsun_v25.db)                  │
│                                                     │
│  hat:  code + gtfs_route_id, gtfs_route_short_name  │
│  durak: id  + gtfs_stop_id, gtfs_stop_name          │
│  sefer: id  + gtfs_trip_id, gtfs_route_id           │
└──────────┬───────────────────────┬──────────────────┘
           │                       │
           ▼                       ▼
   ┌───────────────┐      ┌───────────────────┐
   │ GTFS Static   │      │ GTFS Realtime     │
   │ (.zip)        │      │ (Protobuf)        │
   │               │      │                   │
   │ • agency.txt  │      │ • Vehicle         │
   │ • routes.txt  │      │   Positions       │
   │ • stops.txt   │      │ • Occupancy       │
   │ • trips.txt   │      │ • Bearing         │
   │ • stop_times  │      │                   │
   │ • calendar    │      │                   │
   │ • feed_info   │      │                   │
   └───────────────┘      └───────────────────┘
```

## 🗄️ GTFS-Uyumlu Veritabanı

DB tablolarında hem **orijinal API alan adları** hem **GTFS karşılıkları** saklanır:

### `hat` tablosu (Routes)
| Orijinal Alan | GTFS Karşılığı | Açıklama |
|---|---|---|
| `code` | `gtfs_route_id` | ASCII-safe ID (`İ→I, Ş→S`) |
| `short_name` | `gtfs_route_short_name` | Max 12 karakter |
| `name` | `gtfs_route_long_name` | Title Case, prefix temizlenmiş |
| `tip` | `gtfs_route_type` | 0=Tramvay, 3=Otobüs, 4=Tekne, 6=Teleferik |
| `kat` | `gtfs_route_color` | Hex renk kodu |

### `durak` tablosu (Stops)
| Orijinal Alan | GTFS Karşılığı | Açıklama |
|---|---|---|
| `id` | `gtfs_stop_id` | ASCII-safe ID |
| `ad` | `gtfs_stop_name` | Türkçe Title Case |

### `sefer` tablosu (Trips)
| Orijinal Alan | GTFS Karşılığı | Açıklama |
|---|---|---|
| `id` | `gtfs_trip_id` | `T_{id}` formatında ASCII-safe |
| `hat` | `gtfs_route_id` | Route ile eşleşme |
| `gun` | `gtfs_service_id` | 1=Hİ, 2=CMT, 3=PZR, 4=HerGün |

## 🛠️ GTFS Validator Uyumluluğu

[MobilityData GTFS Validator](https://gtfs-validator.mobilitydata.org/) ile test edilmiştir.

### Uygulanan Düzeltmeler

| Uyarı | Durum | Açıklama |
|---|---|---|
| `missing_recommended_file` | ✅ | `feed_info.txt` eklendi |
| `non_ascii_or_non_printable_char` | ✅ | `sanitize_id()` ile tüm ID'ler ASCII |
| `mixed_case_recommended_field` | ✅ | `title_case_tr()` ile Mixed Case |
| `route_long_name_contains_short_name` | ✅ | `clean_long_name()` ile prefix temizleme |
| `route_short_name_too_long` | ✅ | `extract_short_name()` ile max 12 char |
| `stop_without_stop_time` | ✅ | Kullanılmayan duraklar filtrelendi |
| `unusable_trip` | ✅ | Tek duraklı trip'ler atlandı |
| `missing_feed_contact_email_and_url` | ✅ | `feed_contact_email/url` eklendi |

## 📡 API Endpoints

Uygulama çalışırken erişilebilir:

| Endpoint | Açıklama |
|---|---|
| `GET /` | Web harita arayüzü |
| `GET /gtfs/static.zip` | GTFS Static feed (ZIP) |
| `GET /gtfs-rt/vehicle-positions` | GTFS Realtime (Protobuf) |
| `GET /gtfs-rt/vehicle-positions.json` | GTFS Realtime (JSON debug) |
| `GET /api/hat` | Tüm hatlar |
| `GET /api/yakin?lat=&lon=` | Yakın duraklar |
| `GET /api/rota?lat1=&lon1=&lat2=&lon2=` | Akıllı rota |
| `GET /api/health` | Sistem durumu |

## 🚀 Kurulum

```bash
pip install fastapi uvicorn requests beautifulsoup4 gtfs-realtime-bindings
python samsun.py
```

## 📋 GTFS Dosya Yapısı

```
samsun_gtfs_v25.zip
├── agency.txt          # Samulaş A.Ş. bilgileri
├── feed_info.txt       # Feed meta bilgileri + contact
├── routes.txt          # 108 hat (ASCII ID, Title Case)
├── stops.txt           # 1530 durak (filtrelenmiş)
├── trips.txt           # 3773 sefer (unusable filtered)
├── stop_times.txt      # Mesafeye dayalı gerçekçi saatler
└── calendar.txt        # Hİ/CMT/PZR/HerGün servisleri
```

## 📝 Lisans

Bu proje eğitim ve araştırma amaçlıdır. Veriler Samsun Büyükşehir Belediyesi açık API'lerinden sağlanmaktadır.

---

**Geliştirici:** Turan KAYA  
**İletişim:** [GitHub](https://github.com/tarihcituranx)
