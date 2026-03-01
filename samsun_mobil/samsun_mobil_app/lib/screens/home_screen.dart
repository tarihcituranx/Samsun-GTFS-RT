
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../helpers/database_helper.dart';
import '../services/api_service.dart';

// Ana ekran - Harita, Yakın Duraklar ve Nasıl Giderim tabları
class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final MapController _mapController = MapController();
  final dbHelper = DatabaseHelper.instance;

  List<Map<String, dynamic>> _duraklar = [];
  List<Map<String, dynamic>> _yakinDuraklar = [];
  List<dynamic> _yaklasanAraclar = [];
  List<LatLng> _routePolyline = [];
  List<Map<String, dynamic>> _routeResults = [];

  bool _isLoadingMap = true;
  bool _isLoadingNearby = false;
  bool _isRouting = false;

  LatLng _myLocation = const LatLng(41.2867, 36.3300); // Samsun Meydan

  final TextEditingController _baslangicCtrl = TextEditingController();
  final TextEditingController _hedefCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadDuraklar();
    _getLocation();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _baslangicCtrl.dispose();
    _hedefCtrl.dispose();
    super.dispose();
  }

  Future<void> _getLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) return;
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) return;
      }
      final pos = await Geolocator.getCurrentPosition();
      setState(() => _myLocation = LatLng(pos.latitude, pos.longitude));
      _mapController.move(_myLocation, 14.0);
    } catch (_) {}
  }

  Future<void> _loadDuraklar() async {
    final db = await dbHelper.database;
    final duraklar = await db.query(DatabaseHelper.tableDurak);
    setState(() {
      _duraklar = duraklar;
      _isLoadingMap = false;
    });
  }

  Future<void> _loadYakinDuraklar() async {
    setState(() => _isLoadingNearby = true);
    final db = await dbHelper.database;
    double lat = _myLocation.latitude;
    double lon = _myLocation.longitude;

    final nearby = await db.rawQuery(
      "SELECT kod, ad, lat, lon FROM durak WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
      [lat - 0.01, lat + 0.01, lon - 0.01, lon + 0.01]
    );

    double haversine(double lat1, double lon1, double lat2, double lon2) {
      var p = 0.017453292519943295;
      var c = math.cos;
      var a = 0.5 - c((lat2 - lat1) * p) / 2 +
          c(lat1 * p) * c(lat2 * p) * (1 - c((lon2 - lon1) * p)) / 2;
      return 12742000 * math.asin(math.sqrt(a)); // metres
    }

    var result = nearby.where((d) {
      double dist = haversine(lat, lon, d['lat'] as double, d['lon'] as double);
      return dist < 1000;
    }).toList();

    result.sort((a, b) {
      double da = haversine(lat, lon, a['lat'] as double, a['lon'] as double);
      double db2 = haversine(lat, lon, b['lat'] as double, b['lon'] as double);
      return da.compareTo(db2);
    });

    setState(() {
      _yakinDuraklar = result.take(15).toList();
      _isLoadingNearby = false;
    });
  }

  Future<void> _loadAraclar(String durakKod) async {
    final araclar = await ApiService.getDuragaYaklasanAraclar(durakKod);
    setState(() => _yaklasanAraclar = araclar);
  }

  Future<void> _calculateRoute() async {
    if (_hedefCtrl.text.isEmpty) return;
    setState(() {
      _isRouting = true;
      _routePolyline = [];
      _routeResults = [];
    });

    try {
      double startLat = _myLocation.latitude;
      double startLon = _myLocation.longitude;
      double destLat = 41.3323;
      double destLon = 36.2570;

      // Basit metin → koordinat çözümü
      final hedef = _hedefCtrl.text.toLowerCase();
      if (hedef.contains('atakum')) { destLat = 41.3323; destLon = 36.2570; }
      else if (hedef.contains('canik') || hedef.contains('çanik')) { destLat = 41.2530; destLon = 36.3990; }
      else if (hedef.contains('ilkadim') || hedef.contains('ilkadım')) { destLat = 41.2867; destLon = 36.3300; }
      else if (hedef.contains('ondokuz') || hedef.contains('üniversite')) { destLat = 41.3420; destLon = 36.2260; }
      else if (hedef.contains('tekkeköy') || hedef.contains('trekkekoy')) { destLat = 41.2020; destLon = 36.4660; }
      else if (hedef.contains('carsamba') || hedef.contains('çarşamba')) { destLat = 41.2009; destLon = 36.7329; }

      final db = await dbHelper.database;
      final allStops = await db.query(DatabaseHelper.tableDurak);

      double hav(double a1, double b1, double a2, double b2) {
        var p = 0.017453292519943295;
        var c = math.cos;
        var a = 0.5 - c((a2 - a1) * p) / 2 + c(a1 * p) * c(a2 * p) * (1 - c((b2 - b1) * p)) / 2;
        return 12742 * math.asin(math.sqrt(a));
      }

      List<String> startSet = [];
      List<String> endSet = [];
      for (var d in allStops) {
        if (hav(startLat, startLon, d['lat'] as double, d['lon'] as double) <= 1.5) {
          startSet.add("'${d['id']}'");
        }
        if (hav(destLat, destLon, d['lat'] as double, d['lon'] as double) <= 1.5) {
          endSet.add("'${d['id']}'");
        }
      }

      if (startSet.isEmpty || endSet.isEmpty) {
        _showError("Bu bölgede durak bulunamadı.");
        return;
      }

      final directResults = await db.rawQuery("""
        SELECT h1.hat as code, h1.ad as s_ad, h1.sira as s_sira,
               h2.ad as e_ad, h2.sira as e_sira,
               (h2.sira - h1.sira) as stop_diff
        FROM hat_durak h1
        JOIN hat_durak h2 ON h1.hat = h2.hat
        WHERE h1.durak_id IN (${startSet.join(',')})
          AND h2.durak_id IN (${endSet.join(',')})
          AND h1.sira < h2.sira
        ORDER BY stop_diff ASC
        LIMIT 5
      """);

      List<Map<String, dynamic>> routes = [];
      for (var r in directResults) {
        final pathRows = await db.rawQuery(
          "SELECT lat, lon FROM hat_durak WHERE hat=? AND sira >= ? AND sira <= ? ORDER BY sira",
          [r['code'], r['s_sira'], r['e_sira']]
        );
        List<List<double>> coords = pathRows.map((row) => [row['lat'] as double, row['lon'] as double]).toList();
        routes.add({
          'type': 'DIRECT',
          'total_score': r['stop_diff'],
          'polyline': coords,
          'desc': "🚌 ${r['code']} hattına ${r['s_ad']} durağından binin → ${r['e_ad']} durağında inin.",
        });
      }

      if (routes.isNotEmpty) {
        setState(() {
          _routeResults = routes;
          final coords = routes[0]['polyline'] as List<List<double>>;
          if (coords.isNotEmpty) {
            _routePolyline = coords.map((c) => LatLng(c[0], c[1])).toList();
            final bounds = LatLngBounds.fromPoints(_routePolyline);
            _mapController.fitCamera(CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(50)));
            _tabController.animateTo(0); // Haritaya dön
          }
        });
        _showRouteSheet();
      } else {
        _showError("Bu güzergah için rota bulunamadı. Daha geniş bir alan deneyin.");
      }
    } catch (e) {
      _showError("Rota hesaplama hatası: $e");
    } finally {
      setState(() => _isRouting = false);
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red.shade700));
  }

  void _showRouteSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Container(
        height: MediaQuery.of(context).size.height * 0.45,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("📍 Bulunan Rotalar", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Expanded(
              child: ListView.builder(
                itemCount: _routeResults.length,
                itemBuilder: (_, i) {
                  final r = _routeResults[i];
                  return Card(
                    color: Colors.blue.shade50,
                    child: ListTile(
                      leading: const Icon(Icons.directions_bus, color: Colors.blue),
                      title: Text("Doğrudan Hat • ${r['total_score']} durak"),
                      subtitle: Text(r['desc'] ?? '', style: const TextStyle(fontSize: 12)),
                      onTap: () {
                        final coords = r['polyline'] as List<List<double>>;
                        setState(() => _routePolyline = coords.map((c) => LatLng(c[0], c[1])).toList());
                        Navigator.pop(context);
                        _tabController.animateTo(0);
                      },
                    ),
                  );
                },
              ),
            )
          ],
        ),
      ),
    );
  }

  void _showDurakSheet(Map<String, dynamic> durak) async {
    final araclar = await ApiService.getDuragaYaklasanAraclar(durak['kod']?.toString() ?? '');
    if (!mounted) return;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Container(
        height: MediaQuery.of(context).size.height * 0.55,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.location_on, color: Colors.red),
              const SizedBox(width: 8),
              Expanded(child: Text(durak['ad']?.toString() ?? '', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold))),
            ]),
            const Divider(),
            const Text("🚌 Yaklaşan Araçlar (Canlı):", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
            const SizedBox(height: 6),
            if (araclar.isEmpty)
              const Expanded(child: Center(child: Text("Yaklaşan araç verisi bulunamadı.\n(Durak numarası eksik veya servis kapalı)", textAlign: TextAlign.center)))
            else
              Expanded(
                child: ListView.builder(
                  itemCount: araclar.length,
                  itemBuilder: (_, i) {
                    final a = araclar[i];
                    final lineCode = a['BusLineCode']?.toString() ?? '?';
                    final remaining = a['RemainingTimeCurr']?.toString() ?? '?';
                    return ListTile(
                      leading: CircleAvatar(backgroundColor: Colors.red, child: Text(remaining, style: const TextStyle(color: Colors.white, fontSize: 12))),
                      title: Text("Hat: $lineCode"),
                      subtitle: Text("$remaining dakika sonra"),
                    );
                  },
                ),
              )
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🚌 Samsun Ulaşım'),
        centerTitle: true,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          tabs: const [
            Tab(icon: Icon(Icons.map), text: "Harita"),
            Tab(icon: Icon(Icons.near_me), text: "Yakınım"),
            Tab(icon: Icon(Icons.directions), text: "Nasıl Giderim"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // ── TAB 1: HARİTA ──
          _isLoadingMap
              ? const Center(child: CircularProgressIndicator())
              : Stack(children: [
                  FlutterMap(
                    mapController: _mapController,
                    options: MapOptions(initialCenter: _myLocation, initialZoom: 13.0),
                    children: [
                      TileLayer(urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
                      MarkerLayer(markers: [
                        // Benim konumum
                        Marker(
                          point: _myLocation, width: 40, height: 40,
                          child: const Icon(Icons.my_location, color: Colors.blue, size: 30),
                        ),
                        // Duraklar
                        ..._duraklar.map((d) {
                          double lat = (d['lat'] as num).toDouble();
                          double lon = (d['lon'] as num).toDouble();
                          return Marker(
                            point: LatLng(lat, lon), width: 24, height: 24,
                            child: GestureDetector(
                              onTap: () => _showDurakSheet(d),
                              child: const Icon(Icons.directions_bus, color: Colors.red, size: 20),
                            ),
                          );
                        }),
                      ]),
                      if (_routePolyline.isNotEmpty)
                        PolylineLayer(polylines: [
                          Polyline(points: _routePolyline, strokeWidth: 5.0, color: Colors.blue.shade700),
                        ]),
                    ],
                  ),
                  Positioned(
                    bottom: 16, right: 16,
                    child: FloatingActionButton(
                      onPressed: _getLocation,
                      tooltip: 'Konumuma Git',
                      child: const Icon(Icons.my_location),
                    ),
                  ),
                ]),

          // ── TAB 2: YAKIN DURAKLAR ──
          Column(children: [
            Padding(
              padding: const EdgeInsets.all(12.0),
              child: ElevatedButton.icon(
                onPressed: () async { await _getLocation(); await _loadYakinDuraklar(); },
                icon: const Icon(Icons.near_me),
                label: const Text("Yakınımdaki Durakları Bul"),
                style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 48)),
              ),
            ),
            if (_isLoadingNearby) const Center(child: CircularProgressIndicator()),
            Expanded(
              child: _yakinDuraklar.isEmpty
                  ? const Center(child: Text("Butona basarak yakın durakları listeleyin.", textAlign: TextAlign.center))
                  : ListView.builder(
                      itemCount: _yakinDuraklar.length,
                      itemBuilder: (_, i) {
                        final d = _yakinDuraklar[i];
                        return ListTile(
                          leading: const Icon(Icons.directions_bus, color: Colors.red),
                          title: Text(d['ad']?.toString() ?? ''),
                          subtitle: Text("Durak No: ${d['kod'] ?? '?'}"),
                          onTap: () => _showDurakSheet(d),
                        );
                      },
                    ),
            ),
          ]),

          // ── TAB 3: NASIL GİDERİM ──
          SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("🗺️ Offline Rota Hesapla", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                const Text("Rota, internet bağlantısı olmadan yerleşik harita verisiyle hesaplanır.", style: TextStyle(color: Colors.grey, fontSize: 12)),
                const SizedBox(height: 16),
                TextField(
                  controller: _baslangicCtrl,
                  decoration: const InputDecoration(
                    labelText: "Başlangıç (boş bırakın = GPS konumunuz)",
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.my_location, color: Colors.blue),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _hedefCtrl,
                  decoration: const InputDecoration(
                    labelText: "Hedef (ör: Atakum, Ondokuz Mayıs Üniversitesi...)",
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.location_on, color: Colors.red),
                  ),
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _isRouting ? null : _calculateRoute,
                  icon: _isRouting
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.directions),
                  label: Text(_isRouting ? "Hesaplanıyor..." : "Rota Hesapla"),
                  style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                ),
                if (_routeResults.isNotEmpty) ...[
                  const SizedBox(height: 24),
                  const Text("Bulunan Rotalar:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 8),
                  ...List.generate(_routeResults.length, (i) {
                    final r = _routeResults[i];
                    return Card(
                      color: Colors.blue.shade50,
                      child: ListTile(
                        leading: const Icon(Icons.directions_bus, color: Colors.blue),
                        title: Text("Doğrudan Hat • ${r['total_score']} durak"),
                        subtitle: Text(r['desc'] ?? ''),
                        onTap: () {
                          final coords = r['polyline'] as List<List<double>>;
                          setState(() => _routePolyline = coords.map((c) => LatLng(c[0], c[1])).toList());
                          _tabController.animateTo(0);
                        },
                      ),
                    );
                  }),
                ]
              ],
            ),
          ),
        ],
      ),
    );
  }
}
