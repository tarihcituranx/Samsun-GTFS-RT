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
  void initState() { super.initState(); _loadOdaklar(); }

  Future<void> _loadOdaklar() async {
    final odaklar = await DBService().getOdaklar();
    if (mounted) setState(() { _odaklar = odaklar; _isLoading = false; });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator(color: Color(0xFF00BFA5)));

    return Column(children: [
      // Header
      Container(
        width: double.infinity, padding: const EdgeInsets.all(20),
        decoration: const BoxDecoration(
          gradient: LinearGradient(colors: [Color(0xFF004D40), Color(0xFF00695C), Color(0xFF00897B)]),
        ),
        child: Column(children: [
          const Text("🎯 Odak Samsun", style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
          const SizedBox(height: 4),
          Text("Turistik ve Özel Güzergahlar", style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12)),
        ]),
      ),

      // Uyarı
      Container(
        margin: const EdgeInsets.all(8), padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: const Color(0xFF2A2200),
          border: Border.all(color: const Color(0xFFFFAB00).withOpacity(0.2)),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(children: [
          const Text("⚠️ ", style: TextStyle(fontSize: 14)),
          Expanded(child: Text("Fiyatlar değişiklik gösterebilir. Lütfen teyit ediniz.",
            style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.6)))),
        ]),
      ),

      // İletişim
      Container(
        margin: const EdgeInsets.symmetric(horizontal: 8), padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(color: const Color(0xFF152238), borderRadius: BorderRadius.circular(10)),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Icon(Icons.phone, size: 16, color: Color(0xFF2979FF)),
          const SizedBox(width: 6),
          const Text("0362 431 10 12", style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF2979FF), fontSize: 13)),
        ]),
      ),

      // Odak Listesi
      Expanded(
        child: _odaklar.isEmpty
            ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                const Text("🎯", style: TextStyle(fontSize: 48)),
                const SizedBox(height: 12),
                Text("Odak verisi henüz yüklenmemiş", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 14)),
                const SizedBox(height: 4),
                Text("DB güncellendikten sonra burada görünecek", style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 11)),
              ]))
            : ListView.builder(
                padding: const EdgeInsets.all(8), itemCount: _odaklar.length,
                itemBuilder: (_, i) {
                  final o = _odaklar[i];
                  return Container(
                    margin: const EdgeInsets.only(bottom: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF152238),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF00BFA5).withOpacity(0.1)),
                    ),
                    child: ListTile(
                      leading: Container(
                        width: 42, height: 42,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(colors: [Color(0xFF00BFA5), Color(0xFF00897B)]),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Center(child: Text("🎯", style: TextStyle(fontSize: 18))),
                      ),
                      title: Text("${o['kod'] ?? ''} ${o['ad'] ?? ''}", style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: Colors.white)),
                      subtitle: Text(o['gunler']?.toString() ?? '', style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.35))),
                      trailing: Icon(Icons.chevron_right, color: Colors.white.withOpacity(0.2)),
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => OdakDetailScreen(odak: o))),
                    ),
                  );
                },
              ),
      ),
    ]);
  }
}

// ─── ODAK DETAY ───

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
  void initState() { super.initState(); _loadDuraklar(); }

  Future<void> _loadDuraklar() async {
    final id = widget.odak['id']?.toString() ?? '';
    final duraklar = await DBService().getOdakDuraklari(id);
    if (mounted) setState(() { _duraklar = duraklar; _isLoading = false; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("🎯 ${widget.odak['kod'] ?? ''} ${widget.odak['ad'] ?? ''}", style: const TextStyle(fontSize: 14)),
        backgroundColor: const Color(0xFF004D40),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00BFA5)))
          : Column(children: [
              // Info
              Container(
                margin: const EdgeInsets.all(12), padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(colors: [Color(0xFF004D40), Color(0xFF00695C)]),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
                  Column(children: [
                    Text("${_duraklar.length}", style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white)),
                    Text("Durak", style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.5))),
                  ]),
                  if (_duraklar.isNotEmpty)
                    Column(children: [
                      Text("₺${_duraklar.first['fiyat'] ?? '?'}", style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white)),
                      Text("Tam", style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.5))),
                    ]),
                ]),
              ),

              // Harita
              if (_duraklar.isNotEmpty) Container(
                height: 200, margin: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(borderRadius: BorderRadius.circular(14), border: Border.all(color: Colors.white.withOpacity(0.08))),
                clipBehavior: Clip.antiAlias,
                child: FlutterMap(
                  options: MapOptions(
                    initialCenter: LatLng((_duraklar.first['lat'] as num?)?.toDouble() ?? 41.29, (_duraklar.first['lon'] as num?)?.toDouble() ?? 36.33),
                    initialZoom: 12.0,
                  ),
                  children: [
                    TileLayer(urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
                    MarkerLayer(markers: _duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null && (d['lat'] as num).toDouble() > 0).map((d) {
                      final sira = (d['sira'] as num?)?.toInt() ?? 0;
                      return Marker(
                        point: LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()),
                        width: 22, height: 22,
                        child: Container(
                          decoration: BoxDecoration(color: const Color(0xFF00BFA5), shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 1.5)),
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
                  padding: const EdgeInsets.all(8), itemCount: _duraklar.length,
                  itemBuilder: (_, i) {
                    final d = _duraklar[i];
                    return Container(
                      margin: const EdgeInsets.only(bottom: 4),
                      decoration: BoxDecoration(color: const Color(0xFF152238), borderRadius: BorderRadius.circular(10)),
                      child: ListTile(
                        leading: Container(width: 28, height: 28,
                          decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF00BFA5), Color(0xFF00897B)]), borderRadius: BorderRadius.circular(8)),
                          child: Center(child: Text("${i + 1}", style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold))),
                        ),
                        title: Text(d['ad']?.toString() ?? '', style: const TextStyle(fontSize: 13, color: Colors.white)),
                        subtitle: Text("Tam: ₺${d['fiyat'] ?? '?'} / İnd: ₺${d['fiyat_ogr'] ?? '?'}", style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.4))),
                        dense: true,
                      ),
                    );
                  },
                ),
              ),
            ]),
    );
  }
}
