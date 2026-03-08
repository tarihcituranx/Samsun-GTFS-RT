import { useState, useEffect } from "react";

// ─── MGM Türkiye hava durumu kod sistemi (tam liste) ──────────────────────
const WEATHER_CONFIG: Record<string, { icon: string; label: string; color: string; text: string; emoji: string }> = {
  "-9999": { icon: "cloudy",              label: "Bilinmiyor",          color: "#64748b", text: "#fff", emoji: "❓" },
  "A":     { icon: "clear-day",           label: "Açık",                color: "#f59e0b", text: "#fff", emoji: "☀️" },
  "AB":    { icon: "cloudy-1-day",        label: "Az Bulutlu",          color: "#fb923c", text: "#fff", emoji: "🌤️" },
  "PB":    { icon: "cloudy-2-day",        label: "Parçalı Bulutlu",     color: "#94a3b8", text: "#fff", emoji: "⛅" },
  "CB":    { icon: "cloudy-3-day",        label: "Çok Bulutlu",         color: "#64748b", text: "#fff", emoji: "☁️" },
  "HY":    { icon: "rainy-1",             label: "Hafif Yağmurlu",      color: "#3b82f6", text: "#fff", emoji: "🌦️" },
  "Y":     { icon: "rainy-2",             label: "Yağmurlu",            color: "#2563eb", text: "#fff", emoji: "🌧️" },
  "KY":    { icon: "rainy-3",             label: "Kuvvetli Yağmur",     color: "#1d4ed8", text: "#fff", emoji: "🌧️" },
  "KKY":   { icon: "rain-and-snow-mix",   label: "Karla Karışık Yağmur",color: "#7dd3fc", text: "#1e293b", emoji: "🌨️" },
  "HK":    { icon: "snowy-1",             label: "Hafif Kar",           color: "#bae6fd", text: "#1e293b", emoji: "🌨️" },
  "K":     { icon: "snowy-2",             label: "Kar Yağışlı",         color: "#e0f2fe", text: "#1e293b", emoji: "❄️" },
  "YY":    { icon: "snowy-3",             label: "Yoğun Kar",           color: "#f0f9ff", text: "#1e293b", emoji: "❄️" },
  "S":     { icon: "fog",                 label: "Sisli",               color: "#9ca3af", text: "#fff", emoji: "🌫️" },
  "D":     { icon: "haze",                label: "Dumanlı",             color: "#a3a3a3", text: "#fff", emoji: "🌫️" },
  "P":     { icon: "haze",                label: "Puslu",               color: "#a8a29e", text: "#fff", emoji: "🌫️" },
  "GSY":   { icon: "thunderstorms",       label: "Gök Gürültülü Sağanak",color: "#7c3aed", text: "#fff", emoji: "⛈️" },
  "KGY":   { icon: "thunderstorms",       label: "Kuvvetli Sağanak",    color: "#6d28d9", text: "#fff", emoji: "⛈️" },
  "SY":    { icon: "thunderstorms",       label: "Sağanak Yağışlı",     color: "#8b5cf6", text: "#fff", emoji: "🌩️" },
  "MSY":   { icon: "thunderstorms",       label: "Mevzii Sağanak",      color: "#a78bfa", text: "#fff", emoji: "🌩️" },
  "DY":    { icon: "thunderstorms",       label: "Dolu",                color: "#7c3aed", text: "#fff", emoji: "🌩️" },
  "R":     { icon: "wind",                label: "Rüzgarlı",            color: "#0ea5e9", text: "#fff", emoji: "💨" },
  "GKR":   { icon: "wind",                label: "Kum Fırtınası",       color: "#d97706", text: "#fff", emoji: "🌪️" },
  "GG":    { icon: "thunderstorms",       label: "Gök Gürültülü",       color: "#7c3aed", text: "#fff", emoji: "⚡" },
};

// Gece versiyonu olan ikonlar
const NIGHT_ICONS: Record<string, string> = {
  "clear-day":    "clear-night",
  "cloudy-1-day": "cloudy-1-night",
  "cloudy-2-day": "cloudy-2-night",
  "cloudy-3-day": "cloudy-3-night",
};

