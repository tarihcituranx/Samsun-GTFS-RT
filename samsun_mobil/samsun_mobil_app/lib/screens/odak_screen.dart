import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/api_service.dart';
import '../services/db_service.dart';
import '../services/ybs_api_service.dart';

class OdakScreen extends StatefulWidget {
  const OdakScreen({Key? key}) : super(key: key);
  @override
  State<OdakScreen> createState() => _OdakScreenState();
}

class _OdakScreenState extends State<OdakScreen> {
  List<dynamic> _odaklar = [];
  bool _isLoading = true;
  bool _isOfflineFallback = false;

  @override
  void initState() { super.initState(); _loadOdaklar(); }

  Future<void> _loadOdaklar() async {
    // 1. Önce YBS proxy → 2. samsun.py DB → 3. yerel DB
    var dynOdaklar = await YbsApiService().getOdakSamsunWithFallback();
    
    // 3. Son çare: yerel DB
    if (dynOdaklar.isEmpty) {
      _isOfflineFallback = true;
      dynOdaklar = await DBService().getOdaklar();
    }

    if (mounted) {
      setState(() {
        _odaklar = dynOdaklar;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator(color: Color(0xFF00BFA5)));

    return Column(children: [
      // Header
      Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft, end: Alignment.bottomRight,
            colors: [Color(0xFF2979FF), Color(0xFF0D47A1)],
          ),
          boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 10, offset: Offset(0, 4))],
        ),
        child: Row(
          children: [
            Image.asset('assets/odak.png', width: 72, height: 72, fit: BoxFit.contain, errorBuilder: (context, error, stackTrace) => const SizedBox(width: 72)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("Turistik Rotalar", style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold, letterSpacing: 1)),
                  const SizedBox(height: 8),
                  Text("Şehrin turistik ve kültürel rotalarını keşfedin.", style: TextStyle(color: Colors.white.withOpacity(0.85), fontSize: 14)),
                ],
              ),
            ),
          ],
        ),
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
        child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(Icons.phone, size: 16, color: Color(0xFF2979FF)),
          SizedBox(width: 6),
          Text("0362 431 10 12", style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF2979FF), fontSize: 13)),
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
                      title: Text("${o['kod'] ?? o['kodu'] ?? ''} ${o['ad'] ?? o['adi'] ?? ''}", style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: Colors.white)),
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
  List<dynamic> _vehicles = [];
  bool _isLoading = true;
  bool _vehiclesLoading = false;
  bool _odakActive = false;
  String _odakMessage = '';

  @override
  void initState() { super.initState(); _loadDuraklar(); }

  Future<void> _loadDuraklar() async {
    final id = (widget.odak['id'] ?? widget.odak['kodu'] ?? '').toString();
    // Önce proxy'den (fiyat dahil), sonra yerel DB
    var duraklar = await YbsApiService().getOdakDuraklari(id);
    if (duraklar.isEmpty) {
      duraklar = await DBService().getOdakDuraklari(id);
    }
    if (mounted) setState(() { _duraklar = duraklar.map((d) => d is Map<String, dynamic> ? d : Map<String, dynamic>.from(d)).toList(); _isLoading = false; });
  }

  Future<void> _loadVehicles() async {
    // Tüm araçlar (Odak dahil) ASIS RealTimeData ile konum gösteriyor
    // Tramvay ve Teleferik hariç — onlar RealTimeData'da yok
    final kod = (widget.odak['kod'] ?? widget.odak['kodu'] ?? '').toString();
    if (kod.isEmpty) return;
    
    setState(() => _vehiclesLoading = true);
    try {
      final vehicles = await ApiService.getHattakiAraclar(kod);
      if (mounted) {
        setState(() {
          _odakActive = vehicles.isNotEmpty;
          _odakMessage = vehicles.isEmpty ? 'Aktif araç bulunamadı' : '';
          _vehicles = vehicles;
          _vehiclesLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _odakActive = false;
          _odakMessage = 'Araç bilgileri alınamadı. İnternet bağlantınızı kontrol edin.';
          _vehicles = [];
          _vehiclesLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("🎯 ${widget.odak['kod'] ?? widget.odak['kodu'] ?? ''} ${widget.odak['ad'] ?? widget.odak['adi'] ?? ''}", style: const TextStyle(fontSize: 14)),
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
                  if (_vehicles.isNotEmpty)
                    Column(children: [
                      Text("${_vehicles.length}", style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFFFF5252))),
                      Text("Araç", style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.5))),
                    ]),
                ]),
              ),

              // Canlı Araç Butonu
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _vehiclesLoading ? null : _loadVehicles,
                    icon: _vehiclesLoading
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.directions_bus, size: 18),
                    label: Text(_vehiclesLoading ? 'Yükleniyor...' : '🚌 Canlı Araç Takip'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00BFA5),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ),
              ),
              
              // Durum mesajı
              if (_odakMessage.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(color: const Color(0xFF2A2200), borderRadius: BorderRadius.circular(8)),
                    child: Row(children: [
                      const Icon(Icons.schedule, size: 16, color: Color(0xFFFFAB00)),
                      const SizedBox(width: 8),
                      Expanded(child: Text(_odakMessage, style: const TextStyle(fontSize: 12, color: Color(0xFFFFAB00)))),
                    ]),
                  ),
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
                    TileLayer(
            urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            tileProvider: NetworkTileProvider(
              headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.openstreetmap.org/',
              },
            ),
          ),
                    MarkerLayer(markers: [
                      // Durak markerları
                      ..._duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null && (d['lat'] as num).toDouble() > 0).map((d) {
                        final sira = (d['sira'] as num?)?.toInt() ?? 0;
                        return Marker(
                          point: LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()),
                          width: 22, height: 22,
                          child: Container(
                            decoration: BoxDecoration(color: const Color(0xFF00BFA5), shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 1.5)),
                            child: Center(child: Text("$sira", style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold))),
                          ),
                        );
                      }),
                      // Canlı araç markerları
                      ..._vehicles.where((v) => v is Map && v['lat'] != null).map((v) {
                        final lat = double.tryParse(v['lat']?.toString() ?? '0') ?? 0.0;
                        final lon = double.tryParse(v['lon']?.toString() ?? v['lng']?.toString() ?? '0') ?? 0.0;
                        if (lat == 0) return null;
                        return Marker(
                          point: LatLng(lat, lon),
                          width: 28, height: 28,
                          child: Container(
                            decoration: BoxDecoration(color: const Color(0xFFFF5252), shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 2),
                              boxShadow: [BoxShadow(color: const Color(0xFFFF5252).withOpacity(0.4), blurRadius: 6)]),
                            child: const Center(child: Icon(Icons.directions_bus, size: 14, color: Colors.white)),
                          ),
                        );
                      }).whereType<Marker>(),
                    ]),
                  ],
                ),
              ),

              // Durak Listesi
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.all(8), itemCount: _duraklar.length,
                  itemBuilder: (_, i) {
                    final d = _duraklar[i];
                    
                    // Bu durakta olan/yaklaşan odak araçlarını bul (yaklaşık 250 metre çapında eşleştirme)
                    final dLat = (d['lat'] as num?)?.toDouble();
                    final dLon = (d['lon'] as num?)?.toDouble();
                    List<dynamic> onThisStop = [];
                    
                    if (dLat != null && dLon != null && _vehicles.isNotEmpty) {
                      for (var v in _vehicles) {
                        if (v is! Map) continue;
                        final vLat = double.tryParse(v['lat']?.toString() ?? '0') ?? 0.0;
                        final vLon = double.tryParse(v['lon']?.toString() ?? v['lng']?.toString() ?? '0') ?? 0.0;
                        if (vLat == 0) continue;
                        const Distance distance = Distance();
                        final meter = distance(LatLng(dLat, dLon), LatLng(vLat, vLon));
                        if (meter < 250) { // 250 mt hata payı
                          onThisStop.add(v);
                        }
                      }
                    }

                    return Container(
                      margin: const EdgeInsets.only(bottom: 4),
                      decoration: BoxDecoration(color: const Color(0xFF152238), borderRadius: BorderRadius.circular(10)),
                      child: ListTile(
                        leading: Container(width: 28, height: 28,
                          decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF00BFA5), Color(0xFF00897B)]), borderRadius: BorderRadius.circular(8)),
                          child: Center(child: Text("${i + 1}", style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold))),
                        ),
                        title: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(child: Text(d['ad']?.toString() ?? '', style: const TextStyle(fontSize: 13, color: Colors.white))),
                            if (onThisStop.isNotEmpty)
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: onThisStop.map((v) => Container(
                                  margin: const EdgeInsets.only(left: 4),
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(color: const Color(0xFFFF5252), borderRadius: BorderRadius.circular(6)),
                                  child: const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.directions_bus, color: Colors.white, size: 10),
                                      SizedBox(width: 3),
                                      Text("SAMSUN", style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold)),
                                    ],
                                  ),
                                )).toList(),
                              )
                          ],
                        ),
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

