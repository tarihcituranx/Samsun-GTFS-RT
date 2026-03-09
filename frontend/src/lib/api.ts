import { TransitLine, TransitStop, Vehicle } from "@/data/mockData";

const API_BASE = ""; // During dev Vite proxy handles it, in prod it's same origin

// Helper for random colors / colors by type if missing
const getColorForType = (type: string) => {
    switch (type) {
        case 'ekspres': return '#f97316';
        case 'tramvay': return '#22c55e';
        case 'otobus': return '#0ea5e9';
        case 'vapur': return '#0ea5e9';
        case 'teleferik': return '#a855f7';
        case 'samair': return '#64748b';
        case 'ring': return '#eab308';
        case 'odak': return '#10b981';
        default: return '#64748b';
    }
};

export const fetchAllLines = async (): Promise<TransitLine[]> => {
    try {
        // Fetch base bus lines
        const busRes = await fetch(`${API_BASE}/api/hat`);
        const busData: any[] = busRes.ok ? await busRes.json() : [];

        // Fetch odak lines
        const odakRes = await fetch(`${API_BASE}/api/odak`);
        const odakData: any[] = odakRes.ok ? await odakRes.json() : [];

        // Fetch samair lines
        const samairRes = await fetch(`${API_BASE}/api/samair`);
        const samairData: any[] = samairRes.ok ? await samairRes.json() : [];

        const lines: TransitLine[] = [];

        // Process bus/trams
        busData.forEach(item => {
            let type: TransitLine["type"] = "otobus";
            const cat = (item.kat || "").toLowerCase();
            const code = item.code || "";

            // Not: Yeni backend'de bazı "T" kodlu hatlar otobüs; yalnızca kat=tramvay ise tramvay kabul et.
            if (cat.includes("ekspres") || code.startsWith("E")) type = "ekspres";
            else if (cat.includes("tramvay")) type = "tramvay";
            else if (cat.includes("ring") || code.startsWith("R")) type = "ring";
            else if (cat.includes("vapur")) type = "vapur";
            else if (cat.includes("teleferik")) type = "teleferik";

            // renk: backend'den gelen hex rengi kullan, yoksa tipten hesapla
            const color = item.renk ? `#${item.renk}` : getColorForType(type);

            lines.push({
                code: item.code,
                name: item.name,
                type,
                color,
                vehicles: 0,                              // Canlı veriden doldurulacak
                fare: item.tam_fiyat ?? 0,                // Backend'den gelen fiyat
                stops: item.durak_sayisi ?? 0,            // Backend'den gelen durak sayısı
            });
        });

        // Process odak
        odakData.forEach(item => {
            lines.push({
                code: item.kod || item.id,
                name: item.ad,
                type: "odak",
                color: getColorForType("odak"),
                vehicles: 0,
                fare: 15,
                stops: 0,
            });
        });

        // Process Samair
        samairData.forEach(item => {
            lines.push({
                code: item.id.toString(), // Samair uses ID as identifier mostly
                name: item.ad,
                type: "samair",
                color: getColorForType("samair"),
                vehicles: 0,
                fare: 50,
                stops: 0,
            });
        });

        return lines;
    } catch (error) {
        console.error("Failed to fetch lines:", error);
        return [];
    }
};

export const fetchLineStops = async (code: string, type: string): Promise<TransitStop[]> => {
    try {
        let endpoint = "";
        if (type === "odak") {
            endpoint = `${API_BASE}/api/odak/${code}/durak`;
        } else if (type === "samair") {
            endpoint = `${API_BASE}/api/samair/${code}/durak`;
        } else {
            endpoint = `${API_BASE}/api/hat/durak/${code}`;
        }

        const res = await fetch(endpoint);
        if (!res.ok) return [];

        const data: any[] = await res.json();
        return data.map((d, index) => ({
            id: d.id || `${code}-${index}`,
            name: d.ad || d.durak_adi || d.name || "Bilinmeyen Durak",
            lat: parseFloat(d.lat),
            lng: parseFloat(d.lon),
            distance: 0,
            lines: [{ code, mins: 0 }]
        })).filter(s => !isNaN(s.lat) && !isNaN(s.lng));

    } catch (error) {
        console.error(`Failed to fetch stops for line ${code}:`, error);
        return [];
    }
};

