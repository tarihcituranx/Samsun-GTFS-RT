import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowDownUp, Clock, Leaf } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";

const mockRoutes = [
  {
    label: "En Hızlı", duration: 35, fare: 24, transfers: 2, co2: 1.2,
    departure: "09:45", arrival: "10:20",
    steps: [
      { type: "walk", duration: 3, label: "Yürü", color: "" },
      { type: "bus", duration: 18, label: "E1", color: "#f97316" },
      { type: "walk", duration: 5, label: "Yürü", color: "" },
      { type: "bus", duration: 8, label: "19", color: "#0ea5e9" },
      { type: "walk", duration: 1, label: "Yürü", color: "" },
    ],
  },
  {
    label: "En Az Aktarma", duration: 42, fare: 24, transfers: 1, co2: 1.5,
    departure: "09:48", arrival: "10:30",
    steps: [
      { type: "walk", duration: 5, label: "Yürü", color: "" },
      { type: "bus", duration: 32, label: "19", color: "#0ea5e9" },
      { type: "walk", duration: 5, label: "Yürü", color: "" },
    ],
  },
  {
    label: "En Ucuz", duration: 50, fare: 18, transfers: 1, co2: 0.8,
    departure: "09:50", arrival: "10:40",
    steps: [
      { type: "walk", duration: 8, label: "Yürü", color: "" },
      { type: "tram", duration: 35, label: "T1", color: "#22c55e" },
      { type: "walk", duration: 7, label: "Yürü", color: "" },
    ],
  },
];

const RoutePlannerTab = () => {
  const { routeDestination, setRouteDestination, targetLocation, setTargetLocation } = useTransit();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [planned, setPlanned] = useState(false);
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

  const handlePlan = () => {
    if (from && to) setPlanned(true);
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
        />
      </div>

      <div className="mt-3 flex gap-2">
        <button className="flex-1 rounded-full bg-primary py-2.5 text-sm font-semibold text-primary-foreground" onClick={handlePlan}>
          Şimdi Hareket Et
        </button>
        <button className="flex items-center gap-1 rounded-full bg-accent px-4 py-2.5 text-sm font-medium text-foreground">
          <Clock className="h-4 w-4" /> Saat Seç
        </button>
      </div>

      <AnimatePresence>
        {planned && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex flex-col gap-3"
          >
            {mockRoutes.map((route, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass-panel rounded-2xl p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-sora text-sm font-bold text-foreground">{route.label}</span>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="font-mono font-bold text-primary">{route.duration} dk</span>
                    <span className="text-muted-foreground">₺{route.fare}</span>
                  </div>
                </div>

                <div className="flex items-center gap-1 overflow-x-auto pb-1">
                  {route.steps.map((step, j) => (
                    <div key={j} className="flex shrink-0 items-center gap-1">
                      {j > 0 && <span className="text-muted-foreground/50">→</span>}
                      {step.type === "walk" ? (
                        <span className="rounded-lg bg-accent px-2 py-1 text-xs text-muted-foreground">
                          🚶 {step.duration}dk
                        </span>
                      ) : (
                        <span
                          className="rounded-lg px-2 py-1 text-xs font-mono font-bold text-primary-foreground"
                          style={{ backgroundColor: step.color }}
                        >
                          {step.label}: {step.duration}dk
                        </span>
                      )}
                    </div>
                  ))}
                </div>

                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Kalkış: {route.departure} | Varış: {route.arrival} | {route.transfers} aktarma</span>
                  <span className="flex items-center gap-1 text-transit-green">
                    <Leaf className="h-3 w-3" /> -{route.co2}kg CO₂
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
