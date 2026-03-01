import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/samair_service.dart';

class SamAirScreen extends StatefulWidget {
  const SamAirScreen({Key? key}) : super(key: key);

  @override
  State<SamAirScreen> createState() => _SamAirScreenState();
}

class _SamAirScreenState extends State<SamAirScreen> {
  final MapController _mapController = MapController();
  List<Map<String, dynamic>> _liveBuses = [];
  bool _isLoading = true;
  Timer? _timer;

  // Çarşamba Havaalanı Konumu
  final LatLng _airportLocation = const LatLng(41.2589, 36.5564);

  @override
  void initState() {
    super.initState();
    _fetchBuses();
    _timer = Timer.periodic(const Duration(seconds: 15), (_) => _fetchBuses());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetchBuses() async {
    if (!mounted) return;
    final buses = await SamAirService.getLiveSamAirBuses();
    if (!mounted) return;
    setState(() {
      _liveBuses = buses;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('✈️ SamAIR Takip'),
        centerTitle: true,
        backgroundColor: Colors.indigo.shade800,
        foregroundColor: Colors.white,
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: const LatLng(41.2867, 36.3300), // Samsun Merkez
              initialZoom: 11.0,
            ),
            children: [
              TileLayer(
                urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                userAgentPackageName: 'com.example.samsun_transit',
              ),
              MarkerLayer(
                markers: [
                  // Havaalanı İşareti
                  Marker(
                    point: _airportLocation,
                    width: 60,
                    height: 60,
                    child: const Icon(Icons.local_airport, color: Colors.blueAccent, size: 40),
                  ),
                  // Canlı Araçlar
                  ..._liveBuses.map((b) => Marker(
                    point: LatLng(b['lat'] as double, b['lon'] as double),
                    width: 45,
                    height: 45,
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.indigo.shade800, width: 2),
                        boxShadow: const [BoxShadow(blurRadius: 4, color: Colors.black38)],
                      ),
                      child: Center(
                        child: Text(
                          b['lineCode']?.toString() ?? 'H',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.red),
                        ),
                      ),
                    ),
                  )).toList(),
                ],
              ),
            ],
          ),
          
          if (_isLoading)
            const Center(
              child: Card(
                child: Padding(
                  padding: EdgeInsets.all(16.0),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text("SamAIR araçları aranıyor..."),
                    ],
                  ),
                ),
              ),
            ),
            
          Positioned(
            bottom: 20,
            left: 20,
            right: 20,
            child: Card(
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.flight_takeoff, color: Colors.indigo),
                        const SizedBox(width: 8),
                        const Text("Aktif Araçlar", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: Colors.green.shade100, borderRadius: BorderRadius.circular(12)),
                          child: Text("${_liveBuses.length} Görevde", style: TextStyle(color: Colors.green.shade800, fontWeight: FontWeight.bold)),
                        )
                      ],
                    ),
                    const Divider(),
                    if (_liveBuses.isEmpty && !_isLoading)
                       const Text("Şu anda hareket halinde olan SAMAIR aracı bulunmuyor.", style: TextStyle(color: Colors.grey, fontSize: 13)),
                    if (_liveBuses.isNotEmpty)
                      SizedBox(
                        height: 60,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          itemCount: _liveBuses.length,
                          itemBuilder: (context, i) {
                            final b = _liveBuses[i];
                            return Padding(
                              padding: const EdgeInsets.only(right: 8.0),
                              child: Chip(
                                avatar: const Icon(Icons.directions_bus, size: 16, color: Colors.white),
                                label: Text("${b['lineCode']} - ${b['speed']} km/s", style: const TextStyle(color: Colors.white)),
                                backgroundColor: Colors.indigo.shade400,
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
      ),
    );
  }
}
