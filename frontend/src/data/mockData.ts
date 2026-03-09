export interface TransitLine {
  code: string;
  name: string;
  type: "ekspres" | "tramvay" | "otobus" | "vapur" | "teleferik" | "samair" | "ring" | "odak";
  color: string;
  vehicles: number;
  fare: number;
  stops: number;
}

export interface TransitStop {
  id: string | number;
  name: string;
  lat: number;
  lng: number;
  distance: number;
  lines: { code: string; mins: number }[];
}

export interface Vehicle {
  id: string;
  line: string;
  lat: number;
  lng: number;
  speed: number;
  heading: number;
  status: "active" | "delayed" | "stopped";
  yakin?: string; // e.g. "Stadyum", added via the API matching in Samsun api.ts
  plate?: string;
  time?: string;
  hasilat?: string; // Daily revenue added for the Settings feature
}

export interface Place {
  id: number;
  name: string;
  category: "tarihi" | "doga" | "yeme-icme" | "etkinlik";
  description: string;
  emoji: string;
  gradient: string;
}

export const mockLines: TransitLine[] = [
  { code: "E1", name: "Ekspres 1 - Ondokuz Mayıs Üni. ↔ Tekkeköy", type: "ekspres", color: "#f97316", vehicles: 8, fare: 24, stops: 42 },
  { code: "E2", name: "Ekspres 2 - Batıpark ↔ Canik", type: "ekspres", color: "#f97316", vehicles: 6, fare: 24, stops: 38 },
  { code: "T1", name: "Tramvay 1 - Atakum ↔ 19 Mayıs", type: "tramvay", color: "#22c55e", vehicles: 4, fare: 18, stops: 28 },
  { code: "T2", name: "Tramvay 2 - Merkez ↔ Tekkeköy", type: "tramvay", color: "#22c55e", vehicles: 3, fare: 18, stops: 24 },
  { code: "19", name: "19 - Atakum ↔ Hançerli", type: "otobus", color: "#0ea5e9", vehicles: 12, fare: 24, stops: 55 },
  { code: "26", name: "26 - Mert ↔ Çarşamba", type: "otobus", color: "#0ea5e9", vehicles: 9, fare: 24, stops: 48 },
  { code: "V1", name: "Vapur 1 - Samsun ↔ Amisos", type: "vapur", color: "#0ea5e9", vehicles: 2, fare: 35, stops: 5 },
  { code: "OK1", name: "Odak 1 - Sahil Turu", type: "odak", color: "#10b981", vehicles: 2, fare: 15, stops: 12 },
  { code: "OK2", name: "Odak 2 - Tarihi Yerler", type: "odak", color: "#10b981", vehicles: 2, fare: 15, stops: 9 },
  { code: "TF1", name: "Teleferik 1 - Amisos Tepesi", type: "teleferik", color: "#a855f7", vehicles: 6, fare: 30, stops: 3 },
  { code: "HV1", name: "Havalimanı Ekspres", type: "samair", color: "#64748b", vehicles: 3, fare: 50, stops: 8 },
  { code: "R1", name: "Ring 1 - Şehir Merkezi Turu", type: "ring", color: "#eab308", vehicles: 4, fare: 20, stops: 18 },
  { code: "R2", name: "Ring 2 - Sahil Hattı", type: "ring", color: "#eab308", vehicles: 3, fare: 20, stops: 15 },
  { code: "45", name: "45 - Canik ↔ Ladik", type: "otobus", color: "#0ea5e9", vehicles: 5, fare: 28, stops: 32 },
];

export const mockStops: TransitStop[] = [
  { id: 1, name: "Cumhuriyet Meydanı", lat: 41.2867, lng: 36.3300, distance: 120, lines: [{ code: "E1", mins: 2 }, { code: "19", mins: 5 }, { code: "T1", mins: 8 }] },
  { id: 2, name: "Hançerli Kavşağı", lat: 41.2901, lng: 36.3344, distance: 340, lines: [{ code: "E2", mins: 3 }, { code: "26", mins: 7 }] },
  { id: 3, name: "Atatürk Bulvarı", lat: 41.2823, lng: 36.3265, distance: 510, lines: [{ code: "19", mins: 1 }, { code: "R1", mins: 4 }, { code: "45", mins: 11 }] },
  { id: 4, name: "Samsun Limanı", lat: 41.2935, lng: 36.3380, distance: 680, lines: [{ code: "V1", mins: 15 }] },
  { id: 5, name: "Ondokuz Mayıs Üni.", lat: 41.3200, lng: 36.3890, distance: 890, lines: [{ code: "E1", mins: 4 }, { code: "E2", mins: 9 }] },
  { id: 6, name: "Batıpark AVM", lat: 41.2756, lng: 36.3148, distance: 1100, lines: [{ code: "E2", mins: 2 }, { code: "R2", mins: 6 }] },
  { id: 7, name: "Liman Kavşağı", lat: 41.2890, lng: 36.3320, distance: 200, lines: [{ code: "E1", mins: 3 }, { code: "T1", mins: 6 }] },
  { id: 8, name: "Kale Mahallesi", lat: 41.2850, lng: 36.3250, distance: 450, lines: [{ code: "R1", mins: 2 }, { code: "19", mins: 8 }] },
  { id: 9, name: "Çiftlik Caddesi", lat: 41.2920, lng: 36.3400, distance: 750, lines: [{ code: "26", mins: 4 }, { code: "E2", mins: 10 }] },
  { id: 10, name: "Sahil Yolu", lat: 41.2800, lng: 36.3200, distance: 950, lines: [{ code: "R2", mins: 3 }, { code: "T1", mins: 12 }] },
  { id: 11, name: "İstasyon Meydanı", lat: 41.2875, lng: 36.3310, distance: 180, lines: [{ code: "E1", mins: 1 }, { code: "T2", mins: 5 }, { code: "19", mins: 9 }] },
  { id: 12, name: "Amisos Tepesi", lat: 41.2960, lng: 36.3430, distance: 1300, lines: [{ code: "TF1", mins: 8 }] },
];

