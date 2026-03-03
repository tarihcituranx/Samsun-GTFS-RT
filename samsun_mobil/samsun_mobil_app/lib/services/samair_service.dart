import 'dart:convert';
import 'package:http/http.dart' as http;

class SamAirService {
  // Tüm çağrılar Render proxy üzerinden (proje şeması gereği)
  static const String _renderBase = 'https://samsun-gtfs-rt.onrender.com/api';

  // H1, H2, H3, H4, H5 hatlarını takip edeceğiz
  static final List<String> SAMAIR_LINES = ['H1', 'H2', 'H3', 'H4', 'H5'];

  static Future<List<Map<String, dynamic>>> getLiveSamAirBuses() async {
    List<Map<String, dynamic>> allVehicles = [];

    try {
      final futures = SAMAIR_LINES.map((lineCode) =>
        http.get(
          Uri.parse('$_renderBase/proxy/realtime?lineCode=${Uri.encodeComponent(lineCode)}'),
          headers: {'User-Agent': 'SamsunMobilApp/2.0', 'Accept': 'application/json'},
        ).timeout(const Duration(seconds: 10)).catchError((_) => http.Response('[]', 200))
      );
      final responses = await Future.wait(futures);

      for (var response in responses) {
        if (response.statusCode == 200 && response.body.isNotEmpty) {
          try {
            var decodedData = json.decode(response.body);
            List<dynamic> data = decodedData is List ? decodedData : (decodedData is Map && decodedData.containsKey('data') ? decodedData['data'] : [decodedData]);

            for (var item in data) {
              if (item is Map<String, dynamic> && (item.containsKey('enlem') || item.containsKey('Latitude') || item.containsKey('lat'))) {
                allVehicles.add({
                  'lineCode': (item['HatKodu'] ?? item['LineCode'] ?? item['lineCode'] ?? 'SAMAIR').toString(),
                  'lat': double.tryParse((item['enlem'] ?? item['Latitude'] ?? item['lat'] ?? '0').toString()) ?? 0.0,
                  'lon': double.tryParse((item['boylam'] ?? item['Longitude'] ?? item['lon'] ?? '0').toString()) ?? 0.0,
                  'plate': (item['plaka'] ?? item['PlateNumber'] ?? item['plate'] ?? 'Bilinmiyor').toString(),
                  'speed': (item['hiz'] ?? item['Speed'] ?? item['speed'] ?? '0').toString(),
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
