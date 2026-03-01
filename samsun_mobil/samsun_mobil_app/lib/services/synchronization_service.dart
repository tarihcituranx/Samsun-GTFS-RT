
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:samsun_transit/helpers/database_helper.dart';
import 'package:sqflite/sqflite.dart'; // Hata düzeltmesi için eklendi

// samsun.py'nin Collector sınıfının mantığını Flutter/Dart'a taşıyan servis.
// API'lerden veri toplar, temizler, işler ve yerel SQLite veritabanını doldurur.
class SynchronizationService {
  final dbHelper = DatabaseHelper.instance;
  static const ASIS_BASE = 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis';
  static const YBS_BASE = 'https://ybs.samsun.bel.tr/service';

  // --- samsun.py'den Port Edilen Veri Temizleme Mantığı ---
  static final Map<String, String> _turkishCharacterFixes = {
      '¦': 'İ', '‹': 'İ', 'Ý': 'İ',
      '▄': 'Ü', 
      'Ì': 'Ş', '™': 'Ş', 'Þ': 'Ş',
      'Ã': 'Ç', '˙': 'Ç', 'Æ': 'Ç',
      'º': 'Ğ', '°': 'Ğ', 'Ð': 'Ğ',
      'Í': 'Ö', 'Ô': 'Ö',
      'ý': 'ı', '²': 'ı', 
      'Ó': 'ö',
      'ã': 'ü',
      'þ': 'ş', '³': 'ş',
      'ð': 'ğ', 'Ï': 'ğ',
      '®': 'ç', 'æ': 'ç',
  };

  static final List<String> _skipKeywords = [
      'OTOPARK', 'KENT MÜZESİ', 'GÖREVLİ', 'BAŞVURU', 'İADE', 'IADE', 
      'SAMULAŞ - AKTARMA', 'BANDIRMA VAPURU', 'AMAZON KÖYÜ'
  ];

  static String _fixText(String text) {
    if (text == null) return '';
    String fixedText = text;
    _turkishCharacterFixes.forEach((key, value) {
      fixedText = fixedText.replaceAll(key, value);
    });
    return fixedText.trim();
  }

