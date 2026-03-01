import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../services/db_service.dart';
import '../services/api_service.dart';
import 'alarm_screen.dart';
import 'offline_wakeup_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final MapController _mapController = MapController();
  List<Map<String, dynamic>> _duraklar = [];
  bool _isLoading = true;
  
  // Routing variables
  final TextEditingController _baslangicController = TextEditingController();
  final TextEditingController _hedefController = TextEditingController();
  List<LatLng> _routePolyline = [];
  List<Map<String, dynamic>> _routeResults = [];
  bool _isRouting = false;

  @override
  void initState() {
    super.initState();
    _loadDuraklar();
  }

  Future<void> _loadDuraklar() async {
    final duraklar = await DBService().getDuraklar();
    setState(() {
      _duraklar = duraklar;
      _isLoading = false;
    });
  }

  Future<void> _calculateRoute() async {
    if (_hedefController.text.isEmpty) return;
    
    setState(() {
      _isRouting = true;
      _routePolyline = [];
      _routeResults = [];
    });

    try {
      // API call to the local Python backend
      // Note: For physical device, change localhost to the PC's IP address (e.g., 192.168.1.x)
      // For Android emulator, use 10.0.2.2
      final String start = _baslangicController.text.isNotEmpty ? _baslangicController.text : "Samsun Meydan";
      final String url = 'http://10.0.2.2:8000/api/rota?start=${Uri.encodeComponent(start)}&end=${Uri.encodeComponent(_hedefController.text)}';
      
      final response = await http.get(Uri.parse(url));
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        if (data.isNotEmpty) {
          setState(() {
            _routeResults = List<Map<String, dynamic>>.from(data);
            
            // Extract polyline from the best route (index 0)
            if (_routeResults[0]['polyline'] != null) {
              final List<dynamic> coords = _routeResults[0]['polyline'];
              _routePolyline = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList();
              
              // Move map to the center of the route
              if (_routePolyline.isNotEmpty) {
                final bounds = LatLngBounds.fromPoints(_routePolyline);
                _mapController.fitCamera(CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(50)));
              }
            }
          });
          _showRouteResultsBottomSheet();
        } else {
          _showError("Rota bulunamadı.");
        }
      } else {
        _showError("Sunucu hatası: ${response.statusCode}");
      }
    } catch (e) {
      _showError("Bağlantı hatası: Backend çalışmıyor olabilir. ($e)");
    } finally {
      setState(() {
        _isRouting = false;
      });
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  void _showRouteResultsBottomSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
          height: MediaQuery.of(context).size.height * 0.5,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("📍 Bulunan Rotalar", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              Expanded(
                child: ListView.builder(
                  itemCount: _routeResults.length,
                  itemBuilder: (context, index) {
                    final r = _routeResults[index];
                    final isDirect = r['type'] == 'DIRECT';
                    return Card(
                      color: isDirect ? Colors.green.shade50 : Colors.amber.shade50,
                      child: ListTile(
                        leading: Icon(isDirect ? Icons.directions_bus : Icons.transfer_within_a_station, color: isDirect ? Colors.green : Colors.amber.shade800),
                        title: Text(isDirect ? "Doğrudan Hat" : "Aktarmalı Rota (Tahmini)"),
                        subtitle: Text("Puan: ${r['total_score']}"),
                        onTap: () {
                          // Update polyline on map if user clicks another route
                          if (r['polyline'] != null) {
                            setState(() {
                              final List<dynamic> coords = r['polyline'];
                              _routePolyline = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList();
                            });
                            Navigator.pop(context);
                          }
                        },
                      ),
                    );
                  },
                ),
              )
            ],
          ),
        );
      },
    );
  }

  void _onDurakTapped(Map<String, dynamic> durak) async {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) {
        return const Center(child: CircularProgressIndicator());
      },
    );

    String stopId = durak['id'].toString();
    final araclar = await ApiService.getDuragaYaklasanAraclar(stopId);

    Navigator.pop(context);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
          height: MediaQuery.of(context).size.height * 0.65,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                durak['ad'],
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton.icon(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AlarmScreen(durak: durak))),
                    icon: const Icon(Icons.alarm_on, size: 18),
                    label: const Text("Sabah Alarmı"),
                  ),
                  ElevatedButton.icon(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => OfflineWakeUpScreen(durak: durak))),
                    icon: const Icon(Icons.bedtime, size: 18),
                    label: const Text("Uyku Modu"),
                  ),
                ],
              ),
              const Divider(height: 30),
              const Text("Yaklaşan Araçlar (Canlı):", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
              const SizedBox(height: 10),
              if (araclar.isEmpty)
                const Expanded(child: Center(child: Text("Yaklaşan araç verisi bulunamadı.")))
              else
                Expanded(
                  child: ListView.builder(
                    itemCount: araclar.length,
                    itemBuilder: (context, index) {
                      final a = araclar[index];
                      return ListTile(
                        leading: const Icon(Icons.directions_bus, color: Colors.blue),
                        title: Text(a['hatKodu'] ?? 'Bilinmeyen Hat'),
                        trailing: Text("${a['kalanSure'] ?? '?'} dk", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.green)),
                      );
                    },
                  ),
                )
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kişisel Araç Asistanı'),
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Routing Input Panel
                Container(
                  padding: const EdgeInsets.all(12),
                  color: Colors.white,
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _baslangicController,
                              decoration: const InputDecoration(
                                hintText: "Başlangıç (Örn: Mevcut Konum, Atakum)",
                                prefixIcon: Icon(Icons.my_location, color: Colors.blue),
                                border: OutlineInputBorder(),
                                isDense: true,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _hedefController,
                              decoration: const InputDecoration(
                                hintText: "Nereye gideceksiniz? (Örn: Çarşamba)",
                                prefixIcon: Icon(Icons.place, color: Colors.red),
                                border: OutlineInputBorder(),
                                isDense: true,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: _isRouting ? null : _calculateRoute,
                            style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
                            child: _isRouting ? const SizedBox(width:20, height:20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.search),
                          )
                        ],
                      ),
                    ],
                  ),
                ),
                
                // Map Area
                Expanded(
                  child: FlutterMap(
                    mapController: _mapController,
                    options: MapOptions(
                      initialCenter: const LatLng(41.2867, 36.33),
                      initialZoom: 13.0,
                    ),
                    children: [
                      TileLayer(
                        urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'com.samsun.serverless',
                      ),
                      
                      // Routing Polyline Layer
                      if (_routePolyline.isNotEmpty)
                        PolylineLayer(
                          polylines: [
                            Polyline(
                              points: _routePolyline,
                              strokeWidth: 5.0,
                              color: Colors.blue,
                            ),
                          ],
                        ),

                      MarkerLayer(
                        markers: _duraklar.take(500).map((d) {
                          return Marker(
                            point: LatLng(d['lat'], d['lon']),
                            width: 30,
                            height: 30,
                            child: GestureDetector(
                              onTap: () => _onDurakTapped(d),
                              child: Container(
                                decoration: BoxDecoration(
                                  color: Colors.blueGrey,
                                  shape: BoxShape.circle,
                                  border: Border.all(color: Colors.white, width: 2),
                                ),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
