import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";

const SystemStatusBar = () => {
  const { vehicles } = useTransit();
  const busCount = vehicles.filter((v) => v.line.startsWith("E") || v.line === "19" || v.line === "26" || v.line === "45").length;
  const tramCount = vehicles.filter((v) => v.line.startsWith("T")).length;
  const vapurCount = vehicles.filter((v) => v.line.startsWith("V")).length;

  const now = new Date();
  const timeStr = now.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  return (
    <div className="fixed bottom-0 left-[72px] right-0 z-20 hidden glass-panel border-t border-border/30 px-6 py-2 md:flex xl:left-[200px]">
      <div className="flex w-full items-center justify-between font-mono text-xs">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 animate-pulse rounded-full bg-transit-green" />
          <span className="font-bold text-foreground">{APP_CONFIG.name}</span>
          <span className="text-muted-foreground">·</span>
          <span className="text-[10px] text-muted-foreground">{APP_CONFIG.activeCity.name}</span>
        </div>
        <div className="flex items-center gap-6 text-muted-foreground">
          <span>🚌 {busCount} Otobüs</span>
          <span>🚃 {tramCount} Tramvay</span>
          <span>⛴️ {vapurCount} Vapur</span>
          <span className="text-foreground">Son güncelleme: {timeStr}</span>
        </div>
      </div>
    </div>
  );
};

export default SystemStatusBar;