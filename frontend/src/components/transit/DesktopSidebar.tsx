import { motion } from "framer-motion";
import { Globe, Bus, MapPin, Compass, Navigation, Info } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";

type TabId = "harita" | "hatlar" | "yakinim" | "kesfet" | "odak" | "samair" | "rota" | "hakkinda";

const tabs: { id: TabId; label: string; icon?: React.FC<{ className?: string }>; imgSrc?: string }[] = [
  { id: "harita", label: "Harita", icon: Globe },
  { id: "hatlar", label: "Hatlar", icon: Bus },
  { id: "yakinim", label: "Yakınım", icon: MapPin },
  { id: "kesfet", label: "Keşfet", icon: Compass },
  { id: "odak", label: "Odak", imgSrc: "/static/images/odak.png" },
  { id: "samair", label: "Samair", imgSrc: "/static/images/samair.png" },
  { id: "rota", label: "Git", icon: Navigation },
  { id: "hakkinda", label: "Hakkında", icon: Info },
];

const DesktopSidebar = () => {
  const { activeTab, setActiveTab } = useTransit();

  return (
    <aside className="fixed left-0 top-0 z-30 hidden h-full w-[72px] flex-col items-center gap-1 border-r border-border/30 glass-panel py-6 md:flex xl:w-[200px] 2xl:w-[240px]">
      {/* Logo / Brand */}
      <div className="mb-8 flex items-center gap-2 px-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground font-sora font-black text-base shadow-[0_0_16px_hsl(var(--primary)/0.3)]">
          K
        </div>
        <div className="hidden flex-col xl:flex">
          <span className="font-sora font-black text-sm tracking-tight text-foreground">{APP_CONFIG.name}</span>
          <span className="text-[10px] font-semibold text-primary">{APP_CONFIG.activeCity.name}</span>
        </div>
      </div>

      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative flex w-full items-center gap-3 rounded-xl px-5 py-3 transition-all ${
              isActive
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
            }`}
            aria-label={tab.label}
          >
            {isActive && (
              <motion.div
                layoutId="sidebar-active"
                className="absolute left-1 top-1/2 h-8 w-1 -translate-y-1/2 rounded-full bg-primary"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            {tab.icon ? (
              <tab.icon className="h-5 w-5 shrink-0" />
            ) : (
              <img src={tab.imgSrc} alt={tab.label} className="h-5 w-5 shrink-0 object-contain" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }} />
            )}
            <span className="hidden text-sm font-medium xl:block">{tab.label}</span>
          </button>
        );
      })}
    </aside>
  );
};

export default DesktopSidebar;
