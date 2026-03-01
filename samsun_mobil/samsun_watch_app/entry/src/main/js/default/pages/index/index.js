import fetch from '@system.fetch';

export default {
    data: {
        buses: [],
        isLoading: true,
        // Örnek Hardcoded Favori Durak Cihaz ID'si 
        // Gerçek uygulamada bu telefon uygulamasından Bluetooth ile saatin hafızasına itilir (Handoff)
        favoriteStopId: '5065'
    },
    onInit() {
        this.fetchData();
    },
    fetchData() {
        this.isLoading = true;
        this.buses = [];

        // Huawei Watch (HarmonyOS) üzerinden doğrudan ASIS YBS sistemine sunucusuz (serverless) istek!
        fetch.fetch({
            url: 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/SmartStations?stationId=' + this.favoriteStopId,
            header: {
                'Content-Type': 'application/json',
                // WAF/Bot korumasını aşmak için standart bir User-Agent şarttır
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'
            },
            method: 'GET',
            success: (response) => {
                try {
                    console.info("ASIS API Response: " + response.data);
                    let data = JSON.parse(response.data);

                    if (Array.isArray(data)) {
                        this.buses = data;
                    } else if (data) {
                        this.buses = [data]; // Tek veri döndüyse array'e çevir
                    }
                } catch (e) {
                    console.error("JSON Parse Error: " + e);
                }
                this.isLoading = false;
            },
            fail: (data, code) => {
                console.error("Fetch Fail. Code: " + code + ", Data: " + data);
                this.isLoading = false;
            }
        });
    }
}