  // --- API Çağrıları (samsun.py'nin Http sınıfı gibi) ---
  Future<List<dynamic>> _asisApiCall(String endpoint, {Map<String, String>? params}) async {
    try {
      final uri = Uri.parse('$ASIS_BASE/$endpoint').replace(queryParameters: params);
      final response = await http.get(uri, headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
      });
      if (response.statusCode == 200 && response.body.isNotEmpty) {
        var decoded = json.decode(response.body);
        // ASIS API bazen doğrudan liste, bazen { 'data': [...] } döner
        return (decoded is Map && decoded.containsKey('data')) ? decoded['data'] : decoded;
      }
    } catch (e) {
      print('ASIS API Hatası ($endpoint): $e');
    }
    return [];
  }

  // --- Veri Çekme ve İşleme Fonksiyonları (samsun.py'nin Collector metotları) ---

  Future<void> _fetchAndSaveHats() async {
    print('📥 Hatlar çekiliyor...');
    final db = await dbHelper.database;
    
    List<dynamic> lines = await _asisApiCall('Lines');
    List<dynamic> orjLines = await _asisApiCall('OrjLines');

    Set<String> seenCodes = {};
    List<Map<String, dynamic>> hatsToInsert = [];

    // 1. Ana hatları 'Lines' endpoint'inden al
    for (var l in lines) {
      String code = _fixText(l['lineCode']?.toString() ?? '');
      if (code.isNotEmpty && !seenCodes.contains(code)) {
        hatsToInsert.add({
          'code': code,
          'name': _fixText(l['lineName']?.toString() ?? code),
          'tip': l['tip']?.toString() ?? 'gidis',
          'kat': _categorizeHat(code, l['lineName']?.toString() ?? ''),
        });
        seenCodes.add(code);
      }
    }

    // 2. Eksik hatları ve alias'ları 'OrjLines'dan ekle
    for (var l in orjLines) {
      String code = _fixText(l['lineCode']?.toString() ?? '');
      String name = _fixText(l['lineName']?.toString() ?? code);

      if (code.isNotEmpty && !seenCodes.contains(code)) {
        bool shouldSkip = _skipKeywords.any((kw) => code.toUpperCase().contains(kw) || name.toUpperCase().contains(kw));
        if (shouldSkip) continue;

        hatsToInsert.add({
          'code': code,
          'name': name,
          'tip': l['tip']?.toString() ?? 'gidis',
          'kat': _categorizeHat(code, name),
        });
        seenCodes.add(code);
      }
    }

    // 3. Veritabanına toplu ekleme
    if (hatsToInsert.isNotEmpty) {
      final batch = db.batch();
      for (var hat in hatsToInsert) {
        batch.insert(DatabaseHelper.tableHat, hat, conflictAlgorithm: ConflictAlgorithm.replace);
      }
      await batch.commit(noResult: true);
      print('✅ ${hatsToInsert.length} hat veritabanına kaydedildi.');
    }
  }

  Future<void> _fetchAndSaveDuraklar() async {
    print('📥 Duraklar çekiliyor...');
    final db = await dbHelper.database;
    List<dynamic> stops = await _asisApiCall('StopsStations');

    List<Map<String, dynamic>> duraklarToInsert = [];
    Set<String> seenIds = {};

    for (var s in stops) {
      String stopId = s['stopId']?.toString() ?? '';
      if (stopId.isNotEmpty && !seenIds.contains(stopId)) {
        double lat = double.tryParse(s['latitude']?.toString().replaceAll(',', '.') ?? '0.0') ?? 0.0;
        double lon = double.tryParse(s['longitude']?.toString().replaceAll(',', '.') ?? '0.0') ?? 0.0;

        // Geçersiz koordinatları atla
        if (lat < 40 || lat > 43 || lon < 34 || lon > 38) continue;

        String ad = _fixText(s['stopName']?.toString() ?? '');
        String kod = '';
        final match = RegExp(r'^(\d+)').firstMatch(ad);
        if (match != null) {
          kod = match.group(1)!;
        }

        duraklarToInsert.add({
          'id': stopId,
          'kod': kod,
          'ad': ad,
          'lat': lat,
          'lon': lon,
        });
        seenIds.add(stopId);
      }
    }

    if (duraklarToInsert.isNotEmpty) {
      final batch = db.batch();
      for (var durak in duraklarToInsert) {
        batch.insert(DatabaseHelper.tableDurak, durak, conflictAlgorithm: ConflictAlgorithm.replace);
      }
      await batch.commit(noResult: true);
      print('✅ ${duraklarToInsert.length} durak veritabanına kaydedildi.');
    }
  }

  Future<void> _fetchAndSaveGuzergahlar() async {
    print('📥 Güzergahlar çekiliyor...');
    final db = await dbHelper.database;
    final hats = await db.query(DatabaseHelper.tableHat, columns: ['code']);

    await db.delete(DatabaseHelper.tableHatDurak); // Önce eski güzergahları temizle

    int i = 0;
    for (var hat in hats) {
      String code = hat['code'] as String;
      List<dynamic> stopsOnRoute = await _asisApiCall('StopsStations', params: {'lineCode': code});
      
      if (stopsOnRoute.isNotEmpty) {
        final batch = db.batch();
        for (var s in stopsOnRoute) {
            double lat = double.tryParse(s['latitude']?.toString().replaceAll(',', '.') ?? '0.0') ?? 0.0;
            double lon = double.tryParse(s['longitude']?.toString().replaceAll(',', '.') ?? '0.0') ?? 0.0;
            if (lat < 40 || lat > 43 || lon < 34 || lon > 38) continue;

            batch.insert(DatabaseHelper.tableHatDurak, {
              'hat': code,
              'durak_id': s['stopId']?.toString() ?? '',
              'ad': _fixText(s['stopName']?.toString() ?? ''),
              'sira': int.tryParse(s['orderId']?.toString() ?? '0') ?? 0,
              'lat': lat,
              'lon': lon,
            });
        }
        await batch.commit(noResult: true);
      }
      i++;
      if (i % 20 == 0) {
        print('   ... ${i} / ${hats.length} güzergah işlendi.');
      }
    }
    print('✅ Güzergahlar tamamlandı.');
  }

  // --- Ana Senkronizasyon Fonksiyonu ---

  Future<void> runFullSynchronization({bool force = false}) async {
    final db = await dbHelper.database;
    
    // Güncelleme gerekli mi kontrol et (samsun.py'deki gibi)
    if (!force) {
      final lastUpdate = await db.query(DatabaseHelper.tableMeta, where: 'key = ?', whereArgs: ['last_update']);
      if (lastUpdate.isNotEmpty) {
        final lastDate = DateTime.tryParse(lastUpdate.first['value'] as String);
        if (lastDate != null && DateTime.now().difference(lastDate).inDays < 7) {
          print('📦 Veriler güncel. Senkronizasyon atlanıyor.');
          return;
        }
      }
    }

    print('🔄 **Büyük Veri Senkronizasyonu Başladı** 🔄');
    
    // Önce eski verileri temizle
    await db.delete(DatabaseHelper.tableHat);
    await db.delete(DatabaseHelper.tableDurak);
    await db.delete(DatabaseHelper.tableHatDurak);
    // Diğer tablolar... (sefer, fiyat vb. eklenecek)

    await _fetchAndSaveHats();
    await _fetchAndSaveDuraklar();
    await _fetchAndSaveGuzergahlar();
    // Diğer _fetch fonksiyonları buraya gelecek
    
    // Güncelleme zamanını kaydet
    await db.insert(DatabaseHelper.tableMeta, 
      {'key': 'last_update', 'value': DateTime.now().toIso8601String()},
      conflictAlgorithm: ConflictAlgorithm.replace
    );

    print('🎉 **Senkronizasyon Başarıyla Tamamlandı** 🎉');
  }

  // --- Yardımcı Fonksiyonlar ---
  String _categorizeHat(String code, String name) {
    final c = code.toUpperCase();
    final n = name.toUpperCase();

    if (c.startsWith('R') && c.length > 1 && int.tryParse(c.substring(1, 2)) != null) return 'ring';
    if (n.contains('TRAMVAY')) return 'tramvay';
    if (n.contains('TELEFERİK')) return 'teleferik';
    if (c.startsWith('H') && c.length > 1 && int.tryParse(c.substring(1, 2)) != null) return 'havalimani';
    if (n.contains('EKSPRES') || (c.startsWith('E') && c.length > 1 && int.tryParse(c.substring(1, 2)) != null)) return 'ekspres';
    if (['TERME','ÇARŞAMBA','BAFRA','HAVZA','LADİK','KAVAK','ASARCIK'].any((ilce) => n.contains(ilce))) return 'ilce';
    
    return 'otobus';
  }
}
