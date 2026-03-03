
import 'dart:convert';
import 'package:flutter/foundation.dart' show visibleForTesting;
import 'package:http/http.dart' as http;

class ApiService {
  // Render Proxy — tüm API çağrıları proxy üzerinden geçer (proje şeması gereği)
  static const String _renderBase = 'https://samsun-gtfs-rt.onrender.com/api';

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

  /// ASIS API yanıtından veri listesini güvenli şekilde çıkarır.
  /// ASIS bazen düz liste, bazen {"data": [...]} döner.
  static List<dynamic> _extractDataList(dynamic decoded) {
    if (decoded is List) return decoded;
    if (decoded is Map<String, dynamic> && decoded.containsKey('data')) {
      final inner = decoded['data'];
      return inner is List ? inner : [inner];
    }
    return [decoded];
  }

  static String _fixAndCleanText(String text) {
    String fixedText = text;
    _turkishCharacterFixes.forEach((key, value) {
      fixedText = fixedText.replaceAll(key, value);
    });
    return fixedText.trim();
  }

  /// Durağa yaklaşan araçları çeker — Render proxy üzerinden
  static Future<List<dynamic>> getDuragaYaklasanAraclar(String stopId) async {
    try {
      final url = Uri.parse('$_renderBase/proxy/smart_stations?stationId=$stopId');
      final response = await http.get(url, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 12));

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        final data = json.decode(response.body);
        if (data is List) return _cleanSmartStationData(data);
      }
    } catch (e) {
      throw Exception("Bağlantı Hatası: İnternet bağlantınızı kontrol edin. ($e)");
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

  /// Hat canlı araç takibi — Render proxy üzerinden (akıllı eşleştirmeli)
  static Future<List<Map<String, dynamic>>> getHattakiAraclar(String lineCode) async {
    // 1. Önce samsun.py'nin akıllı eşleştirmeli endpoint'ini dene (/api/hat/arac/)
    // Bu endpoint tramvay, samair ve diğer özel hatlar için doğru ASIS kodunu kullanır
    try {
      final url = Uri.parse('$_renderBase/hat/arac/${Uri.encodeComponent(lineCode)}');
      final response = await http.get(url, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 12));

      if (response.statusCode == 200 && response.body.isNotEmpty) {
        final data = json.decode(response.body);
        if (data is List) return _parseRealTimeData(data, lineCode);
      }
    } catch (e) {
      print("hat/arac proxy hatası: $e");
    }

    // 2. Fallback: doğrudan proxy/realtime (basit hat kodları için)
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
      throw Exception("Araç Takip Başarısız - İnternet bağlantınızı kontrol edin. ($e)");
    }
    return [];
  }

  // ─── Test Erişim Metodları (unit test desteği) ───
  @visibleForTesting
  static List<dynamic> extractDataListForTest(dynamic decoded) => _extractDataList(decoded);
  @visibleForTesting
  static List<Map<String, dynamic>> parseRealTimeDataForTest(List<dynamic> data, String lineCode) => _parseRealTimeData(data, lineCode);
  @visibleForTesting
  static List<dynamic> cleanSmartStationDataForTest(List<dynamic> data) => _cleanSmartStationData(data);
  @visibleForTesting
  static String fixAndCleanTextForTest(String text) => _fixAndCleanText(text);

  /// RealTimeData verisini parse et — Proxy ve ASIS formatlarını destekler
  static List<Map<String, dynamic>> _parseRealTimeData(List<dynamic> data, String lineCode) {
    List<Map<String, dynamic>> vehicles = [];
    for (var item in data) {
      if (item is Map<String, dynamic>) {
        // Proxy format: {lat, lon, plate, speed, ...} | ASIS format: {enlem, boylam, plaka, hiz, ...}
        final lat = double.tryParse((item['lat'] ?? item['enlem'] ?? item['Lat'] ?? item['Latitude'] ?? '0').toString()) ?? 0.0;
        final lon = double.tryParse((item['lon'] ?? item['boylam'] ?? item['Lng'] ?? item['Longitude'] ?? '0').toString()) ?? 0.0;
        if (lat > 40 && lat < 43 && lon > 34 && lon < 38) {
          vehicles.add({
            'lat': lat,
            'lon': lon,
            'plate': (item['plate'] ?? item['plaka'] ?? item['PlateNumber'] ?? '').toString(),
            'speed': (item['speed'] ?? item['hiz'] ?? item['Speed'] ?? '0').toString(),
            'lineCode': _fixAndCleanText((item['lineCode'] ?? item['HatKodu'] ?? item['LineCode'] ?? lineCode).toString()),
            'gunlukYolcu': (item['gunlukYolcu'] ?? '0').toString(),
            'seferYolcu': (item['seferYolcu'] ?? '0').toString(),
            'toplamHasilat': (item['toplamHasilat'] ?? '0').toString(),
            'maxHiz': (item['maxHiz'] ?? '0').toString(),
            'yon': (item['yon'] ?? item['Direction'] ?? '0').toString(),
            'mesafe': (item['mesafe'] ?? '0').toString(),
            'lastUpdate': (item['lastUpdate'] ?? item['editDate'] ?? item['tarih'] ?? item['LastLocationTime'] ?? '').toString(),
            'yakin': item['yakin'],
          });
        }
      }
    }
    return vehicles;
  }
}
