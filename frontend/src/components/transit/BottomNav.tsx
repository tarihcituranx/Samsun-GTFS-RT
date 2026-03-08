import { Globe, Bus, MapPin, Compass, Navigation, Info } from "lucide-react";
import { useTransit } from "@/contexts/TransitContext";

type TabId = "harita" | "hatlar" | "yakinim" | "kesfet" | "odak" | "samair" | "rota" | "hakkinda";

const tabs: { id: TabId; label: string; icon?: React.FC<{ className?: string }>; imgSrc?: string }[] = [
  { id: "harita", label: "Harita", icon: Globe },
  { id: "hatlar", label: "Hatlar", icon: Bus },
  { id: "yakinim", label: "Yakın", icon: MapPin },
  { id: "kesfet", label: "Keşfet", icon: Compass },
  { id: "odak", label: "Odak", imgSrc: "/static/images/odak.png" },
  { id: "samair", label: "Samair", imgSrc: "/static/images/samair.png" },
  { id: "rota", label: "Git", icon: Navigation },
  { id: "hakkinda", label: "Hakkında", icon: Info },
];

const BottomNav = () => {
  const { activeTab, setActiveTab } = useTransit();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 md:hidden"
      style={{
        background: "hsl(var(--surface-glass))",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderTop: "1px solid hsl(var(--border) / 0.3)",
        paddingBottom: "env(safe-area-inset-bottom, 0px)",
        height: "calc(60px + env(safe-area-inset-bottom, 0px))",
      }}
    >
      <div className="flex h-[60px] items-start">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const isImageOnly = tab.id === "odak" || tab.id === "samair";
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="relative flex min-w-0 flex-1 flex-col items-center justify-center gap-[2px] px-[1px]"
              style={{
                height: 60,
                minHeight: 44,
                WebkitTapHighlightColor: "transparent",
                border: "none",
                background: "transparent",
              }}
              aria-label={tab.label}
            >
              {isActive && (
                <div className="absolute top-1 h-0.5 w-4 rounded-full bg-primary" />
              )}
              <div className={`transition-transform duration-200 ${isActive ? "scale-110" : "scale-100"} ${isImageOnly ? "mt-1" : ""}`}>
                {tab.icon ? (
                  <tab.icon className={`h-[18px] w-[18px] ${isActive ? "text-primary" : "text-muted-foreground"}`} />
                ) : (
                  <img
                    src={tab.imgSrc}
                    alt={tab.label}
                    className={`object-contain ${isImageOnly ? "h-6 w-auto" : "h-[18px] w-[18px]"}`}
                    onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
                  />
                )}
              </div>
              {!isImageOnly && (
                <span
                  className={`max-w-full truncate text-[8px] font-medium leading-tight ${isActive ? "text-primary" : "text-muted-foreground"
                    }`}
                >
                  {tab.label}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default BottomNav;
