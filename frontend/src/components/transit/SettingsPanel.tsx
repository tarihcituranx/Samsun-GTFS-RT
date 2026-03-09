import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useSettings } from "@/hooks/useSettings";
import { useToast } from "@/hooks/use-toast";
import { useTransit } from "@/contexts/TransitContext";
import { registerFcmToken } from "@/lib/api";

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

const mapSettingItems: { key: "showHasilat" | "showLabels" | "showRoute" | "autoRefresh" | "showAllStops"; label: string }[] = [
  { key: "showHasilat", label: "💰 Günlük Hasılat" },
  { key: "showLabels", label: "🏷️ Durak İsimleri" },
  { key: "showRoute", label: "🗺️ Güzergah Çizgisi" },
  { key: "autoRefresh", label: "🔄 Otomatik Yenileme (5sn)" },
  { key: "showAllStops", label: "📍 Tüm Durakları Göster" },
];

const fontSizeOptions: { value: "normal" | "large" | "xlarge"; label: string }[] = [
  { value: "normal", label: "Normal" },
  { value: "large", label: "Büyük" },
  { value: "xlarge", label: "Çok Büyük" },
];

const SettingsPanel = ({ open, onClose }: SettingsPanelProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const { settings, setSetting, resetAll } = useSettings();
  const { toast } = useToast();
  const { toggleTheme } = useTransit();
  const [notifEnabled, setNotifEnabled] = useState(() =>
    typeof Notification !== "undefined" && Notification.permission === "granted"
  );
  const [notifLoading, setNotifLoading] = useState(false);

  const handleNotificationToggle = async (enable: boolean) => {
    if (typeof Notification === "undefined") {
      toast({ title: "Desteklenmiyor", description: "Bu tarayıcı bildirim API'sini desteklemiyor." });
      return;
    }
    if (!enable) {
      setNotifEnabled(false);
      toast({ title: "Bildirimler kapatıldı", description: "Tarayıcı ayarlarından da kaldırabilirsiniz." });
      return;
    }
    setNotifLoading(true);
    try {
      const perm = await Notification.requestPermission();
      if (perm === "granted") {
        // Gerçek FCM token yerine placeholder kullan (Flutter uygulama için)
        const fakeToken = `web_${Date.now()}_${Math.random().toString(36).slice(2)}`;
        await registerFcmToken(fakeToken, "web");
        setNotifEnabled(true);
        toast({ title: "✅ Bildirimler Açıldı", description: "Samsun toplu taşıma bildirimleri aktif." });
      } else {
        toast({ title: "Bildirim izni reddedildi", description: "Tarayıcı ayarlarından manuel olarak açabilirsiniz." });
      }
    } catch {
      toast({ title: "Bildirim hatası", description: "Bir sorun oluştu, tekrar deneyin." });
    }
    setNotifLoading(false);
  };

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open, onClose]);

  const handleReset = () => {
    const wasDark = document.documentElement.classList.contains("dark");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    resetAll();
    if (wasDark !== prefersDark) toggleTheme();
    toast({ title: "Ayarlar varsayılana çevrildi", description: "Tüm tercihler sıfırlandı." });
    onClose();
  };

  const handleElderlyToggle = (enabled: boolean) => {
    setSetting("elderlyMode", enabled);
    if (enabled) {
      setSetting("fontSize", "xlarge");
      setSetting("highContrast", true);
      setSetting("reducedMotion", true);
      toast({ title: "👴 Yaşlı Modu Açıldı", description: "Büyük yazı, yüksek kontrast ve sakin animasyonlar etkinleştirildi." });
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: -8, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.95 }}
          transition={{ duration: 0.15 }}
          className="absolute right-0 top-14 z-50 w-[280px] max-h-[80vh] overflow-y-auto glass-panel rounded-2xl p-4 border border-border/50 scrollbar-hide"
        >
          {/* ── Harita Ayarları ── */}
          <h3 className="font-sora text-sm font-bold text-foreground mb-3">⚙️ Harita Ayarları</h3>
          <div className="flex flex-col gap-2.5">
            {mapSettingItems.map((item) => (
              <label key={item.key} className="flex items-center justify-between cursor-pointer">
                <span className="text-xs text-foreground">{item.label}</span>
                <input
                  type="checkbox"
                  checked={settings[item.key]}
                  onChange={(e) => setSetting(item.key, e.target.checked)}
                  className="h-4 w-4 rounded border-border accent-primary"
                />
              </label>
            ))}
          </div>

          {/* ── Ayırıcı ── */}
          <div className="my-4 h-px bg-border/40" />

          {/* ── Erişilebilirlik ── */}
          <h3 className="font-sora text-sm font-bold text-foreground mb-3">♿ Erişilebilirlik</h3>
          <div className="flex flex-col gap-3">

            {/* Yaşlı Modu */}
            <label className="flex items-center justify-between cursor-pointer">
              <div className="flex flex-col">
                <span className="text-xs font-medium text-foreground">👴 Yaşlı Modu</span>
                <span className="text-[10px] text-muted-foreground">Büyük yazı + yüksek kontrast + sakin</span>
              </div>
              <input
                type="checkbox"
                checked={settings.elderlyMode}
                onChange={(e) => handleElderlyToggle(e.target.checked)}
                className="h-5 w-5 rounded border-border accent-primary"
              />
            </label>

            {/* Yazı Boyutu */}
            <div>
              <span className="text-xs font-medium text-foreground mb-1.5 block">🔤 Yazı Boyutu</span>
              <div className="flex gap-1.5">
                {fontSizeOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSetting("fontSize", opt.value)}
                    className={[
                      "flex-1 rounded-lg py-1.5 text-[10px] font-semibold transition-all duration-150 border",
                      (settings.elderlyMode ? "xlarge" : settings.fontSize) === opt.value
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-muted/50 text-muted-foreground border-border/40 hover:border-primary/50",
                    ].join(" ")}
                    disabled={settings.elderlyMode}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Yüksek Kontrast */}
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-xs text-foreground">🔲 Yüksek Kontrast</span>
              <input
                type="checkbox"
                checked={settings.highContrast || settings.elderlyMode}
                onChange={(e) => setSetting("highContrast", e.target.checked)}
                disabled={settings.elderlyMode}
                className="h-4 w-4 rounded border-border accent-primary"
              />
            </label>

            {/* Azaltılmış Hareket */}
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-xs text-foreground">🐢 Azaltılmış Hareket</span>
              <input
                type="checkbox"
                checked={settings.reducedMotion || settings.elderlyMode}
                onChange={(e) => setSetting("reducedMotion", e.target.checked)}
                disabled={settings.elderlyMode}
                className="h-4 w-4 rounded border-border accent-primary"
              />
            </label>
          </div>

          {/* ── Bildirimler ── */}
          <div className="my-4 h-px bg-border/40" />
          <h3 className="font-sora text-sm font-bold text-foreground mb-3">🔔 Bildirimler</h3>
          <label className="flex items-center justify-between cursor-pointer">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">
                {notifEnabled ? "🔔 Bildirimler Açık" : "🔕 Bildirimler Kapalı"}
              </span>
              <span className="text-[10px] text-muted-foreground">Hat gecikme ve duyurular</span>
            </div>
            <button
              disabled={notifLoading}
              onClick={() => handleNotificationToggle(!notifEnabled)}
              className={`relative h-6 w-11 rounded-full border transition-all duration-200 ${notifEnabled ? "bg-primary border-primary" : "bg-muted border-border"} ${notifLoading ? "opacity-50" : ""}`}
            >
              <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all duration-200 ${notifEnabled ? "left-5" : "left-0.5"}`} />
            </button>
          </label>

          {/* ── Sıfırla ── */}
          <button
            onClick={handleReset}
            className="mt-4 w-full rounded-xl border border-border py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            🔄 Varsayılana Çevir
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SettingsPanel;
