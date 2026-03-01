import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String ASIS_BASE = 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis';

  // Belirli bir durağa (örneğin 5065) yaklaşan araçları (RealTimeData/SmartStations) sunucusuz çeker
  static Future<List<dynamic>> getDuragaYaklasanAraclar(String stopId) async {
    try {
      // WAF'ı aşmak için standart bir mobil tarayıcı User-Agent Header'ı ekliyoruz
      final headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json',
      };

      final url = Uri.parse('$ASIS_BASE/SmartStations?stationId=$stopId');
      final response = await http.get(url, headers: headers);

      // 200 OK yanıtı olsa bile, body'nin boş veya geçersiz olmadığından emin ol
      if (response.statusCode == 200 && response.body.isNotEmpty) {
        try {
          final data = json.decode(response.body);
          // Gelen verinin bir liste olduğundan emin ol, değilse listeye çevir
          return data is List ? data : [data];
        } catch (e) {
          // JSON parse hatası olursa, bu da bir API sorunudur. Boş liste döndür.
          print("API Hatası (JSON Ayrıştırma): $e");
          return [];
        }
      } else {
        // Başarısız veya boş yanıt durumunda boş liste döndür
        print("API Hatası (Yanıt Kodu: ${response.statusCode} veya Boş İçerik)");
        return [];
      }
    } catch (e) {
      // Genel ağ veya diğer hatalar için boş liste döndür
      print("API Hatası (Genel Bağlantı): $e");
      return [];
    }
  }
}
