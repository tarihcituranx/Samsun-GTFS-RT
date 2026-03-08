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

            if (cat.includes("ekspres") || code.startsWith("E")) type = "ekspres";
            else if (cat.includes("tramvay") || code.startsWith("T")) type = "tramvay";
            else if (cat.includes("ring") || code.startsWith("R")) type = "ring";
            else if (cat.includes("vapur")) type = "vapur";
            else if (cat.includes("teleferik")) type = "teleferik";

            lines.push({
                code: item.code,
                name: item.name,
                type,
                color: getColorForType(type),
                vehicles: 0, // Will be populated by real-time if needed
                fare: 0,     // We can fetch it or just mock it as 24
                stops: 0,    // Will be populated when loaded
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

export const fetchLineVehicles = async (code: string, type?: string): Promise<Vehicle[]> => {
    try {
        let endpoint = `${API_BASE}/api/hat/arac/${code}`;
        if (type === "samair") {
            endpoint = `${API_BASE}/api/proxy_samair_araclar`;
        } else if (type === "odak") {
            endpoint = `${API_BASE}/api/proxy_odak_araclar?hatid=${code}`;
        }

        const res = await fetch(endpoint);
        if (!res.ok) return [];

        const rawData = await res.json();
        const data: any[] = type === "odak" ? (rawData.vehicles || []) : rawData;

        return data.map(v => ({
            id: v.kodu || v.id || v.plate || "v1",
            plate: v.plate || v.plaka || v.Plaka || "Bilinmeyen",
            line: code,
            speed: parseFloat(v.hiz || v.speed || v.Hizi || "0"),
            lat: parseFloat(v.lat || v.enlem || v.Enlem || "0"),
            lng: parseFloat(v.lon || v.boylam || v.Boylam || "0"),
            status: "active" as const,
            heading: parseFloat(v.yon || v.heading || "0"),
            yakin: v.yakin || "",
            hasilat: v.hasilat || v.hasila || v.gunluk_hasilat || undefined
        })).filter(v => !isNaN(v.lat) && !isNaN(v.lng) && v.lat > 0 && v.lng > 0);

    } catch (error) {
        console.error(`Failed to fetch vehicles for ${code}:`, error);
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

export const fetchPlaces = async (): Promise<any[]> => {
    try {
        const res = await fetch(`${API_BASE}/api/mekanlar`);
        if (!res.ok) return [];
        return await res.json();
    } catch (error) {
        console.error("Failed to fetch places:", error);
        return [];
    }
};

export interface RouteEndpointParams {
    start?: string;
    lat1?: number;
    lon1?: number;
    end?: string;
    lat2?: number;
    lon2?: number;
}

export const fetchRoute = async (params: RouteEndpointParams): Promise<any[]> => {
    try {
        const queryParams = new URLSearchParams();
        if (params.start) queryParams.append("start", params.start);
        if (params.lat1) queryParams.append("lat1", params.lat1.toString());
        if (params.lon1) queryParams.append("lon1", params.lon1.toString());
        if (params.end) queryParams.append("end", params.end);
        if (params.lat2) queryParams.append("lat2", params.lat2.toString());
        if (params.lon2) queryParams.append("lon2", params.lon2.toString());

        const res = await fetch(`${API_BASE}/api/rota?${queryParams.toString()}`);
        if (!res.ok) return [];
        return await res.json();
    } catch (error) {
        console.error("Failed to fetch route:", error);
        return [];
    }
};

export const fetchAppVersion = async (): Promise<any> => {
    try {
        const res = await fetch(`${API_BASE}/api/app_version`);
        if (!res.ok) return null;
        return await res.json();
    } catch (error) {
        console.error("Failed to fetch app version:", error);
        return null;
    }
};

export const fetchSamairSchedule = async (id: string): Promise<any> => {
    try {
        const res = await fetch(`${API_BASE}/api/samair/${id}/sefer`);
        if (!res.ok) return null;
        return await res.json();
    } catch (error) {
        console.error("Failed to fetch samair schedule:", error);
        return null;
    }
};
