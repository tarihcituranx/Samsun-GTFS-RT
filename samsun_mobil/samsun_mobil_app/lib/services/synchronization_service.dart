
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

  Future<List<dynamic>> _ybsApiCall(String module, String method, {Map<String, String>? params}) async {
    try {
      // YBS API query param formatı: ?method=<module>&submethod=<method>&token=...
      final queryParams = <String, String>{
        'method': module,
        'submethod': method,
        ...?params,
      };
      final uri = Uri.parse(YBS_BASE).replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'https://odak.samsun.bel.tr/',
      });
      if (response.statusCode == 200 && response.body.isNotEmpty) {
        var decoded = json.decode(response.body);
        if (decoded is Map && decoded.containsKey('data')) return decoded['data'] is List ? decoded['data'] : [];
        if (decoded is Map && decoded.containsKey('root')) return decoded['root'] is List ? decoded['root'] : [];
        if (decoded is List) return decoded;
      }
    } catch (e) {
      print('YBS API Hatası ($module/$method): $e');
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

  Future<void> _fetchAndSaveSeferler() async {
    print('📥 Seferler çekiliyor...');
    final db = await dbHelper.database;
    final hats = await db.query(DatabaseHelper.tableHat, columns: ['code']);
    
    final now = DateTime.now();
    final todayStr = "${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}";

    int count = 0;
    for (var hat in hats) {
      String code = hat['code'] as String;
      List<dynamic> schedules = await _asisApiCall('Schedules', params: {'lineCode': code, 'scheduleDate': todayStr});
      
      if (schedules.isNotEmpty) {
        final batch = db.batch();
        for (var d in schedules) {
          String saat = d['saat']?.toString() ?? d['time']?.toString() ?? '';
          String yon = d['yon']?.toString() ?? '';
          if (saat.isNotEmpty) {
            batch.insert(DatabaseHelper.tableSefer, {
              'hat': code,
              'saat': saat,
              'yon': yon,
              'gun': 'hergun'
            });
            count++;
          }
        }
        await batch.commit(noResult: true);
      }
    }
    print('✅ $count sefer kaydedildi.');
  }

  Future<void> _fetchAndSaveOdak() async {
    print('📥 Odak Turistik Hatlar çekiliyor...');
    final db = await dbHelper.database;
    List<dynamic> odakHatlar = await _ybsApiCall('odak_otobus_public', 'HatlarList');
    int dCount = 0;

    if (odakHatlar.isNotEmpty) {
      final hatBatch = db.batch();
      for (var h in odakHatlar) {
        String code = h['kodu']?.toString() ?? '';
        String name = h['adi']?.toString() ?? '';
        String g_code = "G_$code";
        
        hatBatch.insert(DatabaseHelper.tableOdak, {
          'id': code,
          'ad': name,
          'kod': g_code,
          'gunler': h['gunler']?.toString() ?? ''
        });

        // Also add to main Hat table for generic searching
        hatBatch.insert(DatabaseHelper.tableHat, {
          'code': g_code,
          'name': name,
          'tip': 'odak',
          'kat': 'odak',
        }, conflictAlgorithm: ConflictAlgorithm.ignore);

        // Fetch Duraklar for this Odak
        List<dynamic> duraklar = await _ybsApiCall('odak_otobussefer_public', 'DuraklarByKodu', params: {'kodu': code});
        if (duraklar.isNotEmpty) {
           final dBatch = db.batch();
           for (var i = 0; i < duraklar.length; i++) {
              var d = duraklar[i];
              double lat = double.tryParse(d['lat']?.toString() ?? '0') ?? 0;
              double lon = double.tryParse(d['lon']?.toString() ?? '0') ?? 0;
              dBatch.insert(DatabaseHelper.tableOdakDurak, {
                  'hat': g_code,
                  'ad': d['durak_adi']?.toString() ?? '',
                  'kod': d['durak_kodu']?.toString() ?? '',
                  'sira': i+1,
                  'lat': lat,
                  'lon': lon,
                  'fiyat': d['fiyat']?.toString() ?? '',
                  'fiyat_ogr': d['fiyat_ogr']?.toString() ?? ''
              });
              dCount++;
           }
           await dBatch.commit(noResult: true);
        }
      }
      await hatBatch.commit(noResult: true);
      print('✅ ${odakHatlar.length} Odak Hattı ve $dCount Odak Durağı eklendi.');
    }
  }

  Future<void> _fetchAndSaveSamair() async {
    print('📥 Samair Havalimanı Hatları çekiliyor...');
    final db = await dbHelper.database;
    List<dynamic> hatlar = await _ybsApiCall('samair_ucaksefersaatleri_public', 'LokasyonlarList');
    
    int hatCount = 0;
    int seferCount = 0;

    if (hatlar.isNotEmpty) {
      final batch = db.batch();
      for (var h in hatlar) {
         String name = h['adi']?.toString() ?? '';
         String id = h['id']?.toString() ?? '';
         
         batch.insert(DatabaseHelper.tableSamair, {
           'id': int.tryParse(id) ?? 0,
           'ad': name,
           'kod': "H_$id"
         });

         batch.insert(DatabaseHelper.tableHat, {
           'code': "H_$id",
           'name': name,
           'tip': 'havalimani',
           'kat': 'havalimani',
         }, conflictAlgorithm: ConflictAlgorithm.ignore);
         
         hatCount++;

         List<dynamic> seferler = await _ybsApiCall('samair_ucaksefersaatleri_public', 'HatlarList', params: {'hatid': id});
         if (seferler.isNotEmpty) {
             final sfBatch = db.batch();
             for (var sf in seferler) {
                 sfBatch.insert(DatabaseHelper.tableSamairSefer, {
                     'hat': int.tryParse(id) ?? 0,
                     'saat': sf['saat']?.toString() ?? '',
                     'varis': sf['varis_saati']?.toString() ?? '',
                     'firma': sf['ucak_firmasi']?.toString() ?? '',
                     'ucak_saat': sf['ucak_saatleri']?.toString() ?? '',
                     'tarih': sf['tarih']?.toString() ?? '',
                     'gun_format': sf['formatted_date']?.toString() ?? ''
                 });
                 seferCount++;
             }
             await sfBatch.commit(noResult: true);
         }
      }
      await batch.commit(noResult: true);
      print('✅ $hatCount Samair Hattı ve $seferCount Samair Seferi Eklendi.');
    }
  }

  Future<void> _injectFixedPrices() async {
    print('💰 Sabit Fiyatlar Ekleniyor...');
    final db = await dbHelper.database;
    final now = DateTime.now().toIso8601String();
    
    final batch = db.batch();

    void addPrice(String name, String code, double tam, double indirimli) {
      batch.insert(DatabaseHelper.tableFiyat, {
        'kaynak': 'fixed',
        'hat_adi': name,
        'hat_code': code,
        'tam_fiyat': tam,
        'ogrenci_fiyat': indirimli,
        'guncelleme': now
      }, conflictAlgorithm: ConflictAlgorithm.replace);
    }

    addPrice('Tramvay', 'SAMULAŞ - TRAMVAY', 26.50, 16.50);
    addPrice('Teleferik', 'TELEFERİK', 25.00, 15.00);

    final ringler = await db.rawQuery("SELECT code, name FROM hat WHERE code LIKE 'R%' OR name LIKE 'RING%'");
    for (var r in ringler) addPrice(r['name'] as String, r['code'] as String, 17.00, 12.00);

    final ekspres = await db.rawQuery("SELECT code, name FROM hat WHERE code LIKE 'E%' OR name LIKE 'E%'");
    for (var e in ekspres) addPrice(e['name'] as String, e['code'] as String, 23.50, 15.00);

    final tekneler = await db.rawQuery("SELECT code, name FROM hat WHERE name LIKE '%SAMSUNUM%' OR name LIKE '%GEMİ%'");
    for (var t in tekneler) addPrice(t['name'] as String, t['code'] as String, 200.00, 150.00);

    final samair = await db.rawQuery("SELECT code, name FROM hat WHERE code LIKE 'H_%'");
    for (var s in samair) addPrice(s['name'] as String, s['code'] as String, 120.00, 60.00);

    final odak = await db.rawQuery("SELECT code, name FROM hat WHERE code LIKE 'G_%'");
    for (var o in odak) addPrice(o['name'] as String, o['code'] as String, 250.00, 200.00);

    final ilce = await db.rawQuery("SELECT code, name FROM hat WHERE tip='ilce'");
    for (var i in ilce) addPrice(i['name'] as String, i['code'] as String, 60.00, 30.00);

    await batch.commit(noResult: true);
    print('✅ Sabit Fiyatlar eklendi.');
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
    await db.delete(DatabaseHelper.tableSefer);
    await db.delete(DatabaseHelper.tableFiyat);
    await db.delete(DatabaseHelper.tableOdak);
    await db.delete(DatabaseHelper.tableOdakDurak);
    await db.delete(DatabaseHelper.tableSamair);
    await db.delete(DatabaseHelper.tableSamairDurak);
    await db.delete(DatabaseHelper.tableSamairSefer);

    await _fetchAndSaveHats();
    await _fetchAndSaveDuraklar();
    await _fetchAndSaveGuzergahlar();
    await _fetchAndSaveSeferler();
    await _fetchAndSaveOdak();
    await _fetchAndSaveSamair();
    await _injectFixedPrices();
    
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
    if (['TERME','ÇARŞAMBA','BAFRA','HAVZA','LADİK','KAVAK','ASARCIK','SALIPAZARI','TEKKEKÖY','ALAÇAM','AYVACIK','VEZİRKÖPRÜ','YAKAKENT','19 MAYIS','ONDOKUZMAYIS'].any((ilce) => n.contains(ilce))) return 'ilce';
    
    return 'otobus';
  }
}
