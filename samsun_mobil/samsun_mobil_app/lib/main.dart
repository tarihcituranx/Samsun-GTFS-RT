
import 'package:flutter/material.dart';
import 'package:samsun_transit/services/synchronization_service.dart';
import 'screens/loading_screen.dart'; // Yükleme ekranı için yeni bir sayfa
import 'screens/home_screen.dart';

// Uygulamanın ana başlangıç noktası.
void main() async {
  // Flutter binding'lerinin hazır olduğundan emin ol.
  WidgetsFlutterBinding.ensureInitialized();

  // Senkronizasyon servisini çalıştır ve tamamlanmasını bekle.
  // Bu, uygulamanın, veritabanı hazır olmadan başlamasını engeller.
  final synchronizationService = SynchronizationService();
  await synchronizationService.runFullSynchronization();

  // Senkronizasyon tamamlandıktan sonra ana uygulamayı çalıştır.
  runApp(const SamsunRouteApp());
}

class SamsunRouteApp extends StatelessWidget {
  const SamsunRouteApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Samsun Transit', // Uygulama adını güncelledim
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.red,
        brightness: Brightness.light,
        useMaterial3: true,
        scaffoldBackgroundColor: Colors.grey[100], // Arka plan rengi
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.red.shade700,
          foregroundColor: Colors.white,
          elevation: 4.0,
        ),
      ),
      // Şimdilik ana ekranı doğrudan HomeScreen yapıyoruz.
      // Gelecekte, senkronizasyon durumuna göre LoadingScreen veya HomeScreen gösterilebilir.
      home: const HomeScreen(), 
    );
  }
}
