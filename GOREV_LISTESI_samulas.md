# 📋 GÖREV LİSTESİ — Samsun Ulaşım Sistemi (samulas.html)
**Hazırlayan:** Turan KAYA  
**Tarih:** Mart 2026  
**Durum:** Yapılacaklar — YZ tarafından uygulanacak

---

## ⚠️ ÖNEMLİ BAĞLAM

Bu uygulama Samsun Büyükşehir Belediyesi veya Samulaş'ın **resmi uygulaması değildir.**  
Geliştirici: **Turan KAYA** — bağımsız, gönüllü bir vatandaş projesidir.  
2026 yılı itibarıyla Türkiye'de geçerli **KVKK (6698 sayılı Kanun)** ve **Çerez Yönetmeliği** hükümlerine uygunluk sağlanmalıdır.

---

## 🐛 KRİTİK HATALAR (Önce Bunları Düzelt)

### BUG-1: `weaI` nesnesi içinde tekrarlanan anahtar
```javascript
// SATIR ~179 — GKR anahtarı iki kez tanımlanmış, ikincisi birincinin üzerine yazar
const weaI={...'GKR':'wind',...'GKR':'wind'}; // ← TEKERRÜRLİ, temizle
```
**Düzeltme:** İkinci `'GKR':'wind'` kaydını sil.

---

### BUG-2: `showDisclaimer()` ve `closeInfoModal()` farklı localStorage anahtarı kullanıyor
```javascript
// DOMContentLoaded'da:
localStorage.getItem('hideInfoModal')   // ← 'hideInfoModal' kullanıyor

// showDisclaimer() fonksiyonunda:
localStorage.getItem('disclaimerShown') // ← 'disclaimerShown' kullanıyor — FARKLI ANAHTAR!
```
**Sonuç:** Kullanıcı "Bir daha gösterme" dese bile modal tekrar açılır.  
**Düzeltme:** Her iki yerde de tek tip `'hideInfoModal'` anahtarı kullan. `showDisclaimer()` fonksiyonunu kaldır, `init()` içinde sadece DOMContentLoaded mantığını bırak.

---

### BUG-3: `goRota()` fonksiyonu var olmayan `#rTo` elementini arıyor
```javascript
function goRota(lat, lon, name) {
    ...
    document.getElementById('rTo').value = lat+','+lon; // ← 'rTo' diye bir input YOK!
}
```
**Gerçek input id'leri:** `rotaStart` ve `rotaInput`  
**Düzeltme:** `document.getElementById('rTo')` → `document.getElementById('rotaInput')` olarak değiştir. Değeri `lat+','+lon` yerine `name` (mekan adı) olarak set et, koordinatları `data-lat` / `data-lon` attribute olarak sakla.

---

### BUG-4: `K.odak` ve `K.havalimani` kategorileri için renk `'transparent'`
```javascript
odak:{..., c:'transparent'},
havalimani:{..., c:'transparent'},
```
**Sonuç:** Bu kategorilerdeki otobüs ikonları haritada görünmez (şeffaf arka plan).  
**Düzeltme:**
- `odak` için `c:'#16a34a'` (yeşil)
- `havalimani` için `c:'#dc2626'` (kırmızı)

---

### BUG-5: `setInterval(positionToggle, 500)` performans sorunu
```javascript
setInterval(positionToggle, 500); // Her 500ms'de DOM ölçümü — gereksiz
```
**Düzeltme:** `setInterval`'ı kaldır. Sadece `window.addEventListener('resize', positionToggle)` ve panel açılıp kapandığında manuel çağır.

---

### BUG-6: `shSD()` içinde `upV(kod, ...)` çağrısı — `kod` undefined olabilir
```javascript
async function shSD(id, kod) {
    ...
    upV(kod, '#9333ea'); // ← hat listesinde kod yoksa undefined geçer
}
```
**Düzeltme:** Çağrıdan önce `if(kod)` kontrolü ekle.

---

## 📝 YASAL UYARI METİNLERİ — İYİLEŞTİRME

