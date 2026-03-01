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
        http.get(Uri.parse('$ASIS_BASE/RealTimeData?lineCode=$lineCode'), headers: headers)
      );
      final responses = await Future.wait(futures);

      for (var response in responses) {
        if (response.statusCode == 200 && response.body.isNotEmpty) {
          try {
            var decodedData = json.decode(response.body);
            List<dynamic> data = decodedData is List ? decodedData : [decodedData];

            for (var item in data) {
              if (item is Map<String, dynamic> && item.containsKey('Latitude')) {
                allVehicles.add({
                  'lineCode': item['LineCode']?.toString() ?? 'SAMAIR',
                  'lat': double.tryParse(item['Latitude']?.toString() ?? '0') ?? 0.0,
                  'lon': double.tryParse(item['Longitude']?.toString() ?? '0') ?? 0.0,
                  'plate': item['PlateNumber']?.toString() ?? 'Bilinmiyor',
                  'speed': item['Speed']?.toString() ?? '0',
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
