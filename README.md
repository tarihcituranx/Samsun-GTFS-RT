# 🚌 Kentli — Samsun Ulaşım Uygulaması

Samsun Büyükşehir Belediyesi toplu taşıma verileri için gerçek zamanlı web uygulaması.

> ⚠️ Bu proje Samsun Büyükşehir Belediyesi veya Samulaş A.Ş. ile resmi bağlantılı değildir.

---

## 📐 Proje Mimarisi

```
Samsun-GTFS-RT/
├── samsun.py          # FastAPI backend (tek dosya, tüm API endpointleri)
├── samsun_v26.db      # SQLite veritabanı (ANA VERİ KAYNAĞI)
├── samsun.db          # BOŞ — kullanılmaz, ignore edilebilir
├── frontend/          # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── lib/api.ts                  # Tüm API çağrıları
│   │   ├── contexts/TransitContext.tsx  # Global state (selectedLine, vehicles, stops...)
│   │   ├── components/transit/
│   │   │   ├── LinesTab.tsx            # Hat listesi → setSelectedLine() ile açar
│   │   │   ├── LineDetail.tsx          # Hat detayı (gerçek API verisi)
│   │   │   ├── TabContent.tsx          # Tab router + selectedLine → LineDetail yönlendirme
│   │   │   ├── DetailPanel.tsx         # Sağ panel (sadece durak/araç, hat DEĞİL)
│   │   │   ├── MapCanvas.tsx           # Leaflet harita
│   │   │   └── ...
│   │   └── pages/Index.tsx             # Ana layout
│   └── dist/                           # npm run build çıktısı (backend serve eder)
├── static/            # Leaflet CSS/JS + görseller
└── requirements.txt
```

---

## 🗄️ Veritabanı

**Ana DB:** `samsun_v26.db` — kod içinde `DB = "samsun_v26.db"`

| Tablo | İçerik |
|---|---|
| `hat` | 108 hat (otobüs/tramvay/ekspres...) |
| `durak` | 1630 durak |
| `hat_durak` | Hat-durak ilişkileri (4444 kayıt) |
| `sefer` | Sefer saatleri |
| `fiyat` | Hat ücretleri |
| `odak` | 11 turistik hat |
| `samair` | 5 havayolu hattı |
| `hat_yon` | Hat yönleri (gidiş/dönüş) |

---

## 🚀 Lokal Çalıştırma

```bash
# Backend
pip install -r requirements.txt
python samsun.py          # → http://localhost:8000

# Frontend (dev, ayrı terminal)
cd frontend
npm install
npm run dev               # → http://localhost:8080 (/api proxy → :8000)
```

---

## 🌐 Render Deployment

**Build Command:**
```
pip install -r requirements.txt && cd frontend && npm install && npm run build
```

**Start Command:**
```
uvicorn samsun:app --host 0.0.0.0 --port $PORT
```

> `samsun_v26.db` repo'da bulunmalıdır. `samsun.db` boş bir dosyadır, silinebilir.

---

## 📡 API Endpointleri

| Endpoint | Açıklama |
|---|---|
| `GET /api/hat` | Tüm hatlar (durak_sayisi + tam_fiyat dahil) |
| `GET /api/hat/info/{code}` | Tek hat bilgisi |
| `GET /api/hat/durak/{code}` | Hattın durakları |
| `GET /api/hat/arac/{code}` | Canlı araçlar |
| `GET /api/hat/sefer/{code}` | Sefer saatleri |
| `GET /api/hat/fiyat/{code}` | Ücret bilgisi |
| `GET /api/hat/{code}/yonler` | Gidiş/Dönüş yönleri |
| `GET /api/odak` | Odak (turistik) hatlar |
| `GET /api/samair` | Samair hatları |
| `GET /api/tum_duraklar` | Tüm duraklar (harita) |
| `GET /api/durak_ara?q=` | Durak arama |
| `GET /api/durak_panel/{kod}` | Durağa yaklaşan araçlar (ETA) |
| `GET /api/rota?lat1&lon1&lat2&lon2` | Rota planlama |
| `GET /api/hava` | Hava durumu |
| `GET /api/health` | Sağlık kontrolü |
| `GET /api/proxy/schedules` | Resmi tarife |
| `GET /api/proxy/smart_stations` | Tramvay istasyon verisi |
| `GET /api/proxy/realtime` | ASIS canlı araç |
| `GET /gtfs/static.zip` | GTFS Static paketi |
| `GET /gtfs-rt/vehicle-positions` | GTFS Realtime (Protobuf) |

---

## 🐛 Düzeltilen Hatalar

### v26.1 — Frontend/Backend Senkronizasyonu

| # | Hata | Nerede | Düzeltme |
|---|---|---|---|
| 1 | Hat seçince **siyah ekran** | `LinesTab.tsx` | `setDetailItem` → `setSelectedLine` olarak değiştirildi |
| 2 | `LineDetail.tsx` **hiç render edilmiyordu** | `TabContent.tsx` | `selectedLine` varsa `LineDetail` göster eklendi |
| 3 | Desktop panel **mock/rastgele veri** gösteriyordu | `DetailPanel.tsx` | Hat tipi için sağ panel devre dışı; `LineDetail` sol panelde gösteriliyor |
| 4 | Hat listesinde **0 durak / ₺0** | `samsun.py` + `api.ts` | `/api/hat` artık `durak_sayisi` ve `tam_fiyat` döndürüyor; `api.ts` okuyor |
| 5 | Hat renkleri **yanlış** | `api.ts` | Backend'den gelen `renk` hex alanı artık kullanılıyor |

---

## 📊 Veri Özeti

| | Sayı |
|---|---|
| 🚌 Hatlar | 108 |
| 📍 Duraklar | 1630 |
| 🎯 Odak Hatları | 11 |
| ✈️ Samair | 5 |

---

## ⚙️ Teknolojiler

- **Backend:** Python 3.11, FastAPI, SQLite3, uvicorn
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Leaflet, Framer Motion, shadcn/ui
- **State:** React Context API
- **Harita:** Leaflet.js (CartoDB dark/light tiles)
- **Canlı Veri:** ASIS API, YBS API, Odak API