### GÖREV-L1: `warn-bar` (üst sarı uyarı bandı) metnini güncelle

**Mevcut:**
```
⚠️ YASAL UYARI: Resmi uygulama değildir. Veriler açık kaynaklardan sağlanmaktadır.
```

**Yeni metin:**
```html
<div class="warn-bar">
  ⚠️ Bu uygulama Samsun Büyükşehir Belediyesi veya Samulaş'ın resmi uygulaması 
  <strong>değildir</strong>. Turan KAYA tarafından bağımsız olarak geliştirilmiştir. 
  Veriler açık kaynaklardan derlenmekte olup doğruluğu garanti edilmez.
</div>
```

---

### GÖREV-L2: `pnl-footer` (alt bilgi alanı) metnini güncelle

**Mevcut:**
```
⚠️ YASAL UYARI: Değerler anlık değişebilir. Resmi uygulama değildir.
```

**Yeni:**
```html
<div class="pnl-footer">
  Bu uygulama <strong>gayri resmi</strong>, bağımsız bir vatandaş projesidir. 
  Geliştirici: <strong>Turan KAYA</strong><br>
  Veriler anlık değişebilir; kesin bilgi için lütfen resmi kanalları kullanın.<br>
  📞 Samsun içi <a href="tel:153">153</a> &nbsp;|&nbsp; 
  Samsun dışı <a href="tel:03624311012">0362 431 10 12</a><br>
  <div style="display:flex;gap:12px;justify-content:center;align-items:center;margin-top:4px">
    <a href="https://github.com/tarihcituranx" target="_blank" rel="noopener noreferrer">
      <!-- GitHub SVG ikonu burada kalacak -->
      tarihcituranx
    </a>
    <a href="https://samsunkesfet.com" target="_blank" rel="noopener noreferrer">🏛️ samsunkesfet.com</a>
    <a href="#" onclick="showKvkk()" style="color:var(--text3);font-size:.6rem">🔒 KVKK</a>
    <a href="#" onclick="showCerez()" style="color:var(--text3);font-size:.6rem">🍪 Çerez Politikası</a>
  </div>
</div>
```

---

### GÖREV-L3: `infoModal` (açılış bildirimi) metnini güncelle

**Mevcut başlık:** `⚠️ Önemli Bilgilendirme`

**Yeni tam içerik:**
```html
<h3 style="color:var(--orange);margin-bottom:10px">⚠️ Önemli Bilgilendirme</h3>
<p style="font-size:0.85rem;color:var(--text);margin-bottom:10px">
  Bu uygulama <strong>Turan KAYA</strong> tarafından geliştirilen, 
  <strong>Samsun Büyükşehir Belediyesi veya Samulaş ile hiçbir resmi bağlantısı 
  bulunmayan</strong> bağımsız bir vatandaş projesidir.
</p>
<p style="font-size:0.75rem;color:var(--text2);margin-bottom:10px">
  Gösterilen fiyatlar, sefer saatleri ve araç konumları tahmini veya gecikmiş olabilir.
  Özellikle <strong>Odak (Turistik)</strong> ve tekne hatlarında fiyatlar farklılık 
  gösterebilir. Kesin bilgi için lütfen araç kaptanlarına veya resmi hatta danışın.
</p>
<p style="font-size:0.75rem;color:var(--text2);margin-bottom:15px">
  Bu uygulamayı kullanmaya devam ederek 
  <a href="#" onclick="showKvkk()" style="color:var(--accent)">KVKK Aydınlatma Metni</a>'ni 
  ve <a href="#" onclick="showCerez()" style="color:var(--accent)">Çerez Politikası</a>'nı 
  okuduğunuzu kabul etmiş sayılırsınız.<br><br>
  📞 Samsun içi: <a href="tel:153" style="color:var(--accent)">153</a><br>
  📞 Samsun dışı: <a href="tel:03624311012" style="color:var(--accent)">0362 431 10 12</a>
</p>
```

---

## 🔒 KVKK UYUMLULUĞU (2026 Türkiye)

