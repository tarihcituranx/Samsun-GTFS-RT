# 🚌 Samsun Transit — Google Stitch UI Tasarım Dokümanı

## Uygulama Hakkında
**Samsun Ulaşım** — Samsun ilinin akıllı toplu taşıma uygulaması.
Otobüs, tramvay, deniz ulaşımı, teleferik, turistik hat (Odak) ve havalimanı shuttle (SamAir) bilgilerini tek çatıda sunar.
Canlı araç takibi, durak sorgulama, rota planlama, fiyat bilgisi ve admin yönetim paneli içerir.

**Platform:** Flutter (Android + iOS)
**Dil:** Türkçe (tüm UI metinleri Türkçe)

---

## 🎨 Tasarım Sistemi (Design Tokens)

### Renkler
| Token | Hex | Kullanım |
|-------|-----|----------|
| `primary` | `#2979FF` | Ana butonlar, aktif tab, vurgular |
| `secondary` | `#00BFA5` | Başarı, tamamlanan, Odak tema |
| `background` | `#0A1628` | Scaffold arka plan |
| `surface` | `#152238` | Kart, input, bottom sheet |
| `surfaceAlt` | `#0F1E36` | AppBar, bottom nav, dialog |
| `surfaceLight` | `#1A2940` | Hover/pressed state |
| `error` | `#FF5252` | Hata, çevrimdışı banner |
| `warning` | `#FFAB00` | Uyarı badge |
| `text` | `#FFFFFF` | Başlık metinleri |
| `textSecondary` | `#FFFFFF` opacity 0.6 | Alt metinler |
| `textMuted` | `#546E8A` | İpucu, placeholder |
| `divider` | `#FFFFFF` opacity 0.08 | Çizgi ayırıcılar |
| `busColor` | `#1877F2` | Otobüs hatları |
| `tramColor` | `#E53935` | Tramvay hatları |
| `boatColor` | `#0D47A1` | Deniz hatları |
| `samairGreen` | `#43A047` | SamAir tema |
| `adminCyan` | `#4FC3F7` | Admin panel tema |

