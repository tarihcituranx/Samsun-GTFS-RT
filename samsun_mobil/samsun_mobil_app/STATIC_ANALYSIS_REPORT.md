# 🔍 Static Code Analysis Report — Samsun Mobil App

**Date:** Auto-generated  
**Scope:** Flutter/Dart source code in `samsun_mobil/samsun_mobil_app/`  
**Package Name (pubspec.yaml):** `samsun_mobil_app`

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 5 |
| 🟠 High | 9 |
| 🟡 Medium | 12 |
| 🔵 Low | 6 |
| **Total** | **32** |

---

## 🔴 CRITICAL Issues

### C1. Test files reference wrong package name `samsun_transit`
**Files:** `test/widget_test.dart:11`, `test/synchronization_test.dart:5-6`  
**Description:** Both test files import from `package:samsun_transit/...` but `pubspec.yaml` defines the package name as `samsun_mobil_app`. These tests will **fail to compile**.

```dart
// widget_test.dart line 11
import 'package:samsun_transit/main.dart';         // ❌ WRONG

// synchronization_test.dart lines 5-6
import 'package:samsun_transit/helpers/database_helper.dart';          // ❌ WRONG
import 'package:samsun_transit/services/synchronization_service.dart'; // ❌ WRONG
```

**Fix:**
```dart
import 'package:samsun_mobil_app/main.dart';
import 'package:samsun_mobil_app/helpers/database_helper.dart';
import 'package:samsun_mobil_app/services/synchronization_service.dart';
```

---

### C2. `widget_test.dart` references non-existent class `MyApp`
**File:** `test/widget_test.dart:16`  
**Description:** The test pumps `const MyApp()` but the actual app class in `main.dart` is `SamsunRouteApp`. Additionally, the test expects a counter app (0/1 increment) which has nothing to do with this transit app. This is a leftover Flutter template test.

**Fix:** Rewrite the test to reference `SamsunRouteApp` and test actual app behavior, or delete/stub it.

---

### C3. `synchronization_test.dart` calls non-existent method `DatabaseHelper.deleteDatabase()`
**File:** `test/synchronization_test.dart:53`  
**Description:** `DatabaseHelper` class in `lib/helpers/database_helper.dart` has no `deleteDatabase()` method. This will cause a compile error.

**Fix:** Add a `deleteDatabase()` method to `DatabaseHelper`:
```dart
Future<void> deleteDatabase() async {
  Directory documentsDirectory = await getApplicationDocumentsDirectory();
  String path = join(documentsDirectory.path, _databaseName);
  await databaseFactory.deleteDatabase(path);
  _database = null;
}
```

---

### C4. `synchronization_test.dart` depends on `sqflite_common_ffi` — not in pubspec.yaml
**File:** `test/synchronization_test.dart:7`  
**Description:** The test imports `package:sqflite_common_ffi/sqflite_ffi.dart` but this package is not listed in `pubspec.yaml` dev_dependencies. The test will fail to resolve.

**Fix:** Add to `pubspec.yaml` dev_dependencies:
```yaml
dev_dependencies:
  sqflite_common_ffi: ^2.3.0
```

---

### C5. `database_helper.dart` uses `path_provider` — not in pubspec.yaml dependencies
**File:** `lib/helpers/database_helper.dart:5`  
**Description:** `DatabaseHelper` imports `package:path_provider/path_provider.dart` and calls `getApplicationDocumentsDirectory()`, but `path_provider` is NOT listed as an explicit dependency in `pubspec.yaml`. It gets pulled in transitively (via sqflite/shared_preferences), but this is fragile and not guaranteed across versions.

**Fix:** Add explicit dependency:
```yaml
dependencies:
  path_provider: ^2.1.0
```

---

## 🟠 HIGH Issues

### H1. `Navigator.pushReplacement` — wrong method name
**File:** `lib/main.dart:91`  
**Description:** `Navigator.of(context).pushReplacement(...)` is not a valid Flutter Navigator method. The correct method is `pushReplacement` on `Navigator` (which expects a `Route`) — this actually works, but could be confused with `pushReplacementNamed`. However, `Navigator.of(context).pushReplacement(MaterialPageRoute(...))` IS valid in modern Flutter. *(Reviewed: this is actually correct.)*

**Severity downgraded:** This is valid. No issue.

---

### H2. `SynchronizationService().runFullSynchronization()` — fire-and-forget with no error handling
**File:** `lib/main.dart:94`  
**Description:** After navigating to `HomeScreen`, `runFullSynchronization()` is called as fire-and-forget. If it throws an exception, it will be completely unhandled and silently lost. This is a full database sync involving many HTTP calls.

**Fix:** Wrap in try-catch or add `.catchError()`:
```dart
SynchronizationService().runFullSynchronization().catchError((e) {
  debugPrint('Sync error: $e');
});
```

