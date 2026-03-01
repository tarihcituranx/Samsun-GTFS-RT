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

  // --- FAZ 6: Tam Bağımsız Offline Rota Hesaplama Motoru --- 

  // Haversine method for offline distance calculation between coordinates
  double _calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    var p = 0.017453292519943295; // Math.PI / 180
    var c = math.cos;
    var a = 0.5 - c((lat2 - lat1) * p) / 2 +
        c(lat1 * p) * c(lat2 * p) * (1 - c((lon2 - lon1) * p)) / 2;
    return 12742 * math.asin(math.sqrt(a)); // 2 * R; R = 6371 km
  }

  // Pure SQLite/Dart Routing Algorithm
  Future<List<Map<String, dynamic>>> calculateRouteLocally(double startLat, double startLon, double destLat, double destLon, {double radiusParams = 1.0}) async {
    final db = await database;
    List<Map<String, dynamic>> allRoutes = [];
    
    // 1. Find Stops near Start location (Set A)
    final allStops = await db.query('durak');
    List<int> startStops = [];
    List<int> endStops = [];
    
    for (var d in allStops) {
      double lat = d['lat'] as double;
      double lon = d['lon'] as double;
      if (_calculateDistance(startLat, startLon, lat, lon) <= radiusParams) {
        startStops.add(d['id'] as int);
      }
      if (_calculateDistance(destLat, destLon, lat, lon) <= radiusParams) {
        endStops.add(d['id'] as int);
      }
    }

    if (startStops.isEmpty || endStops.isEmpty) {
       return []; // Target or Start doesn't have any nearby bus stops
    }

    String startSet = startStops.join(',');
    String endSet = endStops.join(',');

    // 2. Direct Routes (SQL INTERSECT)
    String directQuery = """
      SELECT h1.hat as code, 
             h1.durak_ad as s_ad, h1.sira as s_sira, h1.durak_id as s_id,
             h2.durak_ad as e_ad, h2.sira as e_sira, h2.durak_id as e_id,
             (h2.sira - h1.sira) as stop_diff
      FROM hat_durak h1
      JOIN hat_durak h2 ON h1.hat = h2.hat AND h1.direction_id = h2.direction_id
      WHERE h1.durak_id IN ($startSet) 
        AND h2.durak_id IN ($endSet)
        AND h1.sira < h2.sira
      ORDER BY stop_diff ASC
      LIMIT 10
    """;

    try {
      final directResults = await db.rawQuery(directQuery);
      
      for (var r in directResults) {
        // Calculate basic Polyline path for rendering
        int pMin = r['s_sira'] as int;
        int pMax = r['e_sira'] as int;
        String lineCode = r['code'] as String;
        
        final pathRows = await db.rawQuery(
          "SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira",
          [lineCode, pMin, pMax]
        );
        
        List<List<double>> coords = pathRows.map((row) => [row['lat'] as double, row['lon'] as double]).toList();

        allRoutes.add({
          'type': 'DIRECT',
          'total_score': r['stop_diff'], // Less stops = better score
          'polyline': coords,
          'desc': "Mevcut konumunuzdan doğrudan $lineCode hattına binin. ${r['s_ad']} durağından binip ${r['e_ad']} durağında inin.",
          'details': r
        });
      }
    } catch(e) {
      print("Offline Direct Route Error: \$e");
    }

    // 3. One-Transfer Routes (If no direct route)
    if (allRoutes.isEmpty) {
      String transferQuery = """
        SELECT h1.hat as hat1, h1.durak_ad as s1_ad, h1.sira as s1_sira, h1.durak_id as s1_id,
               h2.durak_ad as t1_ad, h2.sira as t1_sira, h2.durak_id as t1_id,
               h3.hat as hat2, h3.durak_ad as t2_ad, h3.sira as t2_sira, h3.durak_id as t2_id,
               h4.durak_ad as e_ad, h4.sira as e_sira, h4.durak_id as e_id
        FROM hat_durak h1
        JOIN hat_durak h2 ON h1.hat = h2.hat AND h1.direction_id = h2.direction_id
        JOIN hat_durak h3 ON h2.durak_id = h3.durak_id AND h1.hat != h3.hat
        JOIN hat_durak h4 ON h3.hat = h4.hat AND h3.direction_id = h4.direction_id
        WHERE h1.durak_id IN ($startSet)
          AND h4.durak_id IN ($endSet)
          AND h1.sira < h2.sira
          AND h3.sira < h4.sira
        LIMIT 5
      """;
      
      try {
        final transferResults = await db.rawQuery(transferQuery);
        // Map transfer results similarly...
        for (var r in transferResults) {
             List<List<double>> coords = [];
             // Leg 1
             final p1Rows = await db.rawQuery("SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira",
                [r['hat1'], r['s1_sira'], r['t1_sira']]);
             coords.addAll(p1Rows.map((row) => [row['lat'] as double, row['lon'] as double]).toList());
             // Leg 2
             final p2Rows = await db.rawQuery("SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira",
                [r['hat2'], r['t2_sira'], r['e_sira']]);
             coords.addAll(p2Rows.map((row) => [row['lat'] as double, row['lon'] as double]).toList());

             allRoutes.add({
                'type': 'TRANSFER',
                'total_score': ((r['t1_sira'] as int) - (r['s1_sira'] as int)) + ((r['e_sira'] as int) - (r['t2_sira'] as int)) + 15,
                'polyline': coords,
                'desc': "Önce ${r['s1_ad']} durağından ${r['hat1']} nolu hatta binin. ${r['t1_ad']} durağında inin ve ${r['hat2']} hattına aktarma yapın. ${r['e_ad']} durağında inin.",
                'details': r
             });
        }
      } catch(e) {
        print("Offline Transfer Route Error: \$e");
      }
    }

    // Sort by score
    allRoutes.sort((a, b) => (a['total_score'] as int).compareTo(b['total_score'] as int));
    
    return allRoutes;
  }
}
