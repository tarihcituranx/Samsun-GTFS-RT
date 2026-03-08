import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useTransit } from "@/contexts/TransitContext";
import { fetchPlaces } from "@/lib/api";

const DiscoverTab = () => {
  const { setActiveTab, setRouteDestination } = useTransit();
  const [cat, setCat] = useState("all");
  const [places, setPlaces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlaces().then(data => {
      setPlaces(data);
      setLoading(false);
    });
  }, []);

  // Extract unique categories from backend data dynamically
  const dynamicCategories = Array.from(new Set(places.map(p => p.cat))).filter(Boolean);
  const categories = [
    { id: "all", label: "Tümü" },
    ...dynamicCategories.map(c => ({ id: c, label: c }))
  ];

  const filtered = cat === "all" ? places : places.filter((p) => p.cat === cat);

  const handleGoWithTransit = (placeName: string) => {
    setRouteDestination(placeName);
    setActiveTab("rota");
  };

  const getEmojiForCat = (category: string) => {
    const lower = category?.toLowerCase() || '';
    if (lower.includes("tarih")) return "🏛️";
    if (lower.includes("müze")) return "🖼️";
    if (lower.includes("anıt")) return "🗽";
    if (lower.includes("doğa") || lower.includes("park")) return "🌲";
    if (lower.includes("yeme")) return "🍽️";
    if (lower.includes("alışveriş")) return "🛍️";
    return "📍";
  };

  const getGradientForIndex = (index: number) => {
    const gradients = [
      "from-orange-500 to-red-500",
      "from-blue-500 to-cyan-500",
      "from-emerald-500 to-teal-500",
      "from-purple-500 to-pink-500",
      "from-amber-500 to-orange-500"
    ];
    return gradients[index % gradients.length];
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

      {loading ? (
        <div className="flex justify-center p-8">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : (
        <>
          {/* Category pills */}
          <div className="scrollbar-hide -mx-4 flex gap-2 overflow-x-auto px-4 pb-3">
            {categories.map((c) => (
              <button
                key={c.id as string}
                onClick={() => setCat(c.id as string)}
                className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-all ${cat === c.id
                    ? "bg-primary text-primary-foreground"
                    : "bg-accent text-muted-foreground"
                  }`}
              >
                {c.label as string}
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
                className={`group relative break-inside-avoid overflow-hidden rounded-2xl bg-gradient-to-br ${getGradientForIndex(i)} p-4 text-white shadow-md ${i % 3 === 0 ? "min-h-[180px]" : "min-h-[140px]"
                  }`}
              >
                {/* Optional background image overlay if image exists */}
                {place.img && (
                  <div
                    className="absolute inset-0 opacity-20 mix-blend-overlay transition-opacity duration-500 group-hover:opacity-40"
                    style={{ backgroundImage: `url(${place.img})`, backgroundSize: 'cover', backgroundPosition: 'center' }}
                  />
                )}

                <div className="relative z-10">
                  <span className="text-3xl drop-shadow-sm">{getEmojiForCat(place.cat)}</span>
                  <h3 className="mt-2 font-sora text-sm font-bold leading-tight drop-shadow-sm">{place.title}</h3>
                  <p className="mt-1 text-xs opacity-90 line-clamp-2 drop-shadow-sm">{place.desc}</p>
                  <button
                    onClick={() => handleGoWithTransit(`${place.lat},${place.lon}`)}
                    className="mt-3 rounded-full bg-black/20 px-3 py-1.5 text-[11px] font-semibold backdrop-blur-md hover:bg-black/40 transition-colors"
                  >
                    Toplu taşımayla git →
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default DiscoverTab;
