import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/ybs_api_service.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({Key? key}) : super(key: key);
  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  final _keyController = TextEditingController();
  final _ybs = YbsApiService();
  
  bool _authenticated = false;
  bool _loading = false;
  
  // Config
  bool _gtfsRtEnabled = true;
  String _gtfsRtMode = 'ondemand';
  int _gtfsRtInterval = 60;
  int _gtfsRtMaxLines = 10;
  int _samairInterval = 7200;
  
  // Stats
  Map<String, dynamic>? _stats;
  Timer? _statsTimer;

  @override
  void initState() {
    super.initState();
    _loadSavedKey();
  }

  @override
  void dispose() {
    _statsTimer?.cancel();
    _keyController.dispose();
    super.dispose();
  }

  Future<void> _loadSavedKey() async {
    final prefs = await SharedPreferences.getInstance();
    final savedKey = prefs.getString('admin_key') ?? '';
    if (savedKey.isNotEmpty) {
      _keyController.text = savedKey;
      _ybs.setAdminKey(savedKey);
      await _login();
    }
  }

  Future<void> _login() async {
    final key = _keyController.text.trim();
    if (key.isEmpty) return;
    
    setState(() => _loading = true);
    _ybs.setAdminKey(key);
    
    final config = await _ybs.getAdminConfig();
    if (config != null && !config.containsKey('error')) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('admin_key', key);
      
      setState(() {
        _authenticated = true;
        _gtfsRtEnabled = config['gtfs_rt_enabled'] ?? true;
        _gtfsRtMode = config['gtfs_rt_mode'] ?? 'ondemand';
        _gtfsRtInterval = config['gtfs_rt_interval'] ?? 60;
        _gtfsRtMaxLines = config['gtfs_rt_max_lines'] ?? 10;
        _samairInterval = config['samair_interval'] ?? 7200;
        _loading = false;
      });
      _loadStats();
      _statsTimer = Timer.periodic(const Duration(seconds: 10), (_) => _loadStats());
    } else {
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('❌ Admin key yanlış veya sunucu yanıt vermedi'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _loadStats() async {
    final stats = await _ybs.getAdminStats();
    if (stats != null && mounted) {
      setState(() => _stats = stats);
    }
  }

  Future<void> _saveConfig() async {
    setState(() => _loading = true);
    final ok = await _ybs.updateAdminConfig(
      gtfsRtEnabled: _gtfsRtEnabled,
      gtfsRtInterval: _gtfsRtInterval,
      gtfsRtMode: _gtfsRtMode,
      gtfsRtMaxLines: _gtfsRtMaxLines,
      samairInterval: _samairInterval,
    );
    setState(() => _loading = false);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(ok ? '✅ Ayarlar kaydedildi' : '❌ Kaydetme başarısız'),
          backgroundColor: ok ? Colors.green : Colors.red,
        ),
      );
    }
  }

  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('admin_key');
    _statsTimer?.cancel();
    setState(() {
      _authenticated = false;
      _stats = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🔐 Admin Panel'),
        actions: _authenticated ? [
          IconButton(icon: const Icon(Icons.logout), onPressed: _logout, tooltip: 'Çıkış'),
        ] : null,
      ),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _authenticated ? _buildPanel() : _buildLogin(),
    );
  }

  Widget _buildLogin() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF2979FF), Color(0xFF00BFA5)]),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(Icons.admin_panel_settings, size: 48, color: Colors.white),
          ),
          const SizedBox(height: 24),
          const Text('Admin Girişi', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 8),
          Text('Sunucu yönetim paneli', style: TextStyle(color: Colors.white.withOpacity(0.5))),
          const SizedBox(height: 32),
          TextField(
            controller: _keyController,
            obscureText: true,
            decoration: const InputDecoration(
              labelText: 'Admin Key',
              prefixIcon: Icon(Icons.key),
              hintText: 'Render\'da tanımlı ADMIN_KEY',
            ),
            onSubmitted: (_) => _login(),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _login,
              icon: const Icon(Icons.login),
              label: const Text('Giriş Yap'),
            ),
          ),
        ]),
      ),
    );
  }

  Widget _buildPanel() {
    return ListView(padding: const EdgeInsets.all(16), children: [
      // Stats Card
      if (_stats != null) _buildStatsCard(),
      const SizedBox(height: 12),
      
      // GTFS-RT Settings
      _buildCard('📡 GTFS-RT Ayarları', [
        SwitchListTile(
          title: const Text('GTFS-RT Aktif'),
          subtitle: Text(_gtfsRtEnabled ? 'Çalışıyor' : 'Kapalı'),
          value: _gtfsRtEnabled,
          activeThumbColor: const Color(0xFF00BFA5),
          onChanged: (v) => setState(() => _gtfsRtEnabled = v),
        ),
        ListTile(
          title: const Text('Mod'),
          subtitle: Text(_gtfsRtMode == 'ondemand' ? 'On-Demand (Akıllı)' : 'Tüm Hatlar'),
          trailing: DropdownButton<String>(
            value: _gtfsRtMode,
            dropdownColor: const Color(0xFF1A2940),
            items: const [
              DropdownMenuItem(value: 'ondemand', child: Text('On-Demand')),
              DropdownMenuItem(value: 'all', child: Text('Tümü')),
            ],
            onChanged: (v) => setState(() => _gtfsRtMode = v!),
          ),
        ),
        ListTile(
          title: const Text('Güncelleme Aralığı'),
          subtitle: Text('$_gtfsRtInterval saniye'),
          trailing: SizedBox(width: 120, child: Slider(
            value: _gtfsRtInterval.toDouble(),
            min: 10, max: 300, divisions: 29,
            label: '${_gtfsRtInterval}s',
            onChanged: (v) => setState(() => _gtfsRtInterval = v.round()),
          )),
        ),
        ListTile(
          title: const Text('Max Hat (All modunda)'),
          subtitle: Text('$_gtfsRtMaxLines hat'),
          trailing: SizedBox(width: 120, child: Slider(
            value: _gtfsRtMaxLines.toDouble(),
            min: 1, max: 50, divisions: 49,
            label: '$_gtfsRtMaxLines',
            onChanged: (v) => setState(() => _gtfsRtMaxLines = v.round()),
          )),
        ),
      ]),
      const SizedBox(height: 12),

      // SamAir Settings
      _buildCard('✈️ SamAir Ayarları', [
        ListTile(
          title: const Text('Güncelleme Aralığı'),
          subtitle: Text('${_samairInterval ~/ 3600} saat'),
          trailing: SizedBox(width: 120, child: Slider(
            value: (_samairInterval / 3600).clamp(1, 24).toDouble(),
            min: 1, max: 24, divisions: 23,
            label: '${_samairInterval ~/ 3600}h',
            onChanged: (v) => setState(() => _samairInterval = (v * 3600).round()),
          )),
        ),
      ]),
      const SizedBox(height: 16),

      // Save Button
      SizedBox(
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: _loading ? null : _saveConfig,
          icon: const Icon(Icons.save),
          label: const Text('💾 Kaydet'),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
            backgroundColor: const Color(0xFF00BFA5),
          ),
        ),
      ),
    ]);
  }

  Widget _buildStatsCard() {
    final s = _stats!;
    final uptime = (s['uptime_seconds'] as num?)?.toInt() ?? 0;
    final vehicles = s['gtfs_rt_vehicles'] ?? 0;
    final activeCount = s['active_line_count'] ?? 0;
    final proxyActive = s['proxy_active'] ?? false;
    final trHour = s['tr_hour'] ?? 0;
    final apiStats = s['api_stats'] ?? {};
    final asisPerMin = apiStats['asis_per_minute'] ?? 0;
    final activeLines = (s['active_lines'] ?? {}) as Map<String, dynamic>;

    return _buildCard('📊 Canlı Durum', [
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Wrap(spacing: 8, runSpacing: 8, children: [
          _chip('⏱', '${uptime ~/ 60}dk'),
          _chip('🚌', '$vehicles araç'),
          _chip('📡', '$activeCount hat'),
          _chip('📊', '$asisPerMin/dk ASIS'),
          _chip('🌐', proxyActive ? '✅ Proxy' : '❌ Proxy'),
          _chip('🕐', '$trHour:xx TR'),
        ]),
      ),
      if (activeLines.isNotEmpty)
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
          child: Wrap(spacing: 6, runSpacing: 6,
            children: activeLines.entries.map((e) => Chip(
              label: Text('${e.key} (${e.value}sn)', style: const TextStyle(fontSize: 11)),
              backgroundColor: const Color(0xFF2979FF).withOpacity(0.2),
              side: BorderSide.none,
              visualDensity: VisualDensity.compact,
            )).toList(),
          ),
        )
      else
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 4, 16, 12),
          child: Text('💤 Kimse araç takip etmiyor', style: TextStyle(color: Colors.white38, fontSize: 12)),
        ),
    ]);
  }

  Widget _chip(String emoji, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1117),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text('$emoji $label', style: const TextStyle(fontSize: 12, color: Colors.white70)),
    );
  }

  Widget _buildCard(String title, List<Widget> children) {
    return Card(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
          child: Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF64FFDA))),
        ),
        ...children,
      ]),
    );
  }
}