### GÖREV-K1: KVKK Aydınlatma Metni Modal'ı Ekle

`</body>` kapatma etiketinden hemen önce aşağıdaki modal HTML'ini ekle:

```html
<!-- KVKK Aydınlatma Metni Modalı -->
<div id="kvkkModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;
  background:rgba(0,0,0,0.6);z-index:10000;align-items:center;justify-content:center;
  padding:20px;backdrop-filter:blur(4px)">
  <div style="background:var(--panel);width:100%;max-width:480px;border-radius:16px;
    padding:24px;box-shadow:var(--shadow2);border:1px solid var(--card-border);
    max-height:85vh;overflow-y:auto">
    
    <h3 style="margin-bottom:12px;color:var(--text)">🔒 KVKK Aydınlatma Metni</h3>
    <p style="font-size:0.7rem;color:var(--text2);margin-bottom:8px">
      <strong>Veri Sorumlusu:</strong> Turan KAYA (Bireysel Geliştirici)<br>
      <strong>İletişim:</strong> github.com/tarihcituranx<br>
      <strong>Son Güncelleme:</strong> Mart 2026
    </p>

    <h4 style="color:var(--accent);margin:12px 0 4px">İşlenen Veriler</h4>
    <ul style="font-size:0.72rem;color:var(--text2);margin-left:20px;line-height:1.6">
      <li><strong>Konum verisi:</strong> Yakınımdaki duraklar ve rota hesaplama için yalnızca 
        oturum süresince tarayıcı belleğinde tutulur, sunucuya <em>gönderilmez</em>.</li>
      <li><strong>localStorage anahtarları:</strong> Tema tercihi, bildirim gizleme tercihi ve 
        uygulama ayarları yalnızca kendi cihazınızda saklanır.</li>
      <li><strong>Üçüncü taraf hizmetler:</strong>
        <ul style="margin-left:15px;margin-top:4px">
          <li>OpenStreetMap / CartoDB — harita kutucukları (anonim istekler)</li>
          <li>Nominatim (OSM) — tersine adres çözümleme (konum koordinatı gönderilir)</li>
          <li>OSRM — rota hesaplama (koordinatlar gönderilir)</li>
          <li>Google Fonts — font yükleme (IP adresi Google'a iletilir)</li>
        </ul>
      </li>
    </ul>

    <h4 style="color:var(--accent);margin:12px 0 4px">Haklarınız (KVKK Md. 11)</h4>
    <p style="font-size:0.72rem;color:var(--text2);line-height:1.6">
      Kişisel verilerinize ilişkin bilgi alma, düzeltme ve silme haklarınız mevcuttur. 
      Uygulama sunucu tarafında kişisel veri <strong>depolamadığından</strong>, 
      cihazınızdaki localStorage verilerini tarayıcı ayarlarından silebilirsiniz.
    </p>

    <h4 style="color:var(--accent);margin:12px 0 4px">Yasal Dayanak</h4>
    <p style="font-size:0.72rem;color:var(--text2)">
      6698 sayılı Kişisel Verilerin Korunması Kanunu ve ilgili ikincil mevzuat.
    </p>

    <button onclick="document.getElementById('kvkkModal').style.display='none'"
      style="margin-top:16px;width:100%;padding:10px;background:var(--accent);color:#fff;
      border:none;border-radius:8px;cursor:pointer;font-weight:600;font-family:inherit">
      Anladım, Kapat
    </button>
  </div>
</div>
```

---

### GÖREV-K2: Çerez / localStorage Politikası Modal'ı Ekle

KVKK modalının hemen altına ekle:

