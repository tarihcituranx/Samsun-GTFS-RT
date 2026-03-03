import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import '../services/db_service.dart';
import '../services/api_service.dart';
import '../services/price_service.dart';
import '../services/offline_service.dart';
import 'hatlar_screen.dart';
import 'samair_screen.dart';
import 'odak_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final MapController _mapController = MapController();
  List<Map<String, dynamic>> _duraklar = [];
  List<Map<String, dynamic>> _yakinDuraklar = [];
  List<LatLng> _routePolyline = [];
  List<Map<String, dynamic>> _routeResults = [];
  List<Map<String, dynamic>> _liveVehicles = [];

  bool _isLoadingMap = true;
  bool _isLoadingNearby = false;
  bool _isRouting = false;
  bool _isOffline = false;
  bool _showNearbyOnly = false;

  String? _activeLineCode;
  Timer? _liveTimer;
  Map<String, dynamic> _prices = {};
  LatLng _myLocation = const LatLng(41.2867, 36.3300);
  LatLng? _targetLocation;

  final TextEditingController _hedefCtrl = TextEditingController();

  // ─── TOAST BİLDİRİM SİSTEMİ ───
  final List<_ToastItem> _toasts = [];
  int _toastIdCounter = 0;

  void _toast(String msg, {IconData icon = Icons.info_outline, Color? color, Duration duration = const Duration(seconds: 3)}) {
    if (!mounted) return;
    final id = _toastIdCounter++;
    setState(() => _toasts.add(_ToastItem(id: id, msg: msg, icon: icon, color: color ?? const Color(0xFF2979FF))));
    Future.delayed(duration, () {
      if (mounted) setState(() => _toasts.removeWhere((t) => t.id == id));
    });
  }

  void _toastInfo(String msg) => _toast(msg, icon: Icons.info_outline, color: const Color(0xFF2979FF));
  void _toastSuccess(String msg) => _toast(msg, icon: Icons.check_circle, color: const Color(0xFF00C853));
  void _toastError(String msg) => _toast(msg, icon: Icons.error_outline, color: const Color(0xFFFF5252), duration: const Duration(seconds: 5));
  void _toastLoading(String msg) => _toast(msg, icon: Icons.sync, color: const Color(0xFFFFAB00));

  @override
  void initState() {
    super.initState();
    _loadDuraklar();
    _getLocation();
    _loadPrices();
    
    // Offline Mod Dinleme
    OfflineService().startMonitoring();
    OfflineService().offlineStream.listen((offline) {
      if (mounted) {
        setState(() => _isOffline = offline);
        if (offline) {
          _toastError("⚠️ İnternet bağlantısı kesildi (Çevrimdışı Mod)");
        } else {
          _toastSuccess("🌐 İnternet bağlantısı sağlandı");
        }
      }
    });

    SharedPreferences.getInstance().then((prefs) {
      if (mounted) setState(() => _showNearbyOnly = prefs.getBool('show_nearby_only') ?? false);
    });
  }

  @override
  void dispose() {
    _liveTimer?.cancel();
    _hedefCtrl.dispose();
    OfflineService().stopMonitoring();
    super.dispose();
  }

  Future<void> _loadPrices() async {
    if (_isOffline) return;
    _toastLoading("💰 Fiyat bilgileri güncelleniyor...");
    try {
      final p = await PriceService.fetchPrices();
      if (mounted) {
        setState(() => _prices = p);
        _toastSuccess("✅ Fiyatlar güncellendi (${p.length} kayıt)");
      }
    } catch (e) {
      _toastError("❌ Fiyat API hatası: $e");
    }
  }

  void _startLiveTracking(String lineCode) {
    if (_isOffline) {
      _toastError("⚠️ Çevrimdışı modda canlı araç takibi yapılamaz");
      return;
    }
    _liveTimer?.cancel();
    _activeLineCode = lineCode;
    _toastInfo("📡 $lineCode hattı canlı takip başlatıldı");
    _fetchLiveVehicles();
    _liveTimer = Timer.periodic(const Duration(seconds: 15), (_) => _fetchLiveVehicles());
  }

  Future<void> _fetchLiveVehicles() async {
    if (_activeLineCode == null || _isOffline) return;
    try {
      final vehicles = await ApiService.getHattakiAraclar(_activeLineCode!);
      if (mounted) {
        final oldCount = _liveVehicles.length;
        setState(() => _liveVehicles = vehicles);
        if (vehicles.length != oldCount) {
          _toastInfo("🚌 ${vehicles.length} araç tespit edildi ($_activeLineCode)");
        }
      }
    } catch (e) {
      _toastError("⚠️ Araç API hatası: $e");
    }
  }

  Future<void> _getLocation() async {
    _toastLoading("📍 Konum tespit ediliyor...");
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _toastError("⚠️ Konum servisi kapalı");
        return;
      }
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          _toastError("⚠️ Konum izni reddedildi");
          return;
        }
      }
      final pos = await Geolocator.getCurrentPosition();
      if (mounted) {
        setState(() => _myLocation = LatLng(pos.latitude, pos.longitude));
        _toastSuccess("✅ Konum: ${pos.latitude.toStringAsFixed(4)}, ${pos.longitude.toStringAsFixed(4)}");
        try { _mapController.move(_myLocation, 14.0); } catch (_) {}
      }
    } catch (e) {
      _toastError("❌ GPS hatası: $e");
    }
  }

  Future<void> _loadDuraklar() async {
    _toastLoading("🗺️ Duraklar yükleniyor...");
    try {
      final duraklar = await DBService().getDuraklar();
      if (mounted) {
        setState(() { _duraklar = duraklar; _isLoadingMap = false; });
        _toastSuccess("✅ ${duraklar.length} durak yüklendi");
      }
    } catch (e) {
      _toastError("❌ DB hatası: $e");
      if (mounted) setState(() => _isLoadingMap = false);
    }
  }

  double _hav(double lat1, double lon1, double lat2, double lon2) {
    var p = 0.017453292519943295;
    var c = math.cos;
    var a = 0.5 - c((lat2 - lat1) * p) / 2 +
        c(lat1 * p) * c(lat2 * p) * (1 - c((lon2 - lon1) * p)) / 2;
    return 12742 * math.asin(math.sqrt(a));
  }

  Future<void> _loadYakinDuraklar() async {
    setState(() => _isLoadingNearby = true);
    _toastLoading("🔍 Yakın duraklar aranıyor...");
    double lat = _myLocation.latitude;
    double lon = _myLocation.longitude;
    var result = _duraklar.where((d) {
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
    _toastSuccess("✅ ${_yakinDuraklar.length} yakın durak bulundu");
  }

  Future<void> _calculateRouteFromCoords(double destLat, double destLon) async {
    setState(() { _isRouting = true; _routePolyline = []; _routeResults = []; _targetLocation = LatLng(destLat, destLon); });
    _toastLoading("🧭 Rota hesaplanıyor...");
    try {
      final routes = await DBService().calculateRouteLocally(
        _myLocation.latitude, _myLocation.longitude, destLat, destLon, radiusParams: 2.0
      );
      if (routes.isNotEmpty) {
        setState(() {
          _routeResults = routes;
          final coords = routes[0]['polyline'] as List;
          if (coords.isNotEmpty) {
            _routePolyline = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList();
            if (_routePolyline.length > 1) {
              _mapController.fitCamera(CameraFit.bounds(bounds: LatLngBounds.fromPoints(_routePolyline), padding: const EdgeInsets.all(50)));
            }
          }
        });
        _toastSuccess("✅ ${routes.length} rota bulundu");
        final firstCode = routes[0]['desc']?.toString() ?? '';
        final codeMatch = RegExp(r'([A-Z0-9]+) hattına').firstMatch(firstCode);
        if (codeMatch != null) _startLiveTracking(codeMatch.group(1)!);
        _showRouteSheet();
      } else {
        _toastError("❌ Bu güzergah için rota bulunamadı");
      }
    } catch (e) { _toastError("❌ Rota hatası: $e"); }
    finally { setState(() => _isRouting = false); }
  }

  Future<void> _calculateRoute() async {
    if (_hedefCtrl.text.isEmpty && _targetLocation == null) return;

    if (_targetLocation != null) {
      await _calculateRouteFromCoords(_targetLocation!.latitude, _targetLocation!.longitude);
    } else {
      // Sunucu tarafında Nominatim geocoding kullan (gerçek mekan arama)
      setState(() { _isRouting = true; _routePolyline = []; _routeResults = []; });
      _toastLoading("🔍 '${_hedefCtrl.text}' aranıyor...");
      try {
        final query = Uri.encodeComponent(_hedefCtrl.text.trim());
        final url = 'https://samsun-gtfs-rt.onrender.com/api/rota?lat1=${_myLocation.latitude}&lon1=${_myLocation.longitude}&end=$query';
        final response = await http.get(Uri.parse(url), headers: {'User-Agent': 'SamsunMobilApp/2.0'}).timeout(const Duration(seconds: 15));
        if (response.statusCode == 200) {
          final data = json.decode(response.body);
          if (data is List && data.isNotEmpty) {
            setState(() {
              _routeResults = data.map<Map<String, dynamic>>((r) => Map<String, dynamic>.from(r)).toList();
              final coords = _routeResults[0]['polyline'] as List?;
              if (coords != null && coords.isNotEmpty) {
                _routePolyline = coords.map((c) => LatLng((c[0] as num).toDouble(), (c[1] as num).toDouble())).toList();
                if (_routePolyline.length > 1) {
                  _mapController.fitCamera(CameraFit.bounds(bounds: LatLngBounds.fromPoints(_routePolyline), padding: const EdgeInsets.all(50)));
                }
              }
            });
            _toastSuccess("✅ ${_routeResults.length} rota bulundu");
            _showRouteSheet();
          } else {
            _toastError("❌ '${_hedefCtrl.text}' için rota bulunamadı");
          }
        } else if (response.statusCode == 400) {
          final err = json.decode(response.body);
          _toastError("❌ ${err['error'] ?? 'Konum bulunamadı'}");
        } else {
          _toastError("❌ Sunucu hatası");
        }
      } catch (e) { _toastError("❌ Rota hatası: $e"); }
      finally { setState(() => _isRouting = false); }
    }
  }

  Future<void> _openInGoogleMaps() async {
    if (_targetLocation == null) return;
    final url = 'https://www.google.com/maps/dir/?api=1&origin=${_myLocation.latitude},${_myLocation.longitude}&destination=${_targetLocation!.latitude},${_targetLocation!.longitude}';
    final uri = Uri.parse(url);
    if (!await launchUrl(uri)) {
      _toastError("❌ Google Haritalar açılamadı");
    }
  }

  void _showRouteSheet() {
    showModalBottomSheet(
      context: context, isScrollControlled: true,
      backgroundColor: const Color(0xFF152238),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => Container(
        height: MediaQuery.of(context).size.height * 0.55,
        padding: const EdgeInsets.only(top: 16, left: 16, right: 16, bottom: 24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)))),
          const SizedBox(height: 16),
          const Text("📍 Bulunan Rotalar", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 12),
          Expanded(
            child: ListView.builder(
              itemCount: _routeResults.length,
              itemBuilder: (_, i) {
                final r = _routeResults[i];
                final isDirect = r['type'] == 'DIRECT';
                final tamFiyat = _prices['TAM']?.toStringAsFixed(2) ?? '--';
                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(colors: isDirect ? [const Color(0xFF1B5E20), const Color(0xFF2E7D32)] : [const Color(0xFF4A2C00), const Color(0xFF5D4037)]),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: ListTile(
                    leading: Icon(isDirect ? Icons.directions_bus : Icons.transfer_within_a_station, color: Colors.white),
                    title: Text(isDirect ? "Direkt Hat" : "Aktarmalı Rota", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(r['desc'] ?? '', style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.8))),
                      const SizedBox(height: 4),
                      Text('💰 $tamFiyat ₺', style: const TextStyle(color: Color(0xFF69F0AE), fontWeight: FontWeight.bold, fontSize: 13)),
                    ]),
                    onTap: () {
                      final coords = r['polyline'] as List;
                      setState(() => _routePolyline = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList());
                      Navigator.pop(context);
                      setState(() => _currentIndex = 0);
                    },
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 12),
          // Google Maps Butonu
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              onPressed: () {
                Navigator.pop(context);
                _openInGoogleMaps();
              },
              icon: const Icon(Icons.map, color: Colors.white),
              label: const Text("Google Haritalar'da Aç (Navigasyon)", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2979FF),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          )
        ]),
      ),
    );
  }

  void _showDurakSheet(Map<String, dynamic> durak) async {
    String durakKod = durak['kod']?.toString() ?? '';
    if (durakKod.isEmpty || durakKod == 'null') {
      durakKod = durak['id']?.toString() ?? '';
    }
    if (durakKod.isEmpty || durakKod == 'null') {
      final ad = durak['ad']?.toString() ?? '';
      final match = RegExp(r'^(\d+)').firstMatch(ad);
      if (match != null) durakKod = match.group(1)!;
    }
    _toastLoading("📡 Durak $durakKod sorgulanıyor...");
    showModalBottomSheet(
      context: context, isScrollControlled: true,
      backgroundColor: const Color(0xFF152238),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => _DurakDetailSheet(
        durak: durak, durakKod: durakKod,
        onResult: (count) {
          if (count > 0) {
            _toastSuccess("✅ $count araç yaklaşıyor (Durak $durakKod)");
          } else {
            _toastInfo("ℹ️ Durağa yaklaşan araç bulunamadı");
          }
        },
      ),
    );
  }

  // ─── EKRANLAR ───

  Widget _buildMapScreen() {
    if (_isLoadingMap) {
      return Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        SizedBox(width: 40, height: 40, child: CircularProgressIndicator(strokeWidth: 3, color: const Color(0xFF2979FF).withOpacity(0.7))),
        const SizedBox(height: 20),
        Text("Duraklar yükleniyor...", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14)),
      ]));
    }
    return Stack(children: [
      FlutterMap(
        mapController: _mapController,
        options: MapOptions(
          initialCenter: _myLocation,
          initialZoom: 13.0,
          onLongPress: (tapPos, latLng) {
            setState(() => _targetLocation = latLng);
            _toastInfo("🎯 Hedef seçildi: ${latLng.latitude.toStringAsFixed(4)}, ${latLng.longitude.toStringAsFixed(4)}");
            showDialog(context: context, builder: (_) => AlertDialog(
              backgroundColor: const Color(0xFF1A2940),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              title: const Text("🎯 Hedef Seçildi", style: TextStyle(color: Colors.white)),
              content: Text("Bu konuma nasıl giderim?", style: TextStyle(color: Colors.white.withOpacity(0.7))),
              actions: [
                TextButton(onPressed: () => Navigator.pop(context), child: Text("İptal", style: TextStyle(color: Colors.white.withOpacity(0.5)))),
                ElevatedButton(
                  onPressed: () { Navigator.pop(context); _calculateRouteFromCoords(latLng.latitude, latLng.longitude); },
                  child: const Text("Rota Hesapla"),
                ),
              ],
            ));
          },
        ),
        children: [
          TileLayer(
            urlTemplate: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
            subdomains: const ['a', 'b', 'c', 'd'],
            userAgentPackageName: 'com.samsun.transit',
          ),
          // Teleferik Hattı Polyline (Batıpark ↔ Amisos Tepesi)
          PolylineLayer(polylines: [
            if (_routePolyline.isNotEmpty)
              Polyline(points: _routePolyline, strokeWidth: 5.0, color: const Color(0xFF2979FF)),
            Polyline(
              points: const [
                LatLng(41.321695, 36.323563), // Batıpark (alt istasyon)
                LatLng(41.318939, 36.322455), // Amisos Tepesi (üst istasyon)
              ],
              strokeWidth: 3.5,
              color: const Color(0xFFFF4081),
              isDotted: true,
            ),
          ]),
          MarkerLayer(markers: [
            // Benim konumum
            Marker(point: _myLocation, width: 40, height: 40, child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF2979FF),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 3),
                boxShadow: [BoxShadow(color: const Color(0xFF2979FF).withOpacity(0.4), blurRadius: 12, spreadRadius: 3)],
              ),
              child: const Center(child: Icon(Icons.person, color: Colors.white, size: 18)),
            )),
            // Hedef
            if (_targetLocation != null)
              Marker(point: _targetLocation!, width: 40, height: 40, child: Container(
                decoration: BoxDecoration(
                  color: Colors.red.shade600,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 3),
                  boxShadow: [BoxShadow(color: Colors.red.withOpacity(0.4), blurRadius: 12, spreadRadius: 3)],
                ),
                child: const Center(child: Icon(Icons.flag, color: Colors.white, size: 18)),
              )),
            ..._liveVehicles.map((v) => Marker(
              point: LatLng(v['lat'] as double, v['lon'] as double),
              width: 38, height: 38,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0xFF2979FF), width: 1.5),
                  boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 4, offset: const Offset(0, 2))],
                ),
                child: Center(
                  child: ClipOval(
                    child: Padding(
                      padding: const EdgeInsets.all(4.0),
                      child: Image.asset(
                        'assets/bus.png',
                        fit: BoxFit.contain,
                        errorBuilder: (context, error, stackTrace) => 
                          const Icon(Icons.directions_bus, color: Color(0xFF2979FF), size: 20),
                      ),
                    ),
                  ),
                ),
              ),
            )).toList(),
            // Teleferik İstasyonları
            Marker(
              point: const LatLng(41.321695, 36.323563), width: 40, height: 40,
              child: Tooltip(
                message: 'Batıpark (Teleferik Alt İstasyon)',
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFFFF4081),
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2.5),
                    boxShadow: [BoxShadow(color: const Color(0xFFFF4081).withOpacity(0.4), blurRadius: 8, spreadRadius: 2)],
                  ),
                  child: const Center(child: Icon(Icons.airline_seat_recline_extra, color: Colors.white, size: 18)),
                ),
              ),
            ),
            Marker(
              point: const LatLng(41.318939, 36.322455), width: 40, height: 40,
              child: Tooltip(
                message: 'Amisos Tepesi (Teleferik Üst İstasyon)',
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFFFF4081),
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2.5),
                    boxShadow: [BoxShadow(color: const Color(0xFFFF4081).withOpacity(0.4), blurRadius: 8, spreadRadius: 2)],
                  ),
                  child: const Center(child: Icon(Icons.terrain, color: Colors.white, size: 18)),
                ),
              ),
            ),
            // Duraklar (en yakın 300 veya sadece yakın)
            ...() {
              var sorted = List<Map<String, dynamic>>.from(_duraklar);
              sorted.sort((a, b) {
                double da = _hav(_myLocation.latitude, _myLocation.longitude, (a['lat'] as num).toDouble(), (a['lon'] as num).toDouble());
                double db = _hav(_myLocation.latitude, _myLocation.longitude, (b['lat'] as num).toDouble(), (b['lon'] as num).toDouble());
                return da.compareTo(db);
              });
              final filtered = _showNearbyOnly
                  ? sorted.where((d) => _hav(_myLocation.latitude, _myLocation.longitude, (d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()) < 1.0)
                  : sorted.take(300);
              return filtered.map((d) {
                double lat = (d['lat'] as num).toDouble();
                double lon = (d['lon'] as num).toDouble();
                if (_showNearbyOnly) {
                  return Marker(
                    point: LatLng(lat, lon),
                    width: 100, height: 45,
                    child: GestureDetector(
                      onTap: () => _showDurakSheet(d),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 28, height: 28,
                            decoration: BoxDecoration(
                              color: const Color(0xFF2979FF),
                              shape: BoxShape.circle,
                              border: Border.all(color: Colors.white, width: 2),
                              boxShadow: [BoxShadow(color: const Color(0xFF2979FF).withOpacity(0.3), blurRadius: 4, spreadRadius: 1)],
                            ),
                            child: const Center(child: Icon(Icons.directions_bus, color: Colors.white, size: 14)),
                          ),
                          Text(d['ad'] ?? '', style: TextStyle(color: Colors.black87, fontSize: 10, fontWeight: FontWeight.bold, shadows: [Shadow(blurRadius: 3, color: Colors.white, offset: const Offset(0, 0)), Shadow(blurRadius: 6, color: Colors.white, offset: const Offset(0, 0))]), overflow: TextOverflow.ellipsis, maxLines: 1),
                        ],
                      ),
                    ),
                  );
                }
                return Marker(
                  point: LatLng(lat, lon), 
                  width: 28, height: 28,
                  child: GestureDetector(
                    onTap: () => _showDurakSheet(d), 
                    child: Container(
                      decoration: BoxDecoration(
                        color: const Color(0xFF2979FF),
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white, width: 2),
                        boxShadow: [BoxShadow(color: const Color(0xFF2979FF).withOpacity(0.3), blurRadius: 4, spreadRadius: 1)],
                      ),
                      child: const Center(child: Icon(Icons.directions_bus, color: Colors.white, size: 14)),
                    ),
                  )
                );
              });
            }(),
          ]),
        ],
      ),
      // FAB'lar
      Positioned(bottom: 16, right: 16,
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          _glassFab(Icons.my_location, () async { await _getLocation(); }),
          const SizedBox(height: 8),
          if (_liveVehicles.isNotEmpty)
            _glassFab(Icons.directions_bus, () {}, badge: '${_liveVehicles.length}'),
        ]),
      ),
      // Durak sayacı
      Positioned(bottom: 16, left: 16,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: const Color(0xFF0A1628).withOpacity(0.85),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white.withOpacity(0.1)),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.location_on, color: Color(0xFF2979FF), size: 14),
            const SizedBox(width: 4),
            Text("${_duraklar.length} durak", style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.8))),
          ]),
        ),
      ),
      // Akıllı Durak (SmartStation) / QR Durak Arama
      Positioned(top: 8, left: 12, right: 12, // Safe area genelde AppBar veya framework halleder ama SafeArea sarmalayınca daha iyi
        child: SafeArea(
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF152238).withOpacity(0.95),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withOpacity(0.1)),
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 4))],
            ),
            child: TextField(
              style: const TextStyle(color: Colors.white, fontSize: 14),
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: "Akıllı Durak No girin (Örn: 10101)",
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 13),
                prefixIcon: const Icon(Icons.qr_code_scanner, color: Color(0xFF69F0AE), size: 20),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              ),
              onSubmitted: (val) {
                final query = val.trim();
                if (query.isNotEmpty) {
                   final find = _duraklar.where((d) {
                     final durakId = d['id']?.toString() ?? '';
                     final kod = d['kod']?.toString() ?? '';
                     final ad = d['ad']?.toString() ?? '';
                     // Adın başındaki sayısal kısmı da akıllı durak no olarak kabul et (ör: "50122 - SOĞUK SU")
                     final adMatch = RegExp(r'^(\d+)').firstMatch(ad);
                     final adKod = adMatch?.group(1) ?? '';
                     return durakId == query || kod == query || adKod == query || ad.toUpperCase().contains(query.toUpperCase());
                   }).toList();
                   if (find.isNotEmpty) {
                      final f = find.first;
                      _mapController.move(LatLng((f['lat'] as num).toDouble(), (f['lon'] as num).toDouble()), 16.0);
                      _showDurakSheet(f);
                   } else {
                      _toastError("❌ Durak bulunamadı: $query");
                   }
                }
              },
            ),
          ),
        ),
      ),
      // TOAST OVERLAY
      ..._buildToastOverlay(),
    ]);
  }

  Widget _glassFab(IconData icon, VoidCallback onTap, {String? badge}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 48, height: 48,
        decoration: BoxDecoration(
          color: const Color(0xFF152238).withOpacity(0.9),
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white.withOpacity(0.15)),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 8)],
        ),
        child: Stack(children: [
          Center(child: Icon(icon, color: const Color(0xFF2979FF), size: 22)),
          if (badge != null)
            Positioned(top: 2, right: 2, child: Container(
              padding: const EdgeInsets.all(3),
              decoration: const BoxDecoration(color: Color(0xFFFF5252), shape: BoxShape.circle),
              child: Text(badge, style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold)),
            )),
        ]),
      ),
    );
  }

  List<Widget> _buildToastOverlay() {
    return List.generate(_toasts.length, (i) {
      final t = _toasts[i];
      return Positioned(
        bottom: 70.0 + (i * 52),
        left: 16, right: 16,
        child: AnimatedOpacity(
          opacity: 1.0,
          duration: const Duration(milliseconds: 300),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFF0F1E36).withOpacity(0.95),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: t.color.withOpacity(0.3)),
              boxShadow: [BoxShadow(color: t.color.withOpacity(0.15), blurRadius: 12)],
            ),
            child: Row(children: [
              Icon(t.icon, color: t.color, size: 18),
              const SizedBox(width: 10),
              Expanded(child: Text(t.msg, style: const TextStyle(color: Colors.white, fontSize: 12))),
            ]),
          ),
        ),
      );
    });
  }

  Widget _buildYakinScreen() {
    return Column(children: [
      Padding(padding: const EdgeInsets.all(12.0),
        child: ElevatedButton.icon(
          onPressed: _isLoadingNearby ? null : () async { await _getLocation(); await _loadYakinDuraklar(); },
          icon: _isLoadingNearby
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Icon(Icons.near_me),
          label: Text(_isLoadingNearby ? "Aranıyor..." : "Yakınımdaki Durakları Bul"),
          style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 52)),
        ),
      ),
      Expanded(
        child: _yakinDuraklar.isEmpty
            ? Center(child: Padding(padding: const EdgeInsets.all(24),
                child: Text("Butona basarak GPS'e yakın (1 km) durakları listeleyin.\n\nGPS izni verildiğinden emin olun.",
                  textAlign: TextAlign.center, style: TextStyle(color: Colors.white.withOpacity(0.4)))))
            : ListView.builder(
                itemCount: _yakinDuraklar.length,
                itemBuilder: (_, i) {
                  final d = _yakinDuraklar[i];
                  final dist = (_hav(_myLocation.latitude, _myLocation.longitude, (d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()) * 1000).round();
                  String durakKodu = d['kod']?.toString() ?? '';
                  if (durakKodu.isEmpty || durakKodu == 'null') {
                    durakKodu = d['id']?.toString() ?? '';
                  }
                  if (durakKodu.isEmpty || durakKodu == 'null') {
                    final ad = d['ad']?.toString() ?? '';
                    final match = RegExp(r'^(\d+)').firstMatch(ad);
                    if (match != null) durakKodu = match.group(1)!;
                  }
                  return Container(
                    margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xFF152238),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white.withOpacity(0.05)),
                    ),
                    child: ListTile(
                      leading: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(colors: [Color(0xFF2979FF), Color(0xFF00BFA5)]),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Center(child: Text(durakKodu.isEmpty ? '?' : durakKodu, style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold))),
                      ),
                      title: Text(d['ad']?.toString() ?? '', style: const TextStyle(color: Colors.white, fontSize: 13)),
                      subtitle: Text("$dist metre", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11)),
                      trailing: Icon(Icons.chevron_right, color: Colors.white.withOpacity(0.3)),
                      onTap: () => _showDurakSheet(d),
                    ),
                  );
                },
              ),
      ),
    ]);
  }

  Widget _buildRotaScreen() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text("🧭 Hibrit Rota", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white)),
        const SizedBox(height: 4),
        Text("Tramvay öncelikli akıllı rota", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 12)),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: const Color(0xFF152238), borderRadius: BorderRadius.circular(12)),
          child: Row(children: [
            const Icon(Icons.my_location, color: Color(0xFF2979FF), size: 20),
            const SizedBox(width: 10),
            Expanded(child: Text("GPS (${_myLocation.latitude.toStringAsFixed(4)}, ${_myLocation.longitude.toStringAsFixed(4)})", style: TextStyle(fontSize: 13, color: Colors.white.withOpacity(0.7)))),
          ]),
        ),
        if (_targetLocation != null) ...[
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [Colors.red.shade900.withOpacity(0.3), Colors.red.shade800.withOpacity(0.2)]),
              borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.red.withOpacity(0.2)),
            ),
            child: Row(children: [
              const Icon(Icons.flag, color: Color(0xFFFF5252), size: 20),
              const SizedBox(width: 10),
              Expanded(child: Text("Hedef: ${_targetLocation!.latitude.toStringAsFixed(4)}, ${_targetLocation!.longitude.toStringAsFixed(4)}",
                style: TextStyle(fontSize: 13, color: Colors.white.withOpacity(0.7)))),
              GestureDetector(onTap: () => setState(() => _targetLocation = null),
                child: Icon(Icons.close, size: 16, color: Colors.white.withOpacity(0.4))),
            ]),
          ),
        ],
        const SizedBox(height: 12),
        TextField(
          controller: _hedefCtrl,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            labelText: "Nereye gitmek istiyorsunuz?",
            hintText: "Cadde, mahalle, mekan adı yazın...",
            prefixIcon: const Icon(Icons.location_on, color: Color(0xFFFF5252)),
            suffixIcon: IconButton(icon: Icon(Icons.clear, color: Colors.white.withOpacity(0.3)), onPressed: () => _hedefCtrl.clear()),
          ),
        ),
        const SizedBox(height: 8),
        Text("Veya haritada istediğiniz yere uzun basın", style: TextStyle(fontSize: 11, color: Colors.amber.withOpacity(0.6))),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: _isRouting ? null : _calculateRoute,
          icon: _isRouting
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Icon(Icons.directions),
          label: Text(_isRouting ? "Hesaplanıyor..." : "Rota Hesapla"),
          style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 52)),
        ),
        if (_routeResults.isNotEmpty) ...[
          const SizedBox(height: 24),
          Divider(color: Colors.white.withOpacity(0.08)),
          const Text("Bulunan Rotalar:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white)),
          const SizedBox(height: 8),
          ...List.generate(_routeResults.length, (i) {
            final r = _routeResults[i];
            final isDirect = r['type'] == 'DIRECT';
            final tamFiyat = _prices['TAM']?.toStringAsFixed(2) ?? '--';
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: isDirect ? [const Color(0xFF1B5E20), const Color(0xFF2E7D32)] : [const Color(0xFF4A2C00), const Color(0xFF5D4037)]),
                borderRadius: BorderRadius.circular(12),
              ),
              child: ListTile(
                leading: Icon(isDirect ? Icons.directions_bus : Icons.transfer_within_a_station, color: Colors.white),
                title: Text(isDirect ? "Direkt Hat" : "Aktarmalı Rota", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(r['desc'] ?? '', style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 12)),
                  Text('💰 $tamFiyat ₺', style: const TextStyle(color: Color(0xFF69F0AE), fontWeight: FontWeight.bold)),
                ]),
                onTap: () {
                  final coords = r['polyline'] as List;
                  setState(() { _routePolyline = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList(); _currentIndex = 0; });
                },
              ),
            );
          }),
        ],
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      _buildMapScreen(),
      HatlarScreen(onLineSelected: _startLiveTracking),
      _buildYakinScreen(),
      _buildRotaScreen(),
      const OdakScreen(),
      const SamAirScreen(),
      const SettingsScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('🚌 Samsun Ulaşım Sistemi'),
        actions: [
          if (_liveVehicles.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Chip(
                label: Text('${_liveVehicles.length} araç', style: const TextStyle(color: Colors.white, fontSize: 10)),
                backgroundColor: const Color(0xFFFF5252),
                side: BorderSide.none,
                padding: EdgeInsets.zero,
                avatar: const Icon(Icons.directions_bus, color: Colors.white, size: 14),
              ),
            ),
          IconButton(icon: const Icon(Icons.phone, size: 20), tooltip: '153',
            onPressed: () => _toastInfo("📞 Samsun içi: 153 • Dışı: 0362 431 10 12")),
        ],
      ),
      body: Column(
        children: [
          if (_isOffline)
            Container(
              width: double.infinity,
              color: const Color(0xFFFF5252),
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: const Text("⚠️ Çevrimdışı Mod - Canlı veriler kullanılamaz", 
                style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold), 
                textAlign: TextAlign.center,
              ),
            ),
          Expanded(
            child: IndexedStack(index: _currentIndex, children: screens),
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.map_outlined), activeIcon: Icon(Icons.map), label: "Harita"),
          BottomNavigationBarItem(icon: Icon(Icons.directions_bus_outlined), activeIcon: Icon(Icons.directions_bus), label: "Hatlar"),
          BottomNavigationBarItem(icon: Icon(Icons.near_me_outlined), activeIcon: Icon(Icons.near_me), label: "Yakınım"),
          BottomNavigationBarItem(icon: Icon(Icons.route_outlined), activeIcon: Icon(Icons.route), label: "Rota"),
          BottomNavigationBarItem(icon: Icon(Icons.explore_outlined), activeIcon: Icon(Icons.explore), label: "Odak"),
          BottomNavigationBarItem(icon: Icon(Icons.flight_takeoff_outlined), activeIcon: Icon(Icons.flight_takeoff), label: "SamAIR"),
          BottomNavigationBarItem(icon: Icon(Icons.settings_outlined), activeIcon: Icon(Icons.settings), label: "Ayarlar"),
        ],
      ),
    );
  }
}

