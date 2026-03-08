import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";

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

const AppFooter = () => {
  const { setShowKVKK, setShowCookie } = useTransit();

  return (
    <footer className="mt-6 border-t border-border/30 pt-4 pb-2">
      {/* Marka */}
      <div className="text-center mb-2">
        <div className="font-sora font-bold text-foreground">{APP_CONFIG.name}</div>
        <div className="text-[10px] text-muted-foreground">
          Gayri resmi, bağımsız vatandaş projesi
        </div>
      </div>

      {/* Geliştirici */}
      <div className="text-center text-[10px] text-muted-foreground mb-1">
        Geliştirici:{" "}
        <a
          href={APP_CONFIG.github}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary font-semibold hover:underline"
        >
          {APP_CONFIG.author}
        </a>
      </div>

      {/* İletişim */}
      <p className="mb-2 text-center text-[10px] text-muted-foreground">
        📞 Samsun içi <a href="tel:153" className="text-primary hover:underline">153</a> ·{" "}
        <a href="tel:03624311012" className="text-primary hover:underline">0362 431 10 12</a>
      </p>

      {/* Linkler */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        <a
          href={APP_CONFIG.github}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground"
        >
          <GitHubIcon className="w-3 h-3" /> tarihcituranx
        </a>
        <a href="https://samsunkesfet.com" target="_blank" rel="noopener noreferrer" className="text-[10px] text-muted-foreground hover:text-foreground">
          🏛️ samsunkesfet.com
        </a>
        <button onClick={() => setShowKVKK(true)} className="text-[10px] text-muted-foreground hover:text-foreground">
          🔒 KVKK
        </button>
        <button onClick={() => setShowCookie(true)} className="text-[10px] text-muted-foreground hover:text-foreground">
          🍪 Çerez Politikası
        </button>
      </div>

      {/* Versiyon */}
      <div className="mt-2 text-center text-[9px] text-muted-foreground/50">
        {APP_CONFIG.website.replace("https://", "")} · {APP_CONFIG.activeCity.name} · 2026
      </div>
    </footer>
  );
};

export default AppFooter;