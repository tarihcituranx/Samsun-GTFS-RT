import { useState, useEffect } from "react";
import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";
import { fetchAppVersion } from "@/lib/api";

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

const AboutTab = () => {
  const { setShowKVKK, setShowCookie } = useTransit();
  const [appData, setAppData] = useState<any>(null);

  useEffect(() => {
    fetchAppVersion().then(data => {
      if (data) setAppData(data);
    });
  }, []);

  return (
    <div className="space-y-6">
      {/* App Header */}
      <div className="text-center">
        <h2 className="font-sora text-2xl font-bold text-foreground">{APP_CONFIG.name}</h2>
        <p className="text-sm text-primary font-medium">{APP_CONFIG.tagline}</p>
        <span className="mt-1 inline-block rounded-full bg-accent px-3 py-0.5 text-[10px] font-mono text-muted-foreground">
          v{APP_CONFIG.version}
        </span>
      </div>

      {appData && (
        <section className="rounded-2xl border border-border/30 bg-accent/50 p-4 space-y-2">
          <h3 className="font-sora text-sm font-bold text-foreground">✨ Yenilikler (v{appData.latest_version})</h3>
          <div className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">
            {appData.release_notes}
          </div>
          {appData.latest_version !== APP_CONFIG.version && (
            <a href={appData.download_url} target="_blank" className="mt-2 block w-full rounded-lg bg-primary/20 p-2 text-center text-xs font-semibold text-primary transition-colors hover:bg-primary/30">
              Güncelleme Mevcut İndir
            </a>
          )}
        </section>
      )}

      {/* Uygulama Hakkında */}
      <section className="rounded-2xl border border-border/30 bg-accent/50 p-4 space-y-2">
        <h3 className="font-sora text-sm font-bold text-foreground">📱 Uygulama Hakkında</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {APP_CONFIG.name}, {APP_CONFIG.activeCity.name} şehrinin toplu taşıma sistemini daha erişilebilir
          hale getirmek amacıyla geliştirilmiş bağımsız bir vatandaş projesidir.
        </p>
        <p className="text-xs text-muted-foreground/70 italic">
          Bu uygulama Samsun Büyükşehir Belediyesi veya Samulaş ile resmi bir bağlantıya sahip değildir.
        </p>
      </section>

      {/* Geliştirici */}
      <section className="rounded-2xl border border-border/30 bg-accent/50 p-4 space-y-3">
        <h3 className="font-sora text-sm font-bold text-foreground">👨‍💻 Geliştirici</h3>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
            <GitHubIcon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">{APP_CONFIG.author}</p>
            <a
              href={APP_CONFIG.github}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary hover:underline"
            >
              github.com/tarihcituranx
            </a>
          </div>
        </div>
        <a
          href={APP_CONFIG.website}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block text-xs text-primary hover:underline"
        >
          🌐 {APP_CONFIG.website.replace("https://", "")}
        </a>
      </section>

      {/* İletişim */}
      <section className="rounded-2xl border border-border/30 bg-accent/50 p-4 space-y-2">
        <h3 className="font-sora text-sm font-bold text-foreground">📞 İletişim & Destek</h3>
        <p className="text-sm text-muted-foreground">
          Samulaş resmi iletişim hatları:
        </p>
        <div className="flex flex-wrap gap-3">
          <a href="tel:153" className="rounded-xl bg-primary/10 px-4 py-2 text-sm font-semibold text-primary hover:bg-primary/20 transition-colors">
            📞 153 <span className="text-xs font-normal">(Samsun içi)</span>
          </a>
          <a href="tel:03624311012" className="rounded-xl bg-primary/10 px-4 py-2 text-sm font-semibold text-primary hover:bg-primary/20 transition-colors">
            📞 0362 431 10 12
          </a>
        </div>
        <div className="flex flex-col gap-2 mt-4">
          <a href="https://samsulas.com.tr/" target="_blank" className="flex items-center gap-2 rounded-xl border border-border/30 bg-accent/20 px-4 py-3 text-sm text-foreground hover:bg-accent/40 transition-colors text-left">
            <span>🚃</span>
            <div>
              <p className="font-medium">Samulaş Resmi Web Sitesi</p>
              <p className="text-xs text-muted-foreground">samsulas.com.tr</p>
            </div>
          </a>
          <a href="https://samsunkesfet.com/" target="_blank" className="flex items-center gap-2 rounded-xl border border-border/30 bg-accent/20 px-4 py-3 text-sm text-foreground hover:bg-accent/40 transition-colors text-left">
            <span>🗺️</span>
            <div>
              <p className="font-medium">Samsun Keşfet</p>
              <p className="text-xs text-muted-foreground">samsunkesfet.com</p>
            </div>
          </a>
        </div>
      </section>

      {/* Yasal */}
      <section className="rounded-2xl border border-border/30 bg-accent/50 p-4 space-y-3">
        <h3 className="font-sora text-sm font-bold text-foreground">📜 Yasal Bilgiler</h3>
        <div className="flex flex-col gap-2">
          <button
            onClick={() => setShowKVKK(true)}
            className="flex items-center gap-2 rounded-xl bg-muted/50 px-4 py-3 text-sm text-foreground hover:bg-muted transition-colors text-left"
          >
            <span>🔒</span>
            <div>
              <p className="font-medium">KVKK Aydınlatma Metni</p>
              <p className="text-xs text-muted-foreground">Kişisel verilerin korunması hakkında</p>
            </div>
          </button>
          <button
            onClick={() => setShowCookie(true)}
            className="flex items-center gap-2 rounded-xl bg-muted/50 px-4 py-3 text-sm text-foreground hover:bg-muted transition-colors text-left"
          >
            <span>🍪</span>
            <div>
              <p className="font-medium">Çerez Politikası</p>
              <p className="text-xs text-muted-foreground">Çerez ve yerel depolama kullanımı</p>
            </div>
          </button>
        </div>
        <p className="text-xs text-muted-foreground/60 leading-relaxed">
          Gösterilen fiyatlar, sefer saatleri ve araç konumları tahmini veya gecikmiş olabilir.
          Kesin bilgi için lütfen Samulaş resmi kanallarını kullanın.
        </p>
      </section>

      {/* Footer */}
      <div className="text-center pb-4">
        <p className="text-[10px] text-muted-foreground/50">
          {APP_CONFIG.website.replace("https://", "")} · {APP_CONFIG.activeCity.name} · 2026
        </p>
      </div>
    </div>
  );
};

export default AboutTab;