export const fetchLineVehicles = async (code: string): Promise<Vehicle[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/hat/arac/${code}`);
        if (!res.ok) return [];

        const data: any[] = await res.json();
        return data.map(v => ({
            id: v.kodu || v.id || v.plate || "v1",
            plate: v.plate || v.plaka || "Bilinmeyen",
            line: code,
            speed: parseFloat(v.hiz || v.speed || "0"),
            lat: parseFloat(v.enlem || v.lat),
            lng: parseFloat(v.boylam || v.lon),
            status: "active" as const,
            heading: parseFloat(v.yon || v.heading || "0"),
            yakin: v.yakin || "",
            hasilat: v.hasilat || v.hasila || v.gunluk_hasilat || undefined
        })).filter(v => !isNaN(v.lat) && !isNaN(v.lng));

    } catch (error) {
        // some lines (odak, samair) might not have live vehicles, ignore error
        return [];
    }
};

export const fetchAllStops = async (): Promise<TransitStop[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/tum_duraklar`);
        if (!res.ok) return [];

        const data: any[] = await res.json();
        return data.map((d) => ({
            id: d.id || d.kod,
            name: d.ad || "Bilinmeyen Durak",
            lat: parseFloat(d.lat),
            lng: parseFloat(d.lon),
            distance: 0,
            lines: [] // These are bare map stops without lines context initially
        })).filter((s) => !isNaN(s.lat) && !isNaN(s.lng));

    } catch (error) {
        console.error("Failed to fetch all stops:", error);
        return [];
    }
};

// ─── Durak Ara ─────────────────────────────────────────────────────────────
export const searchStops = async (query: string): Promise<{ kod: string; ad: string; lat: number; lon: number }[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/durak_ara?q=${encodeURIComponent(query)}`);
        if (!res.ok) return [];
        return await res.json();
    } catch { return []; }
};

// ─── Durak Panel (Canlı ETA) ───────────────────────────────────────────────
export const fetchStopPanel = async (kod: string): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/durak_panel/${encodeURIComponent(kod)}`);
        if (!res.ok) return [];
        return await res.json();
    } catch { return []; }
};

// ─── Rota ─────────────────────────────────────────────────────────────────
export interface RouteResult {
    segments?: Array<{
        type: string;
        line?: string;
        from?: string;
        to?: string;
        duration?: number;
        stops?: number;
        fare?: number;
        color?: string;
    }>;
    total_duration?: number;
    total_fare?: number;
    transfers?: number;
    error?: string;
}

export const fetchRoute = async (params: {
    lat1?: number; lon1?: number; lat2?: number; lon2?: number;
    start?: string; end?: string;
}): Promise<RouteResult | null> => {
    try {
        const q = new URLSearchParams();
        if (params.lat1 !== undefined) q.set("lat1", params.lat1.toString());
        if (params.lon1 !== undefined) q.set("lon1", params.lon1.toString());
        if (params.lat2 !== undefined) q.set("lat2", params.lat2.toString());
        if (params.lon2 !== undefined) q.set("lon2", params.lon2.toString());
        if (params.start) q.set("start", params.start);
        if (params.end) q.set("end", params.end);
        const res = await fetch(`${API_BASE}/api/rota?${q.toString()}`);
        if (!res.ok) return null;
        return await res.json();
    } catch { return null; }
};

// ─── Mekanlar (Keşfet / POI) ──────────────────────────────────────────────
export const fetchPlaces = async (): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/mekanlar`);
        if (!res.ok) return [];
        return await res.json();
    } catch { return []; }
};

// ─── Hat Detayları (info + fiyat + sefer + eşleş) ─────────────────────────
export interface LineFullDetail {
    info?: any;
    fiyat?: { tam_fiyat?: number; indirimli_fiyat?: number };
    sefer?: any[];
    esles?: { code?: string };
}

export const fetchLineFullDetail = async (code: string): Promise<LineFullDetail> => {
    try {
        const [infoRes, fiyatRes, seferRes, eslesRes] = await Promise.allSettled([
            fetch(`${API_BASE}/api/hat/info/${code}`),
            fetch(`${API_BASE}/api/hat/fiyat/${code}`),
            fetch(`${API_BASE}/api/hat/sefer/${code}`),
            fetch(`${API_BASE}/api/hat/esles/${code}`),
        ]);
        return {
            info: infoRes.status === "fulfilled" && infoRes.value.ok ? await infoRes.value.json() : undefined,
            fiyat: fiyatRes.status === "fulfilled" && fiyatRes.value.ok ? await fiyatRes.value.json() : undefined,
            sefer: seferRes.status === "fulfilled" && seferRes.value.ok ? await seferRes.value.json() : undefined,
            esles: eslesRes.status === "fulfilled" && eslesRes.value.ok ? await eslesRes.value.json() : undefined,
        };
    } catch { return {}; }
};

// ─── Hat Yönleri (/api/hat/{code}/yonler) ─────────────────────────────────
export const fetchHatYonler = async (code: string): Promise<{ yon_id: string; yon_adi: string }[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/hat/${encodeURIComponent(code)}/yonler`);
        if (!res.ok) return [];
        return await res.json();
    } catch { return []; }
};

