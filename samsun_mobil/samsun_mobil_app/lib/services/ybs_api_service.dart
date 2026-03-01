import 'dart:convert';
import 'package:http/http.dart' as http;

class YbsApiService {
  static const String _baseUrl = "https://ybs.samsun.bel.tr/service/";
  
  // Singleton Pattern
  static final YbsApiService _instance = YbsApiService._internal();
  factory YbsApiService() => _instance;
  YbsApiService._internal();

  String? _token;
  DateTime? _tokenExpiry;

  static const Map<String, String> _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
  };

  /// Self-caching token pool (200s TTL)
  Future<String?> _getToken() async {
    // Return cached token if valid
    if (_token != null && _tokenExpiry != null) {
      if (DateTime.now().isBefore(_tokenExpiry!)) {
        return _token;
      }
    }

      print("--- YBS API REQUEST ---");
      print("POST $_baseUrl");
      print("Body: {'method': 'getGuestToken'}");
      
      final response = await http.post(
        Uri.parse(_baseUrl),
        headers: _headers,
        body: {'method': 'getGuestToken'},
      ).timeout(const Duration(seconds: 10));

      print("--- YBS API RESPONSE ---");
      print("Status Code: ${response.statusCode}");
      print("Response Body: ${response.body}");

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data != null && data['token'] != null) {
          _token = data['token'];
          // 200s ömrü var, biz garanti olsun diye 180s (3 dakika) veriyoruz.
          _tokenExpiry = DateTime.now().add(const Duration(seconds: 180));
          return _token;
        }
      }
    } catch (e) {
      print("YBS Token Error: $e");
    }
    return null;
  }

  /// Odak Samsun turistik lokasyon verilerini çeker
  /// WAF Bypass: Referer header zorunlu
  Future<List<dynamic>> getOdakSamsun() async {
    final token = await _getToken();
    if (token == null) return [];

    try {
      print("--- YBS ODAK REQUEST ---");
      print("GET $uri");
      
      final response = await http.get(
        uri,
        headers: {
          ..._headers,
          'Referer': 'https://odak.samsun.bel.tr/'
        },
      ).timeout(const Duration(seconds: 15));

      print("--- YBS ODAK RESPONSE ---");
      print("Status Code: ${response.statusCode}");
      print("Response Body (first 200 chars): ${response.body.length > 200 ? response.body.substring(0, 200) : response.body}");

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['status'] == 'SUCCESS' && data['data'] != null) {
           return data['data'] as List<dynamic>;
        }
      }
    } catch (e) {
      print("YBS Odak Error: $e");
    }
    return [];
  }

  /// Belirli bir SamAir hattının sefer saatlerini döner
  Future<List<dynamic>> getSamairSaatleri(int hatId) async {
    final token = await _getToken();
    if (token == null) return [];

    try {
      print("--- YBS SAMAIR SAATLER REQUEST ---");
      print("GET $uri");
      
      final response = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));

      print("--- YBS SAMAIR SAATLER RESPONSE ---");
      print("Status Code: ${response.statusCode}");
      print("Response Body: ${response.body}");

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        // YBS bazen 'data' bazen 'root' array'i içinde döner.
        if (data['data'] != null) return data['data'] as List<dynamic>;
        if (data['root'] != null) return data['root'] as List<dynamic>;
      }
    } catch (e) {
      print("YBS Samair Error for Hat $hatId: $e");
    }
    return [];
  }

  /// Tüm SamAir araç konumlarını (harita için) çeker
  Future<List<dynamic>> getSamairAraclar() async {
    final token = await _getToken();
    if (token == null) return [];

    try {
      print("--- YBS SAMAIR ARACLAR REQUEST ---");
      print("GET $uri");
      
      final response = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));

      print("--- YBS SAMAIR ARACLAR RESPONSE ---");
      print("Status Code: ${response.statusCode}");
      print("Response Body: ${response.body}");

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['data'] != null) return data['data'] as List<dynamic>;
      }
    } catch (e) {
      print("YBS Samair Araclar Error: $e");
    }
    return [];
  }
}
