import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowDownUp, Clock, Leaf } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";
import { fetchRoute } from "@/lib/api";

const RoutePlannerTab = () => {
  const { routeDestination, setRouteDestination, targetLocation, setTargetLocation, plannedRoutes, setPlannedRoutes } = useTransit();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [planned, setPlanned] = useState(false);
  const [loading, setLoading] = useState(false);
  const [swapped, setSwapped] = useState(false);

  // Auto-fill destination from Discover tab
  useEffect(() => {
    if (routeDestination) {
      setTo(routeDestination);
      setRouteDestination(null);
    }
  }, [routeDestination, setRouteDestination]);

  // Auto-fill from map right-click
  useEffect(() => {
    if (targetLocation) {
      setTo(`${targetLocation.lat.toFixed(4)}, ${targetLocation.lng.toFixed(4)}`);
      setTargetLocation(null);
    }
  }, [targetLocation, setTargetLocation]);

  const handleSwap = () => {
    setFrom(to);
    setTo(from);
    setSwapped(!swapped);
  };

  const handlePlan = async () => {
    if (!from && !to) return;
    setLoading(true);
    setPlanned(true);
    setPlannedRoutes([]);

    // Parse coordinates if they are in "lat, lon" format
    let params: any = {};
    if (from.includes(',')) {
      const [lat, lon] = from.split(',').map(s => parseFloat(s.trim()));
      params.lat1 = lat; params.lon1 = lon;
    } else {
      params.start = from;
    }

    if (to.includes(',')) {
      const [lat, lon] = to.split(',').map(s => parseFloat(s.trim()));
      params.lat2 = lat; params.lon2 = lon;
    } else {
      params.end = to;
    }

    const fetchedRoutes = await fetchRoute(params);
    setPlannedRoutes(fetchedRoutes);
    setLoading(false);
  };

  return (
    <div>
      <h2 className="font-sora text-xl font-bold text-foreground mb-3">Rota Planlayıcı</h2>

      <div className="relative flex flex-col gap-2">
        <input
          type="text"
          placeholder="Nereden?"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
          className="glass-panel rounded-2xl px-4 py-3 text-sm font-dm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/30"
          onKeyDown={(e) => e.key === 'Enter' && handlePlan()}
        />
        <motion.button
          onClick={handleSwap}
          animate={{ rotate: swapped ? 180 : 0 }}
          transition={{ type: "spring", stiffness: 300 }}
          className="absolute right-3 top-[38px] z-10 flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg"
          aria-label="Yer değiştir"
        >
          <ArrowDownUp className="h-4 w-4" />
        </motion.button>
        <input
          type="text"
          placeholder="Nereye?"
          value={to}
          onChange={(e) => setTo(e.target.value)}
          className="glass-panel rounded-2xl px-4 py-3 text-sm font-dm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/30"
          onKeyDown={(e) => e.key === 'Enter' && handlePlan()}
        />
      </div>

      <div className="mt-3 flex gap-2">
        <button
          className="flex-1 rounded-full bg-primary py-2.5 text-sm font-semibold text-primary-foreground disabled:opacity-50"
          onClick={handlePlan}
          disabled={loading || (!from && !to)}
        >
          {loading ? "Planlanıyor..." : "Şimdi Hareket Et"}
        </button>
        <button className="flex items-center gap-1 rounded-full bg-accent px-4 py-2.5 text-sm font-medium text-foreground">
          <Clock className="h-4 w-4" /> Saat Seç
        </button>
      </div>

      <AnimatePresence>
        {planned && !loading && plannedRoutes.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 text-center text-sm text-muted-foreground">
            Uygun rota bulunamadı. Lütfen varış noktalarını kontrol edin.
          </motion.div>
        )}

        {planned && loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8 flex justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </motion.div>
        )}

        {planned && !loading && plannedRoutes.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex flex-col gap-3 pb-24"
          >
            {plannedRoutes.map((route: any, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass-panel rounded-2xl p-4 overflow-hidden relative group"
              >
                {/* Glow effect on best route */}
                {i === 0 && <div className="absolute inset-0 bg-primary/5 shadow-[inset_0_0_20px_0_hsl(var(--primary)/20)] pointer-events-none" />}

                <div className="flex items-center justify-between mb-2 relative z-10">
                  <span className="font-sora text-sm font-bold text-foreground">
                    {route.label || (route.type === "DIRECT" ? "Direkt" : "Aktarmalı")} {i === 0 && '✨'}
                  </span>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="font-mono font-bold text-primary">{route.duration} dk</span>
                    <span className="text-muted-foreground">₺{route.fare}</span>
                  </div>
                </div>

                <div className="flex items-center gap-1 overflow-x-auto pb-2 scrollbar-hide relative z-10">
                  {route.steps?.map((step: any, j: number) => (
                    <div key={j} className="flex shrink-0 items-center gap-1">
                      {j > 0 && <span className="text-muted-foreground/50">→</span>}
                      {step.type === "walk" ? (
                        <span className="rounded-lg bg-accent px-2 py-1 text-xs text-muted-foreground">
                          🚶 {step.duration}dk
                        </span>
                      ) : (
                        <span
                          className="rounded-lg px-2 py-1 text-xs font-mono font-bold text-white whitespace-nowrap"
                          style={{ backgroundColor: step.color }}
                        >
                          {step.label}: {step.duration}dk
                        </span>
                      )}
                    </div>
                  ))}

                  {(!route.steps || route.steps.length === 0) && (
                    <span className="rounded-lg bg-accent px-2 py-1 text-xs text-muted-foreground">Rota Detayı Yok</span>
                  )}
                </div>

                <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground relative z-10">
                  <span>Kalkış: {route.departure} | Varış: {route.arrival} | {route.transfers} aktarma</span>
                  <span className="flex items-center gap-[2px] text-transit-green font-medium">
                    <Leaf className="h-[10px] w-[10px]" /> -{route.co2}kg CO₂
                  </span>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RoutePlannerTab;
