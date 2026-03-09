import { useEffect, useState } from "react";
import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";
import { fetchAppVersion, type AppVersionInfo } from "@/lib/api";

const GitHubIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
      0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
      -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
      .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
      -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27
      .68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12
      .51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48
      0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
  </svg>
);

const SplashScreen = () => {
  const { setShowSplash } = useTransit();
  const [phase, setPhase] = useState(0);
  const [versionInfo, setVersionInfo] = useState<AppVersionInfo | null>(null);
  const [showReleaseNotes, setShowReleaseNotes] = useState(false);

  useEffect(() => {
    // Versiyon bilgisini arka planda çek
    fetchAppVersion().then((info) => {
      if (info) setVersionInfo(info);
    });
  }, []);

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 600);
    const t2 = setTimeout(() => setPhase(2), 1400);
    const t3 = setTimeout(() => setPhase(3), 2600);
    const t4 = setTimeout(() => setShowSplash(false), 3200);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); };
  }, [setShowSplash, versionInfo]);

  return (
    <div
      className={[
        "fixed inset-0 z-[9999]",
        "flex flex-col items-center justify-center",
        "bg-[#020617]",
        "transition-opacity duration-500 ease-out",
        phase === 3 ? "opacity-0 pointer-events-none" : "opacity-100",
      ].join(" ")}
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(249,115,22,0.08) 0%, transparent 70%)",
        }}
      />

      <div className="relative flex flex-col items-center gap-8 px-8 w-full max-w-sm">
        {/* K App İkonu */}
        <div
          className={[
            "relative transition-all duration-700",
            phase >= 0 ? "opacity-100 scale-100" : "opacity-0 scale-75",
          ].join(" ")}
        >
          <div
            className="absolute inset-0 rounded-[28px] bg-orange-500/20 animate-ping"
            style={{ animationDuration: "1.8s" }}
          />
          <div
            className="absolute -inset-2 rounded-[32px] bg-orange-500/10 animate-pulse"
            style={{ animationDuration: "2.4s" }}
          />
          <div className="relative w-[88px] h-[88px] rounded-[24px] bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center shadow-[0_0_48px_rgba(249,115,22,0.5)]">
            <span className="text-white font-black text-3xl tracking-tight select-none">K</span>
          </div>
        </div>

        {/* Uygulama adı */}
        <div
          className={[
            "flex flex-col items-center gap-1 transition-all duration-700",
            phase >= 0 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
          ].join(" ")}
          style={{ transitionDelay: "150ms" }}
        >
          <h1 className="text-white text-[26px] font-black tracking-tight text-center leading-none">
            {APP_CONFIG.name}
          </h1>
          <p className="text-slate-500 text-xs font-medium tracking-widest uppercase text-center">
            {APP_CONFIG.tagline}
          </p>
          {/* Şehir badge */}
          <div className="flex items-center gap-1.5 mt-1">
            <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
            <span className="text-orange-400 text-[11px] font-semibold tracking-wide">
              {APP_CONFIG.activeCity.name}
            </span>
          </div>
        </div>

        {/* Partner Logolar (phase 1) */}
        <div
          className={[
            "flex items-center justify-center gap-5 transition-all duration-700",
            phase >= 1 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6",
          ].join(" ")}
        >
          <img
            src="/static/images/sbb_dark.png"
            alt="Samsun Büyükşehir Belediyesi"
            width={130} height={44}
            className="h-10 w-auto object-contain opacity-90 drop-shadow-md"
            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
          />
          <div className="h-8 w-px bg-slate-700 rounded-full" />
          <img
            src="/static/images/samulas_3.png"
            alt="Samulaş"
            width={100} height={44}
            className="h-10 w-auto object-contain opacity-90 drop-shadow-md"
            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
          />
        </div>

        {/* Geliştirici bilgisi (phase 2) */}
        <div
          className={[
            "flex flex-col items-center gap-2 transition-all duration-700",
            phase >= 2 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6",
          ].join(" ")}
        >
          <div className="w-32 h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
          <p className="text-slate-600 text-[10px] font-medium tracking-widest uppercase">
            Geliştirici
          </p>
          <div className="flex items-center gap-2">
            <span className="text-slate-300 text-sm font-bold">{APP_CONFIG.author}</span>
            <span className="text-slate-600 text-xs">·</span>
            <a
              href={APP_CONFIG.github}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors duration-200"
              onClick={(e) => e.stopPropagation()}
            >
              <GitHubIcon className="w-3.5 h-3.5" />
              <span className="text-[11px] font-medium">tarihcituranx</span>
            </a>
          </div>
        </div>

        {/* Yükleme çubuğu */}
        <div className={["w-full transition-all duration-700", phase >= 1 ? "opacity-100" : "opacity-0"].join(" ")}>
          <div className="w-full h-0.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-orange-500 to-orange-400 rounded-full transition-all duration-[2000ms] ease-out"
              style={{ width: phase >= 2 ? "100%" : phase >= 1 ? "60%" : "0%" }}
            />
          </div>
        </div>
      </div>

      {/* Alt not */}
      <div
        className={[
          "absolute bottom-8 left-0 right-0 flex flex-col items-center gap-2 transition-all duration-700",
          phase >= 2 ? "opacity-100" : "opacity-0",
        ].join(" ")}
      >
        {/* Versiyon bilgisi */}
        {versionInfo && (
          <button
            onClick={() => setShowReleaseNotes(true)}
            className="text-slate-500 text-[10px] font-medium hover:text-orange-400 transition-colors"
          >
            v{versionInfo.latest_version} · Yenilikler için tıkla
          </button>
        )}
        <span className="text-slate-700 text-[10px] text-center px-4">
          Gayri resmi, bağımsız vatandaş projesi • Veriler açık kaynaklardan derlenmektedir
        </span>
      </div>

      {/* Release Notes Modal (bilgi amaçlı, kapatılabilir) */}
      {showReleaseNotes && versionInfo && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/80 backdrop-blur-sm" onClick={() => setShowReleaseNotes(false)}>
          <div className="mx-4 rounded-2xl bg-[#0f172a] border border-slate-700 p-6 max-w-sm w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-white font-bold">v{versionInfo.latest_version} Yenilikleri</h2>
              <button onClick={() => setShowReleaseNotes(false)} className="text-slate-500 hover:text-white text-xl leading-none">×</button>
            </div>
            <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">{versionInfo.release_notes}</p>
            <button
              onClick={() => { setShowReleaseNotes(false); setShowSplash(false); }}
              className="mt-4 w-full rounded-xl bg-orange-500 py-2.5 text-sm font-bold text-white hover:bg-orange-400 transition-colors"
            >
              Harika! Başla
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SplashScreen;