```html
<!-- Çerez Politikası Modalı -->
<div id="cerezModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;
  background:rgba(0,0,0,0.6);z-index:10000;align-items:center;justify-content:center;
  padding:20px;backdrop-filter:blur(4px)">
  <div style="background:var(--panel);width:100%;max-width:480px;border-radius:16px;
    padding:24px;box-shadow:var(--shadow2);border:1px solid var(--card-border);
    max-height:85vh;overflow-y:auto">
    
    <h3 style="margin-bottom:12px;color:var(--text)">🍪 Çerez ve Yerel Depolama Politikası</h3>
    <p style="font-size:0.7rem;color:var(--text2);margin-bottom:8px">
      <strong>Son Güncelleme:</strong> Mart 2026
    </p>

    <p style="font-size:0.72rem;color:var(--text2);line-height:1.6;margin-bottom:10px">
      Bu uygulama HTTP çerezi (cookie) <strong>kullanmamaktadır.</strong> 
      Bunun yerine yalnızca tarayıcınızın <code>localStorage</code> alanı kullanılır.
    </p>

    <h4 style="color:var(--accent);margin:10px 0 4px">Saklanan Veriler</h4>
    <table style="width:100%;font-size:0.65rem;border-collapse:collapse;color:var(--text2)">
      <thead>
        <tr style="background:var(--bg3);text-align:left">
          <th style="padding:6px;border:1px solid var(--card-border)">Anahtar</th>
          <th style="padding:6px;border:1px solid var(--card-border)">Amaç</th>
          <th style="padding:6px;border:1px solid var(--card-border)">Süre</th>
        </tr>
      </thead>
      <tbody>
        <tr><td style="padding:5px;border:1px solid var(--card-border)">theme</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Aydınlık/Karanlık tema tercihi</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Süresiz (manuel silinene dek)</td></tr>
        <tr><td style="padding:5px;border:1px solid var(--card-border)">hideInfoModal</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Açılış bildirimini gizle tercihi</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Süresiz</td></tr>
        <tr><td style="padding:5px;border:1px solid var(--card-border)">showHasilat</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Günlük hasılat gösterme ayarı</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Süresiz</td></tr>
        <tr><td style="padding:5px;border:1px solid var(--card-border)">showLabels</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Durak isimlerini göster</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Süresiz</td></tr>
        <tr><td style="padding:5px;border:1px solid var(--card-border)">showRoute</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Güzergah çizgisini göster</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Süresiz</td></tr>
        <tr><td style="padding:5px;border:1px solid var(--card-border)">autoRefresh</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Otomatik yenileme</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Süresiz</td></tr>
        <tr><td style="padding:5px;border:1px solid var(--card-border)">showAllStops</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Tüm durakları haritada göster</td>
            <td style="padding:5px;border:1px solid var(--card-border)">Süresiz</td></tr>
      </tbody>
    </table>

    <h4 style="color:var(--orange);margin:12px 0 4px">Üçüncü Taraf Veri Transferleri</h4>
    <ul style="font-size:0.68rem;color:var(--text2);margin-left:18px;line-height:1.7">
      <li><strong>CartoDB / OpenStreetMap:</strong> Harita görüntüleme — IP + koordinat paylaşımı</li>
      <li><strong>Nominatim (OSM):</strong> Adres çözümleme — GPS koordinatı paylaşımı</li>
      <li><strong>OSRM (project-osrm.org):</strong> Rota hesaplama — rota koordinatları paylaşımı</li>
      <li><strong>Google Fonts:</strong> Font yükleme — IP adresi paylaşımı</li>
    </ul>
    <p style="font-size:0.65rem;color:var(--text3);margin-top:8px">
      Bu hizmetlerin GDPR/KVKK uyumluluğu kendi gizlilik politikalarına tabidir.
    </p>

    <h4 style="color:var(--green);margin:12px 0 4px">Verileri Nasıl Silersiniz?</h4>
    <p style="font-size:0.72rem;color:var(--text2)">
      Ayarlar (⚙️) → "Varsayılana Çevir" butonu tüm localStorage tercihlerini siler.<br>
      Veya tarayıcı ayarları → Site Verileri → Bu siteyi temizle.
    </p>

    <button onclick="document.getElementById('cerezModal').style.display='none'"
      style="margin-top:16px;width:100%;padding:10px;background:var(--accent);color:#fff;
      border:none;border-radius:8px;cursor:pointer;font-weight:600;font-family:inherit">
      Anladım, Kapat
    </button>
  </div>
</div>
```

