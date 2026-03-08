import { motion } from "framer-motion";
import { ArrowLeft, Star } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";
import { mockVehicles } from "@/data/mockData";
import { useEffect, useState } from "react";

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
  const { selectedLine, setSelectedLine, vehicles } = useTransit();
  if (!selectedLine) return null;

  const lineVehicles = vehicles.filter((v) => v.line === selectedLine.code);

  const stops = Array.from({ length: Math.min(12, selectedLine.stops) }, (_, i) => ({
    name: `Durak ${i + 1}`,
    eta: Math.round(Math.random() * 15 + 1),
    passed: i < 3,
    isNext: i === 3,
  }));

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
        <button className="text-muted-foreground" aria-label="Favori">
          <Star className="h-5 w-5" />
        </button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        {[
          { value: selectedLine.stops, label: "Durak" },
          { value: selectedLine.vehicles, label: "Araç 🟢" },
          { value: selectedLine.fare, label: "Ücret ₺" },
        ].map((stat) => (
          <div key={stat.label} className="glass-panel rounded-xl p-3 text-center">
            <AnimatedNumber value={stat.value} />
            <p className="text-xs text-muted-foreground mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Live vehicles */}
      <h4 className="font-sora text-sm font-semibold text-foreground mb-2">Aktif Araçlar</h4>
      <div className="flex flex-col gap-1.5 mb-4">
        {(lineVehicles.length > 0 ? lineVehicles : mockVehicles.slice(0, 3)).map((v) => (
          <div key={v.plate} className="glass-panel flex items-center gap-3 rounded-xl px-3 py-2">
            <span className="font-mono text-xs font-semibold text-foreground">{v.plate}</span>
            <div className="flex-1 h-1.5 rounded-full bg-accent overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${(v.speed / 80) * 100}%`,
                  backgroundColor: v.speed > 50 ? "#22c55e" : v.speed > 30 ? "#eab308" : "#ef4444",
                }}
              />
            </div>
            <span className="font-mono text-xs font-bold text-foreground">{Math.round(v.speed)} km/h</span>
            <span className="text-xs">
              {v.status === "active" ? "🟢" : v.status === "slow" ? "🟡" : "🔴"}
            </span>
          </div>
        ))}
      </div>

      {/* Stop timeline */}
      <h4 className="font-sora text-sm font-semibold text-foreground mb-2">Durak Sırası</h4>
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {stops.map((stop, i) => (
          <div key={i} className="flex items-start gap-3 pb-1">
            <div className="flex flex-col items-center">
              <div
                className={`h-3 w-3 rounded-full border-2 ${
                  stop.passed
                    ? "border-muted-foreground/40 bg-muted-foreground/40"
                    : stop.isNext
                    ? "border-primary bg-primary animate-pulse"
                    : "border-border bg-card"
                }`}
              />
              {i < stops.length - 1 && (
                <div className={`w-0.5 h-8 ${stop.passed ? "bg-muted-foreground/20" : "bg-border"}`} />
              )}
            </div>
            <div className="pb-3">
              <p className={`text-sm ${stop.isNext ? "font-bold text-primary" : stop.passed ? "text-muted-foreground" : "text-foreground"}`}>
                {stop.name}
              </p>
              {!stop.passed && (
                <p className="font-mono text-xs text-muted-foreground">{stop.eta} dk</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

export default LineDetail;
