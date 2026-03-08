import { useState } from "react";
import { TransitProvider, useTransit } from "@/contexts/TransitContext";
import TopBar from "@/components/transit/TopBar";
import MapCanvas from "@/components/transit/MapCanvas";
import BottomNav from "@/components/transit/BottomNav";
import DesktopSidebar from "@/components/transit/DesktopSidebar";
import MobileBottomSheet from "@/components/transit/MobileBottomSheet";
import TabContent from "@/components/transit/TabContent";
import SystemStatusBar from "@/components/transit/SystemStatusBar";
import SplashScreen from "@/components/transit/SplashScreen";
import TransferModal from "@/components/transit/TransferModal";
import DetailPanel from "@/components/transit/DetailPanel";
import ToastSystem from "@/components/transit/ToastSystem";
import DisclaimerModal from "@/components/transit/DisclaimerModal";
import KVKKModal from "@/components/transit/KVKKModal";
import CookieModal from "@/components/transit/CookieModal";
import CookieConsentBanner from "@/components/transit/CookieConsentBanner";

// ─── Piksel sabitleri ──────────────────────────────────────────────────────
const TOPBAR_MOBILE = 96;
const FILTER_TOP = TOPBAR_MOBILE + 4;

const MAP_FILTERS = [
  { key: "buses",   emoji: "🚌", label: "Otobüs"   },
  { key: "trams",   emoji: "🚃", label: "Tramvay"  },
  { key: "ferries", emoji: "⛴️",  label: "Vapur"    },
  { key: "stops",   emoji: "📍", label: "Duraklar" },
] as const;

// ─── BrandLogos ───────────────────────────────────────────────────────────
const BrandLogos = () => {
  const { isDark } = useTransit();

  return (
    <div className="flex flex-shrink-0 items-center justify-center gap-4 border-b border-border/20 px-4 py-3">
      <img
        src={isDark ? "/static/images/sbb_dark.png" : "/static/images/sbb_v2.png"}
        alt="Samsun Büyükşehir Belediyesi"
        title="Samsun Büyükşehir Belediyesi"
        width={130}
        height={44}
        className="h-9 w-auto object-contain drop-shadow-sm transition-opacity duration-300"
        onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
      />
      <div className="h-7 w-px rounded-full bg-border/40" />
      <img
        src={isDark ? "/static/images/samulas_3.png" : "/static/images/samulas.png"}
        alt="Samulaş"
        title="Samulaş"
        width={100}
        height={44}
        className="h-9 w-auto object-contain drop-shadow-sm transition-opacity duration-300"
        onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
      />
    </div>
  );
};

// ─── MapFilterPills (mobil, sadece harita tabında) ────────────────────────
const MapFilterPills = () => {
  const [active, setActive] = useState<Set<string>>(() => new Set(["buses", "trams"]));

  const toggle = (key: string) =>
    setActive((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  return (
    <div
      className="fixed left-0 right-0 z-40 px-3 md:hidden"
      style={{ top: FILTER_TOP }}
    >
      <div className="flex gap-1.5 overflow-x-auto scrollbar-hide pb-1">
        {MAP_FILTERS.map(({ key, emoji, label }) => {
          const isActive = active.has(key);
          return (
            <button
              key={key}
              onClick={() => toggle(key)}
              aria-pressed={isActive}
              className={[
                "shrink-0 flex items-center gap-1 rounded-full whitespace-nowrap",
                "px-2.5 min-h-[36px] text-[11px] font-semibold",
                "border backdrop-blur-md transition-all duration-200 active:scale-95",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                isActive
                  ? "bg-primary border-primary text-primary-foreground shadow-[0_0_12px_hsl(var(--primary)/0.4)]"
                  : "glass-panel border-border/30 text-foreground",
              ].join(" ")}
            >
              <span className="text-sm leading-none">{emoji}</span>
              <span>{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

// ─── DesktopContentPanel ─────────────────────────────────────────────────
const DesktopContentPanel = () => (
  <div className="fixed left-[72px] top-0 z-20 hidden h-full w-[380px] flex-col glass-panel border-r border-border/30 md:flex xl:left-[200px] 2xl:left-[240px] 2xl:w-[400px]">
    <div className="flex-shrink-0" style={{ paddingTop: 64 }}>
      <BrandLogos />
    </div>
    <div className="flex-1 overflow-y-auto p-5 scrollbar-hide">
      <TabContent />
    </div>
  </div>
);

// ─── TransitApp ──────────────────────────────────────────────────────────
const TransitApp = () => {
  const { activeTab, showSplash } = useTransit();
  const [showTransferModal, setShowTransferModal] = useState(false);

  return (
    <div className="h-[100dvh] w-screen overflow-hidden bg-background">
      <SplashScreen />

      {!showSplash && (
        <>
          {/* Harita (en altta) */}
          <MapCanvas />

          {/* TopBar — Mobil: h-14 (56px) | Desktop: h-16 (64px) */}
          <TopBar onOpenSettings={() => setShowTransferModal(true)} />


          {/* Harita filtre butonları (yalnızca mobil + harita tab) */}
          {activeTab === "harita" && <MapFilterPills />}

          {/* ═══ MOBİL ═══ */}
          <MobileBottomSheet>
            <BrandLogos />
            <div className="px-4 pb-6">
              <TabContent />
            </div>
          </MobileBottomSheet>
          <BottomNav />

          {/* ═══ DESKTOP ═══ */}
          <DesktopSidebar />
          <DesktopContentPanel />
          <DetailPanel />
          <SystemStatusBar />

          {/* Modaller */}
          <TransferModal open={showTransferModal} onClose={() => setShowTransferModal(false)} />
          <DisclaimerModal />
          <KVKKModal />
          <CookieModal />
          <CookieConsentBanner />
          <ToastSystem />
        </>
      )}
    </div>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
const Index = () => (
  <TransitProvider>
    <TransitApp />
  </TransitProvider>
);

export default Index;
