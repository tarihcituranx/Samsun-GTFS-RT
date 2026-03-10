import { motion } from "framer-motion";
import { ArrowLeft, Star, ArrowRightLeft } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";
import { useEffect, useState } from "react";
import { getSpecialInfo } from "./SpecialBanners";
import { useSettings } from "@/hooks/useSettings";
import { fetchLineFullDetail, fetchHatYonler, fetchSchedules, fetchRealtimeRaw, fetchStopsStations, fetchLineDirections, type ScheduleItem } from "@/lib/api";

const AnimatedNumber = ({ value }: { value: number }) => {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = Math.ceil(value / 20);
    const interval = setInterval(() => {
      start += step;
      if (start >= value) {
        setDisplay(value);
        clearInterval(interval);
      } else {
        setDisplay(start);
      }
    }, 40);
    return () => clearInterval(interval);
  }, [value]);
  return <span className="font-mono font-bold text-2xl text-primary">{display}</span>;
};

const LineDetail = () => {
  const { selectedLine, setSelectedLine, vehicles, stops } = useTransit();
  const { settings } = useSettings();
  const [lineDetail, setLineDetail] = useState<any>({});
  const [showSefer, setShowSefer] = useState(false);
  const [yonler, setYonler] = useState<{ yon_id: string; yon_adi: string }[]>([]);
  const [activeYonIdx, setActiveYonIdx] = useState(0);   // ← hangi yön seçili
  const [officialSchedules, setOfficialSchedules] = useState<ScheduleItem[]>([]);
  const [showOfficial, setShowOfficial] = useState(false);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().split("T")[0]);
  // ASIS raw fallback state
  const [asisVehicles, setAsisVehicles] = useState<any[]>([]);
  const [asisStops, setAsisStops] = useState<any[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!selectedLine) return;
    setLineDetail({});
    setYonler([]);
    setOfficialSchedules([]);
    setShowSefer(false);
    setShowOfficial(false);
    setAsisVehicles([]);
    setAsisStops([]);
    setActiveYonIdx(0);
    setDetailLoading(true);

    Promise.allSettled([
      fetchLineFullDetail(selectedLine.code).then(setLineDetail),
      // fetchHatYonler önce DB'den çeker; 0 döndüğünde fetchLineDirections (ASIS) ile fallback
      fetchHatYonler(selectedLine.code).then((data) => {
        if (data.length > 0) {
          setYonler(data);
        } else {
          fetchLineDirections(selectedLine.code).then((dirs) => {
            setYonler(dirs.map((d: any) => ({
              yon_id: String(d.directionId ?? d.yon_id ?? ""),
              yon_adi: d.directionName ?? d.yon_adi ?? "",
            })));
          });
        }
      }),
    ]).finally(() => setDetailLoading(false));

    // ASIS raw araç: context vehicles boşsa fallback
    fetchRealtimeRaw(selectedLine.code).then(setAsisVehicles);
    // ASIS raw duraklar: stops boşsa fallback
    fetchStopsStations(selectedLine.code).then(setAsisStops);
  }, [selectedLine?.code]);

  if (!selectedLine) return null;

  // Real vehicles from API
  const lineVehicles = vehicles.filter((v) => v.line === selectedLine.code);

  const tamFiyat = lineDetail.fiyat?.tam_fiyat ?? selectedLine.fare ?? 0;
  const indFiyat = lineDetail.fiyat?.indirimli_fiyat;
  const eslesCode = lineDetail.esles?.code;
  const sefer: any[] = Array.isArray(lineDetail.sefer) ? lineDetail.sefer : [];
  const safeName = String(selectedLine.name || "").toLowerCase();
  const isGidis = safeName.includes("gidiş") || !safeName.includes("dönüş");

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={() => setSelectedLine(null)}
          className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-foreground"
          aria-label="Geri"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div
          className="flex h-12 w-12 items-center justify-center rounded-xl font-sora text-sm font-bold text-primary-foreground"
          style={{ backgroundColor: selectedLine.color }}
        >
          {selectedLine.code}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-sora text-base font-bold text-foreground truncate">{selectedLine.name}</h3>
        </div>
        {/* Gidiş/Dönüş button from real API */}
        {yonler.length > 1 && (
          <div className="flex gap-1">
            {yonler.map((y, idx) => (
              <button
                key={y.yon_id}
                onClick={() => {
                  setActiveYonIdx(idx);
                  setSelectedLine({ ...selectedLine, name: y.yon_adi });
                }}
                className={`flex items-center gap-1 rounded-xl px-2 py-1 text-xs font-semibold border transition-colors ${activeYonIdx === idx ? "bg-primary text-primary-foreground border-primary" : "bg-primary/10 border-primary/20 text-primary"}`}
              >
                <ArrowRightLeft className="h-3 w-3" /> {y.yon_adi}
              </button>
            ))}
          </div>
        )}
        {/* Fallback: esles-based switching when no yonler */}
        {yonler.length <= 1 && eslesCode && (
          <button
            onClick={() => setSelectedLine({ ...selectedLine, code: eslesCode })}
            className="flex items-center gap-1 rounded-xl bg-primary/10 border border-primary/20 px-2 py-1 text-xs font-semibold text-primary"
            title={isGidis ? "Dönüş hattına geç" : "Gidiş hattına geç"}
          >
            <ArrowRightLeft className="h-3 w-3" />
            {isGidis ? "Dönüş" : "Gidiş"}
          </button>
        )}
        <button className="text-muted-foreground" aria-label="Favori">
          <Star className="h-5 w-5" />
        </button>
      </div>

      {/* Special Line Details (Alerts, Timetables) */}
      {getSpecialInfo(selectedLine)}

      {/* Stats grid */}
      {detailLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin text-2xl mr-3">🔄</div>
          <span className="text-sm text-muted-foreground font-medium">Hat bilgileri yükleniyor...</span>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-2 mb-4">
          {[
            { value: stops.length || selectedLine.stops, label: "Durak" },
            { value: lineVehicles.length || selectedLine.vehicles, label: "Araç 🟢" },
            { value: Math.round(tamFiyat), label: "Tam ₺" },
          ].map((stat) => (
            <div key={stat.label} className="glass-panel rounded-xl p-3 text-center">
              <AnimatedNumber value={stat.value} />
              <p className="text-xs text-muted-foreground mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Fiyat detail */}
      {tamFiyat > 0 && (
        <div className="glass-panel rounded-xl p-3 mb-3 flex items-center gap-4 text-sm">
          <div>
            <span className="text-xs text-muted-foreground">Tam</span>
            <p className="font-mono font-bold text-foreground">₺{tamFiyat.toFixed(2)}</p>
          </div>
          {indFiyat && (
            <div>
              <span className="text-xs text-muted-foreground">İndirimli</span>
              <p className="font-mono font-bold text-foreground">₺{indFiyat.toFixed(2)}</p>
            </div>
          )}
        </div>
      )}

      {/* Sefer (Basit) toggle */}
      {sefer.length > 0 && (
        <div className="mb-3">
          <button
            onClick={() => setShowSefer((v) => !v)}
            className="w-full glass-panel rounded-xl px-4 py-2 text-sm font-semibold text-foreground text-left flex items-center justify-between"
          >
            <span>🕐 Sefer Saatleri ({sefer.length})</span>
            <span className="text-muted-foreground">{showSefer ? "▲" : "▼"}</span>
          </button>
          {showSefer && (
            <div className="mt-1 glass-panel rounded-xl p-3 max-h-48 overflow-y-auto scrollbar-hide">
              {sefer.map((s: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-1 border-b border-border/40 last:border-0 text-sm">
                  <span className="font-mono text-foreground">{s.saat || s.departure || s.time || JSON.stringify(s)}</span>
                  {s.gun && <span className="text-xs text-muted-foreground">{s.gun}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Resmi Tarife (proxy/schedules) */}
      <div className="mb-3">
        <button
          onClick={async () => {
            if (!showOfficial && officialSchedules.length === 0) {
              setScheduleLoading(true);
              const data = await fetchSchedules(selectedLine.code, selectedDate);
              setOfficialSchedules(data);
              setScheduleLoading(false);
            }
            setShowOfficial((v) => !v);
          }}
          className="w-full glass-panel rounded-xl px-4 py-2 text-sm font-semibold text-foreground text-left flex items-center justify-between"
        >
          <span>📅 Resmi Tarife {scheduleLoading ? "⏳" : `(${officialSchedules.length || "?"})`}</span>
          <span className="text-muted-foreground">{showOfficial ? "▲" : "▼"}</span>
        </button>
        {showOfficial && (
          <div className="mt-1 glass-panel rounded-xl p-3">
            {/* Date picker */}
            <input
              type="date"
              value={selectedDate}
              onChange={async (e) => {
                setSelectedDate(e.target.value);
                setScheduleLoading(true);
                const data = await fetchSchedules(selectedLine.code, e.target.value);
                setOfficialSchedules(data);
                setScheduleLoading(false);
              }}
              className="w-full mb-2 rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/30"
            />
            {scheduleLoading ? (
              <div className="flex justify-center py-3"><span className="animate-spin text-lg">⏳</span></div>
            ) : officialSchedules.length > 0 ? (
              <div className="max-h-52 overflow-y-auto scrollbar-hide">
                {/* Group by yon */}
                {Array.from(new Set(officialSchedules.map((s) => s.yon || "Tümü"))).map((yon) => (
                  <div key={yon} className="mb-3">
                    <p className="text-xs font-semibold text-primary mb-1 sticky top-0 bg-card/80 py-0.5">🚌 {yon}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {officialSchedules
                        .filter((s) => (s.yon || "Tümü") === yon)
                        .map((s, i) => (
                          <span key={i} className="font-mono text-xs bg-accent rounded-lg px-2 py-1 text-foreground">
                            {s.saat || s.departureTime || "—"}
                          </span>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground text-center py-2">Tarife bulunamadı</p>
            )}
          </div>
        )}
      </div>

      {/* Live vehicles — context > ASIS raw */}
      <h4 className="font-sora text-sm font-semibold text-foreground mb-2">Aktif Araçlar</h4>
      <div className="flex flex-col gap-1.5 mb-4">
        {lineVehicles.length > 0 ? (
          lineVehicles.map((v) => (
            <div key={v.plate} className="glass-panel flex items-center gap-3 rounded-xl px-3 py-2">
              <span className="font-mono text-xs font-semibold text-foreground">{v.plate}</span>
              <div className="flex-1 h-1.5 rounded-full bg-accent overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${(v.speed / 80) * 100}%`, backgroundColor: v.speed > 50 ? "#22c55e" : v.speed > 30 ? "#eab308" : "#ef4444" }} />
              </div>
              <span className="font-mono text-xs font-bold text-foreground">{Math.round(v.speed)} km/h</span>
              <span className="text-xs mr-2">{v.status === "active" ? "🟢" : v.status === "delayed" ? "🟡" : "🔴"}</span>
              {settings.showHasilat && v.hasilat && (
                <span className="text-[10px] bg-green-500/10 text-green-600 dark:text-green-400 font-bold px-1.5 py-0.5 rounded border border-green-500/20 whitespace-nowrap">{v.hasilat} ₺</span>
              )}
            </div>
          ))
        ) : asisVehicles.length > 0 ? (
          // ASIS raw fallback
          asisVehicles.slice(0, 6).map((v: any, i: number) => (
            <div key={v.vehicleId ?? v.plate ?? i} className="glass-panel flex items-center gap-3 rounded-xl px-3 py-2">
              <span className="font-mono text-xs font-semibold text-foreground">{v.plate ?? v.vehiclePlate ?? v.vehicleId ?? "—"}</span>
              <div className="flex-1 min-w-0">
                {v.lat && v.lon ? (
                  <p className="text-[10px] text-muted-foreground font-mono">{Number(v.lat).toFixed(4)}, {Number(v.lon).toFixed(4)}</p>
                ) : <div className="h-1.5 rounded-full bg-accent/40 w-full" />}
              </div>
              <span className="font-mono text-xs font-bold text-foreground">{v.speed ? `${Math.round(v.speed)} km/h` : "ASIS"}</span>
              <span className="text-xs">🟢</span>
            </div>
          ))
        ) : (
          <p className="text-xs text-muted-foreground text-center py-2">Canlı araç verisi bulunamadı.</p>
        )}
      </div>

      {/* Stop timeline — context > ASIS raw */}
      <h4 className="font-sora text-sm font-semibold text-foreground mb-2">Durak Sırası</h4>
      <div className="flex-1 overflow-y-auto scrollbar-hide bg-card/50 rounded-xl p-3 border border-border">
        {(() => {
          const displayStops = stops.length > 0
            ? stops
            : asisStops.map((s: any, i: number) => ({
              id: s.stopId ?? s.stationId ?? i,
              name: s.stopName ?? s.stationName ?? s.name ?? `Durak ${i + 1}`,
              lat: s.lat ?? s.latitude ?? 0,
              lng: s.lng ?? s.longitude ?? 0,
            }));

          if (displayStops.length === 0) return (
            <p className="text-xs text-muted-foreground text-center py-4">Durak bilgisi yükleniyor…</p>
          );

          return displayStops.map((stop: any, i: number) => {
            const vehicleNear = lineVehicles.find(v => v.yakin && (stop.name.includes(v.yakin) || v.yakin.includes(stop.name)));
            return (
              <div key={stop.id || i} className="flex items-start gap-3 pb-1">
                <div className="flex flex-col items-center">
                  <div className={`h-4 w-4 rounded-full border-[3px] shadow-sm ${vehicleNear ? "border-primary bg-primary animate-pulse" : "border-border bg-card"}`} />
                  {i < displayStops.length - 1 && <div className="w-0.5 h-8 bg-border" />}
                </div>
                <div className="pb-3 flex-1">
                  <p className={`text-sm ${vehicleNear ? "font-bold text-primary" : "text-foreground font-medium"} leading-tight`}>
                    {stop.name}
                  </p>
                  {vehicleNear && (
                    <div className="mt-1 flex items-center gap-2">
                      <span className="bg-primary/10 text-primary px-2 py-0.5 rounded-md text-xs font-bold border border-primary/20">
                        🚌 {vehicleNear.plate}
                      </span>
                      <span className="text-xs text-muted-foreground font-mono">{vehicleNear.speed} km/h</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        })()}
      </div>
    </motion.div>
  );
};

export default LineDetail;