const isNightTime = () => {
  const h = new Date().getHours();
  return h < 6 || h >= 20;
};

const getIconName = (hadise: string): string => {
  const cfg = WEATHER_CONFIG[hadise] ?? WEATHER_CONFIG["-9999"];
  let icon = cfg.icon;
  if (isNightTime() && NIGHT_ICONS[icon]) icon = NIGHT_ICONS[icon];
  return icon;
};

// Hissedilen sıcaklık rengi (mavi → yeşil → sarı → turuncu → kırmızı)
const getTempColor = (temp: number): string => {
  if (temp <= 0)  return "#93c5fd";
  if (temp <= 10) return "#67e8f9";
  if (temp <= 18) return "#86efac";
  if (temp <= 25) return "#fde047";
  if (temp <= 32) return "#fb923c";
  return "#f87171";
};

interface WeatherData {
  sicaklik: number;
  hadise: string;
  zaman?: string;
  nem?: number;
  ruzgar_hiz?: number;
  ruzgar_yon?: string;
  hissedilen?: number;
}

const WIND_DIR_TR: Record<string, string> = {
  N: "K", NE: "KD", E: "D", SE: "GD",
  S: "G", SW: "GB", W: "B", NW: "KB",
};

// ─── Yardımcı: Detay hücresi ─────────────────────────────────────────────
const WeatherDetailCell = ({
  icon,
  label,
  value,
  valueColor,
}: {
  icon: string;
  label: string;
  value: string;
  valueColor?: string;
}) => (
  <div className="flex flex-col gap-0.5 rounded-xl bg-muted/30 px-3 py-2">
    <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
      {icon} {label}
    </span>
    <span
      className="font-mono text-sm font-bold tabular-nums"
      style={{ color: valueColor }}
    >
      {value}
    </span>
  </div>
);

