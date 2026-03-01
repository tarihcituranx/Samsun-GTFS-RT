import 'dart:io';
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
}