// ─── Proxy: SmartStations (Tram İstasyonuna Yaklaşan Araçlar) ─────────────
export const fetchSmartStation = async (stationId: string | number): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/proxy/smart_stations?stationId=${stationId}`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch { return []; }
};

// ─── Proxy: RealTimeData (Ham ASIS Hat Araçları) ──────────────────────────
export const fetchRealtimeRaw = async (lineCode: string): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/proxy/realtime?lineCode=${encodeURIComponent(lineCode)}`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch { return []; }
};

// ─── Proxy: StopsStations (ASIS Hat Durakları) ───────────────────────────
export const fetchStopsStations = async (lineCode: string): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/proxy/stops_stations?lineCode=${encodeURIComponent(lineCode)}`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch { return []; }
};

// ─── Proxy: LineDirections (ASIS Hat Yönleri) ────────────────────────────
export const fetchLineDirections = async (lineCode: string): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/proxy/line_directions?lineCode=${encodeURIComponent(lineCode)}`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch { return []; }
};

// ─── Proxy: Schedules (ASIS Resmi Tarife / Sefer Saatleri) ───────────────
export interface ScheduleItem {
    saat?: string;
    yon?: string;
    gun?: string;
    departureTime?: string;
    directionId?: string | number;
}
export const fetchSchedules = async (lineCode: string, scheduleDate?: string): Promise<ScheduleItem[]> => {
    try {
        const date = scheduleDate || new Date().toISOString().split('T')[0];
        const res = await fetch(`${API_BASE}/api/proxy/schedules?lineCode=${encodeURIComponent(lineCode)}&scheduleDate=${date}`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch { return []; }
};

// ─── App Version (Sürüm Kontrolü + Force Update) ─────────────────────────
export interface AppVersionInfo {
    latest_version: string;
    min_version: string;
    release_notes: string;
    download_url: string;
    force_update: boolean;
}
export const fetchAppVersion = async (): Promise<AppVersionInfo | null> => {
    try {
        const res = await fetch(`${API_BASE}/api/app_version`);
        if (!res.ok) return null;
        return await res.json();
    } catch { return null; }
};

// ─── FCM Push Token Kayıt ─────────────────────────────────────────────────
export const registerFcmToken = async (token: string, platform: string = "web"): Promise<boolean> => {
    try {
        const res = await fetch(`${API_BASE}/api/fcm_token`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, platform, version: "3.0.0", locale: "tr" }),
        });
        return res.ok;
    } catch { return false; }
};

// ─── Proxy: Lines (ASIS Raw Hat Listesi) ─────────────────────────────────
export const fetchProxyLines = async (): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/proxy/lines`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch { return []; }
};

// ─── Proxy: Odak Araçlar ────────────────────────────────────────────────
export const fetchProxyOdakVehicles = async (hatid: string | number): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/proxy_odak_araclar?hatid=${encodeURIComponent(String(hatid))}`);
        if (!res.ok) return [];
        const data = await res.json();
        if (Array.isArray(data)) return data;
        if (Array.isArray(data?.vehicles)) return data.vehicles;
        if (Array.isArray(data?.data)) return data.data;
        return [];
    } catch { return []; }
};

// ─── Proxy: Samair Araçlar (YBS canlı) ─────────────────────────────────
export const fetchProxySamairVehicles = async (): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/proxy_samair_araclar`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch { return []; }
};

// ─── Proxy: Samair Saatler (YBS canlı saatler) ──────────────────────────
export const fetchProxySamairSchedules = async (hatid: string | number): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/proxy_samair_saatler?hatid=${encodeURIComponent(String(hatid))}`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch { return []; }
};
