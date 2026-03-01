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

  /// Self-caching token pool (200s TTL)
  Future<String?> _getToken() async {
    // Return cached token if valid
    if (_token != null && _tokenExpiry != null) {
      if (DateTime.now().isBefore(_tokenExpiry!)) {
        return _token;
      }
    }

    try {
      final response = await http.post(
        Uri.parse(_baseUrl),
        body: {'method': 'getGuestToken'},
      ).timeout(const Duration(seconds: 10));

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
      final uri = Uri.parse("$_baseUrl?method=odakSamsun_Crud&token=$token");
      final response = await http.get(
        uri,
        headers: {'Referer': 'https://odak.samsun.bel.tr/'}, // Mandatory WAF bypass
      ).timeout(const Duration(seconds: 15));

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
      final uri = Uri.parse("$_baseUrl?method=samair_ucaksefersaatleri_public&submethod=HatlarList&hatid=$hatId&token=$token");
      final response = await http.get(uri).timeout(const Duration(seconds: 10));

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
      final uri = Uri.parse("$_baseUrl?method=samair_duraklar_public&submethod=araclar&token=$token");
      final response = await http.get(uri).timeout(const Duration(seconds: 10));

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
