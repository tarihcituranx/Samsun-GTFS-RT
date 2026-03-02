
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Render Proxy (Geo-block bypass) — tüm ASIS çağrıları buradan geçer
  static const String _renderBase = 'https://samsun-gtfs-rt.onrender.com/api';
  
  // Doğrudan ASIS (fallback — sadece Türk IP'li cihazlar)
  static const String _asisDirect = 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis';

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

  static final List<String> _skipKeywords = [
    'OTOPARK', 'KENT MÜZESİ', 'GÖREVLİ', 'BAŞVURU', 'İADE', 'IADE', 
    'SAMULAŞ - AKTARMA', 'BANDIRMA VAPURU', 'AMAZON KÖYÜ'
  ];

  static String _fixAndCleanText(String text) {
    String fixedText = text;
    _turkishCharacterFixes.forEach((key, value) {
      fixedText = fixedText.replaceAll(key, value);
    });
    return fixedText.trim();
  }

  /// Durağa yaklaşan araçları çeker — önce Render proxy, başarısız olursa direkt ASIS
  static Future<List<dynamic>> getDuragaYaklasanAraclar(String stopId) async {
    // 1. Render Proxy üzerinden dene (Geo-block bypass)
    try {
      final url = Uri.parse('$_renderBase/proxy/smart_stations?stationId=$stopId');
      final response = await http.get(url, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        final data = json.decode(response.body);
        if (data is List) return _cleanSmartStationData(data);
      }
    } catch (e) {
      print("Proxy SmartStations hatası, direkt deneniyor: $e");
    }

    // 2. Fallback: Doğrudan ASIS (Türk IP'li cihazlar)
    try {
      final url = Uri.parse('$_asisDirect/SmartStations?stationId=$stopId');
      final response = await http.get(url, headers: {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K)',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        final decoded = json.decode(response.body);
        final data = decoded is List ? decoded : [decoded];
        return _cleanSmartStationData(data);
      }
    } catch (e) {
      throw Exception("Bağlantı Hatası: İnternet bağlantınızı kontrol edin.");
    }
    return [];
  }

  /// SmartStation verisini temizle ve filtrele
  static List<dynamic> _cleanSmartStationData(List<dynamic> data) {
    List<dynamic> cleaned = [];
    for (var item in data) {
      if (item is Map<String, dynamic> && item.containsKey('BusLineCode')) {
        String busLineCode = _fixAndCleanText(item['BusLineCode'] as String);
        bool shouldSkip = _skipKeywords.any((kw) => busLineCode.toUpperCase().contains(kw));
        if (shouldSkip) continue;
        item['BusLineCode'] = busLineCode;
        cleaned.add(item);
      }
    }
    return cleaned;
  }

  /// Hat canlı araç takibi — önce Render proxy, fallback direkt ASIS
  static Future<List<Map<String, dynamic>>> getHattakiAraclar(String lineCode) async {
    // 1. Render Proxy üzerinden dene
    try {
      final url = Uri.parse('$_renderBase/proxy/realtime?lineCode=${Uri.encodeComponent(lineCode)}');
      final response = await http.get(url, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        final data = json.decode(response.body);
        if (data is List) return _parseRealTimeData(data, lineCode);
      }
    } catch (e) {
      print("Proxy RealTimeData hatası, direkt deneniyor: $e");
    }

    // 2. Fallback: Doğrudan ASIS
    try {
      final url = Uri.parse('$_asisDirect/RealTimeData?lineCode=${Uri.encodeComponent(lineCode)}');
      final response = await http.get(url, headers: {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K)',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        final decoded = json.decode(response.body);
        final data = decoded is List ? decoded : [decoded];
        return _parseRealTimeData(data, lineCode);
      }
    } catch (e) {
      throw Exception("Araç Takip Başarısız - İnternet bağlantınızı kontrol edin.");
    }
    return [];
  }

  /// RealTimeData verisini parse et
  static List<Map<String, dynamic>> _parseRealTimeData(List<dynamic> data, String lineCode) {
    List<Map<String, dynamic>> vehicles = [];
    for (var item in data) {
      if (item is Map<String, dynamic>) {
        // Proxy endpoint farklı key isimleri kullanabilir
        final lat = double.tryParse((item['Latitude'] ?? item['enlem'] ?? '0').toString()) ?? 0.0;
        final lon = double.tryParse((item['Longitude'] ?? item['boylam'] ?? '0').toString()) ?? 0.0;
        if (lat > 40 && lat < 43 && lon > 34 && lon < 38) {
          vehicles.add({
            'lat': lat,
            'lon': lon,
            'plate': (item['PlateNumber'] ?? item['plaka'] ?? '').toString(),
            'speed': (item['Speed'] ?? item['hiz'] ?? '0').toString(),
            'lineCode': _fixAndCleanText((item['LineCode'] ?? lineCode).toString()),
          });
        }
      }
    }
    return vehicles;
  }
}
