# AI Testing Skill: Samsun Transit Offline App

## Context & Capabilities
You are interacting with a Flutter application (`samsun_mobil_app`) that has recently undergone a major architectural shift to become **100% Serverless and Offline**. 

### Critical Architecture Changes (Phases 6 & 7):
1. **No Backend API Dependency:** The application no longer relies on the Python (`samsun.py`) REST API. All logic has been ported locally.
2. **Offline Dart Routing Engine:** The SQL `INTERSECT` based transit routing (Direct & 1-Transfer) has been natively ported to Dart in `db_service.dart` (`calculateRouteLocally`). It uses built-in Haversine formulas and local SQLite execution entirely on the device.
3. **Native Synchronization:** The Python data collector module has been fully ported into `synchronization_service.dart`. The app now directly calls the Samsun ASIS and YBS APIs to fetch Lines, Stops, Routes, Schedules (`_seferler`), Odak (`_odak`), and Samair (`_samair`) data, saving them directly into the local `samsun_mobil.db` SQLite database.

## 🚨 TESTING CONSTRAINTS (CRITICAL INSTRUCTION) 🚨
**DO NOT USE headless `flutter test` for database or integration logic!**
Because this app relies heavily on `sqflite` and native C-libraries (`libsqlite3.so`), headless unit tests on standard Linux runners will FAIL with library missing errors. 

### How to Test in Google Project IDX:
The user is developing this within Google Project IDX, which provides a **built-in Android Web Emulator**. You must instruct the user to use this emulator for testing, rather than trying to run headless unit tests.

**To verify the app:**
1. Instruct the user to ensure `.idx/dev.nix` is configured with the standard Flutter workspace configuration.
2. Tell the user to click the **"Rebuild Environment"** button in IDX if they haven't already.
3. Once IDX loads, instruct the user to open the **Preview** panel and select **Android**.
4. The project will compile an APK and launch a visual Android Emulator on the right side of the screen.
5. The `samsun_mobil.db` creation, full synchronization, and offline route calculations must be tested interactively within this Android Emulator UI.

### Your Objectives as the Assisting AI:
- If the user shows you a `libsqlite3.so` error, **do not** rewrite the code to fix tests. Remind them to use the IDX Android Preview instead.
- If the user asks to verify the routing logic, guide them to open the "Nasıl Giderim?" (How to Go) tab in the running Android emulator to see the offline calculation in action.
- Acknowledge that the codebase is completely self-sufficient (zero server infrastructure required).
