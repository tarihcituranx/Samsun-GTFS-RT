import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'admin_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notificationsEnabled = true;

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
            _switchItem(Icons.notifications, Colors.blue, 'Bildirimler', _notificationsEnabled, (v) => setState(() => _notificationsEnabled = v)),
            _divider(),
            _infoItem(Icons.dark_mode, Colors.purple, 'Tema', 'Karanlık Mod'),
            _divider(),
            _chevronItem(Icons.language, Colors.orange, 'Dil Seçimi', subtitle: 'Türkçe', onTap: () => _showComingSoon(context)),
          ]),
          const SizedBox(height: 20),

          // Ulaşım Tercihleri
          _sectionHeader('Ulaşım Tercihleri'),
          _card([
            _chevronItem(Icons.directions_bus, const Color(0xFF00BFA5), 'Favori Hatlar', onTap: () => _showComingSoon(context)),
            _divider(),
            _chevronItem(Icons.location_on, const Color(0xFF00BFA5), 'Favori Duraklar', onTap: () => _showComingSoon(context)),
            _divider(),
            _chevronItem(Icons.commute, const Color(0xFF00BFA5), 'Varsayılan Ulaşım Türü', subtitle: 'Otobüs', onTap: () => _showComingSoon(context)),
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
            _chevronItem(Icons.description, Colors.grey, 'Kullanım Koşulları', onTap: () => _showComingSoon(context)),
            _divider(),
            _chevronItem(Icons.info, Colors.grey, 'Hakkında', onTap: () {
              _showAboutDialog(context);
            }),
          ]),
          const SizedBox(height: 24),

          // Versiyon
          Center(
            child: Text('Samsun Ulaşım v2.4.1', style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 13)),
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

  void _showComingSoon(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('🚧 Bu özellik çok yakında eklenecek!', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF152238),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        duration: const Duration(seconds: 2),
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
          Text('Versiyon: 2.4.1', style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 11)),
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
