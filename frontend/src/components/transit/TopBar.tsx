import { Search, Settings, X } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";
import { useState } from "react";
import WeatherWidget from "./WeatherWidget";
import SettingsPanel from "./SettingsPanel";

interface TopBarProps {
  onOpenSettings?: () => void;
}

const TopBar = ({ onOpenSettings }: TopBarProps) => {
  const { isDark, toggleTheme, stops, lines } = useTransit();
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const filtered = query.length > 1
    ? [
      ...lines.filter((l) => l.name.toLowerCase().includes(query.toLowerCase()) || l.code.toLowerCase().includes(query.toLowerCase())).map(l => ({ id: l.code, name: l.name, type: 'line', code: l.code })),
      ...stops.filter((s) => s.name.toLowerCase().includes(query.toLowerCase())).map(s => ({ id: s.id, name: s.name, type: 'stop', code: '' }))
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
    </header>
  );
};

export default TopBar;