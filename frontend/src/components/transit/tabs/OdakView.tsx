import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Phone } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface OdakHat {
  id: number;
  kod: string;
  ad: string;
  kat: string;
}

interface OdakDurak {
  ad: string;
  lat: number;
  lon: number;
  fiyat?: number;
  fiyat_ogr?: number;
  sira: number;
}

interface OdakArac {
  Plaka?: string;
  plate?: string;
  Hizi?: string;
  speed?: string;
  Enlem?: string;
  lat?: number;
  Boylam?: string;
  lon?: number;
}

const OdakView = () => {
  const [hatlar, setHatlar] = useState<OdakHat[]>([]);
  const [selectedHat, setSelectedHat] = useState<OdakHat | null>(null);
  const [duraklar, setDuraklar] = useState<OdakDurak[]>([]);
  const [araclar, setAraclar] = useState<OdakArac[]>([]);
  const [isGidis, setIsGidis] = useState(true);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const fetchHatlar = async () => {
      try {
        const res = await fetch("/api/odak");
        if (!res.ok) throw new Error("Odak hatları yüklenemedi");
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

  const selectHat = async (hat: OdakHat) => {
    setSelectedHat(hat);
    setIsGidis(true);
    try {
      const [durakRes, aracRes] = await Promise.all([
        fetch(`/api/odak/${hat.id}/durak`),
        fetch(`/api/proxy_odak_araclar?hatid=${hat.id}`),
      ]);
      if (durakRes.ok) {
        const d = await durakRes.json();
        setDuraklar(Array.isArray(d) ? d : d.data || []);
      }
      if (aracRes.ok) {
        const a = await aracRes.json();
        setAraclar(a.vehicles || []);
      }
    } catch (err: any) {
      toast({ title: "Hata", description: err.message, variant: "destructive" });
    }
  };

  const toggleDirection = () => {
    if (!selectedHat) return;
    const pair = hatlar.find((h) => h.kod === selectedHat.kod && h.id !== selectedHat.id);
    if (pair) {
      selectHat(pair);
      setIsGidis(!isGidis);
    }
  };

  // Auto refresh vehicles
  useEffect(() => {
    if (!selectedHat) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/proxy_odak_araclar?hatid=${selectedHat.id}`);
        if (res.ok) {
          const data = await res.json();
          setAraclar(data.vehicles || []);
        }
      } catch {}
    }, 5000);
    return () => clearInterval(interval);
  }, [selectedHat]);

  if (selectedHat) {
    const firstFare = duraklar[0]?.fiyat;
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
          <button onClick={toggleDirection} className="rounded-lg bg-destructive/10 px-3 py-1.5 text-xs font-bold text-destructive">
            {isGidis ? "Dönüş ➡" : "← Gidiş"}
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="glass-panel rounded-xl p-3 text-center">
            <span className="font-mono font-bold text-lg text-foreground">{duraklar.length}</span>
            <p className="text-[10px] text-muted-foreground">Durak</p>
          </div>
          <div className="glass-panel rounded-xl p-3 text-center">
            <span className="font-mono font-bold text-lg text-transit-green">{araclar.length}</span>
            <p className="text-[10px] text-muted-foreground">Aktif Araç</p>
          </div>
          {firstFare != null && (
            <div className="glass-panel rounded-xl p-3 text-center">
              <span className="font-mono font-bold text-lg text-foreground">₺{firstFare}</span>
              <p className="text-[10px] text-muted-foreground">Ücret</p>
            </div>
          )}
        </div>

        {/* Vehicles */}
        {araclar.length > 0 && (
          <>
            <h4 className="font-sora text-sm font-semibold text-foreground mb-2">🚌 Canlı Araçlar</h4>
            <div className="flex flex-col gap-1.5 mb-4">
              {araclar.map((a, i) => {
                const plaka = a.Plaka || a.plate || "Bilinmiyor";
                const hiz = a.Hizi || a.speed || "0";
                return (
                  <div key={i} className="glass-panel flex items-center gap-3 rounded-xl px-3 py-2">
                    <span className="font-mono text-xs font-bold" style={{ color: "#16a34a" }}>{plaka}</span>
                    <div className="flex-1" />
                    <span className="font-mono text-xs text-muted-foreground">{parseFloat(String(hiz)).toFixed(0)} km/s</span>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {/* Stops */}
        <h4 className="font-sora text-sm font-semibold text-foreground mb-2">📍 Duraklar</h4>
        <div className="flex flex-col">
          {duraklar.map((d, i) => (
            <div key={i} className="flex items-start gap-3 pb-1">
              <div className="flex flex-col items-center">
                <div className="h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold text-primary-foreground" style={{ backgroundColor: "#16a34a" }}>
                  {i + 1}
                </div>
                {i < duraklar.length - 1 && <div className="w-0.5 h-6 bg-border" style={{ borderLeft: "2px dashed #16a34a40" }} />}
              </div>
              <div className="pb-2">
                <p className="text-sm font-medium text-foreground">{d.ad}</p>
                {d.fiyat != null && (
                  <p className="text-[10px] text-muted-foreground">₺{d.fiyat} / ₺{d.fiyat_ogr ?? "-"}</p>
                )}
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
        <img src="/static/images/odak.png" alt="Odak" className="h-16 rounded-xl shadow" onError={(e) => (e.currentTarget.style.display = "none")} />
        <div>
          <h2 className="font-sora text-xl font-bold text-foreground">Odak Seferleri</h2>
          <p className="text-xs text-muted-foreground">Turistik hat seferleri</p>
        </div>
      </div>

      <a href="tel:03624311012" className="flex items-center gap-2 glass-panel rounded-xl px-4 py-2.5 mb-3 text-sm text-foreground">
        <Phone className="h-4 w-4 text-primary" />
        <span>📞 Bilgi: 0362 431 10 12</span>
      </a>

      <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-3 py-2 mb-4 text-xs text-amber-700 dark:text-amber-400">
        ⚠️ DİKKAT: Fiyatlar değişiklik gösterebilir.
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
              className="glass-panel rounded-xl p-3 text-left border-l-4 border-green-500"
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

export default OdakView;