---

### GÖREV-K3: JavaScript'e `showKvkk()` ve `showCerez()` fonksiyonları ekle

`<script>` bloğunun başına (veya `init()` çağrısından önce) ekle:

```javascript
function showKvkk() {
    document.getElementById('kvkkModal').style.display = 'flex';
    return false;
}
function showCerez() {
    document.getElementById('cerezModal').style.display = 'flex';
    return false;
}
```

---

### GÖREV-K4: Çerez Onay Banner'ı Ekle (İlk Ziyaret)

`<body>` açılışından hemen sonra ekle:

```html
<!-- Çerez/localStorage Onay Banner -->
<div id="cerezBanner" style="display:none;position:fixed;bottom:0;left:0;right:0;
  z-index:9998;background:var(--panel);border-top:1px solid var(--card-border);
  padding:14px 20px;box-shadow:0 -4px 24px rgba(0,0,0,0.15);
  backdrop-filter:blur(12px);display:flex;flex-wrap:wrap;
  align-items:center;justify-content:space-between;gap:10px">
  <div style="font-size:0.72rem;color:var(--text);flex:1;min-width:200px">
    🍪 Bu uygulama yalnızca işlevsellik için <strong>localStorage</strong> kullanır. 
    Kişisel veriniz sunucuya aktarılmaz. 
    <a href="#" onclick="showCerez()" style="color:var(--accent)">Çerez Politikası</a> · 
    <a href="#" onclick="showKvkk()" style="color:var(--accent)">KVKK</a>
  </div>
  <div style="display:flex;gap:8px">
    <button onclick="cerezReddet()" 
      style="padding:8px 16px;background:var(--bg3);border:1px solid var(--card-border);
      border-radius:8px;cursor:pointer;font-size:0.72rem;font-weight:600;
      color:var(--text);font-family:inherit">
      Yalnızca Zorunlu
    </button>
    <button onclick="cerezKabul()" 
      style="padding:8px 16px;background:var(--accent);color:#fff;border:none;
      border-radius:8px;cursor:pointer;font-size:0.72rem;font-weight:600;
      font-family:inherit">
      Tamam, Anladım
    </button>
  </div>
</div>
```

**Banner için JavaScript fonksiyonları** (`init()` çağrısından önce ekle):

```javascript
function cerezKabul() {
    localStorage.setItem('cerezOnay', '1');
    document.getElementById('cerezBanner').style.display = 'none';
}
function cerezReddet() {
    // Sadece zorunlu localStorage anahtarları kalır (tema vs.)
    localStorage.setItem('cerezOnay', 'zorunlu');
    document.getElementById('cerezBanner').style.display = 'none';
}
function checkCerezOnay() {
    const onay = localStorage.getItem('cerezOnay');
    if (!onay) {
        document.getElementById('cerezBanner').style.display = 'flex';
    }
}
```

`init()` fonksiyonunun en sonuna şunu ekle:
```javascript
checkCerezOnay();
```

---

## ✏️ METİN / UX İYİLEŞTİRMELERİ

### GÖREV-U1: `<title>` etiketini güncelle
```html
<!-- Mevcut -->
<title>🇹🇷 🚌 Samsun Ulaşım Sistemi</title>

<!-- Yeni -->
<title>Samsun Ulaşım Rehberi — Gayri Resmi | Turan KAYA</title>
```

---

### GÖREV-U2: `<meta>` açıklama ve author etiketi ekle (`<head>` içine)
```html
<meta name="description" content="Samsun toplu taşıma hatları, canlı araç takibi ve güzergah planlama. Gayri resmi, bağımsız vatandaş projesi. Geliştirici: Turan KAYA">
<meta name="author" content="Turan KAYA">
<meta name="robots" content="index, follow">
```

---

### GÖREV-U3: Tüm harici `<a>` linklerine `rel="noopener noreferrer"` ekle

