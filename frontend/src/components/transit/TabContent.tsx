import { useTransit } from "@/contexts/TransitContext";
import LinesTab from "./LinesTab";
import NearMeTab from "./NearMeTab";
import RoutePlannerTab from "./RoutePlannerTab";
import DiscoverTab from "./DiscoverTab";
import AboutTab from "./AboutTab";
import OdakView from "./tabs/OdakView";
import SamairView from "./tabs/SamairView";
const MapQuickStats = () => {
  const { vehicles } = useTransit();
  const activeCount = vehicles.length;
  return (
    <div className="pb-2">
      <div className="flex items-center gap-3 mb-2">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 animate-pulse rounded-full bg-transit-green" />
          <span className="font-mono text-sm font-bold text-foreground">{activeCount}</span>
          <span className="text-xs text-muted-foreground">aktif araç</span>
        </span>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">
        Haritada araçları ve durakları görmek için tıklayın
      </p>
    </div>
  );
};

const TabContent = () => {
  const { activeTab } = useTransit();

  switch (activeTab) {
    case "harita":
      return <MapQuickStats />;
    case "hatlar":
      return <LinesTab />;
    case "yakinim":
      return <NearMeTab />;
    case "rota":
      return <RoutePlannerTab />;
    case "kesfet":
      return <DiscoverTab />;
    case "hakkinda":
      return <AboutTab />;
    case "odak":
      return <OdakView />;
    case "samair":
      return <SamairView />;
    default:
      return <MapQuickStats />;
  }
};

export default TabContent;
