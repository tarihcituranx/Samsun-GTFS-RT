import json

try:
    with open('asis_samsun_swagger.json', 'r', encoding='utf-8') as f:
        schema = json.load(f)

    doc_markdown = """**Resmi şema tarafımca düzenlenmiştir:** Turan KAYA
**Orijinal Şema:** [https://api.samsun.bel.tr/OHSSoapToJson/swagger/index.html](https://api.samsun.bel.tr/OHSSoapToJson/swagger/index.html)

**SAMSUN TRANSIT - SUPER APP (MASTER API DOKÜMANTASYONU)**
Bu API şeması, Samsun Büyükşehir Belediyesine ait tüm toplu taşıma, akıllı şehir bileşenleri, havaalanı transferleri ve turistik hatların verilerinin Samsun Transit ana projemizde (samsun.py) nasıl çekilip, nasıl işlendiğini anlatan kapsamlı bir "Master Pipeline Rekor" (Yedek) belgesidir.

---

### 1️⃣ Veri Kaynakları ve Bileşenler (Data Sources)

**A. ASİS API (SOAP to JSON Adaptörü)**
- Sistemin ana omurgasıdır. Bütün standart otobüs hatları, tramvay saatleri ve 1600'den fazla durağın temel verisi buradan beslenir.
- **Lines / OrjLines:** Otobüs hatlarının id'leri (Örn: 15, E2, R2) ve uzun isimleri (Örn: `13 KAMALI TOKİ - SOĞUKSU`) çekilir.
- **StopsStations:** Araçların durak koordinatlarını verir.
- **RealTimeData & Schedules:** Araçların anlık lokasyonlarını, plaka numaralarını ve gün içerisindeki operasyon planlarını sunar.  

**B. YBS (Yönetim Bilgi Sistemi) API'leri**
- Diğer özel ve turistik hizmetlerin bağlı olduğu, ayrı bir kimlik doğrulama gerektiren özel sistemdir.
- **Token Mekanizması (Quirk):** Sistemdeki uç noktalara (Örn: Samair veya Odak) istek atabilmek için öncelikle `getGuestToken` adresinden misafir bileti alınır. Bu biletin (token) ömrü 200 saniye ile sınırlıdır. Bu sebeple "samsun.py" içinde özel bir _Token-Pool (Self-Caching)_ mekanizması ile tokenlar süreleri bitene kadar hafızada tutulup her 3 dakikada bir arka planda yenilenir.
- **Samair API'leri:** `samair_ucaksefersaatleri_public` ve `samair_duraklar_public` uç noktalarından Havalimanı otobüslerinin hareket durumları çekilir.
- **Odak Samsun API'si:** Turistik hatlar (Ayvacık Barajı, Şahinkaya Kanyonu vb.) bu noktadan `odakSamsun_Crud` metodu üzerinden çekilir. 

**C. Samulaş Web Sitesi (Scraping)**
- API'lerin doğrudan sağlayamadığı "Bilet Fiyatları" `samulas.com.tr/otobusler` adresinden Beautifulsoup HTML ayrıştırıcısı ile toplanarak fiyat veri tabanına yazılır. E1, E2, E3 gibi kodlarla API ID'leri veritabanı aşamasında birbirleriyle eşleştirilir.

---

### 2️⃣ Pipeline: Veri Geliştirme (Mapping) & Bug Çözümleri (Quirks)

Canlı ortam verileri sisteme işlenirken birçok veri tutarsızlığı on the fly (çalışma anında) çözümlenmektedir:

**1. ID Mapping Operasyonları**
Samair uçuşlarını çekerken Belediye veritabanı ID'leri ile UI (Kullanıcı Arayüzü) ID'leri arasında şu eşleştirmeler (Map) uygulanır:  
- `H1 OMÜ` = YBS ID `3`  
- `H2 TTTM` = YBS ID `4`
- `H3 BAFRA` = YBS ID `5`  
- `H4 ÇARŞAMBA` = YBS ID `9`  
- Express hat kodları alias olarak düzenlenir (Örn: `SAMULAŞ EKSPRES 2-DÖNÜŞ` => `E2`).

**2. Turistik Hatlarda 'Gidiş/Dönüş' API Hatası Çözümü (Quirk)**
Odak API'si Şahinkaya, Kızılırmak ve Ayvacık rotalarında "Gidiş" ve "Dönüş" text değerlerini tam ters formatta (Hatalı) döndürmektedir. `samsun.py` içinde `ODAK_ISIM_DUZELTME` tablosu kullanılarak, durak numaraları (1-2 ve 3-4 gibi) üzerinden "Eğer ilk durak TTTM ise bu aslında Gidiş'tir" mantığı çalıştırılır ve isimler veri tabanına düzeltilmiş haliyle kaydedilir.

**3. Odak API Referer Koruma Duvarı (WAF Bypass)**
`odakSamsun_Crud` metoduna yapılan tüm isteklerde sistemin yetkisiz girişi engellememesi adına HTTP Client başlığına `Referer: https://odak.samsun.bel.tr/` maskesi uygulanır.

**4. Karakter Encoding Probleminin Giderilmesi**
Veriler Windows-1254 altyapısından bozuk encoding ile JSON formatında (Örn: `¦, ‹, Ý` = `İ`) dönebilmektedir. Bunun için `fix_turkish` gibi custom bir regex tabanlı çevirmen filtre sistemiyle Türkçe harf stabilizasyonu sağlanır.

---

### 3️⃣ Veritabanı ve Çıktılar

Bütün bu ASİS, YBS ve Web verileri SQLite (`samsun_v25.db`) veritabanında "hat, durak, guzergah, sefer, canli" tablolarında senkronize edilir. 
Bu temiz ve standardize edilmiş tablo sayesinde standart **(1) GTFS Formatında** ve **(2) GTFS Realtime Formatında** dosyalar üretilebilmekte, böylece Samsun Transit projemiz uluslararası ulaşım analiz altyapıları ile (Google Maps, Moovit vb) tam uyumlu bir ekosisteme kavuşturulmaktadır."""

    schema['info']['description'] = doc_markdown

    with open('asis_samsun_swagger.json', 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print("Belge açıklamaları başarıyla Swagger şemasına enjekte edildi!")
except Exception as e:
    print(f"Hata oluştu: {e}")
