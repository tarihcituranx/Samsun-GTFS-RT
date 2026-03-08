import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useTransit } from "@/contexts/TransitContext";
import { useSettings } from "@/hooks/useSettings";

const SAMSUN_CENTER: [number, number] = [41.2867, 36.3300];
const DARK_TILES = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const LIGHT_TILES = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

const typeToFilter: Record<string, string> = {
  otobus: "buses", ekspres: "buses", samair: "buses", ring: "buses",
  tramvay: "trams", vapur: "ferries", teleferik: "trams",
};

const MapCanvas = () => {
  const { vehicles, stops, globalStops, lines, isDark, mapFilters, setDetailItem, setActiveTab, setTargetLocation, selectedLine } = useTransit();
  const { settings } = useSettings();
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const routeLayerRef = useRef<L.Polyline | null>(null);
  const vehicleMarkersRef = useRef<L.Marker[]>([]);
  const stopMarkersRef = useRef<L.Marker[]>([]);
  const [locationRetryVisible, setLocationRetryVisible] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: SAMSUN_CENTER,
      zoom: 13,
      zoomControl: false,
      attributionControl: false,
    });

    tileLayerRef.current = L.tileLayer(isDark ? DARK_TILES : LIGHT_TILES).addTo(map);
    mapRef.current = map;

    // Right-click context menu
    map.on("contextmenu", (e: L.LeafletMouseEvent) => {
      L.popup()
        .setLatLng(e.latlng)
        .setContent(
          `<button id="map-route-btn" style="padding:8px 16px;background:hsl(24,95%,53%);color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:13px">🧭 Buraya Nasıl Giderim?</button>`
        )
        .openOn(map);

      setTimeout(() => {
        const btn = document.getElementById("map-route-btn");
        if (btn) {
          btn.addEventListener("click", () => {
            map.closePopup();
            setTargetLocation({ lat: e.latlng.lat, lng: e.latlng.lng });
            setActiveTab("rota");
          });
        }
      }, 50);
    });

    // Try geolocation
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLocationRetryVisible(false);
          localStorage.setItem("userLoc", JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude }));
        },
        (err) => {
          if (err.code !== 1) setLocationRetryVisible(true);
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    }

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update tiles on theme change
  useEffect(() => {
    if (!mapRef.current || !tileLayerRef.current) return;
    tileLayerRef.current.setUrl(isDark ? DARK_TILES : LIGHT_TILES);
  }, [isDark]);

  // Stop markers
  useEffect(() => {
    if (!mapRef.current) return;
    stopMarkersRef.current.forEach((m) => m.remove());
    stopMarkersRef.current = [];
    if (!mapFilters.has("stops")) return;

    // Use line-specific stops if a line is selected. 
    // If no line is selected, only render global stops if settings.showAllStops is true
    let stopsToRender: any[] = [];
    if (selectedLine && stops.length > 0) {
      stopsToRender = stops;
    } else if (settings.showAllStops) {
      stopsToRender = globalStops;
    }

    stopsToRender.forEach((stop) => {
      // Different styling if it's a global generic stop vs line-specific stop
      const isGlobal = !stop.lines || stop.lines.length === 0;

      let htmlContent = "";
      if (isGlobal) {
        htmlContent = `<div style="width:12px;height:12px;background:#6366f1;border:2px solid white;border-radius:50%;box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>`;
      } else {
        htmlContent = `<div style="width:14px;height:14px;background:hsl(24,95%,53%);border:2.5px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>`;
      }

      const icon = L.divIcon({
        className: "",
        iconSize: isGlobal ? [12, 12] : [16, 16],
        iconAnchor: isGlobal ? [6, 6] : [8, 8],
        html: htmlContent,
      });

      const marker = L.marker([stop.lat, stop.lng], { icon }).addTo(mapRef.current!);
      marker.on("click", () => setDetailItem({ type: "stop", data: stop }));

      if (settings.showLabels && !isGlobal) {
        marker.bindTooltip(stop.name, {
          direction: 'top',
          offset: [0, -4],
          className: 'font-sora text-xs font-bold leading-none py-1 px-2 border-border shadow-md rounded-md',
          permanent: true,
          opacity: 0.9
        });
      }

      if (isGlobal) {
        marker.bindPopup(
          `<div style="font-family:'DM Sans',sans-serif;font-size:13px;">
            <b style="font-family:'Sora',sans-serif;">${stop.name}</b><br/>
            <div style="font-size:11px;color:#64748b;margin-top:2px;">${String(stop.id).includes('-') ? "Durak İçi" : `Kod: ${stop.id}`}</div>
          </div>`
        );
      } else {
        marker.bindPopup(
          `<div style="font-family:'DM Sans',sans-serif;font-size:13px;">
            <b style="font-family:'Sora',sans-serif;">${stop.name}</b><br/>
            <div style="margin-top:4px;">${stop.lines.map((l) => `<span style="background:#f9731618;color:#f97316;padding:1px 6px;border-radius:6px;font-size:11px;font-family:monospace;font-weight:600;margin-right:3px;">${l.code}: ${l.mins}dk</span>`).join("")}</div>
          </div>`
        );
      }

      stopMarkersRef.current.push(marker);
    });
  }, [mapFilters, stops, globalStops, selectedLine, setDetailItem]);

  // Vehicle markers
  useEffect(() => {
    if (!mapRef.current) return;
    vehicleMarkersRef.current.forEach((m) => m.remove());
    vehicleMarkersRef.current = [];

    vehicles.forEach((v) => {
      const line = lines.find((l) => l.code === v.line);
      if (!line) return;
      const filterKey = typeToFilter[line.type] || "buses";
      if (!mapFilters.has(filterKey as any)) return;

      const color = line.color;
      const icon = L.divIcon({
        className: "",
        iconSize: [48, 28],
        iconAnchor: [24, 14],
        html: `
          <div style="position:relative;display:flex;align-items:center;justify-content:center;">
            <div style="position:absolute;width:40px;height:40px;border-radius:50%;background:${color}30;animation:pulse-ring 1.5s ease-out infinite;top:-6px;left:4px;"></div>
            <div style="background:${color};color:white;font-family:'Sora',sans-serif;font-weight:700;font-size:11px;padding:4px 10px;border-radius:14px;box-shadow:0 2px 8px ${color}60;white-space:nowrap;position:relative;z-index:2;">
              ${v.line}
            </div>
          </div>
        `,
      });
      const marker = L.marker([v.lat, v.lng], { icon }).addTo(mapRef.current!);
      marker.on("click", () => setDetailItem({ type: "vehicle", data: v }));
      marker.bindPopup(
        `<div style="font-family:'DM Sans',sans-serif;font-size:13px;">
          <b style="font-family:'Sora',sans-serif;">${v.line} - ${v.plate}</b><br/>
          <span style="font-family:monospace;font-size:12px;">${Math.round(v.speed)} km/h</span><br/>
          <span style="font-size:11px;">${v.status === "active" ? "🟢 Çalışıyor" : v.status === "delayed" ? "🟡 Yavaş" : "🔴 Durdu"}</span>
        </div>`
      );
      vehicleMarkersRef.current.push(marker);
    });
  }, [vehicles, mapFilters, setDetailItem]);

  // Route drawing for Selected Line
  useEffect(() => {
    if (!mapRef.current) return;

    if (routeLayerRef.current) {
      routeLayerRef.current.remove();
      routeLayerRef.current = null;
    }

    if (!selectedLine || stops.length < 2 || !settings.showRoute) return;

    const drawRouteOSRM = async (coords: [number, number][], color: string) => {
      try {
        let pts = coords;
        if (pts.length > 25) {
          const step = Math.ceil(pts.length / 24);
          const sampled = [pts[0]];
          for (let i = step; i < pts.length - 1; i += step) sampled.push(pts[i]);
          sampled.push(pts[pts.length - 1]);
          pts = sampled;
        }
        const wp = pts.map(c => c[1] + ',' + c[0]).join(';');
        const res = await fetch(`https://router.project-osrm.org/route/v1/driving/${wp}?overview=full&geometries=geojson`);
        if (!res.ok) throw new Error("OSRM fetching failed");

        const data = await res.json();
        if (data.routes && data.routes[0]) {
          const geo = data.routes[0].geometry.coordinates.map((c: any) => [c[1], c[0]]);
          const pl = L.polyline(geo, { color: color, weight: 5, opacity: 0.8 }).addTo(mapRef.current!);
          routeLayerRef.current = pl;
          mapRef.current?.fitBounds(pl.getBounds(), { padding: [40, 40] });
        }
      } catch (e) {
        console.warn('OSRM route error, falling back to direct line:', e);
        const pl = L.polyline(coords, { color: color, weight: 5, opacity: 0.8, dashArray: '8,6' }).addTo(mapRef.current!);
        routeLayerRef.current = pl;
        mapRef.current?.fitBounds(pl.getBounds(), { padding: [40, 40] });
      }
    };

    const coords: [number, number][] = stops.filter(s => s.lat && s.lng).map(s => [s.lat, s.lng]);
    const isDirectLine = selectedLine.type === 'teleferik' || selectedLine.type === 'vapur';

    if (coords.length > 1) {
      if (isDirectLine) {
        const pl = L.polyline(coords, { color: selectedLine.color, weight: 5, opacity: 0.8, dashArray: '8,6' }).addTo(mapRef.current!);
        routeLayerRef.current = pl;
        mapRef.current?.fitBounds(pl.getBounds(), { padding: [40, 40] });
      } else {
        drawRouteOSRM(coords, selectedLine.color);
      }
    }

  }, [selectedLine, stops]);

  const requestLocation = () => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocationRetryVisible(false);
        localStorage.setItem("userLoc", JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude }));
        mapRef.current?.setView([pos.coords.latitude, pos.coords.longitude], 15);
      },
      () => { },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  return (
    <div className="fixed inset-0 z-0">
      <div ref={containerRef} className="h-full w-full" />
      {locationRetryVisible && (
        <button
          onClick={requestLocation}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 bg-blue-500 text-white px-6 py-3 rounded-xl font-bold text-sm shadow-lg animate-pulse md:bottom-12"
        >
          📍 Konumumu Bul
        </button>
      )}
    </div>
  );
};

export default MapCanvas;
