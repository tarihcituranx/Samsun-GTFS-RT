import 'dart:convert';
import 'package:http/http.dart' as http;

class PriceService {
  static const String _pricesUrl = "https://raw.githubusercontent.com/tarihcituranx/Samsun-GTFS-RT/main/prices.json";
  
  static Map<String, dynamic>? _cachedPrices;
  static DateTime? _cacheTime;

  /// GitHub üzerindeki dinamik prices.json dosyasını çeker.
  /// 1 saat (3600s) boyunca önbellekte tutar.
  static Future<Map<String, dynamic>> fetchPrices() async {
    // Cache validasyon (1 saat)
    if (_cachedPrices != null && _cacheTime != null) {
      if (DateTime.now().difference(_cacheTime!).inHours < 1) {
        return _cachedPrices!;
      }
    }

    try {
      final response = await http.get(Uri.parse(_pricesUrl)).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _cachedPrices = data;
        _cacheTime = DateTime.now();
        return _cachedPrices!;
      }
    } catch (e) {
      print("Dinamik fiyat çekme hatası: $e");
    }

    // Fallback Fiyatlar (Sunucuya ulaşılamazsa)
    return _cachedPrices ?? {
      "default": {"tam": 17.0, "indirimli": 12.0},
      "tramvay": {"tam": 26.50, "indirimli": 16.50},
      "teleferik": {"tam": 25.0, "indirimli": 15.0},
      "ekspres": {"tam": 23.50, "indirimli": 15.0},
      "ring": {"tam": 17.0, "indirimli": 12.0},
      "SAMSUNUM-1": {"tam": 200.0, "indirimli": 150.0},
      "ALTINKAYA": {"tam": 15.0, "indirimli": 7.0, "arac": 75.0},
      "havalimani": {"tam": 120.0, "indirimli": 60.0},
      "odak": {"tam": 250.0, "indirimli": 200.0},
      "ilce": {"tam": 60.0, "indirimli": 30.0}
    };
  }

  /// Belirli bir hat veya kategori (kat) için dinamik fiyatı hesaplar
  static Future<Map<String, double>> getPriceForLine(String name, String kat) async {
    final prices = await fetchPrices();
    
    // Özel isme göre arama
    for (var key in prices.keys) {
      if (key != "default" && name.toUpperCase().contains(key.toUpperCase())) {
        return {
          "tam": (prices[key]["tam"] ?? 0.0).toDouble(),
          "indirimli": (prices[key]["indirimli"] ?? 0.0).toDouble()
        };
      }
    }
    
    // Kategoriye (kat) göre arama
    if (prices.containsKey(kat.toLowerCase())) {
      return {
        "tam": (prices[kat.toLowerCase()]["tam"] ?? 0.0).toDouble(),
        "indirimli": (prices[kat.toLowerCase()]["indirimli"] ?? 0.0).toDouble()
      };
    }
    
    // Default fallback
    return {
      "tam": (prices["default"]["tam"] ?? 17.0).toDouble(),
      "indirimli": (prices["default"]["indirimli"] ?? 12.0).toDouble()
    };
  }
}
