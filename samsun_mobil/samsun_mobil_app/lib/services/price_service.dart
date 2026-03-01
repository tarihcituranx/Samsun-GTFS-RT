import 'package:http/http.dart' as http;

class PriceService {
  // samulas.com.tr'den güncel bilet fiyatlarını çeker
  static Future<Map<String, double>> fetchPrices() async {
    Map<String, double> prices = {};
    try {
      final response = await http.get(
        Uri.parse('https://www.samulas.com.tr'),
        headers: {
          'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final body = response.body;

        // Regex ile fiyat bilgilerini çek
        // Örn: "17,00", "12,00" gibi değerleri yakala
        final priceRegex = RegExp(r'(\d+)[,.](\d{2})\s*(?:TL|₺)');
        final matches = priceRegex.allMatches(body);

        List<double> foundPrices = [];
        for (var m in matches) {
          final val = double.tryParse('${m.group(1)}.${m.group(2)}');
          if (val != null && val > 1 && val < 500) {
            foundPrices.add(val);
          }
        }

        // Hat kodu -> fiyat eşleştirmesi (samsun.py HAT_ALIAS mantığı)
        if (foundPrices.isNotEmpty) {
          // Sabit bilinen fiyatlar (DB'den de gelebilir, fallback olarak)
          prices['TAM'] = foundPrices.isNotEmpty ? foundPrices.first : 17.0;
          prices['INDIRIMLI'] = foundPrices.length > 1 ? foundPrices[1] : 12.0;
        }
      }
    } catch (e) {
      print("Fiyat çekme hatası: $e");
    }

    // Fallback fiyatlar
    if (prices.isEmpty) {
      prices['TAM'] = 17.0;
      prices['INDIRIMLI'] = 12.0;
    }

    return prices;
  }
}
