
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:samsun_mobil_app/helpers/database_helper.dart';
import 'package:samsun_mobil_app/services/synchronization_service.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

// This test validates the core data synchronization logic of the application.
// It checks whether the SynchronizationService can successfully fetch data from APIs
// and populate the local database.
void main() {
  // This is CRUCIAL for tests that use platform channels (like path_provider).
  TestWidgetsFlutterBinding.ensureInitialized();

  // --- MOCK SETUP for path_provider ---
  // This is the core of the fix. We are manually creating a "fake" response
  // for the path_provider plugin. When the code asks for the documents directory,
  // this mock will intercept the call and provide a temporary directory for the test.
  const MethodChannel channel =
      MethodChannel('plugins.flutter.io/path_provider');
  
  // Before each test, set up the mock handler.
  setUp(() async {
    channel.setMockMethodCallHandler((MethodCall methodCall) async {
      if (methodCall.method == 'getApplicationDocumentsDirectory') {
        // Use the system's temp directory for a clean, isolated test environment.
        return Directory.systemTemp.createTempSync('test_db').path;
      }
      return null;
    });
  });

  // After each test, remove the mock handler to avoid conflicts with other tests.
  tearDown(() {
    channel.setMockMethodCallHandler(null);
  });
  // --- END MOCK SETUP ---

  // Initialize FFI for sqflite to work in a desktop environment (for command-line testing).
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  test('SynchronizationService should fetch data and populate the database', () async {
    // ARRANGE
    // Set up the synchronization service and database helper.
    final syncService = SynchronizationService();
    final dbHelper = DatabaseHelper.instance;
    
    // Start with a clean slate by deleting any old database file.
    await dbHelper.deleteDatabase();

    // ACT
    // Run the full synchronization process, which is the core function of the new architecture.
    // The 'force: true' parameter ensures the process runs even if a sync has occurred before.
    await syncService.runFullSynchronization(force: true);

    // ASSERT
    // Verify that the synchronization was successful.
    final db = await dbHelper.database;

    // 1. Check if the 'hat' table is populated.
    final hats = await db.query(DatabaseHelper.tableHat);
    print('Verification: Found ${hats.length} records in \'hat\' table.');
    expect(hats.isNotEmpty, isTrue, reason: 'The \'hat\' table should not be empty after synchronization.');

    // 2. Check if the 'durak' table is populated.
    final duraklar = await db.query(DatabaseHelper.tableDurak);
    print('Verification: Found ${duraklar.length} records in \'durak\' table.');
    expect(duraklar.isNotEmpty, isTrue, reason: 'The \'durak\' table should not be empty after synchronization.');
    
    // 3. Check if the 'hat_durak' (route) table is populated.
    final hatDuraklar = await db.query(DatabaseHelper.tableHatDurak);
    print('Verification: Found ${hatDuraklar.length} records in \'hat_durak\' table.');
    expect(hatDuraklar.isNotEmpty, isTrue, reason: 'The \'hat_durak\' table should not be empty after synchronization.');

  }, timeout: const Timeout(Duration(minutes: 5))); // Increase timeout for potentially long API calls.
}
