import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/db_service.dart';
import '../services/api_service.dart';

class HatlarScreen extends StatefulWidget {
  const HatlarScreen({Key? key}) : super(key: key);
  @override
  State<HatlarScreen> createState() => _HatlarScreenState();
}

class _HatlarScreenState extends State<HatlarScreen> {
  List<Map<String, dynamic>> _allHatlar = [];
  List<Map<String, dynamic>> _filteredHatlar = [];
  String _selectedKat = 'dil'; // dil = tümü
  String _searchQuery = '';
  bool _isLoading = true;

  static const Map<String, Map<String, dynamic>> KATEGORILER = {
    'dil': {'icon': '🌐', 'name': 'Tümü', 'color': Color(0xFF333333)},
    'otobus': {'icon': '🚌', 'name': 'Otobüs', 'color': Color(0xFF1877F2)},
    'ekspres': {'icon': '🚀', 'name': 'Ekspres', 'color': Color(0xFF9B59B6)},
    'tramvay': {'icon': '🚋', 'name': 'Tramvay', 'color': Color(0xFFE67E22)},
    'ring': {'icon': '🔄', 'name': 'Ring', 'color': Color(0xFFF39C12)},
    'tekne': {'icon': '🛥️', 'name': 'Tekne', 'color': Color(0xFF3498DB)},
    'teleferik': {'icon': '🚠', 'name': 'Teleferik', 'color': Color(0xFFE91E63)},
    'havalimani': {'icon': '✈️', 'name': 'H.limanı', 'color': Color(0xFFE74C3C)},
    'ilce': {'icon': '🏘️', 'name': 'İlçe', 'color': Color(0xFF1ABC9C)},
  };

  @override
  void initState() {
    super.initState();
    _loadHatlar();
  }

  Future<void> _loadHatlar() async {
    final hatlar = await DBService().getHatlar();
    if (mounted) {
      setState(() {
        _allHatlar = hatlar;
        _filteredHatlar = hatlar;
        _isLoading = false;
      });
    }
  }

  void _filterHatlar() {
    setState(() {
      _filteredHatlar = _allHatlar.where((h) {
        final katMatch = _selectedKat == 'dil' || (h['kat'] ?? 'otobus') == _selectedKat;
        final searchMatch = _searchQuery.isEmpty ||
            (h['code']?.toString() ?? '').toLowerCase().contains(_searchQuery) ||
            (h['name']?.toString() ?? '').toLowerCase().contains(_searchQuery);
        return katMatch && searchMatch;
      }).toList();
    });
  }

  Color _getKatColor(String kat) {
    return (KATEGORILER[kat]?['color'] as Color?) ?? const Color(0xFF1877F2);
  }

