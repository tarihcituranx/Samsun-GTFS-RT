import fetch from '@system.fetch';

export default {
    data: {
        buses: [],
        routes: [],
        isLoading: true,
        isRouting: false,
        favoriteStopId: '5065'
    },
    onInit() {
        this.fetchData();
        this.fetchRoute(); // Otomatik olarak rotayı da getir (Demo amaçlı Meydan-Çarşamba)
    },
    fetchData() {
        this.isLoading = true;
        this.buses = [];

        fetch.fetch({
            url: 'https://api.samsun.bel.tr/OHSSoapToJson/api/Asis/SmartStations?stationId=' + this.favoriteStopId,
            header: {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'
            },
            method: 'GET',
            success: (response) => {
                try {
                    let data = JSON.parse(response.data);
                    if (Array.isArray(data)) {
                        this.buses = data;
                    } else if (data) {
                        this.buses = [data];
                    }
                } catch (e) { }
                this.isLoading = false;
            },
            fail: (data, code) => {
                this.isLoading = false;
            }
        });
    },
    fetchRoute() {
        this.isRouting = true;
        this.routes = [];

        // Watch -> Phone/Backend proxy
        // Gerçek cihaz testinde IP adresi bilgisayarın LAN IP'si yapılmalıdır (örn: http://192.168.1.100:8000)
        fetch.fetch({
            url: 'http://localhost:8000/api/rota?start=Meydan&end=Atakum',
            header: {
                'Content-Type': 'application/json'
            },
            method: 'GET',
            success: (response) => {
                try {
                    let data = JSON.parse(response.data);
                    if (Array.isArray(data)) {
                        this.routes = data;
                    }
                } catch (e) { }
                this.isRouting = false;
            },
            fail: (data, code) => {
                this.isRouting = false;
            }
        });
    }
}
