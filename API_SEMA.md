# Samsun Transit - API ve Sistem Şeması

## 📌 Genel Bakış

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SAMSUN TRANSIT v25                               │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (HTML/JS)  ←→  FastAPI (8000)  ←→  SQLite (samsun_v25.db) │
│                              ↓                       ↓               │
│              ┌───────────────┼───────────────┐       ↓               │
│              ↓               ↓               ↓   GTFS Static Feed    │
│         ASIS API        YBS API       Samulaş Web    (v5)            │
│    (api.samsun.bel.tr) (ybs.samsun)  (samulas.com.tr)                │
└─────────────────────────────────────────────────────────────────────┘

```

---

## 🌐 Dış API Kaynakları

### 1. ASIS API
**Adres:** `https://api.samsun.bel.tr/OHSSoapToJson/api/Asis`

| Endpoint | Parametre | Dönen | Açıklama |
|----------|-----------|-------|----------|
| `/Lines` | - | `[{lineCode, lineName}]` | Tüm otobüs hatları |
| `/OrjLines` | - | `[{lineCode, lineName}]` | Orjinal hat listesi (turistik dahil) |
| `/StopsStations` | `lineCode` | `[{stopId, stopName, latitude, longitude}]` | Hat durakları |
| `/RealTimeData` | `lineCode` | `[{vehiclePlate, latitude, longitude, speed}]` | Canlı araç konumları |
| `/Schedules` | `lineCode, scheduleDate` | `[{departureTime}]` | Sefer saatleri |
| `/LineDirections` | `lineCode` | Yön bilgisi | Gidiş/Dönüş |
| `/SmartStations` | `stationId` | Akıllı durak bilgisi | - |

### 2. Doğrudan API'ler (YBS Devre Dışı, ODAK & SamAir Doğrudan Bağlantı)
YBS servisleri kaldırıldığı için doğrudan belediyenin kendi sitelerinin API'leri Cloudflare bypass ve yedek proxy rotasyonu ile kullanılmaktadır.