export const mockVehicles: Vehicle[] = [
  { id: "v1", plate: "55 SB 8821", line: "E1", speed: 62, lat: 41.2980, lng: 36.3450, status: "active", heading: 145 },
  { id: "v2", plate: "55 SB 9104", line: "E1", speed: 71, lat: 41.3100, lng: 36.3670, status: "active", heading: 145 },
  { id: "v3", plate: "55 SB 7733", line: "E1", speed: 45, lat: 41.3200, lng: 36.3890, status: "delayed", heading: 145 },
  { id: "v4", plate: "55 TR 2201", line: "T1", speed: 55, lat: 41.2867, lng: 36.3300, status: "active", heading: 270 },
  { id: "v5", plate: "55 TR 2205", line: "T1", speed: 58, lat: 41.2810, lng: 36.3200, status: "active", heading: 270 },
  { id: "v6", plate: "55 VR 0011", line: "V1", speed: 24, lat: 41.2940, lng: 36.3385, status: "active", heading: 90 },
  { id: "v7", plate: "55 SB 1122", line: "19", speed: 48, lat: 41.2850, lng: 36.3250, status: "active", heading: 180 },
  { id: "v8", plate: "55 SB 3344", line: "26", speed: 52, lat: 41.2920, lng: 36.3400, status: "active", heading: 220 },
  { id: "v9", plate: "55 TF 0001", line: "TF1", speed: 12, lat: 41.2960, lng: 36.3430, status: "active", heading: 45 },
  { id: "v10", plate: "55 RN 5501", line: "R1", speed: 35, lat: 41.2890, lng: 36.3320, status: "active", heading: 90 },
];

export const mockPlaces: Place[] = [
  { id: 1, name: "Bandırma Vapuru Müzesi", category: "tarihi", description: "Atatürk'ün Samsun'a çıktığı vapurun müze gemisi", emoji: "🚢", gradient: "from-amber-600 to-orange-800" },
  { id: 2, name: "Amazon Köyü", category: "doga", description: "Antik Amazon savaşçılarının efsanevi köyü", emoji: "🏹", gradient: "from-emerald-600 to-green-800" },
  { id: 3, name: "Amisos Tepesi", category: "tarihi", description: "Antik Amisos kenti kalıntıları ve muhteşem manzara", emoji: "🏛️", gradient: "from-violet-600 to-purple-800" },
  { id: 4, name: "Samsun Deniz Müzesi", category: "tarihi", description: "Karadeniz denizcilik tarihi ve eserleri", emoji: "⚓", gradient: "from-blue-600 to-cyan-800" },
  { id: 5, name: "Kıyı Parkı", category: "doga", description: "Sahil boyunca uzanan yeşil park ve yürüyüş yolları", emoji: "🌳", gradient: "from-green-500 to-teal-700" },
  { id: 6, name: "19 Mayıs Stadyumu", category: "etkinlik", description: "Samsunspor'un efsane stadyumu ve etkinlik merkezi", emoji: "⚽", gradient: "from-red-500 to-rose-700" },
  { id: 7, name: "Çarşamba Çarşısı", category: "yeme-icme", description: "Geleneksel lezzetler ve yerel ürünlerin adresi", emoji: "🍽️", gradient: "from-yellow-500 to-amber-700" },
];

export const lineTypeConfig: Record<string, { label: string; emoji: string }> = {
  ekspres: { label: "Ekspres", emoji: "🚌" },
  tramvay: { label: "Tramvay", emoji: "🚃" },
  otobus: { label: "Otobüs", emoji: "🚌" },
  vapur: { label: "Vapur", emoji: "⛴️" },
  odak: { label: "Odak", emoji: "🟢" },
  teleferik: { label: "Teleferik", emoji: "🚡" },
  samair: { label: "Samair", emoji: "✈️" },
  ring: { label: "Ring", emoji: "🔄" },
};

export const transferRules = [
  { type: "Normal", discount: "—", fare: "₺24.00" },
  { type: "Öğrenci", discount: "%50", fare: "₺12.00" },
  { type: "65+ Yaş", discount: "%75", fare: "₺6.00" },
  { type: "Engelli", discount: "%100", fare: "Ücretsiz" },
  { type: "Samsunlu", discount: "%10", fare: "₺21.60" },
];
