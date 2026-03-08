import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Star, MapPin, Gauge } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";
import { type TransitLine, type TransitStop, type Vehicle } from "@/data/mockData";
import { lineStopNames } from "@/data/lineStops";
import { useEffect, useState } from "react";
import { getSpecialInfo } from "./SpecialBanners";
import { useSettings } from "@/hooks/useSettings";

/* ── Animated counter ──────────────────────────────────────────────────────── */
const AnimatedNumber = ({ value }: { value: number }) => {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = Math.ceil(value / 20);
    const interval = setInterval(() => {
      start += step;
      if (start >= value) { setDisplay(value); clearInterval(interval); } else { setDisplay(start); }
    }, 40);
    return () => clearInterval(interval);
  }, [value]);
  return <span className="font-mono font-bold text-2xl text-primary">{display}</span>;
};

/* ── Line Detail ───────────────────────────────────────────────────────────── */
const LineDetailContent = ({ line }: { line: TransitLine }) => {
  const { vehicles, closeDetail } = useTransit();
  const { settings } = useSettings();
  const lineVehicles = vehicles.filter((v) => v.line === line.code);

  const realStops = lineStopNames[line.code] || [];
  const stopCount = realStops.length > 0 ? realStops.length : Math.min(12, line.stops);

  const stops = Array.from({ length: stopCount }, (_, i) => ({
    name: realStops[i] || `Durak ${i + 1}`,
    eta: Math.round(Math.random() * 15 + 1),
    passed: i < 3,
    isNext: i === 3,
  }));

  const specialBanner = getSpecialInfo(line.name.toUpperCase());

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button onClick={closeDetail} className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-foreground" aria-label="Geri">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex h-12 w-12 items-center justify-center rounded-xl font-sora text-sm font-bold text-primary-foreground" style={{ backgroundColor: line.color }}>
          {line.code}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-sora text-base font-bold text-foreground truncate">{line.name}</h3>
        </div>
        <button className="text-muted-foreground" aria-label="Favori"><Star className="h-5 w-5" /></button>
      </div>

      {/* Special banners */}
      {specialBanner}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        {[
          { value: line.stops, label: "Durak" },
          { value: line.vehicles, label: "Araç 🟢" },
          { value: line.fare, label: "Ücret ₺" },
        ].map((s) => (
          <div key={s.label} className="glass-panel rounded-xl p-3 text-center">
            <AnimatedNumber value={s.value} />
            <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Vehicles */}
      <h4 className="font-sora text-sm font-semibold text-foreground mb-2">Aktif Araçlar</h4>
      <div className="flex flex-col gap-1.5 mb-4">
        {lineVehicles.map((v) => (
          <VehicleCard key={v.plate} vehicle={v} stops={realStops} showHasilat={settings.showHasilat} />
        ))}
        {lineVehicles.length === 0 && (
          <p className="text-xs text-muted-foreground my-2 italic">Aktif araç bulunamadı.</p>
        )}
      </div>

      {/* Timeline */}
      <h4 className="font-sora text-sm font-semibold text-foreground mb-2">Durak Sırası</h4>
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {stops.map((stop, i) => (
          <div key={i} className="flex items-start gap-3 pb-1">
            <div className="flex flex-col items-center">
              <div className={`h-3 w-3 rounded-full border-2 ${stop.passed ? "border-muted-foreground/40 bg-muted-foreground/40" : stop.isNext ? "border-primary bg-primary animate-pulse" : "border-border bg-card"}`} />
              {i < stops.length - 1 && <div className={`w-0.5 h-8 ${stop.passed ? "bg-muted-foreground/20" : "bg-border"}`} />}
            </div>
            <div className="pb-3">
              <p className={`text-sm ${stop.isNext ? "font-bold text-primary" : stop.passed ? "text-muted-foreground" : "text-foreground"}`}>{stop.name}</p>
              {!stop.passed && <p className="font-mono text-xs text-muted-foreground">{stop.eta} dk</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/* ── Enhanced Vehicle Card ─────────────────────────────────────────────────── */
const VehicleCard = ({ vehicle, stops, showHasilat }: { vehicle: Vehicle; stops: string[]; showHasilat: boolean }) => {
  // Mock extended data
  const yolcu = Math.floor(Math.random() * 60 + 10);
  const gunlukYolcu = Math.floor(Math.random() * 400 + 100);
  const maxHiz = Math.floor(vehicle.speed + Math.random() * 20 + 5);
  const mesafe = Math.floor(Math.random() * 80 + 10);
  const hasilat = Math.floor(Math.random() * 2000 + 500);

  // Find nearest stop
  const yakinIndex = Math.floor(Math.random() * Math.max(1, stops.length - 4)) + 2;
  const yakinDurak = stops[yakinIndex] || "";
  const sonaDurak = stops.length > 0 ? stops.length - (yakinIndex + 1) : 0;

  // Surrounding stops
  const surrounding = [];
  for (let i = Math.max(0, yakinIndex - 2); i <= Math.min(stops.length - 1, yakinIndex + 2); i++) {
    surrounding.push({ name: stops[i], isCurrent: i === yakinIndex, index: i });
  }

  const durum = vehicle.speed > 50 ? "normal" : vehicle.speed > 20 ? "dikkat" : "uyari";
  const durumIcon = durum === "normal" ? "🔹" : durum === "dikkat" ? "⚠️" : "🔶";

  return (
    <div className="glass-panel rounded-xl px-3 py-2.5">
      <div className="flex items-center justify-between mb-1">
        <span className="flex items-center gap-1.5">
          <span>{durumIcon}</span>
          <span className="font-mono text-xs font-semibold text-foreground">{vehicle.plate}</span>
        </span>
        {sonaDurak > 0 && (
          <span className="text-[10px] text-muted-foreground">🏁 Son durağa {sonaDurak} durak</span>
        )}
      </div>

      {yakinDurak && (
        <p className="text-[10px] text-muted-foreground mb-1.5">📍 {yakinDurak}</p>
      )}

      {/* Surrounding stops mini timeline */}
      {surrounding.length > 0 && (
        <div className="flex items-center gap-1 overflow-x-auto mb-1.5">
          {surrounding.map((s, i) => (
            <span
              key={i}
              className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] ${s.isCurrent
                  ? "bg-primary/15 text-primary font-bold"
                  : "text-muted-foreground"
                }`}
            >
              {s.isCurrent && "📍"}{s.name}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 flex-wrap text-[10px] text-muted-foreground">
        <span>👥 {yolcu} biniş</span>
        <span>📊 Gün:{gunlukYolcu}</span>
        <span>🏎 Max:{maxHiz}</span>
        <span>📏 {mesafe}km</span>
        <span className="font-mono font-bold text-foreground">{Math.round(vehicle.speed)} km/h</span>
        <span>{vehicle.status === "active" ? "🟢" : vehicle.status === "slow" ? "🟡" : "🔴"}</span>
      </div>

      {showHasilat && (
        <div className="mt-1 text-[10px] font-mono text-primary font-semibold">
          💰 ₺{hasilat.toLocaleString("tr-TR")}
        </div>
      )}
    </div>
  );
};

/* ── Stop Detail ───────────────────────────────────────────────────────────── */
const StopDetailContent = ({ stop }: { stop: TransitStop }) => {
  const { closeDetail, lines } = useTransit();
  const [pois, setPois] = useState<any[]>([]);

  useEffect(() => {
    const fetchPOIs = async () => {
      try {
        const res = await fetch(`/api/yakin_mekanlar?lat=${stop.lat}&lon=${stop.lng}&radius=1`);
        if (res.ok) {
          const data = await res.json();
          setPois(Array.isArray(data) ? data : []);
        }
      } catch { }
    };
    fetchPOIs();
  }, [stop.lat, stop.lng]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 mb-4">
        <button onClick={closeDetail} className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-foreground" aria-label="Geri">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <MapPin className="h-6 w-6 text-primary" />
        <div className="flex-1 min-w-0">
          <h3 className="font-sora text-base font-bold text-foreground truncate">{stop.name}</h3>
          <p className="text-xs text-muted-foreground font-mono">{stop.distance < 1000 ? `${stop.distance}m` : `${(stop.distance / 1000).toFixed(1)}km`} uzaklıkta</p>
        </div>
      </div>

      <h4 className="font-sora text-sm font-semibold text-foreground mb-2">Yaklaşan Araçlar</h4>
      <div className="flex flex-col gap-2">
        {stop.lines.map((line) => {
          const lineData = lines.find((l) => l.code === line.code);
          return (
            <div key={line.code} className="glass-panel rounded-xl p-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg font-sora text-xs font-bold text-primary-foreground" style={{ backgroundColor: lineData?.color || "hsl(var(--primary))" }}>
                {line.code}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{lineData?.name || line.code}</p>
              </div>
              <div className="text-right">
                <span className="font-mono text-lg font-bold text-primary">{line.mins}</span>
                <span className="text-xs text-muted-foreground ml-1">dk</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 glass-panel rounded-xl p-3">
        <p className="text-xs text-muted-foreground mb-1">Konum</p>
        <p className="font-mono text-xs text-foreground">{stop.lat.toFixed(4)}, {stop.lng.toFixed(4)}</p>
      </div>

      {/* Nearby POIs */}
      {pois.length > 0 && (
        <div className="mt-4">
          <h4 className="font-sora text-sm font-semibold text-foreground mb-2">🏛️ Yakındaki Turistik Mekanlar</h4>
          <div className="flex flex-col gap-2">
            {pois.map((poi: any) => (
              <div key={poi.id} className="glass-panel rounded-xl p-3 flex items-center gap-3">
                {poi.img && (
                  <img src={poi.img} alt={poi.title} className="h-12 w-12 rounded-lg object-cover" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }} />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{poi.title}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {poi.mesafe_m}m • {poi.cat} {poi.hours ? `• ${poi.hours}` : ""}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/* ── Vehicle Detail ────────────────────────────────────────────────────────── */
const VehicleDetailContent = ({ vehicle }: { vehicle: Vehicle }) => {
  const { closeDetail, lines } = useTransit();
  const lineData = lines.find((l) => l.code === vehicle.line);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 mb-4">
        <button onClick={closeDetail} className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-foreground" aria-label="Geri">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <Gauge className="h-6 w-6 text-primary" />
        <div className="flex-1 min-w-0">
          <h3 className="font-sora text-base font-bold text-foreground">{vehicle.plate}</h3>
          <p className="text-xs text-muted-foreground">Hat: {vehicle.line} — {lineData?.name || ""}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="glass-panel rounded-xl p-3 text-center">
          <span className="font-mono text-2xl font-bold text-primary">{Math.round(vehicle.speed)}</span>
          <p className="text-xs text-muted-foreground mt-1">km/h</p>
        </div>
        <div className="glass-panel rounded-xl p-3 text-center">
          <span className="text-2xl">{vehicle.status === "active" ? "🟢" : vehicle.status === "slow" ? "🟡" : "🔴"}</span>
          <p className="text-xs text-muted-foreground mt-1">
            {vehicle.status === "active" ? "Çalışıyor" : vehicle.status === "slow" ? "Yavaş" : "Durdu"}
          </p>
        </div>
      </div>

      <div className="glass-panel rounded-xl p-3 mb-4">
        <p className="text-xs text-muted-foreground mb-1">Konum</p>
        <p className="font-mono text-xs text-foreground">{vehicle.lat.toFixed(4)}, {vehicle.lng.toFixed(4)}</p>
        <p className="text-xs text-muted-foreground mt-2">Yön: {vehicle.heading}°</p>
      </div>

      {lineData && (
        <div className="glass-panel rounded-xl p-3">
          <p className="text-xs text-muted-foreground mb-1">Hat Bilgisi</p>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg font-sora text-xs font-bold text-primary-foreground" style={{ backgroundColor: lineData.color }}>
              {lineData.code}
            </div>
            <p className="text-sm font-medium text-foreground">{lineData.name}</p>
          </div>
        </div>
      )}
    </div>
  );
};

/* ── Main DetailPanel wrapper ──────────────────────────────────────────────── */
const DetailPanel = () => {
  const { detailItem } = useTransit();

  return (
    <AnimatePresence>
      {detailItem && (
        <motion.div
          key="detail-panel"
          initial={{ x: "100%", opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: "100%", opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="fixed right-0 top-0 z-30 hidden h-full w-[420px] overflow-y-auto glass-panel border-l border-border/30 p-5 pt-20 scrollbar-hide md:block"
        >
          {detailItem.type === "line" && <LineDetailContent line={detailItem.data} />}
          {detailItem.type === "stop" && <StopDetailContent stop={detailItem.data} />}
          {detailItem.type === "vehicle" && <VehicleDetailContent vehicle={detailItem.data} />}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default DetailPanel;
