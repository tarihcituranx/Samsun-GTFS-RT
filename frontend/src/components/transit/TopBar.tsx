import { Search, Settings, X, RefreshCw } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";
import { useState, useEffect } from "react";
import WeatherWidget from "./WeatherWidget";
import SettingsPanel from "./SettingsPanel";
import { fetchAppVersion, type AppVersionInfo } from "@/lib/api";

const CURRENT_VERSION = "2.5.0"; // Backend app_version ile eşleşmeli

interface TopBarProps {
  onOpenSettings?: () => void;
}

const TopBar = ({ onOpenSettings }: TopBarProps) => {
  const { isDark, toggleTheme, stops, lines } = useTransit();
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [updateBanner, setUpdateBanner] = useState<AppVersionInfo | null>(null);

  // Version check on mount (once)
  useEffect(() => {
    fetchAppVersion().then((info) => {
      if (!info) return;
      const parseV = (v: string) => v.split(".").map(Number);
      const latest = parseV(info.latest_version);
      const current = parseV(CURRENT_VERSION);
      const hasUpdate = latest[0] > current[0] || latest[1] > current[1] || latest[2] > current[2];
      if (hasUpdate || info.force_update) setUpdateBanner(info);
    });
  }, []);

  const filtered = query.length > 1
    ? [
      ...lines.filter((l) => String(l.name || "").toLowerCase().includes(query.toLowerCase()) || String(l.code || "").toLowerCase().includes(query.toLowerCase())).map(l => ({ id: String(l.code), name: String(l.name), type: 'line', code: String(l.code) })),
      ...stops.filter((s) => String(s.name || "").toLowerCase().includes(query.toLowerCase())).map(s => ({ id: String(s.id), name: String(s.name), type: 'stop', code: '' }))
    ].slice(0, 5)
    : [];

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 glass-panel border-b border-border/30
                 md:left-[72px] xl:left-[200px] 2xl:left-[240px]"
    >
      <div className="flex flex-col md:flex-row md:items-center md:h-16 md:px-4 md:gap-3">
        {/* Row 1 */}
        <div className="flex items-center justify-between px-3 h-14 md:h-auto md:flex-1">
          {/* Mobile: app name */}
          <div className="flex items-center gap-2 md:hidden">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary shadow-[0_0_12px_hsl(var(--primary)/0.3)]">
              <span className="text-sm font-black leading-none text-primary-foreground">K</span>
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-sm font-black tracking-tight text-foreground">{APP_CONFIG.name}</span>
              <span className="text-[9px] font-semibold text-primary">{APP_CONFIG.activeCity.name}</span>
            </div>
          </div>

          {/* Desktop: search here */}
          <div className="hidden md:flex flex-1 relative">
            <div className="flex flex-1 items-center gap-2 rounded-full border border-border/40 bg-background/60 px-3 py-2">
              <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
              <input
                type="text"
                placeholder="Durak, hat veya yer ara..."
                className="flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
                style={{ fontSize: 16 }}
                value={query}
                onChange={(e) => { setQuery(e.target.value); setSearchOpen(true); }}
                onFocus={() => setSearchOpen(true)}
              />
              {query && (
                <button onClick={() => { setQuery(""); setSearchOpen(false); }} className="text-muted-foreground">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-1.5 shrink-0">
            {/* Desktop brand logos */}
            <div className="hidden items-center gap-2 md:flex mr-4">
              <img
                src={isDark ? "/static/images/sbb_dark.png" : "/static/images/sbb_v2.png"}
                alt="SBB"
                className="h-9 w-auto object-contain drop-shadow"
                onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
              />
              <img
                src={isDark ? "/static/images/samulas_3.png" : "/static/images/samulas.png"}
                alt="Samulaş"
                className="h-9 w-auto object-contain drop-shadow"
                onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
              />
              <div className="h-6 w-px bg-border/40 mx-1" />
            </div>

            <WeatherWidget />
            <button
              onClick={toggleTheme}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border/30 bg-background/60 transition-colors"
              aria-label="Tema değiştir"
            >
              <span className="text-sm">{isDark ? "☀️" : "🌙"}</span>
            </button>
            <div className="relative">
              <button
                onClick={() => setSettingsOpen(!settingsOpen)}
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border/30 bg-background/60 transition-colors"
                aria-label="Ayarlar"
              >
                <Settings className="h-4 w-4 text-foreground" />
              </button>
              <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
            </div>
          </div>
        </div>

        {/* Row 2: Mobile search */}
        <div className="px-3 pb-2 md:hidden">
          <div className="flex items-center gap-2 rounded-full border border-border/40 bg-background/60 px-3 py-2">
            <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
            <input
              type="text"
              placeholder="Durak, hat veya yer ara..."
              className="flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
              style={{ fontSize: 16 }}
              value={query}
              onChange={(e) => { setQuery(e.target.value); setSearchOpen(true); }}
              onFocus={() => setSearchOpen(true)}
            />
            <span className="flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-[10px] font-mono font-semibold text-destructive">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-destructive" />
              CANLI
            </span>
            {query && (
              <button onClick={() => { setQuery(""); setSearchOpen(false); }} className="text-muted-foreground">
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Search results dropdown */}
      {searchOpen && filtered.length > 0 && (
        <div className="absolute left-3 right-3 top-full mt-1 glass-panel rounded-2xl p-2 md:left-4 md:right-auto md:w-[400px]">
          {filtered.map((stop) => (
            <button
              key={stop.id}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-colors hover:bg-primary/10"
              onClick={() => { setQuery(stop.name); setSearchOpen(false); }}
            >
              <span className="text-lg">{stop.type === 'line' ? '🚌' : '📍'}</span>
              <div>
                <p className="font-medium text-foreground">{stop.name}</p>
                <p className="text-xs text-muted-foreground">
                  {stop.type === 'line' ? `Hat Kodu: ${stop.code}` : "Durak"}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Güncelleme Banner */}
      {updateBanner && (
        <div className="bg-primary/10 border-t border-primary/20 px-4 py-2 flex items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-primary font-semibold">
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Yeni sürüm mevcut: v{updateBanner.latest_version}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setUpdateBanner(null)}
              className="rounded-full bg-primary text-primary-foreground px-3 py-1 font-semibold text-xs"
            >
              Tamam
            </button>
            <button onClick={() => setUpdateBanner(null)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

export default TopBar;