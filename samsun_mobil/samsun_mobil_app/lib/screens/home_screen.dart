import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/db_service.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final MapController _mapController = MapController();
  List<Map<String, dynamic>> _duraklar = [];
  bool _isLoading = true;

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

  void _onDurakTapped(Map<String, dynamic> durak) async {
    // API'den sunucusuz veri çekme demosu
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return const Center(child: CircularProgressIndicator());
      },
    );

    String stopId = durak['id'].toString(); // veya gtfs_stop_id
    final araclar = await ApiService.getDuragaYaklasanAraclar(stopId);

    Navigator.pop(context); // Yüklemeyi kapat

    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                durak['ad'],
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              if (araclar.isEmpty)
                const Text("Yaklaşan araç verisi bulunamadı veya WAF/CORS engeline takıldı.")
              else
                ...araclar.map((a) => ListTile(
                  leading: const Icon(Icons.directions_bus, color: Colors.blue),
                  title: Text(a['hatKodu'] ?? 'Bilinmeyen Hat'),
                  trailing: Text("${a['kalanSure'] ?? '?'} dk"),
                )).toList()
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
        title: const Text('Yakın Duraklar (Çevrimdışı DB)'),
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: const LatLng(41.2867, 36.33), // Samsun Merkez
                initialZoom: 13.0,
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.samsun.serverless',
                ),
                MarkerLayer(
                  markers: _duraklar.take(500).map((d) {
                    return Marker(
                      point: LatLng(d['lat'], d['lon']),
                      width: 40,
                      height: 40,
                      child: GestureDetector(
                        onTap: () => _onDurakTapped(d),
                        child: const Icon(
                          Icons.location_on,
                          color: Colors.red,
                          size: 30,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
    );
  }
}
