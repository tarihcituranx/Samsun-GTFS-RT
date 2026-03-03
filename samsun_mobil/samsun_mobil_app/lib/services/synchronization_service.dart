
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:samsun_mobil_app/helpers/database_helper.dart';
import 'package:samsun_mobil_app/services/price_service.dart';
import 'package:sqflite/sqflite.dart';

// samsun.py'nin Collector sınıfının mantığını Flutter/Dart'a taşıyan servis.
// API'lerden veri toplar, temizler, işler ve yerel SQLite veritabanını doldurur.
// Tüm çağrılar Render proxy üzerinden geçer (proje şeması gereği).
class SynchronizationService {
  final dbHelper = DatabaseHelper.instance;
  static const _renderBase = 'https://samsun-gtfs-rt.onrender.com/api';

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
    String fixedText = text;
    _turkishCharacterFixes.forEach((key, value) {
      fixedText = fixedText.replaceAll(key, value);
    });
    return fixedText.trim();
  }

  // --- API Çağrıları (Render Proxy üzerinden — proje şeması gereği) ---
  Future<List<dynamic>> _asisApiCall(String endpoint, {Map<String, String>? params}) async {
    try {
      // ASIS çağrıları proxy üzerinden: /api/proxy/realtime, /api/proxy/smart_stations vb.
      // Genel endpoint'ler için: /api/hat, /api/hat/durak/{code} vb.
      String proxyEndpoint;
      if (endpoint == 'Lines' || endpoint == 'OrjLines') {
        proxyEndpoint = '$_renderBase/hat';
      } else if (endpoint == 'StopsStations') {
        final lineCode = params?['lineCode'];
        proxyEndpoint = lineCode != null && lineCode.isNotEmpty
            ? '$_renderBase/hat/durak/${Uri.encodeComponent(lineCode)}'
            : '$_renderBase/proxy/smart_stations';
        params = lineCode != null ? null : params; // proxy/hat/durak yolunda param gerekmez
      } else if (endpoint == 'Schedules') {
        final lineCode = params?['lineCode'] ?? '';
        proxyEndpoint = '$_renderBase/hat/sefer/${Uri.encodeComponent(lineCode)}';
        params = null;
      } else if (endpoint == 'RealTimeData') {
        proxyEndpoint = '$_renderBase/proxy/realtime';
      } else if (endpoint == 'SmartStations') {
        proxyEndpoint = '$_renderBase/proxy/smart_stations';
      } else {
        proxyEndpoint = '$_renderBase/proxy/${endpoint.toLowerCase()}';
      }

      final uri = params != null && params.isNotEmpty
          ? Uri.parse(proxyEndpoint).replace(queryParameters: params)
          : Uri.parse(proxyEndpoint);
      final response = await http.get(uri, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 15));
      if (response.statusCode == 200 && response.body.isNotEmpty) {
        var decoded = json.decode(response.body);
        if (decoded is Map && decoded.containsKey('data')) return decoded['data'] is List ? decoded['data'] : [];
        if (decoded is List) return decoded;
        return [decoded];
      }
    } catch (e) {
      print('Proxy API Hatası ($endpoint): $e');
    }
    return [];
  }

  Future<List<dynamic>> _ybsApiCall(String module, String method, {Map<String, String>? params}) async {
    try {
      // YBS çağrıları da proxy üzerinden: odak, samair vb.
      String proxyEndpoint;
      if (module.contains('odak')) {
        if (method == 'HatlarList' || method == 'HatlarAllList') {
          proxyEndpoint = '$_renderBase/proxy_odak';
        } else if (method.contains('Durak')) {
          final kodu = params?['kodu'] ?? '';
          proxyEndpoint = '$_renderBase/odak/$kodu/durak';
          params = null;
        } else {
          proxyEndpoint = '$_renderBase/odak';
        }
      } else if (module.contains('samair')) {
        if (method == 'LokasyonlarList') {
          proxyEndpoint = '$_renderBase/samair';
        } else if (method == 'HatlarList') {
          final hatid = params?['hatid'] ?? '';
          proxyEndpoint = '$_renderBase/proxy_samair_saatler?hatid=$hatid';
          params = null;
        } else if (method == 'araclar') {
          proxyEndpoint = '$_renderBase/proxy_samair_araclar';
        } else if (method.contains('Durak')) {
          final hatid = params?['hatid'] ?? params?['hat'] ?? '';
          proxyEndpoint = '$_renderBase/samair/$hatid/durak';
          params = null;
        } else {
          proxyEndpoint = '$_renderBase/samair';
        }
      } else {
        proxyEndpoint = '$_renderBase/proxy_odak';
      }

      final uri = params != null && params.isNotEmpty
          ? Uri.parse(proxyEndpoint).replace(queryParameters: params)
          : Uri.parse(proxyEndpoint);
      final response = await http.get(uri, headers: {
        'User-Agent': 'SamsunMobilApp/2.0',
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 15));
      if (response.statusCode == 200 && response.body.isNotEmpty) {
        var decoded = json.decode(response.body);
        if (decoded is Map && decoded.containsKey('data')) return decoded['data'] is List ? decoded['data'] : [];
        if (decoded is Map && decoded.containsKey('root')) return decoded['root'] is List ? decoded['root'] : [];
        if (decoded is List) return decoded;
        return [decoded];
      }
    } catch (e) {
      print('YBS Proxy Hatası ($module/$method): $e');
    }
    return [];
  }

  // --- Veri Çekme ve İşleme Fonksiyonları (samsun.py'nin Collector metotları) ---

  Future<void> _fetchAndSaveHats() async {
    print('📥 Hatlar çekiliyor...');
    final db = await dbHelper.database;
    
    // Proxy /api/hat hem Lines hem OrjLines'ı birleşik döner
    List<dynamic> lines = await _asisApiCall('Lines');

    Set<String> seenCodes = {};
    List<Map<String, dynamic>> hatsToInsert = [];

    for (var l in lines) {
      // Proxy format: {code, name, tip, kat} | ASIS format: {lineCode, lineName, tip}
      String code = _fixText((l['code'] ?? l['lineCode'] ?? '').toString());
      String name = _fixText((l['name'] ?? l['lineName'] ?? code).toString());
      if (code.isNotEmpty && !seenCodes.contains(code)) {
        bool shouldSkip = _skipKeywords.any((kw) => code.toUpperCase().contains(kw) || name.toUpperCase().contains(kw));
        if (shouldSkip) continue;

        hatsToInsert.add({
          'code': code,
          'name': name,
          'tip': (l['tip'] ?? 'gidis').toString(),
          'kat': _categorizeHat(code, name),
        });
        seenCodes.add(code);
      }
    }

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
    // Proxy /api/hat/durak veya fallback ASIS StopsStations
    List<dynamic> stops = await _asisApiCall('StopsStations');

    List<Map<String, dynamic>> duraklarToInsert = [];
    Set<String> seenIds = {};

    for (var s in stops) {
      // Proxy format: {id, hat, durak_id, ad, sira, lat, lon} | ASIS format: {stopId, stopName, latitude, longitude}
      String stopId = (s['id'] ?? s['durak_id'] ?? s['stopId'] ?? '').toString();
      if (stopId.isNotEmpty && !seenIds.contains(stopId)) {
        double lat = double.tryParse((s['lat'] ?? s['latitude'] ?? '0').toString().replaceAll(',', '.')) ?? 0.0;
        double lon = double.tryParse((s['lon'] ?? s['longitude'] ?? '0').toString().replaceAll(',', '.')) ?? 0.0;

        if (lat < 40 || lat > 43 || lon < 34 || lon > 38) continue;

        String ad = _fixText((s['ad'] ?? s['stopName'] ?? '').toString());
        String kod = (s['kod'] ?? '').toString();
        if (kod.isEmpty) {
          final match = RegExp(r'^(\d+)').firstMatch(ad);
          if (match != null) kod = match.group(1)!;
        }

        duraklarToInsert.add({'id': stopId, 'kod': kod, 'ad': ad, 'lat': lat, 'lon': lon});
        seenIds.add(stopId);
      }
    }

    duraklarToInsert.add({'id': 'T1', 'kod': 'T1', 'ad': 'Teleferik Alt İstasyon', 'lat': 41.3204, 'lon': 36.3231});
    duraklarToInsert.add({'id': 'T2', 'kod': 'T2', 'ad': 'Teleferik Üst İstasyon', 'lat': 41.3246, 'lon': 36.3228});

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

    await db.delete(DatabaseHelper.tableHatDurak);

    int i = 0;
    for (var hat in hats) {
      String code = hat['code'] as String;
      List<dynamic> stopsOnRoute = await _asisApiCall('StopsStations', params: {'lineCode': code});
      
      if (stopsOnRoute.isNotEmpty) {
        final batch = db.batch();
        for (var s in stopsOnRoute) {
            // Proxy format: {hat, ad, kod, sira, lat, lon} | ASIS format: {stopId, stopName, latitude, longitude, orderId}
            double lat = double.tryParse((s['lat'] ?? s['latitude'] ?? '0').toString().replaceAll(',', '.')) ?? 0.0;
            double lon = double.tryParse((s['lon'] ?? s['longitude'] ?? '0').toString().replaceAll(',', '.')) ?? 0.0;
            if (lat < 40 || lat > 43 || lon < 34 || lon > 38) continue;

            batch.insert(DatabaseHelper.tableHatDurak, {
              'hat': code,
              'durak_id': (s['durak_id'] ?? s['kod'] ?? s['stopId'] ?? '').toString(),
              'ad': _fixText((s['ad'] ?? s['stopName'] ?? '').toString()),
              'sira': int.tryParse((s['sira'] ?? s['orderId'] ?? '0').toString()) ?? 0,
              'lat': lat,
              'lon': lon,
            });
        }
        await batch.commit(noResult: true);
      }
      i++;
      if (i % 20 == 0) {
        print('   ... $i / ${hats.length} güzergah işlendi.');
      }
    }
    
    // --- TELEFERİK GÜZERGAHI (Manuel Ekleme) ---
    final teleferikHat = hats.where((h) => h['code'].toString().contains('TELEFERİK')).toList();
    if (teleferikHat.isNotEmpty) {
      String tCode = teleferikHat.first['code'] as String;
      final tBatch = db.batch();
      tBatch.insert(DatabaseHelper.tableHatDurak, {'hat': tCode, 'durak_id': 'T1', 'ad': 'Teleferik Alt İstasyon', 'sira': 1, 'lat': 41.3204, 'lon': 36.3231});
      tBatch.insert(DatabaseHelper.tableHatDurak, {'hat': tCode, 'durak_id': 'T2', 'ad': 'Teleferik Üst İstasyon', 'sira': 2, 'lat': 41.3246, 'lon': 36.3228});
      await tBatch.commit(noResult: true);
      print('🚠 Teleferik güzergahı eklendi.');
    }

    print('✅ Güzergahlar tamamlandı.');
  }

  Future<void> _fetchAndSaveSeferler() async {
    print('📥 Seferler çekiliyor...');
    final db = await dbHelper.database;
    final hats = await db.query(DatabaseHelper.tableHat, columns: ['code']);

    int count = 0;
    for (var hat in hats) {
      String code = hat['code'] as String;
      List<dynamic> schedules = await _asisApiCall('Schedules', params: {'lineCode': code});
      
      if (schedules.isNotEmpty) {
        final batch = db.batch();
        for (var d in schedules) {
          // Proxy format: {hat, saat, yon, gun} | ASIS format: {saat, time, yon}
          String saat = (d['saat'] ?? d['time'] ?? '').toString();
          String yon = (d['yon'] ?? '').toString();
          if (saat.isNotEmpty) {
            batch.insert(DatabaseHelper.tableSefer, {
              'hat': code,
              'saat': saat,
              'yon': yon,
              'gun': (d['gun'] ?? 'hergun').toString(),
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
        // Proxy format: {id, kod, ad, gunler} | YBS format: {kodu, adi, gunler}
        String code = (h['id'] ?? h['kod'] ?? h['kodu'] ?? '').toString();
        String name = (h['ad'] ?? h['adi'] ?? '').toString();
        String gCode = code.startsWith('G_') ? code : "G_$code";
        
        hatBatch.insert(DatabaseHelper.tableOdak, {
          'id': code,
          'ad': name,
          'kod': gCode,
          'gunler': (h['gunler'] ?? '').toString(),
        });

        hatBatch.insert(DatabaseHelper.tableHat, {
          'code': gCode,
          'name': name,
          'tip': 'odak',
          'kat': 'odak',
        }, conflictAlgorithm: ConflictAlgorithm.ignore);

        // Durakları proxy'den çek (fiyat dahil)
        List<dynamic> duraklar = await _ybsApiCall('odak_otobussefer_public', 'DuraklarByKodu', params: {'kodu': code});
        if (duraklar.isNotEmpty) {
           final dBatch = db.batch();
           for (var i = 0; i < duraklar.length; i++) {
              var d = duraklar[i];
              // Proxy format: {ad, kod, sira, lat, lon, fiyat, fiyat_ogr} | YBS format: {durak_adi, durak_kodu, lat, lon, fiyat, fiyat_ogr}
              double lat = double.tryParse((d['lat'] ?? '0').toString()) ?? 0;
              double lon = double.tryParse((d['lon'] ?? '0').toString()) ?? 0;
              dBatch.insert(DatabaseHelper.tableOdakDurak, {
                  'hat': gCode,
                  'ad': (d['ad'] ?? d['durak_adi'] ?? '').toString(),
                  'kod': (d['kod'] ?? d['durak_kodu'] ?? '').toString(),
                  'sira': int.tryParse((d['sira'] ?? '${i+1}').toString()) ?? (i+1),
                  'lat': lat,
                  'lon': lon,
                  'fiyat': (d['fiyat'] ?? d['durak_fiyat'] ?? '').toString(),
                  'fiyat_ogr': (d['fiyat_ogr'] ?? d['durak_fiyat_ogr'] ?? '').toString(),
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
         // Proxy format: {id, kod, ad} | YBS format: {id, adi}
         String name = (h['ad'] ?? h['adi'] ?? '').toString();
         String id = (h['id'] ?? '').toString();
         String kod = (h['kod'] ?? 'H_$id').toString();
         
         batch.insert(DatabaseHelper.tableSamair, {
           'id': int.tryParse(id) ?? 0,
           'ad': name,
           'kod': kod,
         });

         batch.insert(DatabaseHelper.tableHat, {
           'code': kod,
           'name': name,
           'tip': 'havalimani',
           'kat': 'havalimani',
         }, conflictAlgorithm: ConflictAlgorithm.ignore);
         
         hatCount++;

         List<dynamic> seferler = await _ybsApiCall('samair_ucaksefersaatleri_public', 'HatlarList', params: {'hatid': id});
         if (seferler.isNotEmpty) {
             final sfBatch = db.batch();
             for (var sf in seferler) {
                 // Proxy format: {saat, varis, firma, ucak_saat, tarih, gun_format}
                 // YBS format: {saat, varis_saati, ucak_firmasi, ucak_saatleri, tarih, formatted_date}
                 sfBatch.insert(DatabaseHelper.tableSamairSefer, {
                     'hat': int.tryParse(id) ?? 0,
                     'saat': (sf['saat'] ?? '').toString(),
                     'varis': (sf['varis'] ?? sf['varis_saati'] ?? '').toString(),
                     'firma': (sf['firma'] ?? sf['ucak_firmasi'] ?? '').toString(),
                     'ucak_saat': (sf['ucak_saat'] ?? sf['ucak_saatleri'] ?? '').toString(),
                     'tarih': (sf['tarih'] ?? '').toString(),
                     'gun_format': (sf['gun_format'] ?? sf['formatted_date'] ?? '').toString(),
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
    print('💰 Sabit Fiyatlar Ekleniyor (son güncelleme fallback)...');
    final db = await dbHelper.database;
    final now = DateTime.now().toIso8601String();
    
    // Önce proxy'den tüm fiyatları çekmeyi dene (samsun.py'nin samulas.com.tr'den çektiği güncel veriler)
    bool proxySuccess = false;
    try {
      final response = await http.get(
        Uri.parse('https://samsun-gtfs-rt.onrender.com/api/hat'),
        headers: {'User-Agent': 'SamsunMobilApp/2.0'},
      ).timeout(const Duration(seconds: 12));
      
      if (response.statusCode == 200) {
        final hatlar = json.decode(response.body);
        if (hatlar is List && hatlar.isNotEmpty) {
          final batch = db.batch();
          int count = 0;
          for (var hat in hatlar) {
            final code = (hat['code'] ?? '').toString();
            if (code.isEmpty) continue;
            try {
              final fiyatResp = await http.get(
                Uri.parse('https://samsun-gtfs-rt.onrender.com/api/hat/fiyat/${Uri.encodeComponent(code)}'),
                headers: {'User-Agent': 'SamsunMobilApp/2.0'},
              ).timeout(const Duration(seconds: 5));
              
              if (fiyatResp.statusCode == 200) {
                final fiyat = json.decode(fiyatResp.body);
                final tam = (fiyat['tam_fiyat'] as num?)?.toDouble() ?? 0;
                final ind = (fiyat['indirimli_fiyat'] as num?)?.toDouble() ?? 0;
                if (tam > 0) {
                  batch.insert(DatabaseHelper.tableFiyat, {
                    'kaynak': 'proxy',
                    'hat_adi': hat['name'] ?? code,
                    'hat_code': code,
                    'tam_fiyat': tam,
                    'ogrenci_fiyat': ind,
                    'guncelleme': now,
                  }, conflictAlgorithm: ConflictAlgorithm.replace);
                  count++;
                }
              }
            } catch (_) {}
            // Rate limiting: çok hızlı istek atmayalım
            if (count % 10 == 0) await Future.delayed(const Duration(milliseconds: 200));
          }
          if (count > 0) {
            await batch.commit(noResult: true);
            proxySuccess = true;
            print('✅ Proxy fiyatlar: $count hat güncellendi');
          }
        }
      }
    } catch (e) {
      print('⚠️ Proxy fiyat çekme hatası: $e');
    }

    // Proxy başarısız olduysa fallback: Kategori bazlı varsayılan fiyatlar
    if (!proxySuccess) {
      print('⚠️ Proxy fiyatlar alınamadı, kategori bazlı fallback kullanılıyor...');
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

      // Kategori fiyatları — GitHub prices.json fallback ile senkronize
      final prices = await PriceService.fetchPrices();
      final defTam = ((prices['default']?['tam']) ?? 20.0).toDouble();
      final defInd = ((prices['default']?['indirimli']) ?? 14.0).toDouble();
      final tramTam = ((prices['tramvay']?['tam']) ?? 30.0).toDouble();
      final tramInd = ((prices['tramvay']?['indirimli']) ?? 19.0).toDouble();
      final telTam = ((prices['teleferik']?['tam']) ?? 30.0).toDouble();
      final telInd = ((prices['teleferik']?['indirimli']) ?? 18.0).toDouble();
      final expTam = ((prices['ekspres']?['tam']) ?? 27.0).toDouble();
      final expInd = ((prices['ekspres']?['indirimli']) ?? 17.0).toDouble();
      final hvlTam = ((prices['havalimani']?['tam']) ?? 140.0).toDouble();
      final hvlInd = ((prices['havalimani']?['indirimli']) ?? 70.0).toDouble();
      final odakTam = ((prices['odak']?['tam']) ?? 280.0).toDouble();
      final odakInd = ((prices['odak']?['indirimli']) ?? 225.0).toDouble();
      final ilcTam = ((prices['ilce']?['tam']) ?? 70.0).toDouble();
      final ilcInd = ((prices['ilce']?['indirimli']) ?? 35.0).toDouble();

      addPrice('Tramvay', 'SAMULAŞ - TRAMVAY', tramTam, tramInd);
      addPrice('Teleferik', 'TELEFERİK', telTam, telInd);

      final ringler = await db.rawQuery("SELECT code, name FROM hat WHERE code LIKE 'R%' OR name LIKE 'RING%'");
      for (var r in ringler) {
        addPrice(r['name'] as String, r['code'] as String, defTam, defInd);
      }

      final ekspres = await db.rawQuery("SELECT code, name FROM hat WHERE code LIKE 'E%' OR name LIKE 'E%'");
      for (var e in ekspres) {
        addPrice(e['name'] as String, e['code'] as String, expTam, expInd);
      }

      final tekneler = await db.rawQuery("SELECT code, name FROM hat WHERE name LIKE '%SAMSUNUM%' OR name LIKE '%GEMİ%'");
      for (var t in tekneler) {
        addPrice(t['name'] as String, t['code'] as String, ((prices['SAMSUNUM-1']?['tam']) ?? 225.0).toDouble(), ((prices['SAMSUNUM-1']?['indirimli']) ?? 170.0).toDouble());
      }

      final samair = await db.rawQuery("SELECT code, name FROM hat WHERE code LIKE 'H_%'");
      for (var s in samair) {
        addPrice(s['name'] as String, s['code'] as String, hvlTam, hvlInd);
      }

      final odak = await db.rawQuery("SELECT code, name FROM hat WHERE code LIKE 'G_%'");
      for (var o in odak) {
        addPrice(o['name'] as String, o['code'] as String, odakTam, odakInd);
      }

      final ilce = await db.rawQuery("SELECT code, name FROM hat WHERE tip='ilce'");
      for (var i in ilce) {
        addPrice(i['name'] as String, i['code'] as String, ilcTam, ilcInd);
      }

      await batch.commit(noResult: true);
      print('✅ Fallback fiyatlar eklendi.');
    }
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

    // Odak turistik hatlar
    if (n.contains('SAMSUNUM') || n.contains('ALTINKAYA') || n.contains('ODAK') || c.contains('SAMSUNUM')) return 'odak';
    // Tekne/deniz
    if (n.contains('BANDIRMA') || n.contains('VAPUR') || (n.contains('FERİBOT') && !n.contains('TELEFERİK'))) return 'tekne';
    // Ring
    if (c.startsWith('R') && c.length > 1 && int.tryParse(c.substring(1, 2)) != null) return 'ring';
    if (n.contains('TRAMVAY')) return 'tramvay';
    if (n.contains('TELEFERİK')) return 'teleferik';
    if (c.startsWith('H') && c.length > 1 && int.tryParse(c.substring(1, 2)) != null) return 'havalimani';
    if (n.contains('EKSPRES') || (c.startsWith('E') && c.length > 1 && int.tryParse(c.substring(1, 2)) != null)) return 'ekspres';
    if (['TERME','ÇARŞAMBA','BAFRA','HAVZA','LADİK','KAVAK','ASARCIK','SALIPAZARI','TEKKEKÖY','ALAÇAM','AYVACIK','VEZİRKÖPRÜ','YAKAKENT','19 MAYIS','ONDOKUZMAYIS'].any((ilce) => n.contains(ilce))) return 'ilce';
    
    return 'otobus';
  }
}
