import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/db_service.dart';
import '../services/api_service.dart';
import '../services/price_service.dart';

class HatlarScreen extends StatefulWidget {
  final void Function(String lineCode)? onLineSelected;
  const HatlarScreen({Key? key, this.onLineSelected}) : super(key: key);
  @override
  State<HatlarScreen> createState() => _HatlarScreenState();
}

class _HatlarScreenState extends State<HatlarScreen> {
  List<Map<String, dynamic>> _allHatlar = [];
  List<Map<String, dynamic>> _filteredHatlar = [];
  String _selectedKat = 'dil';
  String _searchQuery = '';
  bool _isLoading = true;

  static const Map<String, Map<String, dynamic>> KATEGORILER = {
    'dil': {'icon': '🌐', 'name': 'Tümü', 'color': Color(0xFF546E8A)},
    'otobus': {'icon': '🚌', 'name': 'Otobüs', 'color': Color(0xFF2979FF)},
    'ekspres': {'icon': '🚀', 'name': 'Ekspres', 'color': Color(0xFF7C4DFF)},
    'tramvay': {'icon': '🚋', 'name': 'Tramvay', 'color': Color(0xFFFF9100)},
    'ring': {'icon': '🔄', 'name': 'Ring', 'color': Color(0xFFFFC400)},
    'tekne': {'icon': '🛥️', 'name': 'Tekne', 'color': Color(0xFF00B0FF)},
    'odak': {'icon': '🏕️', 'name': 'Odak', 'color': Color(0xFF4CAF50)},
    'teleferik': {'icon': '🚠', 'name': 'Teleferik', 'color': Color(0xFFFF4081)},
    'havalimani': {'icon': '✈️', 'name': 'H.limanı', 'color': Color(0xFFFF5252)},
    'ilce': {'icon': '🏘️', 'name': 'İlçe', 'color': Color(0xFF00BFA5)},
  };

  @override
  void initState() {
    super.initState();
    _loadHatlar();
  }

  Future<void> _loadHatlar() async {
    final hatlar = await DBService().getHatlar();
    if (mounted) setState(() { _allHatlar = hatlar; _filteredHatlar = hatlar; _isLoading = false; });
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

  Color _getKatColor(String kat) => (KATEGORILER[kat]?['color'] as Color?) ?? const Color(0xFF2979FF);
  String _getKatIcon(String kat) => (KATEGORILER[kat]?['icon'] as String?) ?? '🚌';

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator(color: Color(0xFF2979FF)));