Hedef: `target="_blank"` içeren tüm `<a>` etiketleri.  
Güvenlik açığını kapatır (tabnabbing saldırısı önlemi).

Örnek:
```html
<!-- Mevcut -->
<a href="https://github.com/tarihcituranx" target="_blank">

<!-- Düzeltilmiş -->
<a href="https://github.com/tarihcituranx" target="_blank" rel="noopener noreferrer">
```

---

### GÖREV-U4: Ayarlar panelindeki "resetSettings()" fonksiyonu `cerezOnay` anahtarını da temizlemeli

```javascript
function resetSettings() {
    // Mevcut satırlar...
    localStorage.removeItem('cerezOnay'); // ← BU SATIRI EKLE
    // ...geri kalan mevcut kod
}
```

---

### GÖREV-U5: `infoModal`'da "Bir daha gösterme" checkbox'ının `id`'si ile `closeInfoModal()` uyumunu kontrol et

`chkGosterme` id'li checkbox `closeInfoModal()` içinde `'hideInfoModal'` anahtarı kullanıyor.  
`showDisclaimer()` fonksiyonu ise `'disclaimerShown'` anahtarına bakıyor — BUG-2 ile bağlantılı.  
**Düzeltme:** `showDisclaimer()` fonksiyonunu tamamen sil, `DOMContentLoaded` bloğunu tek kontrol noktası olarak bırak.

---

## 📁 UYGULAMA SIRASI (YZ için öneri)

```
1. BUG-1  → weaI'daki tekrarlı anahtarı sil
2. BUG-2  → localStorage anahtar tutarsızlığını düzelt + showDisclaimer() kaldır
3. BUG-3  → goRota() içindeki '#rTo' referansını düzelt
4. BUG-4  → K.odak ve K.havalimani renklerini güncelle
5. BUG-5  → setInterval(positionToggle, 500) kaldır
6. BUG-6  → shSD içinde upV çağrısına 'if(kod)' guard ekle
7. GÖREV-L1 → warn-bar metnini güncelle
8. GÖREV-L2 → pnl-footer metnini güncelle (KVKK/Çerez linkleri dahil)
9. GÖREV-L3 → infoModal içeriğini güncelle
10. GÖREV-K3 → showKvkk() + showCerez() fonksiyonlarını ekle
11. GÖREV-K4 → Çerez banner HTML + JS ekle + init() içine checkCerezOnay() çağrısı
12. GÖREV-K1 → KVKK modal HTML ekle
13. GÖREV-K2 → Çerez Politikası modal HTML ekle
14. GÖREV-U1 → <title> güncelle
15. GÖREV-U2 → <meta> etiketleri ekle
16. GÖREV-U3 → target="_blank" linklere rel="noopener noreferrer" ekle
17. GÖREV-U4 → resetSettings() içine cerezOnay temizliği ekle
18. GÖREV-U5 → infoModal/showDisclaimer tutarsızlığı (BUG-2 ile birleştirildi)
```

---

## 📌 EK NOTLAR

- **Google Fonts** (`fonts.googleapis.com`) dışarıya IP gönderiyor. KVKK'ya tam uyum için fontları lokal olarak barındırmak tercih edilir. Kısa vadede mevcut yapı kabul edilebilir seviyededir.  
- **Nominatim kullanım koşulları:** OSM'nin `nominatim.openstreetmap.org` servisi yüksek hacimli kullanımda `User-Agent` başlığı gerektirir. Fetch çağrısına `headers: { 'User-Agent': 'SamsunUlasimRehberi/1.0 (github.com/tarihcituranx)' }` eklenebilir.  
- Uygulama kendi sunucusunda çalıştığı sürece (`/api/...` endpoint'leri) sunucu tarafında log tutulup tutulmadığı da KVKK kapsamında değerlendirilerek aydınlatma metnine yansıtılmalıdır.

---

*Bu görev listesi Turan KAYA adına hazırlanmıştır. Tüm değişiklikler `samulas.html` dosyası üzerinde uygulanmalıdır.*
