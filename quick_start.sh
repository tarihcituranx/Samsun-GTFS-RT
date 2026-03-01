#!/bin/bash
# GTFS Realtime - Hızlı Başlangıç Script'i
# =========================================
# Samsun Transit GTFS-RT feed'ini başlatır ve test eder

set -e  # Hata durumunda dur

echo "=========================================="
echo "  GTFS Realtime - Hızlı Başlangıç"
echo "=========================================="
echo ""

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Gerekli paketleri kontrol et
echo "📦 Bağımlılıklar kontrol ediliyor..."

check_package() {
    if python3 -c "import $1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $1 yüklü"
        return 0
    else
        echo -e "${RED}✗${NC} $1 eksik"
        return 1
    fi
}

MISSING=0

check_package "fastapi" || MISSING=1
check_package "uvicorn" || MISSING=1
check_package "requests" || MISSING=1
check_package "google.transit" || MISSING=1

if [ $MISSING -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Eksik paketler yükleniyor...${NC}"
    pip install fastapi uvicorn requests gtfs-realtime-bindings protobuf
    echo -e "${GREEN}✓ Paketler yüklendi${NC}"
fi

echo ""

# Mevcut Python dosyasını kontrol et
if [ ! -f "samsun.py" ]; then
    echo -e "${RED}❌ samsun.py bulunamadı!${NC}"
    echo "Lütfen bu script'i samsun.py ile aynı dizinde çalıştırın."
    exit 1
fi

echo -e "${GREEN}✓ samsun.py bulundu${NC}"
echo ""

# Arka planda sunucuyu başlat
echo "🚀 Samsun Transit sunucusu başlatılıyor..."
python3 samsun.py > server.log 2>&1 &
SERVER_PID=$!
echo "   PID: $SERVER_PID"
echo "   Log: server.log"

# Sunucunun başlamasını bekle
echo ""
echo "⏳ Sunucu hazırlanıyor (30 saniye)..."
sleep 30

# Sunucu sağlığını kontrol et
echo ""
echo "🔍 Sunucu sağlık kontrolü..."

if curl -s -I http://localhost:8000/ | grep -q "200 OK"; then
    echo -e "${GREEN}✓ Web arayüzü çalışıyor${NC}"
else
    echo -e "${RED}✗ Web arayüzü yanıt vermiyor${NC}"
fi

if curl -s -I http://localhost:8000/gtfs-rt/vehicle-positions | grep -q "200 OK"; then
    echo -e "${GREEN}✓ GTFS-RT endpoint çalışıyor${NC}"
else
    echo -e "${RED}✗ GTFS-RT endpoint yanıt vermiyor${NC}"
    echo ""
    echo "Son 20 satır log:"
    tail -20 server.log
    exit 1
fi

echo ""

# Test başlat
if [ -f "gtfs_rt_test.py" ]; then
    echo "🧪 GTFS-RT test başlatılıyor..."
    echo ""
    python3 gtfs_rt_test.py test
else
    echo -e "${YELLOW}⚠️  gtfs_rt_test.py bulunamadı, manuel test yapılıyor...${NC}"
    echo ""
    
    # Manuel test
    echo "📊 Feed İstatistikleri:"
    curl -s http://localhost:8000/gtfs-rt/stats | python3 -m json.tool
fi

echo ""
echo "=========================================="
echo "  Başarılı! 🎉"
echo "=========================================="
echo ""
echo "Sunucu çalışıyor:"
echo "  • Web Arayüz: http://localhost:8000"
echo "  • GTFS-RT Feed: http://localhost:8000/gtfs-rt/vehicle-positions"
echo "  • JSON Debug: http://localhost:8000/gtfs-rt/vehicle-positions.json"
echo "  • İstatistikler: http://localhost:8000/gtfs-rt/stats"
echo ""
echo "Sunucuyu durdurmak için:"
echo "  kill $SERVER_PID"
echo ""
echo "Log dosyası:"
echo "  tail -f server.log"
echo ""

# PID'yi dosyaya yaz
echo $SERVER_PID > server.pid
echo "PID server.pid dosyasına kaydedildi"
echo ""

# Monitoring modu (opsiyonel)
read -p "Feed'i canlı izlemek ister misiniz? (e/h) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ee]$ ]]; then
    echo ""
    echo "📡 Feed izleme modu (Ctrl+C ile çıkış)..."
    echo "----------------------------------------"
    
    while true; do
        STATS=$(curl -s http://localhost:8000/gtfs-rt/stats)
        VEHICLE_COUNT=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['vehicle_count'])")
        TIMESTAMP=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['last_update'])")
        
        echo "[$(date '+%H:%M:%S')] Araç: $VEHICLE_COUNT | Güncelleme: $TIMESTAMP"
        sleep 15
    done
fi
