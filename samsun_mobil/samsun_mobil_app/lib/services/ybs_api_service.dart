import 'dart:convert';
import 'package:http/http.dart' as http;

class YbsApiService {
  static const String _ybsUrl = "https://ybs.samsun.bel.tr/service/";
  static const String _renderUrl = "https://samsun-gtfs-rt.onrender.com/api";
  
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

  /// Cloud Sunucusuna (Render) "Şu hatları aktif et" komutu gönderir.
  Future<void> setGtfsConfig(List<String> activeLines) async {
    try {
      final uri = Uri.parse("$_renderUrl/gtfs_config");
      print("--- CLOUD GTFS WAKEUP REQUEST ---");
      final body = json.encode({
        "enabled": true,
        "active_lines": activeLines
      });

      final response = await http.post(
        uri, 
        headers: {
          'User-Agent': 'SamsunMobilApp/2.0',
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: body
      ).timeout(const Duration(seconds: 10));

      print("GTFS Wakeup Status: ${response.statusCode}");
    } catch (e) {
      print("GTFS Wakeup Error: $e");
    }
  }

  /// Self-caching token pool
  Future<String?> _getToken() async {
    if (_token != null && _tokenExpiry != null) {
      if (DateTime.now().isBefore(_tokenExpiry!)) return _token;
    }

    try {
      final response = await http.post(
        Uri.parse(_ybsUrl),
        headers: _headers,
        body: {'method': 'getGuestToken'},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data != null && data['token'] != null) {
          _token = data['token'];
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
  Future<List<dynamic>> getOdakSamsun() async {
    final token = await _getToken();
    if (token == null) return [];

    try {
      final uri = Uri.parse("$_ybsUrl?method=odakSamsun_Crud&token=$token");
      final response = await http.get(
        uri,
        headers: {
          ..._headers,
          'Referer': 'https://odak.samsun.bel.tr/'
        },
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
      final uri = Uri.parse("$_ybsUrl?method=samair_ucaksefersaatleri_public&submethod=HatlarList&hatid=$hatId&token=$token");
      final response = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
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
      final uri = Uri.parse("$_ybsUrl?method=samair_duraklar_public&submethod=araclar&token=$token");
      final response = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));

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
