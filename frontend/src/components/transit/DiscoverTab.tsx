import { useState } from "react";
import { motion } from "framer-motion";
import { mockPlaces } from "@/data/mockData";
import { useTransit } from "@/contexts/TransitContext";

const categories = [
  { id: "all", label: "Tümü" },
  { id: "tarihi", label: "Tarihi Yerler" },
  { id: "doga", label: "Doğa" },
  { id: "yeme-icme", label: "Yeme-İçme" },
  { id: "etkinlik", label: "Etkinlikler" },
];

const DiscoverTab = () => {
  const { setActiveTab, setRouteDestination } = useTransit();
  const [cat, setCat] = useState("all");
  const filtered = cat === "all" ? mockPlaces : mockPlaces.filter((p) => p.category === cat);

  const handleGoWithTransit = (placeName: string) => {
    setRouteDestination(placeName);
    setActiveTab("rota");
  };

  return (
    <div>
      <h2 className="font-sora text-2xl font-bold mb-1">
        <span className="text-gradient-orange">Samsun'u Keşfet</span>
      </h2>
      <p className="text-sm text-muted-foreground mb-4">Şehrin en güzel noktalarını keşfedin</p>

      {/* Featured banner */}
      <div className="mb-4 overflow-hidden rounded-2xl bg-gradient-to-br from-primary via-transit-orange to-transit-yellow p-6 text-primary-foreground">
        <p className="font-sora text-lg font-bold">🌊 Karadeniz'in İncisi</p>
        <p className="mt-1 text-sm opacity-90">Samsun'un tarihi ve doğal güzelliklerini toplu taşımayla keşfedin</p>
      </div>

      {/* Category pills */}
      <div className="scrollbar-hide -mx-4 flex gap-2 overflow-x-auto px-4 pb-3">
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setCat(c.id)}
            className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-all ${
              cat === c.id
                ? "bg-primary text-primary-foreground"
                : "bg-accent text-muted-foreground"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Masonry grid */}
      <div className="mt-2 columns-2 gap-2 space-y-2">
        {filtered.map((place, i) => (
          <motion.div
            key={place.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.06 }}
            className={`break-inside-avoid overflow-hidden rounded-2xl bg-gradient-to-br ${place.gradient} p-4 text-primary-foreground ${
              i % 3 === 0 ? "min-h-[180px]" : "min-h-[140px]"
            }`}
          >
            <span className="text-3xl">{place.emoji}</span>
            <h3 className="mt-2 font-sora text-sm font-bold">{place.name}</h3>
            <p className="mt-1 text-xs opacity-80 line-clamp-2">{place.description}</p>
            <button
              onClick={() => handleGoWithTransit(place.name)}
              className="mt-3 rounded-full bg-primary-foreground/20 px-3 py-1 text-xs font-semibold backdrop-blur-sm hover:bg-primary-foreground/30 transition-colors"
            >
              Toplu taşımayla git →
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default DiscoverTab;
