#!/bin/bash
# Samsun Transit - APK Derle ve GitHub'a Yükle
# Kullanım: bash build_and_push.sh

set -e  # Hata olursa dur

echo "🔄 En güncel kod çekiliyor..."
cd ~/Samsun-GTFS-RT
git pull origin main

echo "📦 Flutter bağımlılıkları yükleniyor..."
cd samsun_mobil/samsun_mobil_app
flutter pub get

echo "🔨 APK derleniyor (release)..."
flutter build apk --release

echo "📤 Değişiklikler ve APK GitHub'a yükleniyor..."
cd ~/Samsun-GTFS-RT

# Tarih ve commit hash ile versiyonlu isim
DATE=$(date +"%Y%m%d_%H%M")
mkdir -p samsun_mobil/releases/latest
cp samsun_mobil/samsun_mobil_app/build/app/outputs/flutter-apk/app-release.apk samsun_mobil/releases/latest/app-release.apk

# SADECE APK'YI DEĞİL, TÜM DEĞİŞİKLİKLERİ EKLE
git add .

# Değişiklikleri commit'le
git commit -m "build: Yeni APK oluşturuldu ve proje dosyaları güncellendi ${DATE}"

# GitHub'a push'la
git push origin main

echo ""
echo "✅ TAMAMLANDI!"
echo "📱 APK: samsun_mobil/releases/latest/app-release.apk"
echo "🔗 GitHub'dan indir: https://github.com/tarihcituranx/Samsun-GTFS-RT/raw/main/samsun_mobil/releases/latest/app-release.apk"