---

### H3. `OfflineService` — `StreamController` never closed
**File:** `lib/services/offline_service.dart:10`  
**Description:** `_offlineController` is a `StreamController<bool>.broadcast()` that is never closed/disposed. Since `OfflineService` is a singleton, this creates a permanent memory allocation. The stream listener in `home_screen.dart:77` is also never cancelled.

**Fix:** Add a `dispose()` method:
```dart
void dispose() {
  _timer?.cancel();
  _offlineController.close();
}
```
And cancel the subscription in `HomeScreen.dispose()`.

---

### H4. `offline_wakeup_screen.dart` — unsafe forced cast `widget.durak['lat'] as double`
**File:** `lib/screens/offline_wakeup_screen.dart:50-51`  
**Description:** The code does `widget.durak['lat'] as double` and `widget.durak['lon'] as double` — these are hard casts that will throw `_TypeError` at runtime if the value is `int`, `String`, or `null` (which is common from SQLite/JSON data).

**Fix:**
```dart
final dbLat = (widget.durak['lat'] as num?)?.toDouble() ?? 0.0;
final dbLon = (widget.durak['lon'] as num?)?.toDouble() ?? 0.0;
```

---

### H5. `offline_wakeup_screen.dart` — GPS stream never cancelled
**File:** `lib/screens/offline_wakeup_screen.dart:45-73`  
**Description:** `Geolocator.getPositionStream().listen(...)` starts a stream subscription but the `StreamSubscription` is never stored or cancelled. When the user navigates back or the widget is disposed, the stream will continue running in the background, potentially calling `setState` on an unmounted widget (the `mounted` check only prevents that specific call, but the stream itself wastes resources).

**Fix:** Store the subscription and cancel it in `dispose()`:
```dart
StreamSubscription<Position>? _positionSubscription;

void dispose() {
  _positionSubscription?.cancel();
  super.dispose();
}
```

---

### H6. Two conflicting database systems — `DBService` vs `DatabaseHelper`
**Files:** `lib/services/db_service.dart`, `lib/helpers/database_helper.dart`  
**Description:** The app has two independent database singletons:
- `DBService` — reads from a pre-bundled read-only `samsun_mobil.db` (asset).
- `DatabaseHelper` — creates a writable `SamsunTransit.db` from scratch.

`SynchronizationService` writes to `DatabaseHelper`'s database, but all screens (`HomeScreen`, `HatlarScreen`, `OdakScreen`, etc.) read from `DBService`'s database. **Data written by sync will never be seen by the UI.** This is a fundamental architectural issue.

**Impact:** The sync process writes data that the app never reads. The app relies entirely on the pre-bundled asset DB.

**Fix:** Either:
1. Make `SynchronizationService` update `DBService`'s database, or
2. Make screens read from `DatabaseHelper`'s database, or
3. Acknowledge that sync is only for future use and the asset DB is the primary source.

---

### H7. `SynchronizationService._asisApiCall` returns raw JSON without type safety
**File:** `lib/services/synchronization_service.dart:53`  
**Description:** The return type handling is fragile:
```dart
return (decoded is Map && decoded.containsKey('data')) ? decoded['data'] : decoded;
```
If `decoded` is a single `Map` (not a `List`), this returns the `Map` directly but the caller expects `List<dynamic>`. This will cause a type error when iterating.

**Fix:** Add explicit List check:
```dart
if (decoded is List) return decoded;
if (decoded is Map && decoded.containsKey('data') && decoded['data'] is List) return decoded['data'];
return [];
```

---

### H8. SQL injection risk in `calculateRouteLocally`
**File:** `lib/services/db_service.dart:183-184`  
**Description:** Stop IDs are inserted directly into SQL strings via string interpolation:
```dart
startStops.add("'$id'");
// ...
final startSet = startStops.join(',');
// Used in: WHERE h1.durak_id IN ($startSet)
```
Although the IDs come from the local database (not user input), this is still a SQL injection anti-pattern. If any stop ID contains a single quote, it will break the query.

**Fix:** Use parameterized queries or at minimum sanitize the IDs.

---

### H9. `admin_screen.dart` — admin key sent as URL query parameter
**File:** `lib/services/ybs_api_service.dart:21,53,72`  
**Description:** The admin key is passed as a plain-text URL query parameter (`?key=$_adminKey`). This means:
- It appears in server access logs
- It may be cached by intermediate proxies
- It's visible in network inspection tools

**Fix:** Send the key as an HTTP header (e.g., `Authorization: Bearer <key>`) instead.

---

## 🟡 MEDIUM Issues

### M1. Version string mismatch
**Files:** `lib/screens/settings_screen.dart:134,157,594`  
**Description:** Version is shown as `v2.5.0` in the header (line 134) and update checker (line 157), but the About dialog shows `2.4.1` (line 594). Meanwhile, `pubspec.yaml` says `1.0.0+1`.

