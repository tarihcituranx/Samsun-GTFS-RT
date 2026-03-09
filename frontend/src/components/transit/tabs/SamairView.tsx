import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Phone } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { fetchProxySamairSchedules, fetchProxySamairVehicles } from "@/lib/api";

interface SamairHat {
  id: number;
  kod: string;
  ad: string;
  kat: string;
}

interface SamairDurak {
  ad: string;
  lat: number;
  lon: number;
  fiyat?: number;
}

interface SeferItem {
  gun_format: string;
  saat: string;
  varis: string;
  firma: string;
  ucak_saat: string;
}

const normalizeCode = (v: any) => String(v || "").toUpperCase().replace(/\s+/g, "");

const filterSamairVehiclesByHat = (items: any[], hatKod: string): any[] => {
  const target = normalizeCode(hatKod);
  if (!target) return items;
  const filtered = items.filter((v) => {
    const lineCode = normalizeCode(v?.lineCode || v?.line || v?.HatKodu);
    return lineCode.includes(target);
  });
  return filtered.length > 0 ? filtered : items;
};

const SamairView = () => {
  const [hatlar, setHatlar] = useState<SamairHat[]>([]);
  const [selectedHat, setSelectedHat] = useState<SamairHat | null>(null);
  const [duraklar, setDuraklar] = useState<SamairDurak[]>([]);
  const [seferler, setSeferler] = useState<SeferItem[]>([]);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [araclar, setAraclar] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const fetchHatlar = async () => {
      try {
        const res = await fetch("/api/samair");
        if (!res.ok) throw new Error("Samair hatları yüklenemedi");
        const data = await res.json();
        setHatlar(Array.isArray(data) ? data : []);
      } catch (err: any) {
        toast({ title: "Hata", description: err.message, variant: "destructive" });
      } finally {
        setLoading(false);
      }
    };
    fetchHatlar();
  }, []);

  const selectHat = async (hat: SamairHat) => {
    setSelectedHat(hat);
    try {
      const [durakRes, seferRes, allSamairVehicles] = await Promise.all([
        fetch(`/api/samair/${hat.id}/durak`),
        fetchProxySamairSchedules(hat.id),
        fetchProxySamairVehicles(),
      ]);
      if (durakRes.ok) {
        const d = await durakRes.json();
        setDuraklar(d.data || (Array.isArray(d) ? d : []));
      }
      setSeferler(seferRes);
      setLastUpdate(null);
      setAraclar(filterSamairVehiclesByHat(allSamairVehicles, hat.kod));
    } catch (err: any) {
      toast({ title: "Hata", description: err.message, variant: "destructive" });
    }
  };

  // Auto refresh vehicles
  useEffect(() => {
    if (!selectedHat) return;
    const interval = setInterval(async () => {
      try {
        const allVehicles = await fetchProxySamairVehicles();
        setAraclar(filterSamairVehiclesByHat(allVehicles, selectedHat.kod));
      } catch {}
    }, 5000);
    return () => clearInterval(interval);
  }, [selectedHat]);

  if (selectedHat) {
    // Group seferler by day
    const grouped: Record<string, SeferItem[]> = {};
    seferler.forEach((s) => {
      if (!grouped[s.gun_format]) grouped[s.gun_format] = [];
      grouped[s.gun_format].push(s);
    });

    return (
      <div>
        <div className="flex items-center gap-3 mb-4">
          <button onClick={() => setSelectedHat(null)} className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-foreground">
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div className="flex-1 min-w-0">
            <h3 className="font-sora text-base font-bold text-foreground truncate">{selectedHat.ad}</h3>
            <p className="text-xs text-muted-foreground font-mono">{selectedHat.kod}</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="glass-panel rounded-xl p-3 text-center">
            <span className="font-mono font-bold text-lg text-foreground">{duraklar.length}</span>
            <p className="text-[10px] text-muted-foreground">Durak</p>
          </div>
          <div className="glass-panel rounded-xl p-3 text-center">
            <span className="font-mono font-bold text-lg" style={{ color: "#9333ea" }}>{araclar.length}</span>
            <p className="text-[10px] text-muted-foreground">Aktif Araç</p>
          </div>
          <div className="glass-panel rounded-xl p-3 text-center">
            <span className="font-mono font-bold text-lg text-foreground">{seferler.length}</span>
            <p className="text-[10px] text-muted-foreground">Sefer</p>
          </div>
        </div>

        {/* Vehicles */}
        {araclar.length > 0 && (
          <>
            <h4 className="font-sora text-sm font-semibold text-foreground mb-2">🚌 Canlı Araçlar</h4>
            <div className="flex flex-col gap-1.5 mb-4">
              {araclar.map((a: any, i: number) => (
                <div key={i} className="glass-panel flex items-center gap-3 rounded-xl px-3 py-2">
                  <span className="font-mono text-xs font-bold" style={{ color: "#9333ea" }}>{a.Plaka || a.plate || "?"}</span>
                  <div className="flex-1" />
                  <span className="font-mono text-xs text-muted-foreground">{parseFloat(String(a.Hizi || a.speed || 0)).toFixed(0)} km/h</span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Seferler */}
        {seferler.length > 0 && (
          <>
            <h4 className="font-sora text-sm font-semibold text-foreground mb-2">✈️ Uçuş & Servis Saatleri</h4>
            {lastUpdate && <p className="text-[10px] text-muted-foreground mb-2">Son Güncelleme: {lastUpdate}</p>}
            {Object.entries(grouped).map(([day, items]) => (
              <div key={day} className="mb-3">
                <p className="text-xs font-semibold text-foreground mb-1.5">{day}</p>
                <div className="flex flex-col gap-1.5">
                  {items.map((s, i) => (
                    <div key={i} className="glass-panel rounded-xl p-3 border-l-4" style={{ borderLeftColor: "#9333ea" }}>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm font-bold text-foreground">{s.saat}</span>
                        <span className="text-xs text-muted-foreground">{s.firma}</span>
                      </div>
                      <p className="text-xs text-foreground font-medium mt-0.5">{s.varis}</p>
                      <p className="text-[10px] text-muted-foreground">{s.ucak_saat}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </>
        )}

        {/* Stops */}
        <h4 className="font-sora text-sm font-semibold text-foreground mb-2 mt-4">📍 Duraklar</h4>
        <div className="flex flex-col">
          {duraklar.map((d, i) => (
            <div key={i} className="flex items-start gap-3 pb-1">
              <div className="flex flex-col items-center">
                <div className="h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold text-primary-foreground" style={{ backgroundColor: "#9333ea" }}>
                  {i + 1}
                </div>
                {i < duraklar.length - 1 && <div className="w-0.5 h-6" style={{ borderLeft: "2px dashed #9333ea40" }} />}
              </div>
              <div className="pb-2">
                <p className="text-sm font-medium text-foreground">{d.ad}</p>
                {d.fiyat != null && <p className="text-[10px] text-muted-foreground">₺{d.fiyat}</p>}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <img src="/static/images/samair.png" alt="Samair" className="h-16 rounded-xl shadow" onError={(e) => (e.currentTarget.style.display = "none")} />
        <div>
          <h2 className="font-sora text-xl font-bold text-foreground">Samair Seferleri</h2>
          <p className="text-xs text-muted-foreground">Havalimanı servis hatları</p>
        </div>
      </div>

      <a href="tel:03624311012" className="flex items-center gap-2 glass-panel rounded-xl px-4 py-2.5 mb-3 text-sm text-foreground">
        <Phone className="h-4 w-4 text-primary" />
        <span>📞 Bilgi: 0362 431 10 12</span>
      </a>

      <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-3 py-2 mb-4 text-xs text-amber-700 dark:text-amber-400">
        ⚠️ Test verileridir. Veriler her saat başı güncellenir.
      </div>

      {loading ? (
        <div className="flex flex-col gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-panel rounded-2xl p-4 animate-pulse">
              <div className="h-4 w-3/4 rounded bg-muted" />
              <div className="h-3 w-1/2 rounded bg-muted mt-2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {hatlar.map((hat) => (
            <motion.button
              key={hat.id}
              onClick={() => selectHat(hat)}
              whileTap={{ scale: 0.98 }}
              className="glass-panel rounded-xl p-3 text-left border-l-4" style={{ borderLeftColor: "#9333ea" }}
            >
              <p className="font-sora text-sm font-bold text-foreground">{hat.ad}</p>
              <p className="text-xs text-muted-foreground font-mono">{hat.kod}</p>
            </motion.button>
          ))}
          {hatlar.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">Henüz veri yok</p>}
        </div>
      )}
    </div>
  );
};

export default SamairView;
