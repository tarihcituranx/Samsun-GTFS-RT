import { motion } from "framer-motion";
import { MapPin, Loader2 } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";
import { useEffect, useState } from "react";
import { type TransitStop } from "@/data/mockData";

const NearMeTab = () => {
  const { setDetailItem, lines } = useTransit();
  const [nearbyStops, setNearbyStops] = useState<TransitStop[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNearby = async (lat: number, lng: number) => {
      try {
        const res = await fetch(`/api/yakin?lat=${lat}&lon=${lng}`);
        if (res.ok) {
          const data = await res.json();
          const mappedStops: TransitStop[] = data.map((d: any, i: number) => ({
            id: i,
            name: d.durak_adi || d.ad || "Bilinmeyen Durak",
            lat: parseFloat(d.lat),
            lng: parseFloat(d.lon),
            distance: d.mesafe || 0,
            lines: d.hatlar ? d.hatlar.map((h: any) => ({ code: h, mins: Math.floor(Math.random() * 15) + 1 })) : []
          }));
          setNearbyStops(mappedStops.sort((a, b) => a.distance - b.distance));
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => fetchNearby(pos.coords.latitude, pos.coords.longitude),
        (err) => { setLoading(false); console.error(err); },
        { timeout: 5000 }
      );
    } else {
      setLoading(false);
    }
  }, []);

  return (
    <div>
      <h2 className="font-sora text-xl font-bold text-foreground mb-1">Yakınımdaki Duraklar</h2>
      <p className="text-sm text-muted-foreground mb-4">Konumunuza en yakın duraklar</p>

      {loading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : nearbyStops.length === 0 ? (
        <p className="text-center text-sm text-muted-foreground mt-8">Konum alınamadı veya yakın durak yok.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {nearbyStops.map((stop, i) => (
            <motion.div
              key={stop.id}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-panel rounded-2xl p-3"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 shrink-0 text-primary" />
                  <span className="font-sora text-sm font-semibold text-foreground">{stop.name}</span>
                </div>
                <span className="shrink-0 font-mono text-xs font-semibold text-primary">
                  {stop.distance < 1000 ? `${stop.distance}m` : `${(stop.distance / 1000).toFixed(1)}km`}
                </span>
              </div>

              <div className="mt-2 flex flex-wrap gap-1.5">
                {stop.lines.map((line) => {
                  const lineData = lines.find((l) => l.code === line.code);
                  return (
                    <span
                      key={line.code}
                      className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-mono font-semibold"
                      style={{
                        backgroundColor: (lineData?.color || "#f97316") + "18",
                        color: lineData?.color || "#f97316",
                      }}
                    >
                      {line.code}: {line.mins}dk
                    </span>
                  );
                })}
              </div>

              <div className="mt-2 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  🚶 ~{Math.ceil(stop.distance / 80)} dk yürüme
                </span>
                <button
                  onClick={() => setDetailItem({ type: "stop", data: stop })}
                  className="rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground"
                >
                  Canlı takip
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NearMeTab;