#### 🛡️ Proxy ve Cloudflare Bypass Mimarisi
* **Tek Türk Proxy Yapılandırması:** Render ortamında çevre değişkenleri (`PROXY_HOST`, `PROXY_PORT`, `PROXY_USER`, `PROXY_PASS`) üzerinden tanımlanan tek bir Türk IP'li proxy birincil olarak kullanılır.
* **Bypass & Rotasyon Mantığı:**
  * ODAK ve SamAir doğrudan API'leri Cloudflare korumalıdır. İstekler `cloudscraper` kütüphanesi yardımıyla atlatılır.
  * İstekler başarısız olduğunda 3 denemeli retry mekanizması devreye girer:
    * **1. ve 2. Deneme:** Tanımlı olan birincil Türk proxy'si (ve varsa `proxy_https_auth.csv` içindeki yedek proxy'ler) sırayla kullanılır.
    * **3. Deneme (Fallback):** Doğrudan bağlantı (proxy'siz) denenerek WAF'ın bypass edilmesi amaçlanır.

#### ODAK Doğrudan API
**Adres:** `https://odak.samsun.bel.tr/doit.php`

| Action | Parametreler | Dönen | Açıklama |
|--------|--------------|-------|----------|
| `HatlarAllList` | - | `[{id, hat_adi, hat_aciklama, kod, gunler}]` | Tüm odak hatları |
| `GetHatDuraklar` | `hatid` | `[{id, ad, kod, sira, lat, lon, fiyat, fiyat_ogr}]` | Odak hat durakları |

#### SamAir Doğrudan API
**Adres:** `https://samair.samsun.bel.tr/api.php`

| m | a (Action) | Parametreler | Dönen | Açıklama |
|---|------------|--------------|-------|----------|
| `samair_public` | `DuraklarList` | - | `[{durak_adi, durak_fiyat, lat, lon}]` | Samair durakları |
| `samair_public` | `UcakSeferSaatleri` | `hatid` | `[{saat, varis_saati, ucak_firmasi}]` | Uçuş seferleri |

### 3. Samulaş Web Scraping
**Adres:** `https://samulas.com.tr`

| Sayfa | Veri |
|-------|------|
| `/otobusler?page=N` | Hat listesi linkler |
| `/otobus-detay/X` | Fiyat (tam, öğrenci, indirimli) |

---

## 🗄️ Veritabanı Şeması (SQLite)

### Ana Tablolar

```sql
-- Hat bilgileri
hat(code TEXT PRIMARY KEY, name TEXT, tip TEXT, kat TEXT, alias TEXT)

-- Hat durakları (ASIS)
hat_durak(id INTEGER, hat TEXT, ad TEXT, kod TEXT, sira INTEGER, lat REAL, lon REAL)

-- Sefer saatleri
sefer(id INTEGER, hat TEXT, saat TEXT, gun_tipi TEXT)

-- Fiyatlar
fiyat(id INTEGER, kaynak TEXT, hat_adi TEXT, hat_code TEXT, 
      tam_fiyat REAL, indirimli_fiyat REAL, ogrenci_fiyat REAL,
      aktarma1 TEXT, aktarma2 REAL, link TEXT, guncelleme TEXT)
```

### Odak Tabloları

```sql
-- Turistik hatlar
odak(id TEXT PRIMARY KEY, ad TEXT, kod TEXT, gunler TEXT)

-- Odak durakları
odak_durak(id INTEGER, hat TEXT, ad TEXT, kod TEXT, sira INTEGER, 
           lat REAL, lon REAL, fiyat REAL, fiyat_ogr REAL)
```

### Samair Tabloları

```sql
-- Havalimanı hatları
samair(id INTEGER PRIMARY KEY, kod TEXT, ad TEXT)

-- Samair durakları
samair_durak(id INTEGER, hat INTEGER, ad TEXT, sira INTEGER, 
             lat REAL, lon REAL, fiyat TEXT)

-- Uçuş seferleri
samair_sefer(id INTEGER, hat INTEGER, tarih TEXT, saat TEXT, 
             varis TEXT, firma TEXT, ucak_kodu TEXT)
```

---

## 🔌 Local API Endpointleri (FastAPI)

### Temel Hatlar

| Endpoint | Method | Dönen | Açıklama |
|----------|--------|-------|----------|
| `/` | GET | HTML | Ana sayfa UI |
| `/api/hat` | GET | `[{code, name, tip, kat}]` | Tüm hatlar |
| `/api/hat/info/{code}` | GET | `{code, name, tip, kat, alias}` | Hat detayı |
| `/api/hat/durak/{code}` | GET | `[{ad, kod, sira, lat, lon}]` | Hat durakları |
| `/api/hat/sefer/{code}` | GET | `[{saat, gun_tipi}]` | Sefer saatleri |
| `/api/hat/fiyat/{code}` | GET | `{tam_fiyat, indirimli_fiyat, aktarma1}` | Fiyat bilgisi |
| `/api/hat/arac/{code}` | GET | `[{plate, lat, lon, speed}]` | Canlı araçlar |
| `/api/hat/esles/{code}` | GET | `{code}` | Gidiş↔Dönüş eşleştirme |

### Odak (Turistik)

| Endpoint | Method | Parametre | Dönen | Açıklama |
|----------|--------|-----------|-------|----------|
| `/api/odak` | GET | - | `[{id, ad, kod}]` | Tüm Odak hatları (DB'den) |
| `/api/odak/{id}/durak` | GET | - | `[{ad, fiyat, lat, lon}]` | Odak durakları (DB'den) |
| `/api/proxy_odak` | GET | - | `[{id, kod, ad, gunler}]` | Doğrudan API'den normalize edilmiş tüm odak hatları listesi (Proxy + WAF Aşar) |
| `/api/proxy_odak_araclar` | GET | `hatid` | `{"active": bool, "vehicles": [...]}` | ASIS üzerinden dinamik eşleştirilen canlı araç konumları |

### Samair (Havalimanı)

| Endpoint | Method | Parametre | Dönen | Açıklama |
|----------|--------|-----------|-------|----------|
| `/api/samair` | GET | - | `[{id, kod, ad}]` | Tüm Samair hatları (DB'den) |
| `/api/samair/{id}/durak` | GET | - | `[{ad, fiyat, lat, lon}]` | Samair durakları (DB'den) |
| `/api/samair/{id}/sefer` | GET | - | `{data: [{saat, firma}]}` | Uçuş seferleri (DB'den) |
| `/api/proxy_samair_saatler` | GET | `hatid` | `[{saat, varis, firma, ucak_saat, tarih, gun_format}]` | Doğrudan API'den normalize edilmiş uçuş sefer saatleri (Proxy + WAF Aşar) |
| `/api/proxy_samair_araclar` | GET | - | `[{lat, lon, plate, speed, lineCode}]` | ASIS üzerinden filtrelenmiş canlı SamAir araç konumları |

### Konum Tabanlı

| Endpoint | Method | Parametre | Açıklama |
|----------|--------|-----------|----------|
| `/api/yakin` | GET | `lat, lon` | Yakındaki duraklar |
| `/api/rota` | GET | `lat1, lon1, lat2, lon2` | Yol tarifi |
| `/api/durak_panel/{kod}` | GET | `kod` | Durak detayı |

### 📱 Mobil API Proxy Geçitleri
Bu endpoint'ler, istemci (mobil/web) tarafında CORS ve WAF engellerini aşmak amacıyla ASIS API çağrılarını sunucu üzerinden tüneller:

| Endpoint | Method | Parametre | Açıklama |
|----------|--------|-----------|----------|
| `/api/proxy/lines` | GET | - | Alfabetik ve etiketli tüm hatlar |
| `/api/proxy/orjlines` | GET | - | Orijinal hat listesi |
| `/api/proxy/smart_stations` | GET | `stationId` | Akıllı durak bilgisi (yaklaşan araçlar) |
| `/api/proxy/realtime` | GET | `lineCode` | Belirli bir hattın canlı araç konumları |
| `/api/proxy/stops_stations` | GET | `lineCode` | Belirli bir hattın durakları |
| `/api/proxy/line_directions` | GET | `lineCode` | Belirli bir hattın gidiş/dönüş yön bilgisi |
| `/api/proxy/schedules` | GET | `lineCode, scheduleDate` | Belirli bir hattın sefer saatleri |
| `/api/debug/proxy` | GET | - | Proxy bağlantı testi (ASIS/YBS durumları) |

---

## 🔧 Kod Sınıfları (samsun.py)

### Http Sınıfı
```python
class Http:
    def asis(self, ep, **p)                     # ASIS API çağrısı
    def odak_direct(self, action, **params)     # ODAK doğrudan API çağrısı (Cloudscraper bypass)
    def samair_direct(self, action, **params)   # Samair doğrudan API çağrısı (Cloudscraper bypass)
    def get_next_proxy(self, attempt=1)         # 3. denemede direct fallback yapan proxy seçici
    def ybs_token(self)                         # Pasif (YBS kaldırıldı)
    def ybs(self, method, submethod=None, **kw) # Pasif (YBS kaldırıldı)
```

### Database Sınıfı
```python
class Database:
    def connect(self)          # DB bağlan (SQLite ve Supabase REST RPC desteği / db_seed.json otomatik seed)
    def ex(self, q, p=())      # Execute
    def get(self, q, p=())     # Select çoklu
    def one(self, q, p=())     # Select tek
    def guncelleme_gerekli()   # 7 gün kontrol
```

### Collector Sınıfı
```python
class Collector:
    def veri_cek(self)         # Tüm veri güncelle
    def _hatlar(self)          # ASIS Lines + OrjLines
    def _duraklar(self)        # ASIS StopsStations
    def _seferler(self)        # ASIS Schedules
    def _samulas_fiyatlar(self)# Web scraping
    def _odak(self)            # ODAK doğrudan API üzerinden turistik hatları günceller
    def _samair_duraklar(self) # Samair doğrudan API üzerinden durak ve seferleri günceller
    def canli(self, kod)       # RealTimeData
```

---

## 🔄 Veri Akışı

```
                    BAŞLANGIÇ
                        ↓
           ┌───────────────────────┐
           │  guncelleme_gerekli() │  (7 günde 1)
           └───────────┬───────────┘
                       ↓
    ┌──────────────────┼──────────────────┐
    ↓                  ↓                  ↓
 ASIS API        Doğrudan API'ler     Web Scrape
    ↓            (ODAK & SamAir)          ↓
 Lines                 ↓            samulas.com.tr
 OrjLines        odak_direct        /otobusler
 StopsStations   samair_direct      /otobus-detay
 Schedules             ↓                  ↓
    ↓           ┌──────┴──────┐           ↓
    ↓           ↓             ↓           ↓
hat            odak        samair      fiyat
hat_durak      odak_durak  samair_durak
sefer                      samair_sefer
                                
           └───────────────────────────────┘
                        ↓
             Supabase DB / SQLite
                        ↓
               FastAPI Endpoints
                        ↓
             UI (Browser & Mobile)
```

---

## ⚠️ Bilinen Eşleştirmeler

### HAT_ALIAS (OrjLines → Kısa Kod)
```python
'SAMULAŞ EKSPRES 2-GİDİŞ' → 'E2'
'SAMULAŞ EKSPRES 7-GİDİŞ' → 'E7'
'15/A BÜYÜK CAMİ-SOĞUKSU' → '15'
'28' → 'R2'
```

### SAMAIR_HATLAR (ID Mapping)
```python
1: H1 OMÜ-HAVALİMANI    → ybs_hatid: [3]
2: H2 TTTM-HAVALİMANI   → ybs_hatid: [4]
3: H3 BAFRA-HAVALİMANI  → ybs_hatid: [5]
4: H4 ÇARŞAMBA-HAVALİMANI → ybs_hatid: [9]
```

---

## 📊 Mevcut Durum

| Kategori | Değer |
|----------|-------|
| Toplam Hat | 107 |
| Fiyat Eşleşme | 74/74 (%100) |
| Odak Koordinatlı | 67/72 (%93) |
| Samair Fiyatlı | 90/209 (%43) |
| Samair Sefer | 130 |

---

## 📝 Veri Tutarsızlıkları ve Düzeltmeler

API kaynaklarından gelen verilerde bazı tutarsızlıklar tespit edilmiştir. 
Bu durum düzeltilmiş olup, ileride benzer durumlarla karşılaşılırsa aşağıdaki eşleştirme referans alınabilir.

### Odak (YBS API) - Gidiş/Dönüş Eşleştirmesi

YBS API'de hat isimleri ile durak sıraları uyumsuz gelebilir. Düzeltme yapılırken:

| YBS Hat ID | YBS'deki İsim | Düzeltilmiş İsim | İlk Durak | Son Durak |
|------------|---------------|------------------|-----------|-----------|
| 1 | Şahinkaya Kanyonu Gidiş | **Dönüş** | Şahinkaya | TTTM |
| 2 | Şahinkaya Kanyonu Dönüş | **Gidiş** | TTTM | Şahinkaya |
| 3 | Kızılırmak Deltası Gidiş | **Dönüş** | Kızılırmak | TTTM |
| 4 | Kızılırmak Deltası Dönüş | **Gidiş** | TTTM | Kızılırmak |
| 5 | Ayvacık Baraj Gölü Gidiş | **Dönüş** | Ayvacık | TTTM |
| 6 | Ayvacık Baraj Gölü Dönüş | **Gidiş** | TTTM | Ayvacık |

> **Not:** "Gidiş" = Şehir merkezinden (TTTM) hedefe giden hat.  
> "Dönüş" = Hedeften şehir merkezine (TTTM) dönen hat.

### Samair (YBS API) - Durak Eşleştirmesi

Samair duraklarında da benzer durum söz konusudur. ASIS StopsStations referans alınarak koordinatlar eşleştirilmiştir.

### Düzeltme Scriptleri

- `odak_isim_duzelt.py` - Odak gidiş/dönüş isim düzeltmesi
- `odak_koordinat_ekle.py` - ASIS'ten koordinat eşleştirmesi
- `samair_fiyat_zenginlestir.py` - Samair fiyat düzeltmesi

---

## 🚀 Son Eklemeler (v25.1)

### 1. Tramvay Koordinat Düzeltmesi (CSV Entegrasyonu)
- **Kaynak:** `ulasim.samulas.co.trRaylı Sistem kopyası kopyası- Samsun Hafif Raylı Sistem Hattı.csv`
- **İşleyiş:** `samsun.py` başlatıldığında bu CSV dosyası okunur ve durak koordinatları belleğe yüklenir.
- **Dinamik Düzeltme:** `/api/hat/durak/{code}` endpoint'i, veritabanından gelen veriyi bellekteki CSV verisiyle (eşleşme varsa) anlık olarak değiştirerek sunar. Bu sayede veritabanı orijinalliği korunurken, haritada doğru konumlar gösterilir.

### 2. UI Geliştirmeleri ve Bilgi Kutucukları
Özel hatlar için `shL` (Show Line) fonksiyonu içerisinde HTML enjeksiyonu ile detaylı bilgi kutucukları eklenmiştir:

| Hat | Özellikler |
|-----|------------|
| **Samsunum-1** | Sefer saatleri, Fiyat (200 TL), Hava durumu uyarısı |
| **Samsunum-2** | "ÇALIŞMAMAKTADIR" uyarısı (DSİ çalışması) |
| **Samsunum-3** | "Doldukça Kalkar" bilgisi |
| **Altınkaya** | Feribot araç/yolcu fiyat tarifesi, Kuruçay/Kayıkbaşı kalkış saatleri |
| **Teleferik** | Çalışma saatleri (10:30-22:00), Tarihçe |
| **Tramvay** | Sefer Sıklığı Tabloları (Hafta İçi, Cmt, Pazar tab'lı yapı), İletişim |

### 3. Tramvay Sefer Sıklığı Tabloları
Tramvay detay ekranında, kullanıcıların sefer sıklıklarını kolayca görebilmesi için sekmeli (Tab) yapıya sahip HTML tabloları entegre edilmiştir.
- **Sekmeler:** Hafta İçi, Cumartesi, Pazar
- **İçerik:** Saat aralıklarına göre sefer sıklığı (dk) ve ilk/son sefer saatleri.

### 4. Güncel Fiyatlandırma (Hardcoded)
Bazı hatların fiyatları, API'den gelmediği veya güncel olmadığı için `samsun.py` içerisinde sabitlenmiştir:
- **Tramvay:** 26.50 TL (Tam)
- **Teleferik:** 25.00 TL
- **Samsunum:** 200.00 TL / 150.00 TL (Öğrenci)
- **Altınkaya:** 15.00 TL (Yolcu), 75-580 TL (Araç)

---

## 🚌 GTFS Static Feed Oluşturucu (v5)

Google Maps ve diğer harita servisleri için standart veri formatı (GTFS) üreten modül sisteme entegre edilmiştir.

### 📌 Özellikler (v5 - Kusursuz Sürüm)
1.  **Tam Otomatik Üretim:** `samsun_v25.db` veritabanından güncel veriyi çeker.
2.  **Kusursuz Validasyon:** MobilityData GTFS Validator üzerinde **0 Error, 0 Warning**.
3.  **Çoklu Dil Desteği (`translations.txt`):**
    - 🇬🇧 İngilizce (en)
    - 🇩🇪 Almanca (de)
    - 🇫🇷 Fransızca (fr)
    - 🇷🇺 Rusça (ru)
    - 🇸🇦 Arapça (ar)
    - *Hat isimleri ve duraklar için otomatik çeviri.*
4.  **Akıllı Filtreleme:** Kullanılmayan duraklar ve hatalı shape dosyaları otomatik temizlenir.
5.  **Detaylı Bilgi:** `wheelchair_accessible`, `bikes_allowed`, `trip_headsign` gibi opsiyonel alanlar doludur.

### 📂 Üretilen Dosyalar
| Dosya | İçerik | Özellik |
|-------|--------|---------|
| `agency.txt` | Samulaş Kurumsal Bilgileri | `agency_email`, `agency_fare_url` ekli |
| `routes.txt` | Hat Listesi | Title Case isimlendirme, Renk kodları |
| `trips.txt` | Sefer Bilgileri | `trip_headsign` (Tabela), Bisiklet/Engelli durumu |
| `stops.txt` | Durak Konumları | Kullanılmayanlar filtrelenmiş |
| `stop_times.txt` | Tahmini Varışlar | Mesafe bazlı gerçekçi simülasyon |
| `shapes.txt` | Güzergah Çizgileri | `foreign_key_violation` korumalı |
| `calendar.txt` | Çalışma Günleri | `trip_coverage` uyarısı için optimize |
| `feed_info.txt` | Yayıncı Bilgisi | SBB İletişim, v5.0 sürüm etiketi |
| `attributions.txt`| Emeği Geçenler | Samulaş Data + SBB Otorite |
| `translations.txt`| Çeviriler | 5 Dilde Hat ve Kurum isimleri |

### 🚀 Kullanım
```bash
python create_gtfs_static_v5.py
# Çıktı: samsun_gtfs_static.zip
```

