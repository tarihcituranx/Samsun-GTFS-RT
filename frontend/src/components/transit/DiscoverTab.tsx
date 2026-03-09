import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTransit } from "@/contexts/TransitContext";
import { fetchPlaces } from "@/lib/api";

const DiscoverTab = () => {
  const { setActiveTab, setRouteDestination } = useTransit();
  const [cat, setCat] = useState("all");
  const [places, setPlaces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlace, setSelectedPlace] = useState<any | null>(null);

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

  const handleGoWithTransit = (lat: number, lon: number, title: string) => {
    setRouteDestination(`${lat},${lon}`); // Passing coords as string
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

  if (selectedPlace) {
    return (
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="flex flex-col space-y-4"
      >
        <button
          onClick={() => setSelectedPlace(null)}
          className="self-start rounded-full bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition-colors hover:bg-accent/80"
        >
          ← Geri
        </button>

        <div className="overflow-hidden rounded-2xl bg-card shadow-sm border">
          {selectedPlace.img && (
            <img
              src={selectedPlace.img}
              alt={selectedPlace.title}
              className="h-48 w-full object-cover"
              onError={(e) => { (e.target as HTMLImageElement).src = '/static/images/placeholder.png'; }}
            />
          )}
          <div className="p-4">
            <h2 className="font-sora text-xl font-bold">{selectedPlace.title}</h2>
            <div className="mt-2 inline-block rounded-md bg-primary/10 px-2 py-1 text-xs font-semibold text-primary">
              {selectedPlace.cat}
            </div>
            <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
              {selectedPlace.desc}
            </p>

            <div className="mt-4 flex gap-4">
              <div className="flex flex-col items-center justify-center rounded-xl bg-accent p-3 flex-1">
                <span className="text-xl mb-1">🕐</span>
                <span className="text-xs font-medium text-center">{selectedPlace.hours || "Bilinmiyor"}</span>
              </div>
              {selectedPlace.sections && (
                <div className="flex flex-col items-center justify-center rounded-xl bg-accent p-3 flex-1">
                  <span className="text-xl font-bold mb-1">{selectedPlace.sections}</span>
                  <span className="text-xs font-medium">Bölüm</span>
                </div>
              )}
            </div>

            {selectedPlace.audio?.tr && (
              <div className="mt-5">
                <h3 className="mb-2 text-sm font-semibold flex items-center gap-2">
                  <span>🔊</span> Sesli Anlatım
                </h3>
                <audio controls className="w-full h-10" preload="none">
                  <source src={selectedPlace.audio.tr} type="audio/mpeg" />
                  Tarayıcınız ses oynatmayı desteklemiyor.
                </audio>
              </div>
            )}

            <button
              onClick={() => handleGoWithTransit(selectedPlace.lat, selectedPlace.lon, selectedPlace.title)}
              className="mt-6 w-full rounded-xl bg-primary py-3 text-sm font-bold text-primary-foreground transition-colors hover:bg-primary/90 flex items-center justify-center gap-2"
            >
              🗺️ İstikamet: Oraya Git
            </button>

            {selectedPlace.url && (
              <a
                href={selectedPlace.url}
                target="_blank"
                rel="noreferrer"
                className="mt-3 block w-full rounded-xl border border-border py-3 text-center text-sm font-semibold text-foreground transition-colors hover:bg-accent flex items-center justify-center gap-2"
              >
                🏛️ samsunkesfet.com'da Görüntüle
              </a>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

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
                onClick={() => setSelectedPlace(place)}
                className={`group relative break-inside-avoid overflow-hidden rounded-2xl bg-gradient-to-br ${getGradientForIndex(i)} p-4 text-white shadow-md cursor-pointer ${i % 3 === 0 ? "min-h-[180px]" : "min-h-[140px]"
                  }`}
              >
                {/* Optional background image overlay if image exists */}
                {place.img && (
                  <div
                    className="absolute inset-0 opacity-20 mix-blend-overlay transition-opacity duration-500 group-hover:opacity-40"
                    style={{ backgroundImage: `url(${place.img})`, backgroundSize: 'cover', backgroundPosition: 'center' }}
                  />
                )}

                <div className="relative z-10 pointer-events-none">
                  <span className="text-3xl drop-shadow-sm">{getEmojiForCat(place.cat)}</span>
                  <h3 className="mt-2 font-sora text-sm font-bold leading-tight drop-shadow-sm">{place.title}</h3>
                  <p className="mt-1 text-xs opacity-90 line-clamp-2 drop-shadow-sm">{place.desc}</p>
                  <div className="mt-3 inline-block rounded-full bg-black/20 px-3 py-1.5 text-[11px] font-semibold backdrop-blur-md">
                    Detayları gör →
                  </div>
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
