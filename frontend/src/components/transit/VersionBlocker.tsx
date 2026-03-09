import { useState, useEffect } from "react";
import { fetchAppVersion } from "@/lib/api";
import { APP_CONFIG } from "@/contexts/TransitContext";
import { AlertTriangle, Download } from "lucide-react";

// Simple semantic version compare (e.g. "2.5.0" vs "2.0.0")
const isVersionOlder = (current: string, min: string) => {
    const cParts = current.split('.').map(Number);
    const mParts = min.split('.').map(Number);

    for (let i = 0; i < Math.max(cParts.length, mParts.length); i++) {
        const c = cParts[i] || 0;
        const m = mParts[i] || 0;
        if (c < m) return true;
        if (c > m) return false;
    }
    return false;
};

const VersionBlocker = () => {
    const [blocked, setBlocked] = useState(false);
    const [appData, setAppData] = useState<any>(null);

    // Detect if running inside a mobile app wrapper (WebView) or PWA
    const isMobileApp = () => {
        if (typeof window === "undefined" || typeof navigator === "undefined") return false;
        const ua = navigator.userAgent || navigator.vendor || (window as any).opera;
        const isAndroidWebView = ua.includes('wv');
        const isIOSWebView = /(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/i.test(ua);
        const isFlutter = !!(window as any).flutter_inappwebview;
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches || (navigator as any).standalone;

        return isAndroidWebView || isIOSWebView || isFlutter || isStandalone;
    };

    useEffect(() => {
        // Sadece mobil uygulama veya PWA (WebView) ortamındaysa engelleme yap
        if (!isMobileApp()) {
            return;
        }

        fetchAppVersion().then(data => {
            if (data) {
                setAppData(data);
                if (data.force_update || isVersionOlder(APP_CONFIG.version, data.min_version)) {
                    setBlocked(true);
                }
            }
        });
    }, []);

    if (!blocked || !appData) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/95 backdrop-blur-sm p-6">
            <div className="w-full max-w-sm rounded-[32px] border border-border/50 bg-card p-8 shadow-2xl text-center flex flex-col items-center">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-3xl bg-red-500/10 text-red-500">
                    <AlertTriangle className="h-8 w-8" />
                </div>

                <h2 className="mb-2 font-sora text-xl font-bold text-foreground">Güncelleme Gerekli</h2>
                <p className="mb-6 text-sm text-muted-foreground leading-relaxed">
                    Uygulamanın çalışmaya devam edebilmesi için yeni sürüme (v{appData.latest_version}) güncellenmesi gerekmektedir.
                </p>

                <a
                    href={appData.download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex w-full items-center justify-center gap-2 rounded-2xl bg-primary px-6 py-4 text-sm font-bold text-primary-foreground transition-transform active:scale-95"
                >
                    <Download className="h-4 w-4" />
                    Hemen Güncelle
                </a>
            </div>
        </div>
    );
};

export default VersionBlocker;
