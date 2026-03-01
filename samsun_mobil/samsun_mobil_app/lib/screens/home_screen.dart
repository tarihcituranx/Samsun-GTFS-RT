
import 'package:flutter/material.dart';
import 'package:samsun_transit/helpers/database_helper.dart';

// Yeniden yapılandırılmış ana ekran.
// Artık verileri doğrudan ve güvenilir bir şekilde yerel veritabanından çeker.
// Bu, samsun.py'nin web arayüzünün mobil karşılığıdır.
class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // Veritabanından gelen hatları tutacak olan Future
  late Future<List<Map<String, dynamic>>> _hatlarFuture;
  final dbHelper = DatabaseHelper.instance;

  @override
  void initState() {
    super.initState();
    // Ekran ilk yüklendiğinde veritabanından hatları çek
    _hatlarFuture = _fetchHatsFromDb();
  }

  // Veritabanından hatları çeken asenkron fonksiyon
  Future<List<Map<String, dynamic>>> _fetchHatsFromDb() async {
    final db = await dbHelper.database;
    // Hatları kategorilerine göre sırala (samsun.py gibi)
    return await db.query(DatabaseHelper.tableHat, orderBy: 'kat, name');
  }

  // Hat kategorisine göre ikon ve renk belirleyen yardımcı fonksiyon
  Widget _getIconForCategory(String? category) {
    IconData iconData;
    Color color;

    switch (category) {
      case 'tramvay':
        iconData = Icons.tram;
        color = Colors.orange;
        break;
      case 'ring':
        iconData = Icons.sync_alt;
        color = Colors.amber;
        break;
      case 'ekspres':
        iconData = Icons.rocket_launch;
        color = Colors.purple;
        break;
      case 'havalimani':
        iconData = Icons.airplanemode_active;
        color = Colors.red;
        break;
      case 'ilce':
        iconData = Icons.holiday_village;
        color = Colors.teal;
        break;
      default: // otobus ve diğerleri
        iconData = Icons.directions_bus;
        color = Colors.blue;
    }
    return Icon(iconData, color: color);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Samsun Ulaşım Rehberi'),
        centerTitle: true,
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _hatlarFuture,
        builder: (context, snapshot) {
          // Veri yükleniyor durumunda
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          // Hata durumunda
          if (snapshot.hasError) {
            return Center(child: Text('Bir hata oluştu: ${snapshot.error}'));
          }
          // Veri yok veya boş ise
          if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.bus_alert, size: 60, color: Colors.grey),
                  SizedBox(height: 16),
                  Text(
                    'Yerel veritabanında hat bulunamadı.\nUygulamayı yeniden başlatmayı deneyin.',
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            );
          }

          // Veri başarıyla yüklendiğinde
          final hatlar = snapshot.data!;
          return ListView.builder(
            itemCount: hatlar.length,
            itemBuilder: (context, index) {
              final hat = hatlar[index];
              final hatAdi = hat['name'] as String? ?? 'Bilinmiyor';
              final hatKodu = hat['code'] as String? ?? '';
              final hatKategorisi = hat['kat'] as String?;

              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                child: ListTile(
                  leading: _getIconForCategory(hatKategorisi),
                  title: Text(hatAdi),
                  subtitle: Text(hatKodu),
                  onTap: () {
                    // TODO: Hat detay ekranına gitme fonksiyonu eklenecek.
                    // Bu ekranda, seçilen hattın durakları ve canlı araçları gösterilecek.
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Detaylar yakında: $hatKodu')),
                    );
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }
}