### Tipografi
| Style | Font | Size | Weight |
|-------|------|------|--------|
| `h1` | System (Segoe UI) | 28sp | Bold |
| `h2` | System | 22sp | Bold |
| `h3` | System | 17sp | W700 |
| `subtitle` | System | 14sp | W500 |
| `body` | System | 14sp | Normal |
| `caption` | System | 12sp | Normal |
| [chip](file:///c:/Users/mete2/OneDrive/Masa%C3%BCst%C3%BC/test/samsun_mobil/samsun_mobil_app/lib/screens/admin_screen.dart#305-315) | System | 11sp | W600 |
| `badge` | System | 10sp | W600 |

### Köşe Yarıçapları
| Token | Değer |
|-------|-------|
| `cardRadius` | 14dp |
| `buttonRadius` | 12dp |
| `chipRadius` | 20dp |
| `fabRadius` | 16dp |
| `sheetRadius` | 20dp (üst) |

### Gölgeler
- Kartlar: `elevation: 0` (flat dark theme), `border: 1px divider`
- FAB: `blur: 12, spread: 2, color: primary@30%`
- Header: `blur: 10, offset: (0,4), color: black@26%`

---

## 📱 Ekranlar (7 Tab + Splash)

### Tab 0: Splash Screen
> Uygulama açılışında 1.2 saniye gösterilir, sonra ana ekrana geçer

- **Arka plan:** Gradient `background → surfaceLight → surfaceAlt`
- **Üst-Orta (Logolar):** İki logo yan yana, yatay hizalı, gap 20dp
  - **Sol:** SBB (Samsun Büyükşehir Belediyesi) logosu — 80×80, beyaz/şeffaf, borderRadius 16
  - **Sağ:** Samulaş logosu (samulas.png) — 80×80, beyaz/şeffaf, borderRadius 16
  - Her iki logo arasında ince dikey ayırıcı (`divider` renk, 1px, 40dp yükseklik)
- **Ortada:** Uygulama ikonu — 100×100 container, gradient `primary → secondary`, borderRadius 28, box-shadow primary@30%
  - İçinde: 🚌 emoji 48pt, scale animasyonu (0.9–1.1, 800ms, reverse)
- **Alt-Orta:**
  - "Samsun Ulaşım" — 30pt bold beyaz
  - "Akıllı Toplu Taşıma" — 14pt muted, letterSpacing 2
- **En Alt (krediler):**
  - "By Turan KAYA" — 12pt, textMuted renk, letterSpacing 1.5, italic
  - Altında: ince çizgi `divider` renk, width 60dp
- **Progress:** CircularProgressIndicator 32×32, strokeWidth 2.5, color primary@70%

---

### Tab 1: 🗺️ Harita (Ana Ekran)
> Tam ekran harita, durak işaretçileri, canlı araç markerları, FAB'lar

**AppBar:**
- Başlık: "🚌 Samsun Ulaşım"
- Sağ: Eğer canlı araç varsa → kırmızı chip "X araç" (icon: directions_bus)
- Sağ: Telefon ikonu (153 info toast)

**Harita:**
- OpenStreetMap tile layer
- Samsun merkez: `41.2867, 36.33`
- Zoom: 13
- Durak markerları: Küçük mavi daireler (8×8, `primary` renk)
- Aktif araç markerları: Kırmızı oklar (yön açısıyla döndürülmüş)
- Durak tap → Bottom Sheet (Durak Detay)
- Rota çizgisi: mavi polyline

**FAB'lar (sağ alt, dikey sıra):**
1. 🎯 Konumuma Git (my_location icon)
2. 🔎 Hat Arama (search icon) → HatArama dialog
3. 🚌 Canlı Takip başlat/durdur (directions_bus icon, badge: araç sayısı)

**FAB Stili:** Glassmorphism efekti
- Background: `surfaceAlt@85%`
- Border: `1px white@15%`
- backdropFilter: blur(10)
- Size: 48×48, borderRadius 16
- Icon: white, size 22
- Badge (varsa): kırmızı daire, sağ üst, 16×16

**Çevrimdışı Banner:** (en üstte)
- Full width, error renk arka plan
- "⚠️ Çevrimdışı Mod - Canlı veriler kullanılamaz"
- Bold 13pt, beyaz, center

**Durak Bottom Sheet:** (tap on marker)
- Sheet radius 20 üst
- Durak adı (h3), Durak No (chip), Koordinatlar (caption muted)
- Yaklaşan araçlar listesi:
  - Her satır: Hat kodu chip (primary arka plan) + Kalan süre + Plaka
  - Pull-to-refresh

---

### Tab 2: 🚌 Hatlar
> Tüm otobüs/tramvay/deniz hatlarını kategorize listele

**Üst Arama Barı:**
- TextField: filled, surfaceAlt arka plan, borderRadius 12
- Hint: "Hat ara... (örn: E1, Atakum)"
- Prefix icon: search
- Debounce: 300ms

**Kategori Chip'leri:** (yatay scroll)
- Tümü | 🚌 Otobüs | 🚋 Tramvay | ⛴ Deniz | 🚡 Teleferik
- Aktif: primary arka plan, beyaz text
- Pasif: surfaceAlt arka plan, muted text

**Hat Listesi:**
- Her kart:
  - Sol: Hat kodu (büyük, bold, hat renginde) — Otobüs: busColor, Tramvay: tramColor
  - Orta: Hat adı (body), Yön bilgisi (caption muted)
  - Sağ: Chevron ikonu
  - Alt: Fiyat chip'i (varsa) — "17.00 TL" yeşil chip
- Tap → Hat Detay Bottom Sheet
  - Durak listesi (sıralı)
  - Sefer saatleri
  - "🚌 Canlı Takip Başlat" butonu
  - Fiyat detayı

---

### Tab 3: 📍 Yakınım
> Kullanıcı konumuna en yakın duraklar + yaklaşan araçlar

**Boş Durum:** (konum izni yoksa)
- İcon: location_disabled, boyut 64, muted
- "Konum izni gerekli" text
- "İzin Ver" elevated button

**Liste Görünümü:**
- Her kart:
  - Durak adı (h3)
  - Mesafe badge: "350m" chip, warning renk
  - Hat chip'leri (o duraktan geçen hatlar)
  - "Yaklaşan araç yok" veya süre listesi
- Pull-to-refresh

---

### Tab 4: 🧭 Rota
> A noktasından B noktasına toplu taşıma rotası hesapla

**Form:**
- "📍 Nereden" TextField (filled, konum ikonu prefix)
  - Otomatik doldur: "Mevcut Konum", veya yer adı yazma
- "📍 Nereye" TextField
- "🔄 Yer Değiştir" ikonu (ortada, döndürme animasyonu)
- "🧭 Rota Hesapla" büyük buton (full width, primary)

**Sonuç Kartı:**
- "X Rota Bulundu" başlık
- Her rota kartı:
  - Hat chip'leri sıralı (aktarma varsa ok ikonu aralarında)
  - Toplam süre, toplam mesafe
  - Yürüme mesafesi (icon: directions_walk)
  - "Haritada Göster" butonu → Tab 1'e geç, polyline çiz
  - "Google Maps'te Aç" link

---

### Tab 5: 📍 Odak Samsun
> Şehrin turistik ve kültürel rotaları (Şahinkaya, Ladik, vb.)

**Header:** Gradient `primary → #0D47A1`
- Sol: Başlık bloğu
  - "📍 ODAK Samsun" başlık (28pt bold beyaz)
  - "Şehrin turistik ve kültürel rotalarını keşfedin." subtitle
- **Sağ: [odak.png](file:///c:/Users/mete2/OneDrive/Masa%C3%BCst%C3%BC/test/samsun_mobil/samsun_mobil_app/assets/odak.png) logosu (60×60)** — Resmi Odak Samsun logosu, beyaz kenar, hafif gölge, borderRadius 12

**Uyarı Banner:** Amber tonu arka plan
- ⚠️ "Bu veriler Odak Samsun API'sinden alınır, güncel olmayabilir"

**Hat Listesi:**
- Her kart:
  - Sol: 🎯 emoji container (42×42, gradient secondary → #00897B, borderRadius 12)
  - Orta: Rota kodu + adı (h3), Çalışma günleri (caption muted)
  - Sağ: Chevron
  - Tap → Rota Detay
    - Durak listesi + harita
    - **🚌 Canlı Araç Takip butonu** (secondary renk, full width)
    - Canlı araç marker'ları haritada kırmızı daire + otobüs ikonu

---

### Tab 6: ✈️ SamAir
> Samsun-Çarşamba havalimanı shuttle ve uçuş bilgileri

**Header:** Gradient `samairGreen → #1B5E20`
- Sol: Başlık bloğu
  - "✈️ SamAIR" başlık (28pt bold beyaz)
  - "Samsun-Çarşamba Havalimanı Shuttle" subtitle
- **Sağ: [samair.png](file:///c:/Users/mete2/OneDrive/Masa%C3%BCst%C3%BC/test/samsun_mobil/samsun_mobil_app/assets/samair.png) logosu (60×60)** — SamAir resmi logosu, beyaz kenar, borderRadius 12

**Hat Listesi:**
- 5 hat kartı (her biri farklı güzergah)
- Kart:
  - Sol: ✈️ emoji container (42×42, gradient samairGreen → #1B5E20)
  - Hat adı
  - "Sefer Saatleri" expandable section
  - "🚌 Canlı Araç" butonu → canlı marker haritada

**Sefer Saatleri Tablosu:**
- Saat | Varış | Firma | Uçak Saati | Tarih
- Zebra stripe arka plan (surfaceAlt / surface)
- Bugünün seferleri vurgulanır (primary border)

---

### Tab 7: 🔐 Admin Panel
> Sadece admin key ile erişilebilir sunucu yönetim paneli

**Giriş Ekranı:** (authenticate olmadan)
- Ortada: 48pt admin_panel_settings ikonu, gradient container
- "Admin Girişi" başlık
- "Sunucu yönetim paneli" subtitle muted
- TextField: obscureText, "Admin Key" label, key prefix icon
- "Giriş Yap" elevated button (full width)

**Panel Ekranı:** (authenticate olduktan sonra)
- AppBar: "🔐 Admin Panel" + Logout ikonu sağda

**📊 Canlı Durum Kartı:**
- Chip grid (wrap):
  - ⏱ Uptime | 🚌 Araç sayısı | 📡 Aktif hat | 📊 ASIS/dk | 🌐 Proxy | 🕐 TR Saat
- Aktif hatlar chip listesi (varsa her biri ayrı chip)
- Yoksa: "💤 Kimse araç takip etmiyor" muted text
- 10 saniyede bir auto-refresh

**📡 GTFS-RT Ayarları Kartı:**
- Switch: "GTFS-RT Aktif" (accent: secondary)
- Dropdown: Mod → "On-Demand (Akıllı)" / "Tümü"
- Slider: Güncelleme aralığı (10–300 saniye)
- Slider: Max hat (1–50)

**✈️ SamAir Ayarları Kartı:**
- Slider: Güncelleme aralığı (1–24 saat)

**💾 Kaydet Butonu:** (full width, secondary renk)
- Başarı → yeşil snackbar "✅ Kaydedildi"
- Hata → kırmızı snackbar "❌ Başarısız"

---

## 🧩 Ortak Bileşenler

### Bottom Navigation Bar
- 7 tab: Harita | Hatlar | Yakınım | Rota | Odak | SamAIR | Admin
- Arka plan: surfaceAlt
- Aktif renk: primary
- Pasif renk: textMuted (#546E8A)
- Type: fixed (tüm label'lar görünür)
- Aktif label: 11pt W600
- Pasif label: 10pt

### Toast/Snackbar Overlay
- Üstten kayarak gelen bildirimler
- 4 varyant: info (primary), success (secondary), error (error), loading (amber)
- İkon + mesaj + otomatik kapanma (3sn)
- Stack çakışabilir (max 3)

### Glassmorphism Card
- Background: surface@85%
- Border: 1px white@10%
- BorderRadius: 14
- backdrop-filter: blur(8px)

### Chip/Badge
- Primary chip: primary arka plan, beyaz text, borderRadius 20
- Outline chip: transparent arka plan, primary border
- Mini badge: 16×16 kırmızı daire, beyaz text

### Loading State
- CircularProgressIndicator: primary renk, strokeWidth 2.5
- Skeleton loader: shimmer efekti surface → surfaceLight

---

## 📐 Responsive Kuralları
- Max content width: Cihaz genişliği
- Padding: 16dp standart, 20dp header/hero alanları
- Card margin: 8dp
- Icon size: 20–24dp standart, 14dp mini, 48dp hero
- Touch target: minimum 48×48dp

---

## 🌙 Dark Mode Only
Uygulama sadece dark mode kullanır. Light mode yok.
Tüm tasarım dark arka plan üzerine açık yazı prensibiyle çalışır.

---

## 📱 Navigasyon Akışı

```
Splash → HomeScreen (7 Tab)
  ├── Tab 0: Harita
  │   ├── Durak Tap → DurakDetay BottomSheet
  │   ├── FAB Search → Hat Seçim Dialog
  │   └── FAB Live → Canlı Araç Overlay
  ├── Tab 1: Hatlar
  │   └── Hat Tap → HatDetay BottomSheet → Canlı Takip
  ├── Tab 2: Yakınım
  │   └── Durak Tap → DurakDetay BottomSheet
  ├── Tab 3: Rota
  │   └── Sonuç → Haritada Göster (Tab 0)
  ├── Tab 4: Odak
  │   └── Rota Tap → Durak Listesi + Harita + [Canlı Araç]
  ├── Tab 5: SamAir
  │   └── Hat Tap → Sefer Saatleri + Canlı Araç
  └── Tab 6: Admin
      ├── Login → Config Panel
      └── Canlı İstatistikler
```
