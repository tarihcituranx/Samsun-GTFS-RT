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

      // Not: Asis API "SmartStations" veya "StopsStations" uçları üzerinden çalışır (Parametre test edilmelidir)
      final url = Uri.parse('$ASIS_BASE/SmartStations?stationId=$stopId');
      final response = await http.get(url, headers: headers);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data is List ? data : [data];
      } else {
        return [];
      }
    } catch (e) {
      print("API Hatası (Sunucusuz Bağlantı): $e");
      return [];
    }
  }
}
