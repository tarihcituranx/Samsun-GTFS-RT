
import 'dart:io';
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';
import 'package:path_provider/path_provider.dart';

// samsun.py'nin veritabanı şemasını temel alan merkezi veritabanı yardımcısı.
class DatabaseHelper {

  static final _databaseName = "SamsunTransit.db";
  static final _databaseVersion = 1;

  // Tablo ve Sütun Adları (samsun.py'den alınmıştır)
  static final tableHat = 'hat';
  static final tableDurak = 'durak';
  static final tableHatDurak = 'hat_durak';
  static final tableSefer = 'sefer';
  static final tableFiyat = 'fiyat';
  static final tableOdak = 'odak';
  static final tableOdakDurak = 'odak_durak';
  static final tableSamair = 'samair';
  static final tableSamairDurak = 'samair_durak';
  static final tableSamairSefer = 'samair_sefer';
  static final tableMeta = 'meta';


  // Singleton sınıf yapısı
  DatabaseHelper._privateConstructor();
  static final DatabaseHelper instance = DatabaseHelper._privateConstructor();

  // Sadece tek bir uygulama çapında veritabanı referansı
  static Database? _database;
  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  // Veritabanını açar, eğer yoksa oluşturur.
  _initDatabase() async {
    Directory documentsDirectory = await getApplicationDocumentsDirectory();
    String path = join(documentsDirectory.path, _databaseName);
    return await openDatabase(path,
        version: _databaseVersion,
        onCreate: _onCreate);
  }

  // Veritabanı ilk kez oluşturulduğunda tabloları yaratan SQL komutları.
  // Bu şema, samsun.py'nin _create_tables fonksiyonundan esinlenmiştir.
  Future _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE $tableMeta(
        key TEXT PRIMARY KEY, 
        value TEXT
      )
      ''');

    await db.execute('''
      CREATE TABLE $tableHat (
        code TEXT PRIMARY KEY, 
        name TEXT, 
        tip TEXT, 
        kat TEXT,
        alias TEXT, 
        short_name TEXT
      )
      ''');

    await db.execute('''
      CREATE TABLE $tableDurak (
        id TEXT PRIMARY KEY, 
        kod TEXT, 
        ad TEXT, 
        lat REAL, 
        lon REAL
      )
      ''');

    await db.execute('''
      CREATE TABLE $tableHatDurak (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        hat TEXT, 
        durak_id TEXT, 
        ad TEXT, 
        sira INT, 
        lat REAL, 
        lon REAL,
        FOREIGN KEY (hat) REFERENCES $tableHat (code),
        FOREIGN KEY (durak_id) REFERENCES $tableDurak (id)
      )
      ''');
    
    await db.execute('''
      CREATE TABLE $tableSefer (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        hat TEXT, 
        saat TEXT, 
        yon TEXT, 
        gun TEXT,
        FOREIGN KEY (hat) REFERENCES $tableHat (code)
      )
      ''');

    await db.execute('''
      CREATE TABLE $tableFiyat (
        id INTEGER PRIMARY KEY,
        kaynak TEXT, 
        hat_adi TEXT, 
        hat_code TEXT,
        tam_fiyat REAL DEFAULT 0, 
        ogrenci_fiyat REAL DEFAULT 0,
        guncelleme TEXT
      )
      ''');
    
    await db.execute('''
      CREATE TABLE $tableOdak (
        id TEXT PRIMARY KEY, 
        ad TEXT, 
        kod TEXT, 
        gunler TEXT
      )
      ''');

    await db.execute('''
      CREATE TABLE $tableOdakDurak (
        id INTEGER PRIMARY KEY, 
        hat TEXT, 
        ad TEXT, 
        kod TEXT, 
        sira INT, 
        lat REAL, 
        lon REAL, 
        fiyat TEXT, 
        fiyat_ogr TEXT
      )
      ''');
      
    await db.execute('''
      CREATE TABLE $tableSamair (
        id INTEGER PRIMARY KEY, 
        ad TEXT, 
        kod TEXT
      )
      ''');

    await db.execute('''
      CREATE TABLE $tableSamairDurak (
        id INTEGER PRIMARY KEY, 
        hat INTEGER, 
        ad TEXT, 
        kod TEXT, 
        sira INT, 
        lat REAL, 
        lon REAL, 
        fiyat TEXT
      )
      ''');

    await db.execute('''
      CREATE TABLE $tableSamairSefer (
        id INTEGER PRIMARY KEY, 
        hat INTEGER, 
        saat TEXT, 
        varis TEXT, 
        firma TEXT, 
        ucak_saat TEXT, 
        tarih TEXT, 
        gun_format TEXT
      )
      ''');
      
    // İndeksler (samsun.py'deki gibi)
    await db.execute("CREATE INDEX idx_hd ON $tableHatDurak(hat)");
    await db.execute("CREATE INDEX idx_sf ON $tableSefer(hat)");
    await db.execute("CREATE INDEX idx_dk_latlon ON $tableDurak(lat, lon)");
  }
}
