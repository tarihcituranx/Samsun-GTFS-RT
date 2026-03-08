import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
// transit context v2
import { mockVehicles, type Vehicle, type TransitLine, type TransitStop } from "@/data/mockData";
import { fetchAllLines, fetchLineStops, fetchLineVehicles } from "@/lib/api";

// ─── Uygulama yapılandırması (ileride şehir değişimi için altyapı) ──────────
export const APP_CONFIG = {
  name: "Kentli",
  tagline: "Şehrinin Rehberi",
  version: "1.0.0",
  author: "Turan KAYA",
  github: "https://github.com/tarihcituranx",
  website: "https://kentli.app",
  activeCity: {
    id: "samsun",
    name: "Samsun",
    lat: 41.2867,
    lng: 36.3300,
    color: "#f97316",
  },
} as const;

type TabId = "harita" | "hatlar" | "yakinim" | "rota" | "kesfet" | "odak" | "samair" | "hakkinda";

export type DetailItem =
  | { type: "line"; data: TransitLine }
  | { type: "stop"; data: TransitStop }
  | { type: "vehicle"; data: Vehicle }
  | null;

export type MapFilterKey = "buses" | "trams" | "ferries" | "stops";

interface TransitContextType {
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  isDark: boolean;
  toggleTheme: () => void;
  selectedLine: TransitLine | null;
  setSelectedLine: (line: TransitLine | null) => void;
  lines: TransitLine[];
  stops: TransitStop[];
  vehicles: Vehicle[];
  isLoading: boolean;
  showSplash: boolean;
  setShowSplash: (v: boolean) => void;
  detailItem: DetailItem;
  setDetailItem: (item: DetailItem) => void;
  closeDetail: () => void;
  mapFilters: Set<MapFilterKey>;
  toggleMapFilter: (key: MapFilterKey) => void;
  routeDestination: string | null;
  setRouteDestination: (dest: string | null) => void;
  targetLocation: { lat: number; lng: number } | null;
  setTargetLocation: (loc: { lat: number; lng: number } | null) => void;
  showKVKK: boolean;
  setShowKVKK: (v: boolean) => void;
  showCookie: boolean;
  setShowCookie: (v: boolean) => void;
}

const TransitContext = createContext<TransitContextType | null>(null);

export const useTransit = () => {
  const ctx = useContext(TransitContext);
  if (!ctx) throw new Error("useTransit must be inside TransitProvider");
  return ctx;
};

export const TransitProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTabRaw] = useState<TabId>("harita");
  const setActiveTab = useCallback((tab: TabId) => {
    setActiveTabRaw(tab);
    setSelectedLine(null);
    setDetailItem(null);
  }, []);
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("transit-theme") === "dark";
    }
    return false;
  });
  const [selectedLine, setSelectedLine] = useState<TransitLine | null>(null);

  // Real data states
  const [lines, setLines] = useState<TransitLine[]>([]);
  const [stops, setStops] = useState<TransitStop[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [showSplash, setShowSplash] = useState(true);
  const [detailItem, setDetailItem] = useState<DetailItem>(null);
  const [mapFilters, setMapFilters] = useState<Set<MapFilterKey>>(
    new Set(["buses", "trams", "ferries", "stops"])
  );
  const [routeDestination, setRouteDestination] = useState<string | null>(null);
  const [targetLocation, setTargetLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [showKVKK, setShowKVKK] = useState(false);
  const [showCookie, setShowCookie] = useState(false);

  const closeDetail = useCallback(() => {
    setDetailItem(null);
    setSelectedLine(null);
    setStops([]);
    setVehicles([]);
  }, []);

  const toggleMapFilter = useCallback((key: MapFilterKey) => {
    setMapFilters((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }, []);

  const toggleTheme = useCallback(() => {
    setIsDark((prev) => {
      const next = !prev;
      localStorage.setItem("transit-theme", next ? "dark" : "light");
      return next;
    });
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  // Fetch lines on app load
  useEffect(() => {
    const loadLines = async () => {
      setIsLoading(true);
      const data = await fetchAllLines();
      if (data && data.length > 0) {
        setLines(data);
      }
      setIsLoading(false);
    };
    loadLines();
  }, []);

  // Fetch stops and start polling vehicles when a line is selected
  useEffect(() => {
    if (selectedLine) {
      setDetailItem({ type: "line", data: selectedLine });

      // Load stops
      fetchLineStops(selectedLine.code, selectedLine.type).then(data => setStops(data));

      // Initial vehicles fetch
      fetchLineVehicles(selectedLine.code).then(data => setVehicles(data));

      // Poll vehicles globally for the selected line
      const interval = setInterval(async () => {
        const liveData = await fetchLineVehicles(selectedLine.code);
        setVehicles(liveData);
      }, 10000);

      return () => clearInterval(interval);
    } else {
      // Clear interval by return closure, also clear data if unselected
      setStops([]);
      setVehicles([]);
    }
  }, [selectedLine]);

  return (
    <TransitContext.Provider
      value={{
        activeTab,
        setActiveTab,
        isDark,
        toggleTheme,
        selectedLine,
        setSelectedLine,
        lines,
        stops,
        vehicles,
        isLoading,
        showSplash,
        setShowSplash,
        detailItem,
        setDetailItem,
        closeDetail,
        mapFilters,
        toggleMapFilter,
        routeDestination,
        setRouteDestination,
        targetLocation,
        setTargetLocation,
        showKVKK,
        setShowKVKK,
        showCookie,
        setShowCookie,
      }}
    >
      {children}
    </TransitContext.Provider>
  );
};