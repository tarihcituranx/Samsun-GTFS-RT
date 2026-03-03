import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/ybs_api_service.dart';
import '../services/samair_service.dart';

class SamAirScreen extends StatefulWidget {
  const SamAirScreen({Key? key}) : super(key: key);

  @override
  State<SamAirScreen> createState() => _SamAirScreenState();
}

class _SamAirScreenState extends State<SamAirScreen> with SingleTickerProviderStateMixin {
  final MapController _mapController = MapController();
  List<dynamic> _liveBuses = [];
  bool _isLoading = true;
  Timer? _timer;
  late TabController _tabController;

  // Çarşamba Havaalanı Konumu
  final LatLng _airportLocation = const LatLng(41.2589, 36.5564);

  final List<Map<String, dynamic>> _lines = [
    {'id': 3, 'code': 'H1', 'name': 'OMÜ - İlkadım', 'color': Color(0xFF2979FF)},
    {'id': 4, 'code': 'H2', 'name': 'TTTM - Canik', 'color': Color(0xFF00BFA5)},
    {'id': 5, 'code': 'H3', 'name': 'Bafra - 19 Mayıs', 'color': Color(0xFFFF5252)},
    {'id': 9, 'code': 'H4', 'name': 'Çarşamba - Salıpazarı', 'color': Color(0xFFFFAB00)},
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
    _fetchLiveBuses();
    _timer = Timer.periodic(const Duration(seconds: 15), (_) => _fetchLiveBuses());
  }

  @override
  void dispose() {
    _timer?.cancel();
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchLiveBuses() async {
    // 1. Önce YBS proxy dene
    var buses = await YbsApiService().getSamairAraclar();
    // 2. YBS boşsa, ASIS RealTimeData üzerinden H1-H4 çek
    if (buses.isEmpty) {
      buses = await SamAirService.getLiveSamAirBuses();
    }
    if (mounted) {
      setState(() {
        _liveBuses = buses;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // TabBar
        Container(
          color: const Color(0xFF0F1E36),
          child: TabBar(
            controller: _tabController,
            isScrollable: true,
            indicatorColor: const Color(0xFF2979FF),
            labelColor: const Color(0xFF2979FF),
            unselectedLabelColor: Colors.white54,
            tabs: const [
              Tab(icon: Icon(Icons.map), text: "Harita"),
              Tab(text: "H1 OMÜ"),
              Tab(text: "H2 TTTM"),
              Tab(text: "H3 Bafra"),
              Tab(text: "H4 Çarşamba"),
            ],
          ),
        ),
        
        // TabBarView
        Expanded(
          child: TabBarView(
            controller: _tabController,
            physics: const NeverScrollableScrollPhysics(), // Harita kaydırması ile çakışmasın
            children: [
              _buildMapTab(),
              _SamAirScheduleTab(lineId: 3, lineName: 'H1', color: const Color(0xFF2979FF)),
              _SamAirScheduleTab(lineId: 4, lineName: 'H2', color: const Color(0xFF00BFA5)),
              _SamAirScheduleTab(lineId: 5, lineName: 'H3', color: const Color(0xFFFF5252)),
              _SamAirScheduleTab(lineId: 9, lineName: 'H4', color: const Color(0xFFFFAB00)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMapTab() {
    return Stack(
      children: [
        FlutterMap(
          mapController: _mapController,
          options: MapOptions(
            initialCenter: const LatLng(41.2867, 36.3300),
            initialZoom: 11.0,
          ),
          children: [
            TileLayer(
              urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
              tileProvider: NetworkTileProvider(
                headers: {
                  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                  'Referer': 'https://www.openstreetmap.org/',
                },
              ),
            ),
            MarkerLayer(
              markers: [
                // Havaalanı İşareti
                Marker(
                  point: _airportLocation,
                  width: 60, height: 60,
                  child: Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF152238),
                      shape: BoxShape.circle,
                      border: Border.all(color: const Color(0xFF2979FF), width: 2),
                    ),
                    child: const Icon(Icons.local_airport, color: Color(0xFF2979FF), size: 30),
                  ),
                ),
                // Canlı Araçlar — ASIS: lat/lon/plate/speed, YBS: Enlem/Boylam/Plaka/Hizi
                ..._liveBuses.where((b) {
                  final hasAsis = b['lat'] != null && b['lon'] != null;
                  final hasYbs = b['Enlem'] != null && b['Boylam'] != null;
                  return hasAsis || hasYbs;
                }).map((b) {
                  // ASIS format (samair_service.dart) veya YBS format
                  final lat = (b['lat'] as double?) ?? (double.tryParse((b['Enlem'] ?? '0').toString().replaceAll(',', '.')) ?? 0);
                  final lon = (b['lon'] as double?) ?? (double.tryParse((b['Boylam'] ?? '0').toString().replaceAll(',', '.')) ?? 0);
                  final hizi = (b['speed'] ?? b['hiz'] ?? b['Hizi'] ?? '0').toString();
                  final plaka = (b['plate'] ?? b['plaka'] ?? b['Plaka'] ?? 'SAMAIR').toString();
                  final hatKodu = (b['lineCode'] ?? b['HatKodu'] ?? '').toString();
                  
                  return Marker(
                    point: LatLng(lat, lon),
                    width: 45, height: 45,
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(colors: [Color(0xFF2979FF), Color(0xFF00BFA5)]),
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white, width: 2),
                        boxShadow: [BoxShadow(blurRadius: 8, color: const Color(0xFF2979FF).withOpacity(0.5))],
                      ),
                      child: Center(
                        child: Text(
                          plaka.length > 3 ? plaka.substring(plaka.length - 4) : plaka,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10, color: Colors.white),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ],
            ),
          ],
        ),
        
        if (_isLoading)
          Center(
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(color: const Color(0xFF152238).withOpacity(0.9), borderRadius: BorderRadius.circular(16)),
              child: const Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(color: Color(0xFF2979FF)),
                  SizedBox(height: 16),
                  Text("SamAIR araçları YBS'den yükleniyor...", style: TextStyle(color: Colors.white)),
                ],
              ),
            ),
          ),
          
        Positioned(
          bottom: 20, left: 20, right: 20,
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF152238),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withOpacity(0.05)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      Image.asset('assets/samair.png', width: 24, height: 24, fit: BoxFit.contain, errorBuilder: (context, error, stackTrace) => const Icon(Icons.flight_takeoff, color: Color(0xFF2979FF))),
                      const SizedBox(width: 8),
                      const Text("YBS Canlı Filo", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white)),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(color: const Color(0xFF2979FF).withOpacity(0.2), borderRadius: BorderRadius.circular(12)),
                        child: Text("${_liveBuses.length} Araç", style: const TextStyle(color: Color(0xFF2979FF), fontWeight: FontWeight.bold)),
                      )
                    ],
                  ),
                  const Divider(color: Colors.white12, height: 24),
                  if (_liveBuses.isEmpty && !_isLoading)
                     Text("Şu anda hareket halinde olan SAMAIR aracı bulunmuyor.", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13)),
                  if (_liveBuses.isNotEmpty)
                    SizedBox(
                      height: 40,
                      child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _liveBuses.length,
                        itemBuilder: (context, i) {
                          final b = _liveBuses[i];
                          final plaka = b['Plaka']?.toString() ?? '?';
                          final hizi = b['Hizi']?.toString() ?? '0';
                          return Padding(
                            padding: const EdgeInsets.only(right: 8.0),
                            child: Chip(
                              avatar: CircleAvatar(
                                backgroundColor: Colors.white.withOpacity(0.05),
                                radius: 20,
                                child: const Icon(Icons.flight_takeoff, color: Colors.white70),
                              ),
                              label: Text("$plaka - $hizi km/s", style: const TextStyle(color: Colors.white, fontSize: 11)),
                              backgroundColor: const Color(0xFF2979FF),
                              side: BorderSide.none,
                            ),
                          );
                        },
                      ),
                    )
                ],
              ),
            ),
          ),
        )
      ],
    );
  }
}

