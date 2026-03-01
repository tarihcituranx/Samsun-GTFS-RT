import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../services/db_service.dart';
import '../services/api_service.dart';
import '../services/price_service.dart';
import 'samair_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final MapController _mapController = MapController();

  List<Map<String, dynamic>> _duraklar = [];
  List<Map<String, dynamic>> _yakinDuraklar = [];
  List<LatLng> _routePolyline = [];
  List<Map<String, dynamic>> _routeResults = [];
  
  // Canlı Araç Takibi
  String? _activeLineCode;
  Timer? _liveTrackingTimer;
  List<LatLng> _liveVehicles = [];

  bool _isLoadingMap = true;
  bool _isLoadingNearby = false;
  bool _isRouting = false;

  List<dynamic> _yaklasanAraclar = [];
  LatLng _myLocation = const LatLng(41.2867, 36.3300);

  final TextEditingController _hedefCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadDuraklar();
    _getLocation();
  }

  @override
  void dispose() {
    _liveTrackingTimer?.cancel();
    _tabController.dispose();
    _hedefCtrl.dispose();
    super.dispose();
  }

  void _startLiveTracking(String lineCode) {
    _liveTrackingTimer?.cancel();
    _activeLineCode = lineCode;
    _fetchLiveVehicles();
    _liveTrackingTimer = Timer.periodic(const Duration(seconds: 15), (_) => _fetchLiveVehicles());
  }

  Future<void> _fetchLiveVehicles() async {
    if (_activeLineCode == null || !mounted) return;
    
    // T1, T2 gibi hat isimlerini temizle (ASIS API'de sadece numaralar veya belirli kodlar var)
    String reqCode = _activeLineCode!;
    if (reqCode.startsWith('T')) reqCode = reqCode; // Tramvay
    
    final araclar = await ApiService.getHattakiAraclar(reqCode);
    if (!mounted) return;
    
    List<LatLng> newVehicles = [];
    for (var a in araclar) {
      if (a['Latitude'] != null && a['Longitude'] != null) {
        newVehicles.add(LatLng(
          double.tryParse(a['Latitude'].toString()) ?? 0.0,
          double.tryParse(a['Longitude'].toString()) ?? 0.0,
        ));
      }
    }
    setState(() {
      _liveVehicles = newVehicles;
    });
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
      if (mounted) {
        setState(() => _myLocation = LatLng(pos.latitude, pos.longitude));
        _mapController.move(_myLocation, 14.0);
      }
    } catch (_) {}
  }

  Future<void> _loadDuraklar() async {
    // samsun_mobil.db (assets) üzerinden durakları yükle
    final duraklar = await DBService().getDuraklar();
    if (mounted) {
      setState(() {
        _duraklar = duraklar;
        _isLoadingMap = false;
      });
    }
  }

  double _hav(double lat1, double lon1, double lat2, double lon2) {
    var p = 0.017453292519943295;
    var c = math.cos;
    var a = 0.5 - c((lat2 - lat1) * p) / 2 +
        c(lat1 * p) * c(lat2 * p) * (1 - c((lon2 - lon1) * p)) / 2;
    return 12742 * math.asin(math.sqrt(a)); // km
  }

  Future<void> _loadYakinDuraklar() async {
    setState(() => _isLoadingNearby = true);
    final allDuraklar = await DBService().getDuraklar();
    double lat = _myLocation.latitude;
    double lon = _myLocation.longitude;

    var result = allDuraklar.where((d) {
      return _hav(lat, lon, (d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()) < 1.0;
    }).toList();

    result.sort((a, b) {
      double da = _hav(lat, lon, (a['lat'] as num).toDouble(), (a['lon'] as num).toDouble());
      double db2 = _hav(lat, lon, (b['lat'] as num).toDouble(), (b['lon'] as num).toDouble());
      return da.compareTo(db2);
    });

    setState(() {
      _yakinDuraklar = result.take(15).toList();
      _isLoadingNearby = false;
    });
  }

  Future<void> _calculateRoute() async {
    if (_hedefCtrl.text.isEmpty) return;
    setState(() { _isRouting = true; _routePolyline = []; _routeResults = []; });

    try {
      double destLat = 41.3323, destLon = 36.2570; // default: Atakum
      final h = _hedefCtrl.text.toLowerCase();
      if (h.contains('atakum'))        { destLat = 41.3323; destLon = 36.2570; }
      else if (h.contains('canik') || h.contains('çanik')) { destLat = 41.2530; destLon = 36.3990; }
      else if (h.contains('ilkadim') || h.contains('ilkadım')) { destLat = 41.2867; destLon = 36.3300; }
      else if (h.contains('ondokuz') || h.contains('üniversite') || h.contains('universite')) { destLat = 41.3420; destLon = 36.2260; }
      else if (h.contains('tekkeköy') || h.contains('tekkekov')) { destLat = 41.2020; destLon = 36.4660; }
      else if (h.contains('carsamba') || h.contains('çarşamba')) { destLat = 41.2009; destLon = 36.7329; }
      else if (h.contains('bafra'))    { destLat = 41.5680; destLon = 35.9100; }
      else if (h.contains('terme'))    { destLat = 41.2100; destLon = 36.9800; }
      else if (h.contains('meydan'))   { destLat = 41.2867; destLon = 36.3300; }

      final routes = await DBService().calculateRouteLocally(
        _myLocation.latitude, _myLocation.longitude, destLat, destLon, radiusParams: 2.0
      );

      // Fiyatları çek ve eşleştir
      Map<String, double> livePrices = {};
      try {
        livePrices = await PriceService.fetchPrices();
      } catch (_) {}

      if (routes.isNotEmpty) {
        setState(() {
          _routeResults = routes;
          
          // Fiyat entegrasyonu
          for(var r in _routeResults) {
            String cCode = r['code']?.toString() ?? r['hat1']?.toString() ?? '';
            if (cCode.isNotEmpty) {
               // T1/T2 için T1 kodunu kullan (Aynı fiyat)
               if (cCode.startsWith('T')) cCode = 'T1';
               r['price'] = livePrices[cCode] ?? "Bilinmiyor";
            }
          }

          final coords = routes[0]['polyline'] as List;
          if (coords.isNotEmpty) {
            _routePolyline = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList();
            if (_routePolyline.length > 1) {
              final bounds = LatLngBounds.fromPoints(_routePolyline);
              _mapController.fitCamera(CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(50)));
            }
            _tabController.animateTo(0);
          }
        });
        _showRouteSheet();
      } else {
        _showError("Bu güzergah için rota bulunamadı. Farklı bir bölge adı deneyin.");
      }
    } catch (e) {
      _showError("Hata: $e");
    } finally {
      setState(() => _isRouting = false);
    }
  }

  void _showError(String msg) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red.shade700));
  }

  void _showRouteSheet() {
    showModalBottomSheet(
      context: context, isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Container(
        height: MediaQuery.of(context).size.height * 0.5,
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text("📍 Bulunan Rotalar", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Expanded(
            child: ListView.builder(
              itemCount: _routeResults.length,
              itemBuilder: (_, i) {
                final r = _routeResults[i];
                final isDirect = r['type'] == 'DIRECT';
                return Card(
                  color: isDirect ? Colors.blue.shade50 : Colors.amber.shade50,
                  child: ListTile(
                    leading: Icon(isDirect ? Icons.directions_bus : Icons.transfer_within_a_station,
                        color: isDirect ? Colors.blue : Colors.amber.shade800),
                    title: Text(isDirect ? "✅ Direkt Hat" : "🔄 Aktarmalı Rota"),
                    subtitle: Text(r['desc'] ?? '', style: const TextStyle(fontSize: 12)),
                    onTap: () {
                      final coords = r['polyline'] as List;
                      setState(() {
                        _routePolyline = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList();
                        _liveVehicles = [];
                        _activeLineCode = null;
                      });
                      
                      // Hat kodunu al ve canlı takibi başlat
                      String? lineCode;
                      if (isDirect) {
                         lineCode = r['code']?.toString();
                      } else {
                         lineCode = r['hat1']?.toString(); // Aktarmalıda ilk hattı takip et
                      }
                      
                      if (lineCode != null && lineCode.isNotEmpty) {
                        _startLiveTracking(lineCode);
                      }

                      Navigator.pop(context);
                      _tabController.animateTo(0);
                    },
                  ),
                );
              },
            ),
          ),
        ]),
      ),
    );
  }

  void _showDurakSheet(Map<String, dynamic> durak) async {
    // DB'de kod boşsa, "32302 - KORUPARK" gibi addan baştaki rakamları çek
    String durakKod = durak['kod']?.toString() ?? '';
    if (durakKod.isEmpty || durakKod == 'null') {
      final ad = durak['ad']?.toString() ?? '';
      final match = RegExp(r'^(\d+)').firstMatch(ad);
      if (match != null) durakKod = match.group(1)!;
    }
    
    showModalBottomSheet(
      context: context, isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => _DurakDetailSheet(durak: durak, durakKod: durakKod),
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
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          isScrollable: true,
          tabs: const [
            Tab(icon: Icon(Icons.map), text: "Harita"),
            Tab(icon: Icon(Icons.near_me), text: "Yakınım"),
            Tab(icon: Icon(Icons.directions), text: "Nasıl Giderim"),
            Tab(icon: Icon(Icons.flight_takeoff), text: "SamAIR"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // TAB 1: HARİTA
          _isLoadingMap
              ? const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text("Duraklar yükleniyor...")
                ]))
              : Stack(children: [
                  FlutterMap(
                    mapController: _mapController,
                    options: MapOptions(initialCenter: _myLocation, initialZoom: 13.0),
                    children: [
                      TileLayer(
                        urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                        userAgentPackageName: 'com.example.samsun_transit',
                      ),
                      if (_routePolyline.isNotEmpty)
                        PolylineLayer(polylines: [
                          Polyline(points: _routePolyline, strokeWidth: 5.0, color: Colors.blue.shade700),
                        ]),
                      MarkerLayer(markers: [
                        ..._liveVehicles.map((v) => Marker(
                          point: v,
                          width: 40,
                          height: 40,
                          child: Container(
                            decoration: const BoxDecoration(
                              color: Colors.white,
                              shape: BoxShape.circle,
                              boxShadow: [BoxShadow(blurRadius: 5, color: Colors.black26)],
                            ),
                            child: const Icon(Icons.directions_bus, color: Colors.red, size: 24),
                          ),
                        )),
                        Marker(
                          point: _myLocation, width: 36, height: 36,
                          child: const Icon(Icons.my_location, color: Colors.blue, size: 30),
                        ),
                        ...() {
                          // Sadece konuma en yakın 300 durağı haritada göster (performans için)
                          var sortedDuraklar = List<Map<String, dynamic>>.from(_duraklar);
                          sortedDuraklar.sort((a, b) {
                            double da = _hav(_myLocation.latitude, _myLocation.longitude, (a['lat'] as num).toDouble(), (a['lon'] as num).toDouble());
                            double db = _hav(_myLocation.latitude, _myLocation.longitude, (b['lat'] as num).toDouble(), (b['lon'] as num).toDouble());
                            return da.compareTo(db);
                          });
                          
                          return sortedDuraklar.take(300).map((d) {
                            double lat = (d['lat'] as num).toDouble();
                            double lon = (d['lon'] as num).toDouble();
                            return Marker(
                              point: LatLng(lat, lon), width: 22, height: 22,
                              child: GestureDetector(
                                onTap: () => _showDurakSheet(d),
                                child: const Icon(Icons.directions_bus, color: Colors.indigo, size: 18),
                              ),
                            );
                          });
                        }(),
                      ]),
                    ],
                  ),
                  Positioned(bottom: 16, right: 16,
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      FloatingActionButton.small(
                        heroTag: 'locate',
                        onPressed: () async { await _getLocation(); },
                        tooltip: 'Konumumu Bul',
                        child: const Icon(Icons.my_location),
                      ),
                    ]),
                  ),
                  Positioned(bottom: 16, left: 16,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), boxShadow: const [BoxShadow(blurRadius: 4, color: Colors.black26)]),
                      child: Text("${_duraklar.length} durak yüklendi", style: const TextStyle(fontSize: 12)),
                    ),
                  ),
                ]),

          // TAB 2: YAKIN DURAKLAR
          Column(children: [
            Padding(padding: const EdgeInsets.all(12.0),
              child: ElevatedButton.icon(
                onPressed: _isLoadingNearby ? null : () async { await _getLocation(); await _loadYakinDuraklar(); },
                icon: _isLoadingNearby
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.near_me),
                label: Text(_isLoadingNearby ? "Aranıyor..." : "Yakınımdaki Durakları Bul"),
                style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 48)),
              ),
            ),
            Expanded(
              child: _yakinDuraklar.isEmpty
                  ? const Center(child: Padding(padding: EdgeInsets.all(24),
                      child: Text("Butona basarak GPS'e yakın (1 km) durakları listeleyin.\n\nGPS izni vermildiğinden emin olun.", textAlign: TextAlign.center, style: TextStyle(color: Colors.grey))))
                  : ListView.builder(
                      itemCount: _yakinDuraklar.length,
                      itemBuilder: (_, i) {
                        final d = _yakinDuraklar[i];
                        final dist = (_hav(_myLocation.latitude, _myLocation.longitude,
                            (d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()) * 1000).round();
                        
                        // DB'de kod boşsa, "32302 - KORUPARK" gibi addan baştaki rakamları çek
                        String durakKodu = d['kod']?.toString() ?? '';
                        if (durakKodu.isEmpty || durakKodu == 'null') {
                          final ad = d['ad']?.toString() ?? '';
                          final match = RegExp(r'^(\d+)').firstMatch(ad);
                          if (match != null) durakKodu = match.group(1)!;
                        }

                        return ListTile(
                          leading: CircleAvatar(backgroundColor: Colors.indigo, child: Text(durakKodu.isEmpty ? '?' : durakKodu, style: const TextStyle(color: Colors.white, fontSize: 10))),
                          title: Text(d['ad']?.toString() ?? ''),
                          subtitle: Text("$dist metre uzakta"),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => _showDurakSheet(d),
                        );
                      },
                    ),
            ),
          ]),

          // TAB 3: NASIL GİDERİM
          SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text("🧭 Offline Rota Hesapla", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              const Text("İnternet bağlantısı olmadan, cihazınızdaki veritabanıyla anlık hesaplama yapılır.", style: TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(12)),
                child: Row(children: [
                  const Icon(Icons.my_location, color: Colors.blue),
                  const SizedBox(width: 10),
                  Text("GPS Konumunuz (${_myLocation.latitude.toStringAsFixed(4)}, ${_myLocation.longitude.toStringAsFixed(4)})", style: const TextStyle(fontSize: 13)),
                ]),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _hedefCtrl,
                decoration: InputDecoration(
                  labelText: "Nereye gitmek istiyorsunuz?",
                  hintText: "Ör: Atakum, Üniversite, Tekkeköy, Çarşamba...",
                  border: const OutlineInputBorder(),
                  prefixIcon: const Icon(Icons.location_on, color: Colors.red),
                  suffixIcon: IconButton(icon: const Icon(Icons.clear), onPressed: () => _hedefCtrl.clear()),
                ),
              ),
              const SizedBox(height: 8),
              const Text("Desteklenen bölgeler: Atakum, Canik, İlkadım, Üniversite (OMÜ), Tekkeköy, Çarşamba, Bafra, Terme, Meydan", style: TextStyle(fontSize: 11, color: Colors.grey)),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _isRouting ? null : _calculateRoute,
                icon: _isRouting ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.directions),
                label: Text(_isRouting ? "Hesaplanıyor..." : "Rota Hesapla"),
                style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 52)),
              ),
              if (_routeResults.isNotEmpty) ...[
                const SizedBox(height: 24),
                const Divider(),
                const Text("Bulunan Rotalar:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 8),
                ...List.generate(_routeResults.length, (i) {
                  final r = _routeResults[i];
                  final isDirect = r['type'] == 'DIRECT';
                  final priceVal = r['price'];
                  String priceStr = priceVal is double ? '${priceVal.toStringAsFixed(2)} ₺' : priceVal.toString();
                  
                  return Card(
                    color: isDirect ? Colors.green.shade50 : Colors.amber.shade50,
                    child: ListTile(
                      leading: Icon(isDirect ? Icons.directions_bus : Icons.transfer_within_a_station,
                          color: isDirect ? Colors.green : Colors.amber.shade800),
                      title: Text(isDirect ? "✅ Direkt Hat" : "🔄 Aktarmalı Rota"),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(r['desc'] ?? ''),
                          const SizedBox(height: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(4), border: Border.all(color: Colors.blue.shade200)),
                            child: Text("Ücret: $priceStr", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.blue)),
                          )
                        ],
                      ),
                      onTap: () {
                        final coords = r['polyline'] as List;
                        setState(() {
                          _routePolyline = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList();
                          _liveVehicles = [];
                          _activeLineCode = null;
                        });
                        
                        String? lineCode = isDirect ? r['code']?.toString() : r['hat1']?.toString();
                        if (lineCode != null && lineCode.isNotEmpty) _startLiveTracking(lineCode);
                        
                        _tabController.animateTo(0);
                      },
                    ),
                  );
                }),
              ],
            ]),
          ),
           const SamAirScreen(),
        ],
      ),
    );
  }
}