**Fix:** Use a single source of truth. Read version from pubspec or define a single constant.

---

### M2. `PriceService.getPriceForLine` — potential null dereference
**File:** `lib/services/price_service.dart:72`  
**Description:** The fallback accesses `prices["default"]["tam"]` without null-checking `prices["default"]`. If the prices map somehow doesn't have a "default" key, this throws `NoSuchMethodError`.

**Fix:**
```dart
final defaultPrices = prices["default"] as Map<String, dynamic>?;
return {
  "tam": (defaultPrices?["tam"] ?? 17.0).toDouble(),
  "indirimli": (defaultPrices?["indirimli"] ?? 12.0).toDouble()
};
```

---

### M3. `home_screen.dart` — price lookup uses wrong key `_prices['TAM']`
**Files:** `lib/screens/home_screen.dart:312,823`  
**Description:** The code accesses `_prices['TAM']` to display fare, but `PriceService.fetchPrices()` returns keys like `"default"`, `"tramvay"`, `"ring"`, etc. There is no `"TAM"` key. This will always show `'--'`.

**Fix:** Look up the appropriate category price based on the route type.

---

### M4. `SamAirService` uses deprecated ASIS URLs directly — no geo-block bypass
**File:** `lib/services/samair_service.dart:5,20`  
**Description:** `SamAirService.getLiveSamAirBuses()` calls `api.samsun.bel.tr` directly without going through the Render proxy. The `ApiService` explicitly has Render proxy as primary with direct ASIS as fallback, but `SamAirService` only uses direct ASIS. This means it will fail for users outside Turkey.

**Fix:** Route through the Render proxy like `ApiService` does, or use `YbsApiService().getSamairAraclar()` as primary (which `samair_screen.dart` already does as first attempt).

---

### M5. `home_screen.dart` — `OfflineService` stream listener not cancelled
**File:** `lib/screens/home_screen.dart:77`  
**Description:** `OfflineService().offlineStream.listen(...)` creates a subscription that is never cancelled in `dispose()`. This can cause memory leaks and calls to `setState` after disposal.

**Fix:** Store and cancel the `StreamSubscription<bool>` in `dispose()`.

---

### M6. `synchronization_service.dart` — Odak durak batch committed inside hat batch loop
**File:** `lib/services/synchronization_service.dart:281-327`  
**Description:** In `_fetchAndSaveOdak()`, the code creates `hatBatch` at line 282, then inside the loop creates separate `dBatch` instances for durak data and commits them individually (line 323). But the `hatBatch` that inserts into both `tableOdak` and `tableHat` is committed only at line 327 — *after* the durak batches. If the durak foreign keys reference hat data that hasn't been committed yet, this could fail (though SQLite may not enforce FKs by default).

---

### M7. `OfflineService` uses `InternetAddress.lookup` — not available on Web
**File:** `lib/services/offline_service.dart:29`  
**Description:** `dart:io`'s `InternetAddress.lookup()` is not available on Flutter Web. Since `pubspec.yaml` includes a `web/` directory, this service will crash on web builds.

**Fix:** Use conditional imports or the `connectivity_plus` package for cross-platform support.

---

### M8. `hatlar_screen.dart` — Image.asset with colorBlendMode may not work as expected
**File:** `lib/screens/hatlar_screen.dart:153`  
**Description:** `Image.asset('assets/SBB Logo 9.png', color: Colors.white, colorBlendMode: BlendMode.srcIn)` — applying `srcIn` blend on a PNG assumes the logo has transparency. If it's a JPEG-style image with opaque background, the result will look wrong (white rectangle).

---

### M9. `settings_screen.dart` — `_showDataRefreshDialog` doesn't actually refresh data
**File:** `lib/screens/settings_screen.dart:377`  
**Description:** The "Verileri Yenile" button shows a snackbar saying "Veriler yenileniyor..." but never actually calls `SynchronizationService().runFullSynchronization(force: true)` or any DB refresh. It's a no-op.

**Fix:** Add actual data refresh logic.

---

### M10. `settings_screen.dart:412` — uses `context.mounted` on `BuildContext`
**File:** `lib/screens/settings_screen.dart:412`  
**Description:** `context.mounted` is only available on `BuildContext` from Flutter 3.7+. The SDK constraint is `>=3.2.3 <4.0.0` which is fine, but `context.mounted` should be `mounted` when used inside a `State` class (which it is here). Using `context.mounted` works but is unusual inside State.

---

### M11. `home_screen.dart` — `_mapController` used before map is ready
**File:** `lib/screens/home_screen.dart:163`  
**Description:** `_mapController.move()` is called in `_getLocation()` which runs in `initState()`. If the map hasn't mounted yet, this will throw an error. The code wraps it in `try { ... } catch (_) {}` which silently swallows the error, but it means the map won't center on initial load.

