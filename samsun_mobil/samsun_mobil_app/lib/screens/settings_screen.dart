import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notificationsEnabled = true;
  bool _showNearbyOnly = false;
  String _selectedLanguage = 'Türkçe';
  String _defaultTransport = 'Otobüs';
  List<String> _favoriHatlar = [];
  List<String> _favoriDuraklar = [];

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _notificationsEnabled = prefs.getBool('notifications_enabled') ?? true;
      _showNearbyOnly = prefs.getBool('show_nearby_only') ?? false;
      _selectedLanguage = prefs.getString('language') ?? 'Türkçe';
      _defaultTransport = prefs.getString('default_transport') ?? 'Otobüs';
      _favoriHatlar = prefs.getStringList('favori_hatlar') ?? [];
      _favoriDuraklar = prefs.getStringList('favori_duraklar') ?? [];
    });
  }

  Future<void> _savePreference(String key, dynamic value) async {
    final prefs = await SharedPreferences.getInstance();
    if (value is bool) {
      await prefs.setBool(key, value);
    } else if (value is String) {
      await prefs.setString(key, value);
    } else if (value is List<String>) {
      await prefs.setStringList(key, value);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A1628),
      appBar: AppBar(
        title: const Text('⚙️ Ayarlar', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        backgroundColor: const Color(0xFF0F1E36),
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Uygulama Ayarları
          _sectionHeader('Uygulama Ayarları'),
          _card([
            _switchItem(Icons.notifications, Colors.blue, 'Bildirimler', _notificationsEnabled, (v) {
              setState(() => _notificationsEnabled = v);
              _savePreference('notifications_enabled', v);
            }),
            _divider(),
            _switchItem(Icons.near_me, Colors.green, 'Sadece Yakın Durakları Göster', _showNearbyOnly, (v) {
              setState(() => _showNearbyOnly = v);
              _savePreference('show_nearby_only', v);
            }),
            _divider(),
            _infoItem(Icons.dark_mode, Colors.purple, 'Tema', 'Karanlık Mod'),
            _divider(),
            _chevronItem(Icons.language, Colors.orange, 'Dil Seçimi', subtitle: _selectedLanguage, onTap: () => _showLanguageDialog(context)),
          ]),
          const SizedBox(height: 20),

          // Ulaşım Tercihleri
          _sectionHeader('Ulaşım Tercihleri'),
          _card([
            _chevronItem(Icons.directions_bus, const Color(0xFF00BFA5), 'Favori Hatlar',
              subtitle: _favoriHatlar.isEmpty ? 'Henüz yok' : '${_favoriHatlar.length} hat',
              onTap: () => _showFavoriHatlarDialog(context)),
            _divider(),
            _chevronItem(Icons.location_on, const Color(0xFF00BFA5), 'Favori Duraklar',
              subtitle: _favoriDuraklar.isEmpty ? 'Henüz yok' : '${_favoriDuraklar.length} durak',
              onTap: () => _showFavoriDuraklarDialog(context)),
            _divider(),
            _chevronItem(Icons.commute, const Color(0xFF00BFA5), 'Varsayılan Ulaşım Türü', subtitle: _defaultTransport, onTap: () => _showTransportDialog(context)),
          ]),
          const SizedBox(height: 20),

          // Veri Yönetimi
          _sectionHeader('Veri Yönetimi'),
          _card([
            _chevronItem(Icons.system_update, Colors.blue, 'Güncelleme Kontrolü', onTap: _checkForUpdate),
            _divider(),
            _chevronItem(Icons.refresh, Colors.teal, 'Verileri Yenile', onTap: () => _showDataRefreshDialog(context)),
            _divider(),
            _chevronItem(Icons.delete_outline, Colors.red.shade300, 'Önbelleği Temizle', onTap: () => _showClearCacheDialog(context)),
          ]),
          const SizedBox(height: 20),

          // Hesap ve Güvenlik
          _sectionHeader('Hesap ve Güvenlik'),
          _card([
            _chevronItem(Icons.vpn_key, Colors.red, 'Admin Panel Girişi', onTap: () async {
              const url = 'https://samsun-gtfs-rt.onrender.com/admin';
              if (await canLaunchUrl(Uri.parse(url))) {
                await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
              }
            }),
          ]),
          const SizedBox(height: 20),

          // Bilgi
          _sectionHeader('Bilgi'),
          _card([
            _chevronItem(Icons.description, Colors.grey, 'Kullanım Koşulları', onTap: () => _showTermsDialog(context)),
            _divider(),
            _chevronItem(Icons.privacy_tip, Colors.grey, 'Gizlilik Politikası', onTap: () => _showPrivacyDialog(context)),
            _divider(),
            _chevronItem(Icons.info, Colors.grey, 'Hakkında', onTap: () {
              _showAboutDialog(context);
            }),
          ]),
          const SizedBox(height: 24),

          // Versiyon
          Center(
            child: Text('Samsun Ulaşım Sistemi v2.5.0', style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 13)),
          ),
          const SizedBox(height: 4),
          Center(
            child: Text('By Turan KAYA', style: TextStyle(color: Colors.white.withOpacity(0.15), fontSize: 11, fontStyle: FontStyle.italic)),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  // ─── GÜNCELLEME KONTROLÜ ───
  Future<void> _checkForUpdate() async {
    try {
      // Render proxy üzerinden sürüm kontrolü (repo gizli, GitHub API'ye doğrudan erişilemez)
      final response = await http.get(
        Uri.parse('https://samsun-gtfs-rt.onrender.com/api/app_version'),
        headers: {'User-Agent': 'SamsunMobilApp/2.0', 'Accept': 'application/json'},
      ).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final latestVersion = (data['latest_version'] ?? '').toString();
        const currentVersion = '2.5.0';
        final latestParts = latestVersion.split('.').map((s) => int.tryParse(s) ?? 0).toList();
        final curParts = currentVersion.split('.').map((s) => int.tryParse(s) ?? 0).toList();
        bool isNewer = false;
        for (int i = 0; i < curParts.length; i++) {
          final t = i < latestParts.length ? latestParts[i] : 0;
          if (t > curParts[i]) { isNewer = true; break; }
          if (t < curParts[i]) break;
        }
        final releaseNotes = data['release_notes'] ?? '';
        final downloadUrl = data['download_url'] ?? '';
        final forceUpdate = data['force_update'] == true;
        if (isNewer && mounted) {
          showDialog(
            context: context,
            barrierDismissible: !forceUpdate,
            builder: (ctx) => AlertDialog(
              backgroundColor: const Color(0xFF152238),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              title: Text('🆕 Yeni Sürüm: v$latestVersion', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              content: SingleChildScrollView(
                child: Text(releaseNotes, style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 13)),
              ),
              actions: [
                if (!forceUpdate)
                  TextButton(onPressed: () => Navigator.pop(ctx), child: Text('Sonra', style: TextStyle(color: Colors.white.withOpacity(0.5)))),
                ElevatedButton(
                  onPressed: () async {
                    Navigator.pop(ctx);
                    if (downloadUrl.isNotEmpty && await canLaunchUrl(Uri.parse(downloadUrl))) {
                      await launchUrl(Uri.parse(downloadUrl), mode: LaunchMode.externalApplication);
                    }
                  },
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2979FF)),
                  child: const Text('Güncelle'),
                ),
              ],
            ),
          );
        } else if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text('✅ Güncel sürümdesiniz', style: TextStyle(color: Colors.white)),
              backgroundColor: const Color(0xFF00BFA5),
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Güncelleme kontrolü başarısız: $e', style: const TextStyle(color: Colors.white)),
            backgroundColor: const Color(0xFFFF5252),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    }
  }

  // ─── DİL SEÇİMİ ───
  void _showLanguageDialog(BuildContext context) {
    final languages = ['Türkçe', 'English'];
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('🌐 Dil Seçimi', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: languages.map((lang) => RadioListTile<String>(
            title: Text(lang, style: const TextStyle(color: Colors.white)),
            value: lang,
            groupValue: _selectedLanguage,
            activeColor: const Color(0xFF2979FF),
            onChanged: (v) {
              setState(() => _selectedLanguage = v!);
              _savePreference('language', v!);
              Navigator.pop(ctx);
            },
          )).toList(),
        ),
      ),
    );
  }

  // ─── VARSAYILAN ULAŞIM TÜRÜ ───
  void _showTransportDialog(BuildContext context) {
    final types = [
      {'name': 'Otobüs', 'icon': Icons.directions_bus},
      {'name': 'Tramvay', 'icon': Icons.tram},
      {'name': 'Tekne', 'icon': Icons.directions_boat},
      {'name': 'Teleferik', 'icon': Icons.airline_seat_recline_extra},
    ];
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('🚌 Varsayılan Ulaşım Türü', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: types.map((t) => RadioListTile<String>(
            title: Row(children: [
              Icon(t['icon'] as IconData, color: Colors.white70, size: 20),
              const SizedBox(width: 8),
              Text(t['name'] as String, style: const TextStyle(color: Colors.white)),
            ]),
            value: t['name'] as String,
            groupValue: _defaultTransport,
            activeColor: const Color(0xFF00BFA5),
            onChanged: (v) {
              setState(() => _defaultTransport = v!);
              _savePreference('default_transport', v!);
              Navigator.pop(ctx);
            },
          )).toList(),
        ),
      ),
    );
  }

  // ─── FAVORİ HATLAR ───
  void _showFavoriHatlarDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('⭐ Favori Hatlar', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: SizedBox(
          width: double.maxFinite,
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            if (_favoriHatlar.isEmpty)
              Padding(
                padding: const EdgeInsets.all(20),
                child: Text('Henüz favori hat eklemediniz.\n\nHat detay sayfasından favori ekleyebilirsiniz.',
                  textAlign: TextAlign.center, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13)),
              )
            else
              ...List.generate(_favoriHatlar.length, (i) => ListTile(
                leading: const Icon(Icons.directions_bus, color: Color(0xFF00BFA5)),
                title: Text(_favoriHatlar[i], style: const TextStyle(color: Colors.white)),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline, color: Color(0xFFFF5252), size: 20),
                  onPressed: () {
                    setState(() => _favoriHatlar.removeAt(i));
                    _savePreference('favori_hatlar', _favoriHatlar);
                    Navigator.pop(ctx);
                    _showFavoriHatlarDialog(context);
                  },
                ),
              )),
          ]),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Kapat', style: TextStyle(color: Color(0xFF2979FF)))),
        ],
      ),
    );
  }

  // ─── FAVORİ DURAKLAR ───
  void _showFavoriDuraklarDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('📍 Favori Duraklar', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: SizedBox(
          width: double.maxFinite,
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            if (_favoriDuraklar.isEmpty)
              Padding(
                padding: const EdgeInsets.all(20),
                child: Text('Henüz favori durak eklemediniz.\n\nHaritada durak seçerek favori ekleyebilirsiniz.',
                  textAlign: TextAlign.center, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13)),
              )
            else
              ...List.generate(_favoriDuraklar.length, (i) => ListTile(
                leading: const Icon(Icons.location_on, color: Color(0xFF00BFA5)),
                title: Text(_favoriDuraklar[i], style: const TextStyle(color: Colors.white)),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline, color: Color(0xFFFF5252), size: 20),
                  onPressed: () {
                    setState(() => _favoriDuraklar.removeAt(i));
                    _savePreference('favori_duraklar', _favoriDuraklar);
                    Navigator.pop(ctx);
                    _showFavoriDuraklarDialog(context);
                  },
                ),
              )),
          ]),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Kapat', style: TextStyle(color: Color(0xFF2979FF)))),
        ],
      ),
    );
  }

  // ─── VERİ YENİLE ───
  void _showDataRefreshDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('🔄 Verileri Yenile', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Text('Tüm hat, durak ve sefer verileri sunucudan yeniden yüklenecek.\n\nDevam etmek istiyor musunuz?',
          style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 13)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text('İptal', style: TextStyle(color: Colors.white.withOpacity(0.5)))),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: const Text('✅ Veriler yenileniyor...', style: TextStyle(color: Colors.white)),
                  backgroundColor: const Color(0xFF00BFA5),
                  behavior: SnackBarBehavior.floating,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00BFA5)),
            child: const Text('Yenile'),
          ),
        ],
      ),
    );
  }

  // ─── ÖNBELLEK TEMİZLE ───
  void _showClearCacheDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('🗑️ Önbelleği Temizle', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Text('Uygulama önbelleği temizlenecek. Bu işlem sonrası veriler tekrar yüklenecektir.\n\nDevam etmek istiyor musunuz?',
          style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 13)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text('İptal', style: TextStyle(color: Colors.white.withOpacity(0.5)))),
          ElevatedButton(
            onPressed: () async {
              final prefs = await SharedPreferences.getInstance();
              await prefs.clear();
              if (context.mounted) {
                Navigator.pop(ctx);
                setState(() {
                  _favoriHatlar = [];
                  _favoriDuraklar = [];
                  _notificationsEnabled = true;
                  _selectedLanguage = 'Türkçe';
                  _defaultTransport = 'Otobüs';
                });
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: const Text('✅ Önbellek temizlendi', style: TextStyle(color: Colors.white)),
                    backgroundColor: const Color(0xFF00BFA5),
                    behavior: SnackBarBehavior.floating,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red.shade700),
            child: const Text('Temizle'),
          ),
        ],
      ),
    );
  }

  // ─── KULLANIM KOŞULLARI ───
  void _showTermsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('📄 Kullanım Koşulları', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _termsSection('1. Genel', 'Bu uygulama Samsun Büyükşehir Belediyesi toplu taşıma hizmetleri hakkında bilgi sağlamak amacıyla geliştirilmiştir.'),
            _termsSection('2. Veri Kullanımı', 'Uygulama, konum bilginizi yalnızca yakın durak ve rota hesaplama için kullanır. Kişisel verileriniz üçüncü taraflarla paylaşılmaz.'),
            _termsSection('3. Sorumluluk', 'Sefer saatleri ve güzergah bilgileri bilgilendirme amaçlıdır. Gerçek zamanlı değişiklikler olabilir. Güncel bilgi için 153 veya 0362 431 10 12 numarasını arayınız.'),
            _termsSection('4. Fikri Mülkiyet', 'Uygulama içeriği ve tasarımı Samsun Büyükşehir Belediyesi ve Samulaş A.Ş. mülkiyetindedir.'),
            _termsSection('5. Güncellemeler', 'Uygulama zaman zaman güncellenebilir. Kullanmaya devam ederek güncel koşulları kabul etmiş sayılırsınız.'),
          ]),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Tamam', style: TextStyle(color: Color(0xFF2979FF)))),
        ],
      ),
    );
  }

  Widget _termsSection(String title, String body) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
        const SizedBox(height: 4),
        Text(body, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
      ]),
    );
  }

  // ─── GİZLİLİK POLİTİKASI ───
  void _showPrivacyDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('🔒 Gizlilik Politikası', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _termsSection('Konum Verisi', 'Konum bilginiz yalnızca yakın durak tespiti ve rota hesaplama için cihazınızda işlenir. Sunucuya gönderilmez.'),
            _termsSection('Yerel Depolama', 'Favori hat/durak tercihleriniz yalnızca cihazınızda saklanır.'),
            _termsSection('API İletişimi', 'Uygulama, canlı araç konumları ve sefer bilgileri için ASİS ve YBS API\'lerine bağlanır. Bu bağlantılarda kişisel veri gönderilmez.'),
            _termsSection('İletişim', 'Gizlilik ile ilgili sorularınız için: 0362 431 10 12'),
          ]),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Tamam', style: TextStyle(color: Color(0xFF2979FF)))),
        ],
      ),
    );
  }

  Widget _sectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(title.toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.35), fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1.2)),
    );
  }

  Widget _card(List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF152238),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(children: children),
    );
  }

  Widget _divider() => Divider(height: 1, color: Colors.white.withOpacity(0.05), indent: 56);

  Widget _iconBox(IconData icon, Color color) {
    return Container(
      width: 36, height: 36,
      decoration: BoxDecoration(color: color.withOpacity(0.15), borderRadius: BorderRadius.circular(10)),
      child: Icon(icon, size: 20, color: color),
    );
  }

  Widget _switchItem(IconData icon, Color color, String title, bool value, ValueChanged<bool> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(children: [
        _iconBox(icon, color),
        const SizedBox(width: 12),
        Expanded(child: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500, fontSize: 14))),
        Switch(value: value, onChanged: onChanged, activeThumbColor: const Color(0xFF00BFA5)),
      ]),
    );
  }

  Widget _infoItem(IconData icon, Color color, String title, String info) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(children: [
        _iconBox(icon, color),
        const SizedBox(width: 12),
        Expanded(child: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500, fontSize: 14))),
        Text(info, style: TextStyle(color: Colors.white.withOpacity(0.35), fontSize: 13)),
      ]),
    );
  }

  Widget _chevronItem(IconData icon, Color color, String title, {String? subtitle, VoidCallback? onTap}) {
    return InkWell(
      onTap: onTap ?? () {},
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(children: [
          _iconBox(icon, color),
          const SizedBox(width: 12),
          Expanded(child: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500, fontSize: 14))),
          if (subtitle != null) ...[
            Text(subtitle, style: TextStyle(color: Colors.white.withOpacity(0.35), fontSize: 13)),
            const SizedBox(width: 4),
          ],
          Icon(Icons.chevron_right, size: 16, color: Colors.white.withOpacity(0.2)),
        ]),
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF152238),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Hakkında', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            ClipRRect(borderRadius: BorderRadius.circular(12),
              child: Image.asset('assets/SBB Logo 9.png', width: 48, height: 48, fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const SizedBox(width: 48))),
            const SizedBox(width: 12),
            ClipRRect(borderRadius: BorderRadius.circular(12),
              child: Image.asset('assets/samulas.png', width: 48, height: 48, fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const SizedBox(width: 48))),
          ]),
          const SizedBox(height: 16),
          const Text('Samsun Ulaşım', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text('Samsun Büyükşehir Belediyesi toplu taşıma uygulaması. Otobüs, tramvay, deniz, teleferik, Odak turistik hatlar ve SamAir havalimanı shuttle bilgilerini sunar.',
            style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13)),
          const SizedBox(height: 12),
          Text('Geliştirici: Turan KAYA', style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12, fontStyle: FontStyle.italic)),
          const SizedBox(height: 4),
          Text('Versiyon: 2.5.0', style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 11)),
          const SizedBox(height: 12),
          // Partnerler
          Text('İş Ortakları', style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1)),
          const SizedBox(height: 8),
          Row(children: [
            ClipRRect(borderRadius: BorderRadius.circular(8),
              child: Image.asset('assets/odak.png', width: 32, height: 32, fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const SizedBox(width: 32))),
            const SizedBox(width: 8),
            Text('Odak Samsun', style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
          ]),
          const SizedBox(height: 6),
          Row(children: [
            ClipRRect(borderRadius: BorderRadius.circular(8),
              child: Image.asset('assets/samair.png', width: 32, height: 32, fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const SizedBox(width: 32))),
            const SizedBox(width: 8),
            Text('SamAir', style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
          ]),
        ]),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Tamam', style: TextStyle(color: Color(0xFF2979FF))),
          ),
        ],
      ),
    );
  }
}