// Durak detay alt sheet widget (canlı araç bilgisi)
class _DurakDetailSheet extends StatefulWidget {
  final Map<String, dynamic> durak;
  final String durakKod;
  const _DurakDetailSheet({required this.durak, required this.durakKod});
  @override
  State<_DurakDetailSheet> createState() => _DurakDetailSheetState();
}

class _DurakDetailSheetState extends State<_DurakDetailSheet> {
  List<dynamic> _araclar = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final araclar = await ApiService.getDuragaYaklasanAraclar(widget.durakKod);
    if (mounted) setState(() { _araclar = araclar; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.55,
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Icon(Icons.location_on, color: Colors.red),
          const SizedBox(width: 8),
          Expanded(child: Text(widget.durak['ad']?.toString() ?? '', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold))),
        ]),
        Text("Durak No: ${widget.durakKod}", style: const TextStyle(color: Colors.grey, fontSize: 12)),
        const Divider(height: 20),
        const Text("🚌 Yaklaşan Araçlar (Canlı):", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
        const SizedBox(height: 8),
        if (_loading)
          const Expanded(child: Center(child: CircularProgressIndicator()))
        else if (_araclar.isEmpty)
          const Expanded(child: Center(child: Text("Bu durağa yaklaşan araç bulunamadı.\n(ASIS API yanıt vermedi veya araç yok)", textAlign: TextAlign.center, style: TextStyle(color: Colors.grey))))
        else
          Expanded(
            child: ListView.builder(
              itemCount: _araclar.length,
              itemBuilder: (_, i) {
                final a = _araclar[i];
                final lineCode = a['BusLineCode']?.toString() ?? '?';
                final remaining = a['RemainingTimeCurr']?.toString() ?? '?';
                return ListTile(
                  leading: CircleAvatar(backgroundColor: Colors.red.shade700, child: Text(remaining, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold))),
                  title: Text("$lineCode Hattı", style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text("Yaklaşık $remaining dakika sonra gelecek"),
                );
              },
            ),
          ),
      ]),
    );
  }
}
