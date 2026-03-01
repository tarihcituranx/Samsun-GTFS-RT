
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
          print("API Hatası (JSON Ayrıştırma): $e");
          return [];
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
        print("API Hatası (Yanıt Kodu: ${response.statusCode} veya Boş İçerik)");
        return [];
      }
    } catch (e) {
      print("API Hatası (Genel Bağlantı): $e");
      return [];
    }
  }

  // Belirli bir hatta anlık sefer yapan tüm araçları çeker (Live Tracking)
  static Future<List<dynamic>> getHattakiAraclar(String lineCode) async {
    try {
      final headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json',
      };

      final url = Uri.parse('$ASIS_BASE/RealTimeData?lineCode=$lineCode');
      final response = await http.get(url, headers: headers);

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        final List<dynamic> data;
        try {
          var decodedData = json.decode(response.body);
          data = decodedData is List ? decodedData : [decodedData];
        } catch (e) {
          print("API Hatası (JSON Ayrıştırma - RealTimeData): $e");
          return [];
        }

        List<dynamic> cleanedData = [];
        for (var item in data) {
          if (item is Map<String, dynamic> && item.containsKey('Latitude') && item.containsKey('Longitude')) {
            // İstenmeyen hat kontrolü
            if (item.containsKey('LineCode')) {
              String lCode = item['LineCode']?.toString() ?? '';
              bool shouldSkip = _skipKeywords.any((keyword) => lCode.toUpperCase().contains(keyword));
              if (shouldSkip) continue;
            }
            cleanedData.add(item);
          }
        }
        return cleanedData;
      } else {
        print("API Hatası (RealTimeData Yanıt Kodu: ${response.statusCode})");
        return [];
      }
    } catch (e) {
      print("API Hatası (RealTimeData Bağlantı): $e");
      return [];
    }
  }
}
