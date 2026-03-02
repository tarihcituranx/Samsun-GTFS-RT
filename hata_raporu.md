# Hata Raporu: 'ilce' Hat Kategorizasyonunda Eksik İlçeler

**Tarih:** 24 Mayıs 2024

**Özet:**

`samsun.py` ve `samsun - Kopya.py` dosyalarındaki `get_hat_tipi` fonksiyonu, otobüs hatlarını isimlerine göre kategorize etmektedir. 'İlçe' kategorisi için kullanılan ilçe listesinde Samsun'un bazı ilçelerinin eksik olduğu tespit edilmiştir. Bu durum, ilgili ilçelere giden otobüs hatlarının yanlış kategorize edilmesine ve sonuç olarak seyahat süresi tahminleri gibi kategoriye bağımlı diğer işlevlerin hatalı çalışmasına neden olmaktadır.

**Detaylar:**

Mevcut kodda, bir hattın 'ilce' hattı olup olmadığını kontrol eden liste aşağıdaki gibidir:

```python
['TERME','ÇARŞAMBA','BAFRA','HAVZA','LADİK','KAVAK','ASARCIK','SALIPAZARI','TEKKEKÖY']
```

**Eksik Olan ve Eklenmesi Gereken İlçeler:**

Samsun'un diğer ilçeleri incelendiğinde, şehirlerarası taşımacılık tanımına uyan aşağıdaki ilçelerin listeye eklenmesi gerekmektedir:

*   ALAÇAM
*   AYVACIK
*   VEZİRKÖPRÜ
*   YAKAKENT
*   19 MAYIS (veya ONDOKUZMAYIS)

**Beklenen Davranış:**

İsimlerinde yukarıda belirtilen eksik ilçe adlarını içeren otobüs hatlarının (`SAMSUN-ALAÇAM` gibi) 'ilce' olarak kategorize edilmesi gerekmektedir.

**Mevcut Davranış:**

Bu hatlar, ilçe listesinde bulunmadıkları için varsayılan kategori olan 'otobus' olarak sınıflandırılmaktadır. Bu durum, `samsun - Kopya.py` dosyasında görüldüğü gibi 'ilce' hatları için belirlenmiş farklı ortalama hız (`60 km/s`) ve durak bekleme süresi (`3.0 dk`) gibi parametrelerin uygulanmamasına yol açar.

**Önerilen Çözüm:**

Eksik ilçe isimlerinin `samsun.py` (satır 745) ve `samsun - Kopya.py` (satır 507) dosyalarındaki ilgili listeye eklenmesi. "19 Mayıs" ilçesi için hem "19 MAYIS" hem de "ONDOKUZMAYIS" ifadelerinin eklenmesi, ismin farklı kullanımlarına karşı robust bir çözüm sağlayacaktır.

**Düzeltilmiş Kod Örneği:**

```python
# samsun.py: line 745
if any(x in n for x in ['TERME','ÇARŞAMBA','BAFRA','HAVZA','LADİK','KAVAK','ASARCIK','SALIPAZARI','TEKKEKÖY', 'ALAÇAM', 'AYVACIK', 'VEZİRKÖPRÜ', 'YAKAKENT', '19 MAYIS', 'ONDOKUZMAYIS']): return 'ilce'
```