    return Column(children: [
      // Arama
      Padding(
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
        child: TextField(
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: "Hat ara...",
            prefixIcon: Icon(Icons.search, size: 20, color: Colors.white.withOpacity(0.4)),
            filled: true, fillColor: const Color(0xFF152238),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
          ),
          onChanged: (v) { _searchQuery = v.toLowerCase(); _filterHatlar(); },
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
            final count = kat == 'dil' ? _allHatlar.length : _allHatlar.where((h) => (h['kat'] ?? 'otobus') == kat).length;
            final isSelected = _selectedKat == kat;
            final c = info['color'] as Color;

            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 4),
              child: GestureDetector(
                onTap: () { _selectedKat = _selectedKat == kat ? 'dil' : kat; _filterHatlar(); },
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    gradient: isSelected ? LinearGradient(colors: [c, c.withOpacity(0.7)]) : null,
                    color: isSelected ? null : const Color(0xFF152238),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: isSelected ? c : Colors.white.withOpacity(0.08)),
                  ),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    Text("${info['icon']} ", style: const TextStyle(fontSize: 12)),
                    Text("${info['name']} ($count)", style: TextStyle(fontSize: 11, fontWeight: isSelected ? FontWeight.bold : FontWeight.normal, color: isSelected ? Colors.white : Colors.white.withOpacity(0.6))),
                  ]),
                ),
              ),
            );
          }).toList(),
        ),
      ),

      // Sonuç sayısı
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text("${_filteredHatlar.length} hat", style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.35))),
          if (_selectedKat != 'dil')
            GestureDetector(
              onTap: () { _selectedKat = 'dil'; _filterHatlar(); },
              child: Text("Filtreyi Temizle ✕", style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.35))),
            ),
        ]),
      ),

      // Hat Listesi
      Expanded(
        child: _filteredHatlar.isEmpty
            ? Center(child: Text("Hat bulunamadı.", style: TextStyle(color: Colors.white.withOpacity(0.3))))
            : ListView.builder(
                itemCount: _filteredHatlar.length,
                itemBuilder: (_, i) {
                  final h = _filteredHatlar[i];
                  final kat = h['kat']?.toString() ?? 'otobus';
                  final code = h['code']?.toString() ?? '';
                  final name = h['name']?.toString() ?? code;
                  final color = _getKatColor(kat);
                  final icon = _getKatIcon(kat);

                  Widget leadingIcon;
                  if (kat == 'havalimani') {
                    leadingIcon = Image.asset('assets/samair.png', width: 28, height: 28, fit: BoxFit.contain);
                  } else if (kat == 'tekne') {
                    leadingIcon = Text(icon, style: const TextStyle(fontSize: 20)); // Tekne için samulas logosu tam uymayabilir, emoji kalabilir veya logo.png eklenebilir.
                  } else if (kat == 'otobus' || kat == 'ring' || kat == 'ekspres' || kat == 'tramvay') {
                    // Ana Samulas taşıtları için logo
                    leadingIcon = Image.asset('assets/SBB Logo 9.png', width: 28, height: 28, fit: BoxFit.contain, color: Colors.white, colorBlendMode: BlendMode.srcIn); // Beyazlatılmış Icon tarzı kullanım için
                  } else {
                    leadingIcon = Text(icon, style: const TextStyle(fontSize: 20));
                  }

                  return Container(
                    margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xFF152238),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: color.withOpacity(0.1)),
                    ),
                    child: ListTile(
                      leading: Container(
                        width: 42, height: 42,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(colors: [color, color.withOpacity(0.6)]),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Center(child: leadingIcon),
                      ),
                      title: Text(name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: Colors.white)),
                      subtitle: Text(code, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: color.withOpacity(0.15), borderRadius: BorderRadius.circular(8)),
                        child: Text(kat.toUpperCase(), style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.bold)),
                      ),
                      onTap: () {
                        // Tam hat kodunu gönder — samsun.py /api/hat/arac akıllı eşleştirme yapar
                        widget.onLineSelected?.call(code);
                        Navigator.push(context, MaterialPageRoute(builder: (_) => HatDetailScreen(code: code, name: name, kat: kat)));
                      },
                    ),
                  );
                },
              ),
      ),
    ]);
  }
}

