import 'dart:convert';
import 'package:http/http.dart' as http;

class SamAirService {
  static const String ASIS_BASE = 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis';

  // H1, H2, H3, H4 hatlarını takip edeceğiz
  static final List<String> SAMAIR_LINES = ['H1', 'H2', 'H3', 'H4'];

  static Future<List<Map<String, dynamic>>> getLiveSamAirBuses() async {
    List<Map<String, dynamic>> allVehicles = [];

    final headers = {
      'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
      'Accept': 'application/json',
    };

    try {
      final futures = SAMAIR_LINES.map((lineCode) =>
        http.get(Uri.parse('$ASIS_BASE/RealTimeData?lineCode=${Uri.encodeComponent(lineCode)}'), headers: headers)
      );
      final responses = await Future.wait(futures);

      for (var response in responses) {
        if (response.statusCode == 200 && response.body.isNotEmpty) {
          try {
            var decodedData = json.decode(response.body);
            List<dynamic> data = decodedData is List ? decodedData : (decodedData is Map && decodedData.containsKey('data') ? decodedData['data'] : [decodedData]);

            for (var item in data) {
              if (item is Map<String, dynamic> && (item.containsKey('enlem') || item.containsKey('Latitude'))) {
                // Gerçek ASIS: enlem/boylam/plaka/hiz/HatKodu (Türkçe)
                // Fallback: Latitude/Longitude/PlateNumber/Speed/LineCode (PascalCase — eski)
                allVehicles.add({
                  'lineCode': (item['HatKodu'] ?? item['LineCode'] ?? 'SAMAIR').toString(),
                  'lat': double.tryParse((item['enlem'] ?? item['Latitude'] ?? '0').toString()) ?? 0.0,
                  'lon': double.tryParse((item['boylam'] ?? item['Longitude'] ?? '0').toString()) ?? 0.0,
                  'plate': (item['plaka'] ?? item['PlateNumber'] ?? 'Bilinmiyor').toString(),
                  'speed': (item['hiz'] ?? item['Speed'] ?? '0').toString(),
                });
              }
            }
          } catch (_) {}
        }
      }
    } catch (e) {
      print("SamAir Canlı Takip Hatası: $e");
    }

    return allVehicles;
  }
}
