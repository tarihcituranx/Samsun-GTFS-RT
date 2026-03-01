import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/db_service.dart';

class OdakScreen extends StatefulWidget {
  const OdakScreen({Key? key}) : super(key: key);
  @override
  State<OdakScreen> createState() => _OdakScreenState();
}

class _OdakScreenState extends State<OdakScreen> {
  List<Map<String, dynamic>> _odaklar = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadOdaklar();
  }

  Future<void> _loadOdaklar() async {
    final odaklar = await DBService().getOdaklar();
    if (mounted) {
      setState(() {
        _odaklar = odaklar;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Column(
      children: [
        // Header
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: [Colors.green.shade700, Colors.green.shade400]),
          ),
          child: const Column(
            children: [
              Text("🎯 Odak Samsun Gezileri", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              SizedBox(height: 4),
              Text("Turistik ve Özel Rotalar", style: TextStyle(color: Colors.white70, fontSize: 12)),
            ],
          ),
        ),

        // Uyarı
        Container(
          margin: const EdgeInsets.all(8),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: Colors.amber.shade50,
            border: Border.all(color: Colors.amber.shade200),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Row(
            children: [
              Text("⚠️ ", style: TextStyle(fontSize: 16)),
              Expanded(child: Text("Fiyatlar değişiklik gösterebilir. Tam/İndirimli tarifeleri için lütfen teyit ediniz.", style: TextStyle(fontSize: 11, color: Colors.brown))),
            ],
          ),
        ),

        // İletişim
        Container(
          margin: const EdgeInsets.symmetric(horizontal: 8),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(8)),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.phone, size: 16, color: Colors.blue),
              SizedBox(width: 6),
              Text("Bilgi: 0362 431 10 12", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue, fontSize: 13)),
            ],
          ),
        ),

        // Odak Listesi
        Expanded(
          child: _odaklar.isEmpty
              ? const Center(child: Text("Odak verisi bulunamadı.", style: TextStyle(color: Colors.grey)))
              : ListView.builder(
                  padding: const EdgeInsets.all(8),
                  itemCount: _odaklar.length,
                  itemBuilder: (_, i) {
                    final o = _odaklar[i];
                    return Card(
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      child: ListTile(
                        leading: const CircleAvatar(backgroundColor: Colors.green, child: Text("🎯", style: TextStyle(fontSize: 18))),
                        title: Text("${o['kod'] ?? ''} ${o['ad'] ?? ''}", style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        subtitle: Text(o['gunler']?.toString() ?? '', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => _openOdakDetail(context, o),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  void _openOdakDetail(BuildContext context, Map<String, dynamic> odak) {
    Navigator.push(context, MaterialPageRoute(builder: (_) => OdakDetailScreen(odak: odak)));
  }
}

// ─── ODAK DETAY EKRANI ───

class OdakDetailScreen extends StatefulWidget {
  final Map<String, dynamic> odak;
  const OdakDetailScreen({Key? key, required this.odak}) : super(key: key);
  @override
  State<OdakDetailScreen> createState() => _OdakDetailScreenState();
}

class _OdakDetailScreenState extends State<OdakDetailScreen> {
  List<Map<String, dynamic>> _duraklar = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDuraklar();
  }

  Future<void> _loadDuraklar() async {
    final id = widget.odak['id']?.toString() ?? '';
    final duraklar = await DBService().getOdakDuraklari(id);
    if (mounted) {
      setState(() {
        _duraklar = duraklar;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("🎯 ${widget.odak['kod'] ?? ''} ${widget.odak['ad'] ?? ''}", style: const TextStyle(fontSize: 14)),
        backgroundColor: Colors.green.shade700,
        foregroundColor: Colors.white,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Bilgi Kartı
                Container(
                  margin: const EdgeInsets.all(12),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(12)),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      Column(children: [
                        Text("${_duraklar.length}", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.green.shade700)),
                        const Text("Durak", style: TextStyle(fontSize: 11, color: Colors.grey)),
                      ]),
                      if (_duraklar.isNotEmpty)
                        Column(children: [
                          Text("₺${_duraklar.first['fiyat'] ?? '?'}", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.green.shade700)),
                          const Text("Tam", style: TextStyle(fontSize: 11, color: Colors.grey)),
                        ]),
                    ],
                  ),
                ),

                // Harita
                if (_duraklar.isNotEmpty)
                  Container(
                    height: 200,
                    margin: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade300)),
                    clipBehavior: Clip.antiAlias,
                    child: FlutterMap(
                      options: MapOptions(
                        initialCenter: LatLng(
                          (_duraklar.first['lat'] as num?)?.toDouble() ?? 41.29,
                          (_duraklar.first['lon'] as num?)?.toDouble() ?? 36.33,
                        ),
                        initialZoom: 12.0,
                      ),
                      children: [
                        TileLayer(urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", userAgentPackageName: 'com.example.samsun_transit'),
                        MarkerLayer(markers: _duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null && (d['lat'] as num).toDouble() > 0).map((d) {
                          final sira = (d['sira'] as num?)?.toInt() ?? 0;
                          return Marker(
                            point: LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()),
                            width: 22, height: 22,
                            child: Container(
                              decoration: BoxDecoration(color: Colors.green, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 1.5)),
                              child: Center(child: Text("$sira", style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold))),
                            ),
                          );
                        }).toList()),
                      ],
                    ),
                  ),

                // Durak Listesi
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.all(8),
                    itemCount: _duraklar.length,
                    itemBuilder: (_, i) {
                      final d = _duraklar[i];
                      return Card(
                        child: ListTile(
                          leading: CircleAvatar(backgroundColor: Colors.green, radius: 14, child: Text("${i + 1}", style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold))),
                          title: Text(d['ad']?.toString() ?? '', style: const TextStyle(fontSize: 13)),
                          subtitle: Text("Tam: ₺${d['fiyat'] ?? '?'} / İndirimli: ₺${d['fiyat_ogr'] ?? '?'}", style: const TextStyle(fontSize: 11, color: Colors.grey)),
                          dense: true,
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }
}