// ─── HAT DETAY ───

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

  Color get _katColor => (_HatlarScreenState.KATEGORILER[widget.kat]?['color'] as Color?) ?? const Color(0xFF2979FF);

  @override
  void initState() { super.initState(); _loadData(); _startLiveTracking(); }

  @override
  void dispose() { _liveTimer?.cancel(); super.dispose(); }

  Future<void> _loadData() async {
    final results = await Future.wait([
      DBService().getDurakGuzergahi(widget.code),
      DBService().getFiyat(widget.code),
      DBService().getSeferler(widget.code),
      PriceService.getPriceForLine(widget.name, widget.kat), // Dinamik Fiyat Çekimi
    ]);
    if (mounted) {
      setState(() {
        _duraklar = results[0] as List<Map<String, dynamic>>;
        _seferler = results[2] as List<Map<String, dynamic>>;
        
        // Fiyat Birleştirme: YBS API (Dinamik) + Yerel Veritabanı (Fallback)
        final dbPrice = results[1] as Map<String, dynamic>?;
        final dynPrice = results[3] as Map<String, double>;
        
        _fiyat = {};
        if (dbPrice != null) _fiyat!.addAll(dbPrice);
        
        // Github JSON dinamik fiyatlarını önceliklendir (statik ezme)
        _fiyat!['tam_fiyat'] = dynPrice['tam'];
        _fiyat!['indirimli_fiyat'] = dynPrice['indirimli'];

        _isLoading = false;
      });
    }
  }

  void _startLiveTracking() {
    _fetchVehicles();
    _liveTimer = Timer.periodic(const Duration(seconds: 15), (_) => _fetchVehicles());
  }

  Future<void> _fetchVehicles() async {
    // Tam hat kodunu gönder — samsun.py /api/hat/arac akıllı eşleştirme yapar
    try {
      final vehicles = await ApiService.getHattakiAraclar(widget.code);
      if (mounted) setState(() => _liveVehicles = vehicles);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.name, style: const TextStyle(fontSize: 14)),
        backgroundColor: _katColor.withOpacity(0.8),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2979FF)))
          : SingleChildScrollView(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _buildSpecialBanner(),

              // Fiyat
              if (_fiyat != null) Container(
                width: double.infinity, margin: const EdgeInsets.all(12), padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [_katColor, _katColor.withOpacity(0.5)]),
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [BoxShadow(color: _katColor.withOpacity(0.2), blurRadius: 16, spreadRadius: 2)],
                ),
                child: Column(children: [
                  Text("Bilet Ücreti", style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 12)),
                  Text("₺${(_fiyat!['tam_fiyat'] ?? '--')}", style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
                  Text("İndirimli: ₺${(_fiyat!['indirimli_fiyat'] ?? '--')}", style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12)),
                ]),
              ),

              // Info Kartları
              Padding(padding: const EdgeInsets.symmetric(horizontal: 12), child: Row(children: [
                _infoCard("Durak", "${_duraklar.length}", Icons.location_on),
                const SizedBox(width: 8),
                _infoCard("Araç", "${_liveVehicles.length}", Icons.directions_bus),
                const SizedBox(width: 8),
                _infoCard("Sefer", "${_seferler.length}", Icons.schedule),
              ])),

              // Harita
              if (_duraklar.isNotEmpty) Container(
                height: 250, margin: const EdgeInsets.all(12),
                decoration: BoxDecoration(borderRadius: BorderRadius.circular(14), border: Border.all(color: Colors.white.withOpacity(0.08))),
                clipBehavior: Clip.antiAlias,
                child: FlutterMap(
                  mapController: _mapController,
                  options: MapOptions(
                    initialCenter: LatLng((_duraklar.first['lat'] as num?)?.toDouble() ?? 41.29, (_duraklar.first['lon'] as num?)?.toDouble() ?? 36.33),
                    initialZoom: 12.0,
                    onMapReady: () {
                      if (_duraklar.length > 1) {
                        final points = _duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null).map((d) => LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble())).toList();
                        if (points.length > 1) _mapController.fitCamera(CameraFit.bounds(bounds: LatLngBounds.fromPoints(points), padding: const EdgeInsets.all(30)));
                      }
                    },
                  ),
                  children: [
                    TileLayer(
                      urlTemplate: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
                      subdomains: const ['a', 'b', 'c', 'd'],
                      userAgentPackageName: 'com.samsun.transit',
                    ),
                    PolylineLayer(polylines: [Polyline(
                      points: _duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null).map((d) => LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble())).toList(),
                      strokeWidth: 4.0, color: _katColor,
                    )]),
                    MarkerLayer(markers: [
                      ..._duraklar.where((d) => (d['lat'] as num?)?.toDouble() != null).map((d) {
                        final sira = (d['sira'] as num?)?.toInt() ?? 0;
                        return Marker(point: LatLng((d['lat'] as num).toDouble(), (d['lon'] as num).toDouble()), width: 20, height: 20,
                          child: Container(
                            decoration: BoxDecoration(color: _katColor, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 1.5)),
                            child: Center(child: Text("$sira", style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold))),
                          ));
                      }),
                      ..._liveVehicles.map((v) => Marker(
                        point: LatLng(v['lat'] as double, v['lon'] as double), width: 48, height: 48,
                        child: GestureDetector(
                          onTap: () => _showVehicleDetail(context, v),
                          child: Container(
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(colors: [Color(0xFFFF5252), Color(0xFFD50000)]),
                              shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 2),
                              boxShadow: [BoxShadow(blurRadius: 8, color: const Color(0xFFFF5252).withOpacity(0.5))],
                            ),
                            child: Center(child: Text(
                              (v['plate']?.toString() ?? '').length > 3 ? (v['plate'].toString()).substring(v['plate'].toString().length - 3) : '🚌',
                              style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold),
                            )),
                          ),
                        ),
                      )),
                    ]),
                  ],
                ),
              ),

              // Canlı Araçlar
              if (_liveVehicles.isNotEmpty) ...[
                Padding(padding: const EdgeInsets.symmetric(horizontal: 12), child: Text("🚌 Canlı Araçlar", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white.withOpacity(0.9)))),
                ...(_liveVehicles.map((v) {
                  final gunlukYolcu = v['gunlukYolcu'] ?? '0';
                  final seferYolcu = v['seferYolcu'] ?? '0';
                  final hasilat = v['toplamHasilat'] ?? '0';
                  final maxHiz = v['maxHiz'] ?? '0';
                  return Container(
                    margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: const Color(0xFF1A2940), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFFF5252).withOpacity(0.15))),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      // Plaka + Hız
                      Row(children: [
                        Container(width: 36, height: 36, decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFFFF5252), Color(0xFFD50000)]), borderRadius: BorderRadius.circular(8)),
                          child: const Center(child: Icon(Icons.directions_bus, color: Colors.white, size: 16))),
                        const SizedBox(width: 10),
                        Expanded(child: Text(v['plate']?.toString() ?? 'Bilinmiyor', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white))),
                        Text("${v['speed']} km/s", style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.6), fontWeight: FontWeight.w600)),
                      ]),
                      const SizedBox(height: 8),
                      // İstatistikler
                      Row(children: [
                        _vehicleStat(Icons.people, "$seferYolcu", "Sefer"),
                        _vehicleStat(Icons.groups, "$gunlukYolcu", "Günlük"),
                        _vehicleStat(Icons.payments, "₺$hasilat", "Hasılat"),
                        _vehicleStat(Icons.speed, "$maxHiz", "Max km/s"),
                      ]),
                    ]),
                  );
                })),
              ],

              // Sefer Saatleri
              if (_seferler.isNotEmpty) ...[
                Padding(padding: const EdgeInsets.all(12), child: Text("🕐 Sefer Saatleri (${_seferler.length})", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white.withOpacity(0.9)))),
                Container(
                  height: 120, margin: const EdgeInsets.symmetric(horizontal: 12),
                  child: GridView.builder(
                    scrollDirection: Axis.horizontal,
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, mainAxisSpacing: 6, crossAxisSpacing: 6, childAspectRatio: 0.5),
                    itemCount: _seferler.length,
                    itemBuilder: (_, i) {
                      final s = _seferler[i];
                      return Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(color: _katColor.withOpacity(0.15), borderRadius: BorderRadius.circular(8), border: Border.all(color: _katColor.withOpacity(0.2))),
                        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                          Text(s['saat']?.toString() ?? '', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: _katColor)),
                          Text(s['yon']?.toString() ?? '', style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.4))),
                        ]),
                      );
                    },
                  ),
                ),
              ],

              // Durak Listesi
              Padding(padding: const EdgeInsets.all(12), child: Text("📍 Duraklar (${_duraklar.length})", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white.withOpacity(0.9)))),
              ..._duraklar.asMap().entries.map((entry) {
                final i = entry.key;
                final d = entry.value;
                
                // Bu durakta olan/yaklaşan araçları bul (yaklaşık 150 metre çapında eşleştirme)
                final dLat = (d['lat'] as num?)?.toDouble();
                final dLon = (d['lon'] as num?)?.toDouble();
                List<Map<String, dynamic>> onThisStop = [];
                
                if (dLat != null && dLon != null && _liveVehicles.isNotEmpty) {
                  for (var v in _liveVehicles) {
                    final vLat = v['lat'] as double;
                    final vLon = v['lon'] as double;
                    const Distance distance = Distance();
                    final meter = distance(LatLng(dLat, dLon), LatLng(vLat, vLon));
                    if (meter < 250) { // 250 mt hata payı
                      onThisStop.add(v);
                    }
                  }
                }

                return Container(
                  margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 1),
                  child: ListTile(
                    leading: Container(width: 28, height: 28, decoration: BoxDecoration(gradient: LinearGradient(colors: [_katColor, _katColor.withOpacity(0.6)]), borderRadius: BorderRadius.circular(8)),
                      child: Center(child: Text("${i + 1}", style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)))),
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
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.directions_bus, color: Colors.white, size: 10),
                                  const SizedBox(width: 3),
                                  Text(v['plate'].toString().replaceAll(RegExp(r'\s+'), ''), style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold)),
                                ],
                              ),
                            )).toList(),
                          )
                      ],
                    ),
                    dense: true,
                  ),
                );
              }),
              const SizedBox(height: 20),
            ])),
    );
  }

  Widget _infoCard(String label, String value, IconData icon) {
    return Expanded(child: Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: const Color(0xFF152238), borderRadius: BorderRadius.circular(12)),
      child: Column(children: [
        Icon(icon, color: _katColor, size: 22),
        const SizedBox(height: 4),
        Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: _katColor)),
        Text(label, style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.4))),
      ]),
    ));
  }

  Widget _vehicleStat(IconData icon, String value, String label) {
    return Expanded(child: Column(children: [
      Row(mainAxisAlignment: MainAxisAlignment.center, mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: Colors.white.withOpacity(0.4)),
        const SizedBox(width: 3),
        Text(value, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.white.withOpacity(0.7))),
      ]),
      Text(label, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3))),
    ]));
  }

  Widget _buildSpecialBanner() {
    final name = widget.name.toUpperCase();
    if (name.contains('TRAMVAY')) return _banner(const Color(0xFF2A1800), const Color(0xFFFF9100), '🚋', 'Tramvay Hattı', '0362 431 10 12');
    if (name.contains('TELEFERİK')) return _banner(const Color(0xFF2A0020), const Color(0xFFFF4081), '🚠', 'Batıpark - Amisos Tepesi', '10:30 - 22:00 | 323m hat');
    if (name.contains('ECZANELER') && name.contains('TEKKEKÖY') && name.contains('GİDİŞ')) return _banner(const Color(0xFF2A1800), const Color(0xFFFF9100), '🚋', 'ECZANELER-TEKKEKÖY Gidiş', 'Tramvay hattı • Sefer saatleri eklenecek');
    if (name.contains('YURTLAR') && name.contains('BELEDİYE')) return _banner(const Color(0xFF2A1800), const Color(0xFFFF9100), '🚋', 'YURTLAR-BELEDİYE EVLERİ', 'Tramvay hattı • Sefer saatleri eklenecek');
    if (name.contains('BELEDİYE') && name.contains('YURTLAR') && name.contains('DÖNÜŞ')) return _banner(const Color(0xFF2A1800), const Color(0xFFFF9100), '🚋', 'BELEDİYE EVLERİ-YURTLAR Dönüş', 'Tramvay hattı • Sefer saatleri eklenecek');
    if (name.contains('TEKKEKÖY') && name.contains('ECZANELER') && name.contains('DÖNÜŞ')) return _banner(const Color(0xFF2A1800), const Color(0xFFFF9100), '🚋', 'TEKKEKÖY-ECZANELER Dönüş', 'Tramvay hattı • Sefer saatleri eklenecek');
    if (name.contains('SAMSUNUM-1')) return _banner(const Color(0xFF1A2200), const Color(0xFFFFC400), '⛴️', 'Samsunum-1', 'Odak turları bölümünden bilgi alınız');
    if (name.contains('SAMSUNUM-2')) return _banner(const Color(0xFF2A0000), const Color(0xFFFF5252), '🛑', 'Çalışmıyor', 'DSİ çalışması nedeniyle askıda');
    if (name.contains('SAMSUNUM-3')) return _banner(const Color(0xFF001A2A), const Color(0xFF00B0FF), 'ℹ️', 'Samsunum-3', 'Odak turları bölümünden bilgi alınız');
    if (name.contains('ALTINKAYA') || name.contains('FERİBOT')) return _banner(const Color(0xFF1A1A1A), const Color(0xFF546E8A), '⛴️', 'Altınkaya 55', 'Fiyat ve sefer saatleri için arayınız');
    return const SizedBox.shrink();
  }

  Widget _banner(Color bg, Color accent, String icon, String title, String body) {
    return Container(
      width: double.infinity, margin: const EdgeInsets.all(12), padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12), border: Border.all(color: accent.withOpacity(0.3))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text("$icon $title", style: TextStyle(fontWeight: FontWeight.bold, color: accent, fontSize: 14)),
        const SizedBox(height: 4),
        Text(body, style: TextStyle(color: accent.withOpacity(0.7), fontSize: 12)),
      ]),
    );
  }

  // Premium araç detay bottom sheet — KVKK uyumlu (şoför bilgisi hariç)
  void _showVehicleDetail(BuildContext context, Map<String, dynamic> v) {
    final plate = v['plate']?.toString() ?? 'Bilinmiyor';
    final speed = v['speed']?.toString() ?? '0';
    final gunlukYolcu = v['gunlukYolcu']?.toString() ?? '0';
    final seferYolcu = v['seferYolcu']?.toString() ?? '0';
    final hasilat = v['toplamHasilat']?.toString() ?? '0';
    final maxHiz = v['maxHiz']?.toString() ?? '0';
    final mesafe = v['mesafe']?.toString() ?? '0';
    final yon = v['yon']?.toString() ?? '0';
    final lastUpdate = v['lastUpdate']?.toString() ?? '';
    // Son güncelleme zamanını kısa formatla
    String updateStr = '';
    if (lastUpdate.isNotEmpty) {
      try {
        final dt = DateTime.parse(lastUpdate);
        updateStr = '${dt.hour.toString().padLeft(2,'0')}:${dt.minute.toString().padLeft(2,'0')}:${dt.second.toString().padLeft(2,'0')}';
      } catch (_) { updateStr = lastUpdate; }
    }

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (_) => Container(
        decoration: const BoxDecoration(
          color: Color(0xFF152238),
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          // Handle bar
          Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 16),
          // Plaka + Hız
          Row(children: [
            Container(width: 48, height: 48,
              decoration: BoxDecoration(gradient: LinearGradient(colors: [_katColor, _katColor.withOpacity(0.6)]), borderRadius: BorderRadius.circular(12)),
              child: const Center(child: Icon(Icons.directions_bus, color: Colors.white, size: 24))),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(plate, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
              Text(widget.name, style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5))),
            ])),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(color: _katColor.withOpacity(0.2), borderRadius: BorderRadius.circular(12)),
              child: Text('$speed km/s', style: TextStyle(fontWeight: FontWeight.bold, color: _katColor, fontSize: 16)),
            ),
          ]),
          const Divider(color: Colors.white12, height: 28),
          // İstatistik grid
          Row(children: [
            _detailStat(Icons.people, seferYolcu, 'Sefer Yolcu'),
            _detailStat(Icons.groups, gunlukYolcu, 'Günlük Yolcu'),
            _detailStat(Icons.payments, '₺$hasilat', 'Hasılat'),
          ]),
          const SizedBox(height: 12),
          Row(children: [
            _detailStat(Icons.speed, '$maxHiz km/s', 'Max Hız'),
            _detailStat(Icons.straighten, '${(int.tryParse(mesafe) ?? 0) ~/ 1000} km', 'Mesafe'),
            _detailStat(Icons.navigation, '$yon°', 'Yön'),
          ]),
          if (updateStr.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('Son güncelleme: $updateStr', style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.3))),
          ]
        ]),
      ),
    );
  }

  Widget _detailStat(IconData icon, String value, String label) {
    return Expanded(child: Container(
      padding: const EdgeInsets.all(10),
      margin: const EdgeInsets.symmetric(horizontal: 3),
      decoration: BoxDecoration(color: const Color(0xFF1A2940), borderRadius: BorderRadius.circular(10)),
      child: Column(children: [
        Icon(icon, size: 18, color: _katColor.withOpacity(0.7)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white)),
        Text(label, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.4))),
      ]),
    ));
  }
}
