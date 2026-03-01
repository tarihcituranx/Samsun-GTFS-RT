
import 'package:flutter/material.dart';

// Uygulama ilk açıldığında veya büyük veri güncellemeleri sırasında
// gösterilecek olan bekleme ekranı.
class LoadingScreen extends StatelessWidget {
  final String message;

  const LoadingScreen({
    Key? key,
    this.message = 'Veriler hazırlanıyor...\nLütfen bekleyin.',
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.red.shade700,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Yükleme animasyonu
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
            ),
            const SizedBox(height: 24),
            // Bilgilendirme mesajı
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
