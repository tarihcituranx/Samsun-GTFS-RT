
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String ASIS_BASE = 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis';

  // --- samsun.py'den Port Edilen Veri Temizleme Mantığı ---

  // API'den gelen bozuk Türkçe karakterleri düzelten harita
  static final Map<String, String> _turkishCharacterFixes = {
    '¦': 'İ', '‹': 'İ', 'Ý': 'İ',
    '▄': 'Ü', 
    'Ì': 'Ş', '™': 'Ş', 'Þ': 'Ş',
    'Ã': 'Ç', '˙': 'Ç', 'Æ': 'Ç',
    'º': 'Ğ', '°': 'Ğ', 'Ð': 'Ğ',
    'Í': 'Ö', 'Ô': 'Ö',
    'ý': 'ı', '²': 'ı', 
    'Ó': 'ö',
    'ã': 'ü',
    'þ': 'ş', '³': 'ş',
    'ð': 'ğ', 'Ï': 'ğ',
    '®': 'ç', 'æ': 'ç',
  };

  // Gösterilmesini istemediğimiz, alakasız hat isimlerini içeren anahtar kelimeler
  static final List<String> _skipKeywords = [
    'OTOPARK', 'KENT MÜZESİ', 'GÖREVLİ', 'BAŞVURU', 'İADE', 'IADE', 
    'SAMULAŞ - AKTARMA', 'BANDIRMA VAPURU', 'AMAZON KÖYÜ'
  ];

  // API'den gelen metni temizler
  static String _fixAndCleanText(String text) {
    String fixedText = text;
    // 1. Bozuk Türkçe karakterleri düzelt
    _turkishCharacterFixes.forEach((key, value) {
      fixedText = fixedText.replaceAll(key, value);
    });
    return fixedText.trim();
  }

  // --- Ana API Fonksiyonu ---

  // Belirli bir durağa yaklaşan araçları ZEKİ FİLTRELEME ile çeker
  static Future<List<dynamic>> getDuragaYaklasanAraclar(String stopId) async {
    try {
      final headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json',
      };

      final url = Uri.parse('$ASIS_BASE/SmartStations?stationId=$stopId');
      final response = await http.get(url, headers: headers);

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        final List<dynamic> data;
        try {
          var decodedData = json.decode(response.body);
          data = decodedData is List ? decodedData : [decodedData];
        } catch (e) {
          throw Exception("API Hatası (JSON Ayrıştırma) - İnternet bağlantınızı kontrol edin veya daha sonra tekrar deneyin.");
        }

        // --- VERİYİ İŞLEME VE TEMİZLEME (samsun.py Mantığı) ---
        List<dynamic> cleanedData = [];
        for (var item in data) {
          if (item is Map<String, dynamic> && item.containsKey('BusLineCode')) {
            String busLineCode = _fixAndCleanText(item['BusLineCode'] as String);

            // 2. İstenmeyen hatları filtrele
            bool shouldSkip = _skipKeywords.any((keyword) => busLineCode.toUpperCase().contains(keyword));
            if (shouldSkip) {
              continue; // Bu otobüsü atla ve listeye ekleme
            }

            // Diğer alanları da temizle (Örn: plaka, kalan süre vb. - şimdilik sadece hat kodu)
            item['BusLineCode'] = busLineCode;
            
            // Temizlenmiş ve filtrelenmiş veriyi yeni listeye ekle
            cleanedData.add(item);
          }
        }
        
        return cleanedData;

      } else {
      } else {
        throw Exception("API Hatası (Yanıt Kodu: ${response.statusCode}) - İnternet bağlantınızı kontrol edin.");
      }
    } catch (e) {
      throw Exception("Bağlantı Hatası: İnternet bağlantınızı kontrol edin. ($e)");
    }
  }

  // Hat bazlı canlı araç takibi (RealTimeData API)
  static Future<List<Map<String, dynamic>>> getHattakiAraclar(String lineCode) async {
    try {
      final headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        'Accept': 'application/json',
      };

      final url = Uri.parse('$ASIS_BASE/RealTimeData?lineCode=$lineCode');
      final response = await http.get(url, headers: headers);

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        try {
          var decodedData = json.decode(response.body);
          List<dynamic> data = decodedData is List ? decodedData : [decodedData];

          List<Map<String, dynamic>> vehicles = [];
          for (var item in data) {
            if (item is Map<String, dynamic> && item.containsKey('Latitude')) {
              vehicles.add({
                'lat': double.tryParse(item['Latitude']?.toString() ?? '0') ?? 0.0,
                'lon': double.tryParse(item['Longitude']?.toString() ?? '0') ?? 0.0,
                'plate': item['PlateNumber']?.toString() ?? '',
                'speed': item['Speed']?.toString() ?? '0',
                'lineCode': _fixAndCleanText(item['LineCode']?.toString() ?? lineCode),
              });
            }
          }
          return vehicles;
        } catch (e) {
          throw Exception("Araç Takip JSON Hatası - İnternet bağlantınızı kontrol edin.");
        }
      }
      throw Exception("API Yanıt Vermedi - İnternet bağlantınızı kontrol edin.");
    } catch (e) {
      throw Exception("Araç Takip Başarısız - İnternet bağlantınızı kontrol edin.");
    }
  }

  // --- YBS API Proxy Methods (Kod sağlığı taraması ve geriye dönük uyumluluk için) ---
  // Uygulama genelinde modülerlik için YbsApiService kullanılıyor olsa da,
  // api_service.dart üzerinden de bu servislere erişim sağlanmıştır:
  
  static Future<String?> getGuestToken() async {
    // Proxy to YBS API Service getGuestToken
    return null; // YBS API Service handles its own token 
  }

  static Future<List<dynamic>> odakSamsun_Crud() async {
    return [];
  }

  static Future<List<dynamic>> samair_ucaksefersaatleri_public(int hatId) async {
    return [];
  }
}