  String _getKatIcon(String kat) {
    return (KATEGORILER[kat]?['icon'] as String?) ?? '🚌';
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Column(
      children: [
        // Arama
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
          child: TextField(
            decoration: InputDecoration(
              hintText: "Hat ara...",
              prefixIcon: const Icon(Icons.search, size: 20),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 12),
              filled: true,
              fillColor: Colors.grey.shade100,
            ),
            onChanged: (v) {
              _searchQuery = v.toLowerCase();
              _filterHatlar();
            },
          ),
        ),

        // Kategori Chip'leri
        SizedBox(
          height: 50,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 8),
            children: KATEGORILER.entries.map((e) {
              final kat = e.key;
              final info = e.value;
              final count = kat == 'dil'
                  ? _allHatlar.length
                  : _allHatlar.where((h) => (h['kat'] ?? 'otobus') == kat).length;
              final isSelected = _selectedKat == kat;

              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 4),
                child: ChoiceChip(
                  label: Text("${info['icon']} ${info['name']} ($count)", style: TextStyle(fontSize: 11, color: isSelected ? Colors.white : Colors.black87)),
                  selected: isSelected,
                  selectedColor: info['color'] as Color,
                  backgroundColor: Colors.grey.shade200,
                  onSelected: (_) {
                    _selectedKat = _selectedKat == kat ? 'dil' : kat;
                    _filterHatlar();
                  },
                ),
              );
            }).toList(),
          ),
        ),

        // Hat Listesi
        Expanded(
          child: _filteredHatlar.isEmpty
              ? const Center(child: Text("Hat bulunamadı.", style: TextStyle(color: Colors.grey)))
              : ListView.builder(
                  itemCount: _filteredHatlar.length,
                  itemBuilder: (_, i) {
                    final h = _filteredHatlar[i];
                    final kat = h['kat']?.toString() ?? 'otobus';
                    final code = h['code']?.toString() ?? '';
                    final name = h['name']?.toString() ?? code;
                    final color = _getKatColor(kat);
                    final icon = _getKatIcon(kat);

                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      child: ListTile(
                        leading: Container(
                          width: 40, height: 40,
                          decoration: BoxDecoration(
                            color: color.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Center(child: Text(icon, style: const TextStyle(fontSize: 20))),
                        ),
                        title: Text(name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        subtitle: Text(code, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)),
                        trailing: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(8)),
                          child: Text(kat.toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold)),
                        ),
                        onTap: () => _openHatDetail(context, code, name, kat),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  void _openHatDetail(BuildContext context, String code, String name, String kat) {
    Navigator.push(context, MaterialPageRoute(builder: (_) => HatDetailScreen(code: code, name: name, kat: kat)));
  }
}

// ─── HAT DETAY EKRANI ───

class HatDetailScreen extends StatefulWidget {
  final String code, name, kat;
  const HatDetailScreen({Key? key, required this.code, required this.name, required this.kat}) : super(key: key);
  @override
  State<HatDetailScreen> createState() => _HatDetailScreenState();
}

class _HatDetailScreenState extends State<HatDetailScreen> {
  List<Map<String, dynamic>> _duraklar = [];
  List<Map<String, dynamic>> _liveVehicles = [];
  List<Map<String, dynamic>> _seferler = [];
  Map<String, dynamic>? _fiyat;
  bool _isLoading = true;
  Timer? _liveTimer;
  final MapController _mapController = MapController();

  Color get _katColor {
    return (_HatlarScreenState.KATEGORILER[widget.kat]?['color'] as Color?) ?? Colors.blue;
  }

  @override
  void initState() {
    super.initState();
    _loadData();
    _startLiveTracking();
  }

  @override
  void dispose() {
    _liveTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    // Parallel loading - 3x hızlı
    final results = await Future.wait([
      DBService().getDurakGuzergahi(widget.code),
      DBService().getFiyat(widget.code),
      DBService().getSeferler(widget.code),
    ]);
    if (mounted) {
      setState(() {
        _duraklar = results[0] as List<Map<String, dynamic>>;
        _fiyat = results[1] as Map<String, dynamic>?;
        _seferler = results[2] as List<Map<String, dynamic>>;
        _isLoading = false;
      });
    }
  }

  void _startLiveTracking() {
    _fetchVehicles();
    _liveTimer = Timer.periodic(const Duration(seconds: 15), (_) => _fetchVehicles());
  }

  Future<void> _fetchVehicles() async {
    String lineCode = widget.code.split(' ').first.split('/').first;
    final vehicles = await ApiService.getHattakiAraclar(lineCode);
    if (mounted) setState(() => _liveVehicles = vehicles);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.name, style: const TextStyle(fontSize: 14)),
        backgroundColor: _katColor,
        foregroundColor: Colors.white,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildSpecialBanner(),

                  if (_fiyat != null)
                    Container(
                      width: double.infinity,
                      margin: const EdgeInsets.all(12),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [_katColor, _katColor.withOpacity(0.7)]),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(children: [
                        const Text("Bilet Ücreti", style: TextStyle(color: Colors.white70, fontSize: 12)),
                        Text("₺${(_fiyat!['tam_fiyat'] ?? 17).toStringAsFixed(2)}", style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
                        Text("İndirimli: ₺${(_fiyat!['indirimli_fiyat'] ?? 12).toStringAsFixed(2)}", style: const TextStyle(color: Colors.white70, fontSize: 12)),
                      ]),
                    ),

                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Row(children: [
                      _infoCard("Durak", "${_duraklar.length}", Icons.location_on),
                      const SizedBox(width: 8),
                      _infoCard("Araç", "${_liveVehicles.length}", Icons.directions_bus),
                      const SizedBox(width: 8),
                      _infoCard("Sefer", "${_seferler.length}", Icons.schedule),
                    ]),
                  ),

                  // Harita
                  if (_duraklar.isNotEmpty)
                    Container(
                      height: 250,
                      margin: const EdgeInsets.all(12),
                      decoration: BoxDecoration(borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade300)),
                      clipBehavior: Clip.antiAlias,
                      child: FlutterMap(
                        mapController: _mapController,
                        options: MapOptions(
                          initialCenter: LatLng(
                            (_duraklar.first['lat'] as num?)?.toDouble() ?? 41.29,
                            (_duraklar.first['lon'] as num?)?.toDouble() ?? 36.33,
                          ),
                          initialZoom: 12.0,
                          onMapReady: () {
                            if (_duraklar.length > 1) {
                              final points = _duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null).map((d) =>
                                LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble())).toList();
                              if (points.length > 1) {
                                _mapController.fitCamera(CameraFit.bounds(bounds: LatLngBounds.fromPoints(points), padding: const EdgeInsets.all(30)));
                              }
                            }
                          },
                        ),
                        children: [
                          TileLayer(urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", userAgentPackageName: 'com.example.samsun_transit'),
                          PolylineLayer(polylines: [
                            Polyline(
                              points: _duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null).map((d) =>
                                LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble())).toList(),
                              strokeWidth: 4.0, color: _katColor,
                            ),
                          ]),
                          MarkerLayer(markers: [
                            ..._duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null).map((d) {
                              final sira = (d['sira'] as num?)?.toInt() ?? 0;
                              return Marker(
                                point: LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()),
                                width: 20, height: 20,
                                child: Container(
                                  decoration: BoxDecoration(color: _katColor, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 1.5)),
                                  child: Center(child: Text("$sira", style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold))),
                                ),
                              );
                            }),
                            ..._liveVehicles.map((v) => Marker(
                              point: LatLng(v['lat'] as double, v['lon'] as double),
                              width: 32, height: 32,
                              child: Container(
                                decoration: BoxDecoration(color: Colors.red.shade700, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 2)),
                                child: const Center(child: Icon(Icons.directions_bus, color: Colors.white, size: 16)),
                              ),
                            )),
                          ]),
                        ],
                      ),
                    ),

                  // Canlı Araçlar
                  if (_liveVehicles.isNotEmpty) ...[
                    const Padding(padding: EdgeInsets.symmetric(horizontal: 12), child: Text("🚌 Canlı Araçlar", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15))),
                    ...(_liveVehicles.map((v) => ListTile(
                      leading: CircleAvatar(backgroundColor: Colors.red.shade700, child: const Icon(Icons.directions_bus, color: Colors.white, size: 16)),
                      title: Text(v['plate']?.toString() ?? 'Bilinmiyor', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                      subtitle: Text("${v['speed']} km/s", style: const TextStyle(fontSize: 11)),
                    ))),
                  ],

                  // Sefer Saatleri
                  if (_seferler.isNotEmpty) ...[
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text("🕐 Sefer Saatleri (${_seferler.length})", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    ),
                    Container(
                      height: 120,
                      margin: const EdgeInsets.symmetric(horizontal: 12),
                      child: GridView.builder(
                        scrollDirection: Axis.horizontal,
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2, mainAxisSpacing: 6, crossAxisSpacing: 6, childAspectRatio: 0.5,
                        ),
                        itemCount: _seferler.length,
                        itemBuilder: (_, i) {
                          final s = _seferler[i];
                          return Container(
                            padding: const EdgeInsets.all(6),
                            decoration: BoxDecoration(color: _katColor.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                            child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                              Text(s['saat']?.toString() ?? '', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: _katColor)),
                              Text(s['yon']?.toString() ?? '', style: const TextStyle(fontSize: 9, color: Colors.grey)),
                            ]),
                          );
                        },
                      ),
                    ),
                  ],

                  // Durak Listesi
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text("📍 Duraklar (${_duraklar.length})", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  ),
                  ..._duraklar.asMap().entries.map((entry) {
                    final i = entry.key;
                    final d = entry.value;
                    return ListTile(
                      leading: CircleAvatar(backgroundColor: _katColor, radius: 14, child: Text("${i + 1}", style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold))),
                      title: Text(d['ad']?.toString() ?? '', style: const TextStyle(fontSize: 13)),
                      dense: true,
                    );
                  }),
                  const SizedBox(height: 20),
                ],
              ),
            ),
    );
  }

  Widget _infoCard(String label, String value, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(10)),
        child: Column(
          children: [
            Icon(icon, color: _katColor, size: 24),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: _katColor)),
            Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _buildSpecialBanner() {
    final name = widget.name.toUpperCase();

    if (name.contains('TRAMVAY')) {
      return _banner(Colors.orange.shade50, Colors.orange.shade800, '🚋', 'Tramvay Hattı', 'Sefer aralıkları için: 0362 431 10 12');
    }
    if (name.contains('TELEFERİK')) {
      return _banner(Colors.pink.shade50, Colors.pink.shade800, '🚠', 'Batıpark - Amisos Tepesi', 'Çalışma Saatleri: 10:30 - 22:00\n323 metre uzunluğunda hat');
    }
    if (name.contains('SAMSUNUM-1')) {
      return _banner(Colors.amber.shade50, Colors.amber.shade800, '⛴️', 'Samsunum-1 Gemisi', 'Sefer Süresi: 1 saat 15 dk\nÜcret: Tam 200₺ / Öğrenci 150₺');
    }
    if (name.contains('SAMSUNUM-2')) {
      return _banner(Colors.red.shade50, Colors.red.shade800, '🛑', 'Çalışmamaktadır', 'DSİ çalışmalarından dolayı su verilemediği için hat askıya alınmıştır.');
    }
    if (name.contains('SAMSUNUM-3')) {
      return _banner(Colors.blue.shade50, Colors.blue.shade800, 'ℹ️', 'Sefer Bilgisi', 'Sefer saatleri doluluğa göre belirlenir.\nÜcret: Tam 200₺ / Öğrenci 150₺');
    }
    if (name.contains('ALTINKAYA') || name.contains('FERİBOT')) {
      return _banner(Colors.grey.shade100, Colors.grey.shade800, '⛴️', 'Altınkaya 55 Feribot', 'Yolcu: Tam 15₺ / Öğr 7₺\nOtomobil: 75₺ | Kamyon: 290₺');
    }
    return const SizedBox.shrink();
  }

  Widget _banner(Color bg, Color textColor, String icon, String title, String body) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.all(12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text("$icon $title", style: TextStyle(fontWeight: FontWeight.bold, color: textColor, fontSize: 14)),
        const SizedBox(height: 6),
        Text(body, style: TextStyle(color: textColor.withOpacity(0.8), fontSize: 12)),
      ]),
    );
  }
}
