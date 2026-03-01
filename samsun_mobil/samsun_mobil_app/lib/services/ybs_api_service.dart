import 'dart:convert';
import 'package:http/http.dart' as http;

class YbsApiService {
  // Yeni Render Cloud Sunucumuz (Python Proxy & GTFS Engine)
  static const String _baseUrl = "https://samsun-gtfs-rt.onrender.com/api";
  
  // Singleton Pattern
  static final YbsApiService _instance = YbsApiService._internal();
  factory YbsApiService() => _instance;
  YbsApiService._internal();

  static const Map<String, String> _headers = {
    'User-Agent': 'SamsunMobilApp/2.0 (Android; CloudSync)',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };

  /// Cloud Sunucusuna (Render) "Şu hatları aktif et" komutu gönderir.
  /// Sunucu bu komutu alınca uyku modundan çıkar ve sadece bu hatları YBS'den çeker.
  Future<void> setGtfsConfig(List<String> activeLines) async {
    try {
      final uri = Uri.parse("$_baseUrl/gtfs_config");
      print("--- CLOUD GTFS WAKEUP REQUEST ---");
      print("POST $uri -> active_lines: $activeLines");
      
      final body = json.encode({
        "enabled": true,
        "active_lines": activeLines
      });

      final response = await http.post(
        uri, 
        headers: _headers,
        body: body
      ).timeout(const Duration(seconds: 10));

      print("--- CLOUD GTFS WAKEUP RESPONSE ---");
      print("Status Code: ${response.statusCode}");
    } catch (e) {
      print("GTFS Wakeup Error: $e");
    }
  }

  /// Odak Samsun turistik lokasyon verilerini çeker (Proxy üzerinden)
  Future<List<dynamic>> getOdakSamsun() async {
    try {
      // Python sunucusundaki /api/ybs/... uçları Odak için ayarlanmalı veya
      // Python sunucusu yerine doğrudan odak endpointi yazılmalı.
      // EĞER SAMSUN.PY YBS PROXY DESTEĞİNE SAHİP DEĞİLSE BU KISIM ŞİMDİLİK STATİK KALIR VEYA 
      // SAMSUN.PY İÇERİSİNE ODAK/SAMAİR PROXY EKLENİR.
      // Not: Kullanıcı "samsun.py orada çalışabilir tüm apiler daha rahat çalışır" demişti.
      // O yüzden bu istekleri doğrudan Render'daki Python projemizin oluşturacağı proxy endpointine atıyoruz.
      final uri = Uri.parse("$_baseUrl/proxy_odak"); // Varsayımsal Python proxy endpoint'i
      print("--- CLOUD PROXY ODAK REQUEST ---");
      
      final response = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 15));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List) return data; // Python proxy formatı
        if (data['data'] != null) return data['data'] as List<dynamic>;
      }
    } catch (e) {
      print("Cloud Odak Error: $e");
    }
    return [];
  }

  /// Belirli bir SamAir hattının sefer saatlerini döner (Proxy üzerinden)
  Future<List<dynamic>> getSamairSaatleri(int hatId) async {
    try {
      final uri = Uri.parse("$_baseUrl/proxy_samair_saatler?hatid=$hatId");
      print("--- CLOUD PROXY SAMAIR SAATLER REQUEST ---");
      
      final response = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List) return data;
        if (data['data'] != null) return data['data'] as List<dynamic>;
        if (data['root'] != null) return data['root'] as List<dynamic>;
      }
    } catch (e) {
      print("Cloud Samair Error for Hat $hatId: $e");
    }
    return [];
  }

  /// Tüm SamAir araç konumlarını çeker (Proxy üzerinden)
  Future<List<dynamic>> getSamairAraclar() async {
    try {
      final uri = Uri.parse("$_baseUrl/proxy_samair_araclar");
      print("--- CLOUD PROXY SAMAIR ARACLAR REQUEST ---");
      
      final response = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List) return data;
        if (data['data'] != null) return data['data'] as List<dynamic>;
      }
    } catch (e) {
      print("Cloud Samair Araclar Error: $e");
    }
    return [];
  }
}
