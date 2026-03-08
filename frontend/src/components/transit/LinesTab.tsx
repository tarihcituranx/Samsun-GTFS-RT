import { Search, X } from "lucide-react";
import { motion } from "framer-motion";
import { lineTypeConfig, type TransitLine } from "@/data/mockData";
import { useTransit } from "@/contexts/TransitContext";
import { useState, useMemo, useRef } from "react";
import { SkeletonList } from "./Skeletons";

const typeOrder = ["all", "ekspres", "otobus", "ring", "tramvay", "teleferik", "odak", "samair"] as const;

type FilterKey = TransitLine["type"] | "all";

const filterLabels: Record<FilterKey, string> = {
  all: "Tümü",
  ekspres: "Ekspres",
  otobus: "Otobüs",
  tramvay: "Tramvay",
  ring: "Ring",
  vapur: "Vapur",
  odak: "Odak",
  teleferik: "Teleferik",
  samair: "Samair",
};

const LinesTab = () => {
  const { setDetailItem, lines: contextLines, isLoading } = useTransit();
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterKey>("all");
  const pillsRef = useRef<HTMLDivElement>(null);

  // Only show filters that have lines
  const availableFilters = useMemo(() => {
    const typesWithLines = new Set(contextLines.map((l) => l.type));
    return typeOrder.filter((t) => t === "all" || typesWithLines.has(t as TransitLine["type"]));
  }, [contextLines]);

  const filteredLines = useMemo(() => {
    let lines = contextLines;

    // Type filter
    if (activeFilter !== "all") {
      lines = lines.filter((l) => l.type === activeFilter);
    }

    // Search filter
    if (query.trim()) {
      const q = query.toLowerCase();
      lines = lines.filter(
        (l) =>
          l.code.toLowerCase().includes(q) ||
          l.name.toLowerCase().includes(q)
      );
    }

    return lines;
  }, [activeFilter, query]);

  return (
    <div className="flex flex-col h-full min-h-0">
      <h2 className="font-sora text-xl font-bold text-foreground mb-3 shrink-0">Hatlar</h2>

      {/* Search */}
      <div className="relative mb-3 shrink-0">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Hat kodu veya adı ara..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full glass-panel rounded-xl pl-9 pr-9 py-2.5 text-sm font-dm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/30"
        />
        {query && (
          <button onClick={() => setQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Filter pills — horizontal scroll */}
      <div
        ref={pillsRef}
        className="flex gap-2 overflow-x-auto scrollbar-hide mb-3 shrink-0 pb-1"
      >
        {availableFilters.map((key) => {
          const isActive = activeFilter === key;
          const config = key !== "all" ? lineTypeConfig[key] : null;
          return (
            <button
              key={key}
              onClick={() => setActiveFilter(key as FilterKey)}
              className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-200 backdrop-blur-md border whitespace-nowrap ${isActive
                  ? "bg-primary border-primary text-primary-foreground shadow-[0_0_12px_hsl(var(--transit-orange)/0.4)]"
                  : "glass-panel border-border/30 text-foreground hover:border-primary/50"
                }`}
            >
              {config ? `${config.emoji} ` : ""}{filterLabels[key as FilterKey]}
            </button>
          );
        })}
      </div>

      {/* Line list */}
      {isLoading ? (
        <SkeletonList count={8} />
      ) : (
        <div className="flex flex-col gap-1 overflow-y-auto scrollbar-hide flex-1 min-h-0 pb-4">
          {filteredLines.map((line, i) => (
            <motion.button
              key={line.code}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.02, duration: 0.2 }}
              onClick={() => setDetailItem({ type: "line", data: line })}
              className="flex items-center gap-3 rounded-xl p-2.5 text-left transition-all hover:bg-accent/50 active:scale-[0.98] glass-panel"
            >
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg font-sora text-xs font-bold text-primary-foreground"
                style={{ backgroundColor: line.color }}
              >
                {line.code}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{line.name}</p>
                <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-transit-green" />
                    {line.vehicles} araç
                  </span>
                  <span>₺{line.fare}</span>
                  <span>{line.stops} durak</span>
                </div>
              </div>
              <span className="text-muted-foreground text-xs">→</span>
            </motion.button>
          ))}

          {filteredLines.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">
              Eşleşen hat bulunamadı
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default LinesTab;