// ─── Ana WeatherWidget ───────────────────────────────────────────────────
const WeatherWidget = () => {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [showDetail, setShowDetail] = useState(false);

  const fetchWeather = async () => {
    try {
      const res = await fetch("/api/hava");
      if (!res.ok) throw new Error("API hatası");
      const data: WeatherData = await res.json();
      if (data?.sicaklik === undefined || data.sicaklik === null) throw new Error("Veri yok");
      setWeather(data);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather();
    const t = setInterval(fetchWeather, 15 * 60 * 1000);
    return () => clearInterval(t);
  }, []);

  // ── Yükleniyor
  if (loading) {
    return (
      <div className="flex items-center gap-1.5 rounded-full bg-muted/50 px-3 py-1.5 animate-pulse">
        <div className="h-5 w-5 rounded-full bg-muted" />
        <div className="h-3 w-10 rounded bg-muted" />
      </div>
    );
  }

  // ── Hata veya veri yok
  if (error || !weather) return null;

  const cfg = WEATHER_CONFIG[weather.hadise] ?? WEATHER_CONFIG["-9999"];
  const iconName = getIconName(weather.hadise);
  const tempColor = getTempColor(weather.sicaklik);
  const iconSrc = `/static/weather-icons/animated/${iconName}.svg`;

  let updateTime = "";
  if (weather.zaman) {
    try {
      updateTime = new Date(weather.zaman).toLocaleTimeString("tr-TR", {
        timeZone: "Europe/Istanbul",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch { /* ignore */ }
  }

  return (
    <div className="relative">
      {/* ── Kompakt widget butonu ── */}
      <button
        onClick={() => setShowDetail((v) => !v)}
        title={`Samsun Atakum — ${cfg.label}${updateTime ? ` • ${updateTime}` : ""}`}
        className="flex cursor-pointer select-none items-center gap-2 rounded-full border border-border/40 bg-background/60 px-3 py-1.5 backdrop-blur-sm transition-all duration-200 hover:border-primary/50 dark:bg-white/5"
      >
        {/* Hava ikonu */}
        <img
          src={iconSrc}
          alt={cfg.label}
          width={32}
          height={32}
          className="h-8 w-8 object-contain drop-shadow-sm"
          onError={(e) => {
            const el = e.currentTarget;
            el.style.display = "none";
            const span = document.createElement("span");
            span.textContent = cfg.emoji;
            span.className = "text-xl leading-none";
            el.parentNode?.insertBefore(span, el.nextSibling);
          }}
        />

        {/* Sıcaklık */}
        <div className="flex flex-col items-start leading-none">
          <span
            className="font-mono text-sm font-bold tabular-nums"
            style={{ color: tempColor }}
          >
            {Number(weather.sicaklik).toFixed(1)}°C
          </span>
          <span className="mt-0.5 max-w-[64px] truncate text-[9px] font-medium text-muted-foreground">
            {cfg.label}
          </span>
        </div>

        {/* Detay ok ikonu */}
        <svg
          className={`h-3 w-3 text-muted-foreground transition-transform duration-200 ${showDetail ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* ── Detay dropdown ── */}
      {showDetail && (
        <div className="absolute right-0 top-[calc(100%+8px)] z-[200] w-[240px] animate-in fade-in slide-in-from-top-2 glass-panel overflow-hidden rounded-2xl border border-border/40 shadow-xl shadow-black/20 duration-200">
          {/* Renkli üst başlık */}
          <div
            className="flex items-center gap-3 px-4 py-3"
            style={{ background: `${cfg.color}22`, borderBottom: `1px solid ${cfg.color}33` }}
          >
            <img
              src={iconSrc}
              alt={cfg.label}
              width={44}
              height={44}
              className="h-11 w-11 object-contain drop-shadow"
              onError={(e) => { e.currentTarget.style.display = "none"; }}
            />
            <div>
              <div
                className="font-mono text-2xl font-bold tabular-nums"
                style={{ color: tempColor }}
              >
                {Number(weather.sicaklik).toFixed(1)}°C
              </div>
              <div className="mt-0.5 text-xs font-semibold text-foreground/80">
                {cfg.label}
              </div>
            </div>
          </div>

          {/* Detay grid */}
          <div className="grid grid-cols-2 gap-2 p-3">
            {weather.hissedilen !== undefined && (
              <WeatherDetailCell
                icon="🌡️"
                label="Hissedilen"
                value={`${Number(weather.hissedilen).toFixed(0)}°C`}
                valueColor={getTempColor(weather.hissedilen)}
              />
            )}
            {weather.nem !== undefined && (
              <WeatherDetailCell
                icon="💧"
                label="Nem"
                value={`%${weather.nem}`}
                valueColor={weather.nem > 70 ? "#60a5fa" : "#94a3b8"}
              />
            )}
            {weather.ruzgar_hiz !== undefined && (
              <WeatherDetailCell
                icon="💨"
                label="Rüzgar"
                value={`${weather.ruzgar_hiz} km/s`}
                valueColor={weather.ruzgar_hiz > 40 ? "#f87171" : "#94a3b8"}
              />
            )}
            {weather.ruzgar_yon && (
              <WeatherDetailCell
                icon="🧭"
                label="Yön"
                value={WIND_DIR_TR[weather.ruzgar_yon] ?? weather.ruzgar_yon}
                valueColor="#94a3b8"
              />
            )}
          </div>

          {/* Alt bilgi */}
          <div className="flex items-center justify-between px-3 pb-3">
            <span className="text-[10px] text-muted-foreground">📍 Samsun Atakum</span>
            {updateTime && (
              <span className="font-mono text-[10px] text-muted-foreground">⏱ {updateTime}</span>
            )}
          </div>

          {/* Koşul renk indikatörü */}
          <div
            className="h-1 w-full"
            style={{ background: `linear-gradient(90deg, ${cfg.color}88, ${cfg.color})` }}
          />
        </div>
      )}

      {/* Overlay: detay açıkken dışarı tıklanınca kapat */}
      {showDetail && (
        <div
          className="fixed inset-0 z-[199]"
          onClick={() => setShowDetail(false)}
        />
      )}
    </div>
  );
};

export default WeatherWidget;
