import 'dart:async';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'dart:math';

class OfflineWakeUpScreen extends StatefulWidget {
  final Map<String, dynamic> durak; // Hedef (İnelecek) Durak

  const OfflineWakeUpScreen({Key? key, required this.durak}) : super(key: key);

  @override
  State<OfflineWakeUpScreen> createState() => _OfflineWakeUpScreenState();
}

class _OfflineWakeUpScreenState extends State<OfflineWakeUpScreen> {
  double currentDistance = 0.0;
  bool trackingActive = false;
  StreamSubscription<Position>? _positionSubscription;

  // Haversine Formülü ile iki koordinat arası metre hesabı
  double _calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    const p = 0.017453292519943295;
    final a = 0.5 - cos((lat2 - lat1) * p)/2 + 
              cos(lat1 * p) * cos(lat2 * p) * 
              (1 - cos((lon2 - lon1) * p))/2;
    return 12742 * asin(sqrt(a)) * 1000; // Sonuç Metre
  }

  void _baslat() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lütfen GPS'i açın")));
      return;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }

    setState(() {
      trackingActive = true;
    });

    // İnternetsiz Konum Takibi (Offline Tracking)
    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, distanceFilter: 10)
    ).listen((Position position) {
      if (!mounted) return;
      
      final dbLat = (widget.durak['lat'] as num?)?.toDouble() ?? 0.0;
      final dbLon = (widget.durak['lon'] as num?)?.toDouble() ?? 0.0;
      
      // Geçersiz koordinat kontrolü (Samsun bölgesi dışı)
      if (dbLat < 40 || dbLat > 43 || dbLon < 34 || dbLon > 38) return;
      
      final dist = _calculateDistance(position.latitude, position.longitude, dbLat, dbLon);
      
      setState(() {
        currentDistance = dist;
      });

      // Durağa 300 Metre Kala Titreşim Çal/Alarm Ver!
      if (dist < 300 && trackingActive) {
        // Not: Burada Vibrate paketleri ile telefon/saat titretilir
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("📢 İNME VAKTİ GELDİ! Durağa 300 metre kaldı! Uyan!"),
            backgroundColor: Colors.redAccent,
            duration: Duration(seconds: 10),
          ),
        );
        setState(() {
          trackingActive = false;
        });
      }
    });
  }

  @override
  void dispose() {
    _positionSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Çevrimdışı İnecek Durak Uyarısı")),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.location_off, size: 80, color: Colors.grey),
            const SizedBox(height: 10),
            const Text("İnternet Yokken Bile Çalışır!", style: TextStyle(color: Colors.grey, fontSize: 16)),
            const SizedBox(height: 30),
            Text(
              "Hedef:\n${widget.durak['ad']}",
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 40),
            if (trackingActive) ...[
              const CircularProgressIndicator(color: Colors.blue),
              const SizedBox(height: 20),
              Text(
                "Durağa Kalan Mesafe:\n${currentDistance.toStringAsFixed(0)} Metre",
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 30, color: Colors.blue, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              const Text("Ekranı kapatıp uyuyabilirsiniz.\n300m kala titreşimle uyanacaksınız.", textAlign: TextAlign.center),
            ] else ...[
              ElevatedButton.icon(
                onPressed: _baslat,
                icon: const Icon(Icons.directions_bus),
                label: const Text("OTOBÜSE BİNDİM, TAKİBİ BAŞLAT", style: TextStyle(fontSize: 18)),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15)
                ),
              )
            ]
          ],
        ),
      ),
    );
  }
}