// ─── SCHEDULE TAB ───

class _SamAirScheduleTab extends StatefulWidget {
  final int lineId;
  final String lineName;
  final Color color;

  const _SamAirScheduleTab({required this.lineId, required this.lineName, required this.color});

  @override
  State<_SamAirScheduleTab> createState() => _SamAirScheduleTabState();
}

class _SamAirScheduleTabState extends State<_SamAirScheduleTab> {
  List<dynamic> _schedules = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSchedules();
  }

  Future<void> _loadSchedules() async {
    final s = await YbsApiService().getSamairSaatleri(widget.lineId);
    if (mounted) {
      setState(() {
        _schedules = s;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return Center(child: CircularProgressIndicator(color: widget.color));

    if (_schedules.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.airplanemode_inactive, size: 48, color: Colors.white.withOpacity(0.2)),
            const SizedBox(height: 16),
            Text("Bu hatta ait sefer bulunamadı.", style: TextStyle(color: Colors.white.withOpacity(0.5))),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: _schedules.length,
      itemBuilder: (context, i) {
        final s = _schedules[i];
        final cityTime = s['SehirKalkis']?.toString() ?? '-';
        final flightTime = s['UcusSaati']?.toString() ?? '-';
        final flightNo = s['UcusKodu']?.toString() ?? '';
        final note = s['Aciklama']?.toString() ?? '';

        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          decoration: BoxDecoration(
            color: const Color(0xFF152238),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: widget.color.withOpacity(0.3)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                // Şehirden Kalkış
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("Şehir Kalkış", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11)),
                      Text(cityTime, style: TextStyle(color: widget.color, fontSize: 24, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
                
                // Flight Icon
                Icon(Icons.flight_takeoff, color: Colors.white.withOpacity(0.2), size: 32),
                
                // Uçuş Saati
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text("Uçuş Saati", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11)),
                      Text(flightTime, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                      if (flightNo.isNotEmpty)
                        Text(flightNo, style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
