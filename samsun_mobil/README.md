# Samsun Mobil ve Akıllı Saat (Serverless Projesi)

Bu proje, ana `samsun.py` sisteminin API verilerini ve yerel SQLite veritabanı yedeğini kullanarak, tamamen bağımsız ve **sunucusuz (serverless)** çalışan istemci tabanlı uygulamalardır.

## Alt Projeler

1. `samsun_mobil_app` (Android Flutter): 
   - Harita üzerinden durak listeleme.
   - ASIS API ile doğrudan cihazdan sunucusuz irtibat kurma.
   - **Çevrimdışı İnecek Durak Uyarısı (GPS):** Otobüste uyurken internet olmadan GPS ile takip edip durağa gelmeden titretir.
   - **Akıllı Hazırlanma Alarmı:** Her sabah işe giderken favori otobüsün durağa yaklaşmasına X dakika kala sizi titreşimle uyarır.

2. `samsun_watch_app` (HarmonyOS Saatler):
   - Huawei Watch GT3 SE ve diğer Wearable seriler.
   - Doğrudan Wi-Fi / Bluetooth üstünden favori duraklardaki yaklaşan otobüsleri okur.
   - Telefondan izole otonom çalışabilir.

## Nasıl Başlatılır? (Android / Flutter)
1. Bilgisayarınıza [Flutter SDK](https://docs.flutter.dev/get-started/install) yükleyin.
2. `samsun_mobil/samsun_mobil_app` dizinine girin:
   ```bash
   flutter pub get
   flutter run
   ```
3. Uygulama açılışta `assets/samsun_mobil.db` dosyasını telefonun hafızasına kopyalayacaktır.

## Veritabanı Nasıl Güncellenir?
Eğer ana sunucudaki durak koordinatları veya YBS Samair fiyatları değişirse, sadece:
```bash
cd samsun_mobil
python create_mobile_db.py
```
Komutunu çalıştırmak yeterlidir. Bu betik, ana büyük SQLite veritabanını okur ve mobil uygulamanın içine **birebir, otomatik ve sıkıştırılmış (-%65)** olarak gömer.
