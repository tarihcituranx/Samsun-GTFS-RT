import 'dart:async';
import 'dart:io';

class OfflineService {
  static final OfflineService _instance = OfflineService._internal();
  factory OfflineService() => _instance;
  OfflineService._internal();

  bool isOffline = false;
  final StreamController<bool> _offlineController = StreamController<bool>.broadcast();
  Stream<bool> get offlineStream => _offlineController.stream;

  Timer? _timer;

  /// Servisi başlatır ve her 10 saniyede bir bağlantıyı kontrol eder.
  void startMonitoring() {
    _checkConnection();
    _timer = Timer.periodic(const Duration(seconds: 10), (_) => _checkConnection());
  }

  void stopMonitoring() {
    _timer?.cancel();
    _offlineController.close();
  }

  Future<void> _checkConnection() async {
    bool previousState = isOffline;
    try {
      // DNS üzerinden basit ve hızlı bir ping atarak interneti kontrol ediyoruz.
      final result = await InternetAddress.lookup('google.com').timeout(const Duration(seconds: 3));
      if (result.isNotEmpty && result[0].rawAddress.isNotEmpty) {
        isOffline = false;
      } else {
        isOffline = true;
      }
    } catch (_) {
      isOffline = true;
    }

    if (previousState != isOffline) {
      _offlineController.add(isOffline);
    }
  }
}
