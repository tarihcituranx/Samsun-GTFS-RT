import 'dart:convert';
import 'package:http/http.dart' as http;

class PriceService {
  static const String SAMULAS_URL = 'https://samulas.com.tr';

  static final Map<String, String> _fiyatEslesme = {
    'E2 SOĞUKSU - BALLICA': 'E2',
    'E2 BALLICA - SOĞUKSU': 'E2',
    '15 SOĞUKSU - İLYASKÖY - BÜYÜK CAMİ': '15',
    '15 BÜYÜK CAMİ - SOĞUKSU': '15',
    'TRAMVAY YOLCU ÜCRETLERİ': 'T1', // Tramvay
    '25 200 EVLER-OTOGAR': '25',
    'R2 CEZAEVİ-BÜYÜK CAMİ': 'R2',
    'R2 BÜYÜK CAMİ-CEZAEVİ': 'R2',
  };

  /// Samulas ana sayfasından GÜNCEL fiyatları çeker
  static Future<Map<String, double>> fetchPrices() async {
    Map<String, double> prices = {};
    try {
      final response = await http.get(Uri.parse(SAMULAS_URL), headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36'
      });

      if (response.statusCode != 200) return prices;

      String bodyStr = response.body;

      // Regex ile tablo içi arama: Tüm tr etiketlerini bul (Basit Web Scraping)
      final rowRegex = RegExp(r'<tr[^>]*>([\s\S]*?)<\/tr>');
      final cellRegex = RegExp(r'<t[dh][^>]*>([\s\S]*?)<\/t[dh]>');
      
      final rows = rowRegex.allMatches(bodyStr);

      for (var row in rows) {
        final cellsStr = row.group(1) ?? '';
        final cells = cellRegex.allMatches(cellsStr).map((m) => _cleanHtml(m.group(1) ?? '')).toList();

        if (cells.length >= 2) {
          String hatNameRaw = cells[0].trim();
          String tamFiyatRaw = cells[1].trim();

          // Sadece boş olmayan ve fiyat içeren satırlar
          if (hatNameRaw.isNotEmpty && RegExp(r'\d').hasMatch(tamFiyatRaw)) {
             double? price = _parsePrice(tamFiyatRaw);
             if (price != null) {
                // Eşleştirme tablosunda ara
                String? kisaAd = _fiyatEslesme[hatNameRaw.toUpperCase()];
                if (kisaAd != null) {
                  prices[kisaAd] = price;
                } else if (!hatNameRaw.contains('ÖĞRENCİ LAMB') && RegExp(r'^[A-Z0-9RTE]+').hasMatch(hatNameRaw)) {
                  // Eşleşme yoksa doğrudan ilk kelimeyi al (Örn: R28, 12, E3)
                  String ilk = hatNameRaw.split(' ')[0].trim().toUpperCase();
                  if (ilk.isNotEmpty) prices[ilk] = price;
                }
             }
          }
        }
      }

      // Ayrıca Tramvay default olarak eklensin eğer tabloda farklı adlandırıldıysa
      if (!prices.containsKey('T1')) prices['T1'] = 17.00; // Varsayılan fallback
      if (!prices.containsKey('T2')) prices['T2'] = prices['T1'] ?? 17.0;

    } catch (e) {
      print("Fiyat Çekme Hatası: $e");
    }
    return prices;
  }

  static String _cleanHtml(String text) {
     return text.replaceAll(RegExp(r'<[^>]*>'), '').replaceAll(RegExp(r'&nbsp;'), ' ').trim();
  }

  static double? _parsePrice(String text) {
    // Örn: "17,00 TL" -> 17.00
    try {
      String cln = text.replaceAll('TL', '').replaceAll('₺', '').trim();
      cln = cln.replaceAll(',', '.'); // Türkçe virgülü noktaya çevir
      return double.tryParse(cln);
    } catch (_) {
      return null;
    }
  }
}
