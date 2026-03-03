#!/bin/bash
# ============================================================
# Android Build Fix — Firebase Studio / Nix Ortamı
# Geliştiren: Turan Kaya
# Kullanım: bash android_firebase_fix.sh
# ============================================================

echo "=========================================="
echo " Android Build Fix — Firebase Studio"
echo "=========================================="

# ── ADIM 1: Mevcut Build Tools sürümünü bul ──
echo ""
echo "▶ ADIM 1: Mevcut Android Build Tools kontrol ediliyor..."
echo "Kurulu Build Tools:"
ls $ANDROID_HOME/build-tools/ 2>/dev/null || echo "ANDROID_HOME bulunamadı, deneniyor..."
ls ~/Android/Sdk/build-tools/ 2>/dev/null

BUILDTOOLS=$(ls $ANDROID_HOME/build-tools/ 2>/dev/null | tail -1)
if [ -z "$BUILDTOOLS" ]; then
  BUILDTOOLS=$(ls ~/Android/Sdk/build-tools/ 2>/dev/null | tail -1)
fi
echo "→ Kullanılacak Build Tools: $BUILDTOOLS"

# ── ADIM 2: local.properties düzelt ──
echo ""
echo "▶ ADIM 2: local.properties kontrol ediliyor..."
if [ ! -f android/local.properties ]; then
  echo "sdk.dir=$ANDROID_HOME" > android/local.properties
  echo "→ local.properties oluşturuldu"
else
  echo "→ local.properties mevcut:"
  cat android/local.properties
fi

# ── ADIM 3: build.gradle.kts otomatik düzelt ──
echo ""
echo "▶ ADIM 3: build.gradle.kts düzenleniyor..."
GRADLE_FILE="android/app/build.gradle.kts"
GRADLE_GROOVY="android/app/build.gradle"

if [ -f "$GRADLE_FILE" ]; then
  echo "→ Dosya bulundu: $GRADLE_FILE"
  # buildToolsVersion satırı varsa güncelle, yoksa ekle
  if grep -q "buildToolsVersion" "$GRADLE_FILE"; then
    sed -i "s/buildToolsVersion = \".*\"/buildToolsVersion = \"$BUILDTOOLS\"/" "$GRADLE_FILE"
    echo "→ buildToolsVersion güncellendi: $BUILDTOOLS"
  else
    sed -i "/compileSdk/a\\    buildToolsVersion = \"$BUILDTOOLS\"" "$GRADLE_FILE"
    echo "→ buildToolsVersion eklendi: $BUILDTOOLS"
  fi
elif [ -f "$GRADLE_GROOVY" ]; then
  echo "→ Dosya bulundu: $GRADLE_GROOVY"
  if grep -q "buildToolsVersion" "$GRADLE_GROOVY"; then
    sed -i "s/buildToolsVersion \".*\"/buildToolsVersion \"$BUILDTOOLS\"/" "$GRADLE_GROOVY"
    echo "→ buildToolsVersion güncellendi: $BUILDTOOLS"
  else
    sed -i "/compileSdkVersion/a\\    buildToolsVersion \"$BUILDTOOLS\"" "$GRADLE_GROOVY"
    echo "→ buildToolsVersion eklendi: $BUILDTOOLS"
  fi
else
  echo "⚠ build.gradle dosyası bulunamadı, proje kök dizininde olduğunuzdan emin olun"
fi

# ── ADIM 4: .idx/dev.nix düzelt ──
echo ""
echo "▶ ADIM 4: .idx/dev.nix kontrol ediliyor..."
if [ -f ".idx/dev.nix" ]; then
  echo "→ Mevcut dev.nix:"
  cat .idx/dev.nix
  echo ""
  echo "→ Eğer buildToolsVersion eksikse şunu ekleyin:"
  echo "   buildToolsVersion = \"$BUILDTOOLS\";"
else
  echo "→ .idx/dev.nix bulunamadı, oluşturuluyor..."
  mkdir -p .idx
  cat > .idx/dev.nix << NIXEOF
{ pkgs, ... }: {
  android = {
    enable = true;
    flutter.enable = true;
    buildToolsVersion = "$BUILDTOOLS";
    platformToolsVersion = "34.0.4";
    emulator.enable = false;
  };
}
NIXEOF
  echo "→ .idx/dev.nix oluşturuldu"
fi

# ── ADIM 5: Temizle ve yeniden dene ──
echo ""
echo "▶ ADIM 5: Proje temizleniyor..."
flutter clean
flutter pub get

echo ""
echo "▶ ADIM 6: Test build başlatılıyor..."
flutter build apk --debug 2>&1

echo ""
echo "=========================================="
echo " İşlem tamamlandı!"
echo " Hâlâ hata varsa hata mesajını paylaşın."
echo "=========================================="
