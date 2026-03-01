import 'dart:io';
import 'dart:math' as math;
import 'package:flutter/services.dart';
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

class DBService {
  static final DBService _instance = DBService._internal();
  factory DBService() => _instance;
  DBService._internal();

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDB();
    return _db!;
  }

  Future<Database> _initDB() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'samsun_mobil.db');

    // Cihazda DB yoksa assets'ten kopyala
    final exists = await databaseExists(path);
    if (!exists) {
      // Önce klasörü oluştur
      try {
        await Directory(dirname(path)).create(recursive: true);
      } catch (_) {}

      // Asset'ten byte olarak oku
      final data = await rootBundle.load('assets/samsun_mobil.db');
      final bytes = data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);

      // Cihazın hafızasına yaz
      await File(path).writeAsBytes(bytes, flush: true);
    }

    return await openDatabase(path, readOnly: true); // Sadece okuma
  }

  Future<List<Map<String, dynamic>>> getHatlar() async {
    final db = await database;
    return await db.query('hat');
  }

  Future<List<Map<String, dynamic>>> getDuraklar() async {
    final db = await database;
    return await db.query('durak');
  }

  Future<List<Map<String, dynamic>>> getDurakGuzergahi(String hatCode) async {
    final db = await database;
    return await db.query('hat_durak', where: 'hat = ?', whereArgs: [hatCode], orderBy: 'sira ASC');
  }

  Future<Map<String, dynamic>?> getFiyat(String hatCode) async {
    final db = await database;
    final res = await db.query('fiyat', where: 'hat_code = ?', whereArgs: [hatCode]);
    if (res.isNotEmpty) return res.first;
    return null;
  }

  Future<List<Map<String, dynamic>>> getOdaklar() async {
    final db = await database;
    return await db.query('odak');
  }

  Future<List<Map<String, dynamic>>> getOdakDuraklari(String hatId) async {
    final db = await database;
    return await db.query('odak_durak', where: 'hat = ?', whereArgs: [hatId], orderBy: 'sira ASC');
  }

  Future<List<Map<String, dynamic>>> getSeferler(String hatCode, {String? gun}) async {
    final db = await database;
    if (gun != null) {
      return await db.query('sefer', where: 'hat = ? AND gun = ?', whereArgs: [hatCode, gun], orderBy: 'saat ASC');
    }
    return await db.query('sefer', where: 'hat = ?', whereArgs: [hatCode], orderBy: 'saat ASC');
  }

  // --- FAZ 6: Tam Bağımsız Offline Rota Hesaplama Motoru --- 

  // Haversine method for offline distance calculation between coordinates
  double _calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    var p = 0.017453292519943295; // Math.PI / 180
    var c = math.cos;
    var a = 0.5 - c((lat2 - lat1) * p) / 2 +
        c(lat1 * p) * c(lat2 * p) * (1 - c((lon2 - lon1) * p)) / 2;
    return 12742 * math.asin(math.sqrt(a)); // 2 * R; R = 6371 km
  }

  // Pure SQLite/Dart Routing Algorithm - Tüm tip dönüşüm hataları düzeltildi
  Future<List<Map<String, dynamic>>> calculateRouteLocally(double startLat, double startLon, double destLat, double destLon, {double radiusParams = 1.0}) async {
    final db = await database;
    List<Map<String, dynamic>> allRoutes = [];

    // 1. Find Stops near Start and End locations
    final allStops = await db.query('durak');
    List<String> startStops = [];
    List<String> endStops = [];

    for (var d in allStops) {
      // lat/lon SQLite'tan REAL olarak gelir ama güvenli parse edelim
      final lat = (d['lat'] as num?)?.toDouble() ?? 0.0;
      final lon = (d['lon'] as num?)?.toDouble() ?? 0.0;
      final id = d['id']?.toString() ?? '';
      if (id.isEmpty) continue;

      if (_calculateDistance(startLat, startLon, lat, lon) <= radiusParams) {
        startStops.add("'$id'");
      }
      if (_calculateDistance(destLat, destLon, lat, lon) <= radiusParams) {
        endStops.add("'$id'");
      }
    }

    if (startStops.isEmpty || endStops.isEmpty) return [];

    final startSet = startStops.join(',');
    final endSet = endStops.join(',');

    // 2. Direct Routes - Schema'ya uygun (hat_durak kolonları: hat, durak_id, ad, sira, lat, lon)
    final directQuery = """
      SELECT h1.hat as code,
             h1.ad as s_ad, h1.sira as s_sira,
             h2.ad as e_ad, h2.sira as e_sira,
             (h2.sira - h1.sira) as stop_diff
      FROM hat_durak h1
      JOIN hat_durak h2 ON h1.hat = h2.hat
      WHERE h1.durak_id IN ($startSet)
        AND h2.durak_id IN ($endSet)
        AND h1.sira < h2.sira
      ORDER BY stop_diff ASC
      LIMIT 5
    """;

    try {
      final directResults = await db.rawQuery(directQuery);
      for (var r in directResults) {
        final pMin = (r['s_sira'] as num?)?.toInt() ?? 0;
        final pMax = (r['e_sira'] as num?)?.toInt() ?? 0;
        final lineCode = r['code']?.toString() ?? '';

        final pathRows = await db.rawQuery(
          "SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira",
          [lineCode, pMin, pMax]
        );

        final coords = pathRows.map((row) => [
          (row['lat'] as num?)?.toDouble() ?? 0.0,
          (row['lon'] as num?)?.toDouble() ?? 0.0,
        ]).toList();

        final stopDiff = (r['stop_diff'] as num?)?.toInt() ?? 99;
        // Tramvay önceliği: T1, T2 hatlarına puan avantajı
        final isTram = lineCode.startsWith('T');
        final tramBonus = isTram ? -20 : 0;
        allRoutes.add({
          'type': 'DIRECT',
          'total_score': stopDiff + tramBonus,
          'polyline': coords,
          'desc': "🚌 $lineCode hattına ${r['s_ad']} durağından binin → ${r['e_ad']} durağında inin. ($stopDiff durak)",
        });
      }
    } catch (e) {
      print("Direct Route Error: $e");
    }

    // 3. One-Transfer Routes (if no direct route found)
    if (allRoutes.isEmpty) {
      final transferQuery = """
        SELECT h1.hat as hat1, h1.ad as s_ad, h1.sira as s_sira,
               h2.ad as t_ad, h2.sira as t_sira, h2.durak_id as t_durak,
               h3.hat as hat2, h3.sira as t2_sira,
               h4.ad as e_ad, h4.sira as e_sira
        FROM hat_durak h1
        JOIN hat_durak h2 ON h1.hat = h2.hat
        JOIN hat_durak h3 ON h2.durak_id = h3.durak_id AND h1.hat != h3.hat
        JOIN hat_durak h4 ON h3.hat = h4.hat
        WHERE h1.durak_id IN ($startSet)
          AND h4.durak_id IN ($endSet)
          AND h1.sira < h2.sira
          AND h3.sira < h4.sira
        LIMIT 3
      """;

      try {
        final transferResults = await db.rawQuery(transferQuery);
        for (var r in transferResults) {
          final s1 = (r['s_sira'] as num?)?.toInt() ?? 0;
          final t1 = (r['t_sira'] as num?)?.toInt() ?? 0;
          final t2 = (r['t2_sira'] as num?)?.toInt() ?? 0;
          final e  = (r['e_sira'] as num?)?.toInt() ?? 0;
          List<List<double>> coords = [];

          final p1Rows = await db.rawQuery("SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira", [r['hat1'], s1, t1]);
          coords.addAll(p1Rows.map((row) => [(row['lat'] as num?)?.toDouble() ?? 0.0, (row['lon'] as num?)?.toDouble() ?? 0.0]));
          final p2Rows = await db.rawQuery("SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira", [r['hat2'], t2, e]);
          coords.addAll(p2Rows.map((row) => [(row['lat'] as num?)?.toDouble() ?? 0.0, (row['lon'] as num?)?.toDouble() ?? 0.0]));

          // Tramvay önceliği aktarmalı rotalarda da geçerli
          final hat1Str = r['hat1']?.toString() ?? '';
          final hat2Str = r['hat2']?.toString() ?? '';
          final hasTram = hat1Str.startsWith('T') || hat2Str.startsWith('T');
          final tramBonus2 = hasTram ? -15 : 0;
          allRoutes.add({
            'type': 'TRANSFER',
            'total_score': (t1 - s1) + (e - t2) + 15 + tramBonus2,
            'polyline': coords,
            'desc': "🚌 ${r['hat1']} hattına ${r['s_ad']} durağından binin → ${r['t_ad']} durağında inin.\n🔄 ${r['hat2']} hattına aktarın → ${r['e_ad']} durağında inin.",
          });
        }
      } catch (e) {
        print("Transfer Route Error: $e");
      }
    }

    allRoutes.sort((a, b) => (a['total_score'] as int).compareTo(b['total_score'] as int));
    return allRoutes;
  }
}