---

### M12. `offline_wakeup_screen.dart` — missing `dart:math` import for `sqrt`/`asin`
**File:** `lib/screens/offline_wakeup_screen.dart:3,24`  
**Description:** The file imports `dart:math` and uses `cos`, `asin`, `sqrt` — but these are used without the `math.` prefix. Since `import 'dart:math'` (without `as`) brings them into scope directly, this actually works. However, `cos` at line 21 is called without prefix, which is correct with an unqualified import.

**Severity downgraded:** No issue after review.

---

## 🔵 LOW Issues

### L1. Unused import in `main.dart`
**File:** `lib/main.dart:3`  
**Description:** `import 'package:samsun_mobil_app/services/synchronization_service.dart'` is used (line 94), so this is actually valid. *(No issue after review.)*

---

### L2. `SamAirService.SAMAIR_LINES` includes `H5` but `_lines` in `samair_screen.dart` only has H1-H4
**Files:** `lib/services/samair_service.dart:8`, `lib/screens/samair_screen.dart:25-29`  
**Description:** `SamAirService` defines `['H1', 'H2', 'H3', 'H4', 'H5']` but the screen's `_lines` list only has H1-H4. The tab view has 6 tabs including an H5 tab, but the `_lines` metadata doesn't include H5 (affecting any logic that uses `_lines`).

---

### L3. `admin_screen.dart:264` — potential `int` cast failure
**File:** `lib/screens/admin_screen.dart:264`  
**Description:** `final uptime = (s['uptime_seconds'] ?? 0) as int` — if the server returns `uptime_seconds` as a `double` (e.g., `1234.5`), this cast will throw. Should use `(s['uptime_seconds'] as num?)?.toInt() ?? 0`.

---

### L4. `db_service.dart` — `getHatlar()` modifies cached data in-place
**File:** `lib/services/db_service.dart:53-74`  
**Description:** `_hatlarCache` is populated once and then extra tramway routes are appended. On subsequent calls, the `isNotEmpty` check prevents re-adding, but the cache is a mutable reference that callers could modify. Should return `List.unmodifiable()` or a copy.

---

### L5. `hatlar_screen.dart` — `_selectedKat` default is `'dil'` (unusual/unclear)
**File:** `lib/screens/hatlar_screen.dart:19`  
**Description:** The default category filter `'dil'` means "all" in the KATEGORILER map (🌐 Tümü). The key name `'dil'` (Turkish for "language") is confusing for a filter meaning "all categories". Should be `'tumü'` or `'all'`.

---

### L6. Multiple `print()` statements throughout production code
**Files:** Multiple services and screens  
**Description:** `print()` calls are scattered throughout (`api_service.dart`, `ybs_api_service.dart`, `db_service.dart`, `synchronization_service.dart`, etc.). These should use `debugPrint()` or a proper logging framework to avoid console spam in production.

---

## Architecture Notes (Non-Bug)

1. **Dual-database architecture** (H6 above) is the most impactful issue. The sync service populates a database that the UI never reads from.

2. **No state management** — The app uses raw `setState()` everywhere with no Provider/Riverpod/Bloc. This works but makes data sharing between screens difficult and leads to data duplication.

3. **Singleton services** with no dependency injection make testing harder (contributes to the test issues above).

---

## Files Analyzed

| File | Lines | Issues Found |
|------|-------|-------------|
| `lib/main.dart` | 173 | 2 |
| `lib/screens/home_screen.dart` | 1034 | 4 |
| `lib/screens/hatlar_screen.dart` | 608 | 2 |
| `lib/screens/samair_screen.dart` | 575 | 1 |
| `lib/screens/odak_screen.dart` | 374 | 0 |
| `lib/screens/alarm_screen.dart` | 121 | 0 |
| `lib/screens/settings_screen.dart` | ~620 | 3 |
| `lib/screens/admin_screen.dart` | 327 | 1 |
| `lib/screens/loading_screen.dart` | 42 | 0 |
| `lib/screens/offline_wakeup_screen.dart` | 119 | 2 |
| `lib/services/api_service.dart` | 159 | 0 |
| `lib/services/db_service.dart` | 294 | 2 |
| `lib/services/ybs_api_service.dart` | 162 | 1 |
| `lib/services/price_service.dart` | 76 | 1 |
| `lib/services/samair_service.dart` | 52 | 1 |
| `lib/services/offline_service.dart` | 43 | 2 |
| `lib/services/synchronization_service.dart` | 505 | 2 |
| `lib/helpers/database_helper.dart` | 178 | 1 |
| `test/widget_test.dart` | 30 | 2 |
| `test/synchronization_test.dart` | 80 | 3 |
