import { useTransit, type MapFilterKey } from "@/contexts/TransitContext";

const MAP_FILTERS: { key: MapFilterKey; label: string }[] = [
  { key: "buses", label: "🚌 Otobüsler" },
  { key: "trams", label: "🚃 Tramvaylar" },
  { key: "ferries", label: "⛴️ Vapurlar" },
  { key: "stops", label: "📍 Duraklar" },
];

const MapFilterPills = () => {
  const { mapFilters, toggleMapFilter } = useTransit();

  return (
    <div className="fixed top-[72px] left-4 right-4 z-40 flex gap-2 overflow-x-auto scrollbar-hide md:hidden">
      {MAP_FILTERS.map(({ key, label }) => {
        const isActive = mapFilters.has(key);
        return (
          <button
            key={key}
            onClick={() => toggleMapFilter(key)}
            aria-pressed={isActive}
            className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-200 backdrop-blur-md border ${
              isActive
                ? "bg-primary border-primary text-primary-foreground shadow-[0_0_12px_hsl(var(--transit-orange)/0.4)]"
                : "glass-panel border-border/30 text-foreground hover:border-primary/50"
            }`}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
};

export default MapFilterPills;
