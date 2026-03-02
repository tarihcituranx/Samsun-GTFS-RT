import 'dart:convert';
import 'package:http/http.dart' as http;

class YbsApiService {
  static const String _renderBase = "https://samsun-gtfs-rt.onrender.com/api";
  
  // Singleton Pattern
  static final YbsApiService _instance = YbsApiService._internal();
  factory YbsApiService() => _instance;
  YbsApiService._internal();

  // Admin key (SharedPreferences'dan yüklenir)
  String? _adminKey;
  void setAdminKey(String key) => _adminKey = key;
  String? get adminKey => _adminKey;

  /// Admin config'i oku
  Future<Map<String, dynamic>?> getAdminConfig() async {
    if (_adminKey == null || _adminKey!.isEmpty) return null;
    try {
      final uri = Uri.parse("$_renderBase/admin/config?key=$_adminKey");
      final response = await http.get(uri, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print("Admin Config Error: $e");
    }
    return null;
  }

  /// Admin config'i güncelle
  Future<bool> updateAdminConfig({
    bool? gtfsRtEnabled,
    int? gtfsRtInterval,
    String? gtfsRtMode,
    int? gtfsRtMaxLines,
    int? samairInterval,
  }) async {
    if (_adminKey == null || _adminKey!.isEmpty) return false;
    try {
      final params = <String, String>{};
      if (gtfsRtEnabled != null) params['gtfs_rt_enabled'] = gtfsRtEnabled.toString();
      if (gtfsRtInterval != null) params['gtfs_rt_interval'] = gtfsRtInterval.toString();
      if (gtfsRtMode != null) params['gtfs_rt_mode'] = gtfsRtMode;
      if (gtfsRtMaxLines != null) params['gtfs_rt_max_lines'] = gtfsRtMaxLines.toString();
      if (samairInterval != null) params['samair_interval'] = samairInterval.toString();

      final uri = Uri.parse("$_renderBase/admin/config?key=$_adminKey");
      final response = await http.post(uri, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Content-Type': 'application/x-www-form-urlencoded',
      }, body: params).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['ok'] == true;
      }
    } catch (e) {
      print("Admin Config Update Error: $e");
    }
    return false;
  }

  /// Admin istatistiklerini çek
  Future<Map<String, dynamic>?> getAdminStats() async {
    if (_adminKey == null || _adminKey!.isEmpty) return null;
    try {
      final uri = Uri.parse("$_renderBase/admin/stats?key=$_adminKey");
      final response = await http.get(uri, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print("Admin Stats Error: $e");
    }
    return null;
  }

  /// Odak Samsun turistik hatları — Render proxy üzerinden
  Future<List<dynamic>> getOdakSamsun() async {
    try {
      final uri = Uri.parse("$_renderBase/proxy_odak");
      final response = await http.get(uri, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 12));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List) return data;
      }
    } catch (e) {
      print("Odak Proxy Error: $e");
    }
    return [];
  }

  /// SamAir sefer saatleri — Render proxy üzerinden
  Future<List<dynamic>> getSamairSaatleri(int hatId) async {
    try {
      final uri = Uri.parse("$_renderBase/proxy_samair_saatler?hatid=$hatId");
      final response = await http.get(uri, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List) return data;
      }
    } catch (e) {
      print("SamAir Saatler Proxy Error: $e");
    }
    return [];
  }

  /// SamAir araç konumları — Render proxy üzerinden
  Future<List<dynamic>> getSamairAraclar() async {
    try {
      final uri = Uri.parse("$_renderBase/proxy_samair_araclar");
      final response = await http.get(uri, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List) return data;
      }
    } catch (e) {
      print("SamAir Araclar Proxy Error: $e");
    }
    return [];
  }
}