// ─── TOAST DATA CLASS ───
class _ToastItem {
  final int id;
  final String msg;
  final IconData icon;
  final Color color;
  _ToastItem({required this.id, required this.msg, required this.icon, required this.color});
}

// ─── DURAK DETAY ALT SHEET ───

class _DurakDetailSheet extends StatefulWidget {
  final Map<String, dynamic> durak;
  final String durakKod;
  final Function(int count)? onResult;
  const _DurakDetailSheet({required this.durak, required this.durakKod, this.onResult});
  @override
  State<_DurakDetailSheet> createState() => _DurakDetailSheetState();
}

class _DurakDetailSheetState extends State<_DurakDetailSheet> {
  List<dynamic> _araclar = [];
  bool _loading = true;
  String _statusMsg = "ASIS API sorgulanıyor...";

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _statusMsg = "📡 Durak ${widget.durakKod} sorgulanıyor...");
    try {
      final araclar = await ApiService.getDuragaYaklasanAraclar(widget.durakKod);
      if (mounted) {
        setState(() {
          _araclar = araclar;
          _loading = false;
          _statusMsg = araclar.isNotEmpty ? "✅ ${araclar.length} araç yaklaşıyor" : "ℹ️ Yaklaşan araç bulunamadı";
        });
        widget.onResult?.call(araclar.length);
      }
    } catch (e) {
      if (mounted) setState(() { _loading = false; _statusMsg = "❌ API hatası: $e"; });
      widget.onResult?.call(0);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.55,
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)))),
        const SizedBox(height: 16),
        Row(children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF2979FF), Color(0xFF00BFA5)]),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Center(child: Icon(Icons.location_on, color: Colors.white, size: 22)),
          ),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(widget.durak['ad']?.toString() ?? '', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
            Text("Durak No: ${widget.durakKod}", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 12)),
          ])),
        ]),
        const SizedBox(height: 12),
        // Status mesajı
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: _loading ? const Color(0xFF1A2940) : (_araclar.isNotEmpty ? const Color(0xFF1B3A1B) : const Color(0xFF1A2940)),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(children: [
            if (_loading) const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF2979FF)))
            else Icon(_araclar.isNotEmpty ? Icons.check_circle : Icons.info, size: 14, color: _araclar.isNotEmpty ? const Color(0xFF69F0AE) : const Color(0xFF546E8A)),
            const SizedBox(width: 8),
            Expanded(child: Text(_statusMsg, style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.7)))),
          ]),
        ),
        const SizedBox(height: 12),
        if (_loading)
          const Expanded(child: Center(child: CircularProgressIndicator(color: Color(0xFF2979FF))))
        else if (_araclar.isEmpty)
          Expanded(child: Center(child: Text("Bu durağa yaklaşan araç yok\n\n(ASIS API yanıt vermedi veya araç yok)",
            textAlign: TextAlign.center, style: TextStyle(color: Colors.white.withOpacity(0.3)))))
        else
          Expanded(
            child: ListView.builder(
              itemCount: _araclar.length,
              itemBuilder: (_, i) {
                final a = _araclar[i];
                final lineCode = a['BusLineCode']?.toString() ?? '?';
                final remaining = a['RemainingTimeCurr']?.toString() ?? '?';
                return Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  decoration: BoxDecoration(color: const Color(0xFF1A2940), borderRadius: BorderRadius.circular(10)),
                  child: ListTile(
                    leading: Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFFFF5252), Color(0xFFD50000)]), borderRadius: BorderRadius.circular(10)),
                      child: Center(child: Text("${remaining}dk", style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold))),
                    ),
                    title: Text("$lineCode Hattı", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                    subtitle: Text("~$remaining dakika", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
                  ),
                );
              },
            ),
          ),
      ]),
    );
  }
}
