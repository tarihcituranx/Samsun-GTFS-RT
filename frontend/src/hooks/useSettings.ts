import { useState, useCallback, useEffect } from "react";

export interface Settings {
  showHasilat: boolean;
  showLabels: boolean;
  showRoute: boolean;
  autoRefresh: boolean;
  showAllStops: boolean;
  // Erişilebilirlik
  fontSize: "normal" | "large" | "xlarge";
  highContrast: boolean;
  reducedMotion: boolean;
  elderlyMode: boolean;
}

const DEFAULTS: Settings = {
  showHasilat: false,
  showLabels: true,
  showRoute: true,
  autoRefresh: true,
  showAllStops: false,
  fontSize: "normal",
  highContrast: false,
  reducedMotion: false,
  elderlyMode: false,
};

const getBoolean = (key: string, defaultValue: boolean): boolean => {
  const val = localStorage.getItem(key);
  if (val === null) return defaultValue;
  return val === "1";
};

const getString = <T extends string>(key: string, defaultValue: T): T => {
  const val = localStorage.getItem(key);
  if (val === null) return defaultValue;
  return val as T;
};

// Yaşlı modu otomatik algılama: büyük ekran + dokunmatik + yavaş bağlantı ipuçları
const detectElderlyHints = (): boolean => {
  if (typeof window === "undefined") return false;
  // Kullanıcı daha önce tercih yaptıysa algılama
  if (localStorage.getItem("elderlyMode") !== null) return false;
  // prefers-reduced-motion + büyük font tercihi birlikte → muhtemel yaşlı kullanıcı
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // OS-level büyük font kontrolü (>16px base genelde yaşlı/erişilebilirlik ayarı)
  const largeFontHint = parseFloat(getComputedStyle(document.documentElement).fontSize) > 18;
  return prefersReduced && largeFontHint;
};

export const useSettings = () => {
  const [revision, setRevision] = useState(0);

  const settings: Settings = {
    showHasilat: getBoolean("showHasilat", DEFAULTS.showHasilat),
    showLabels: getBoolean("showLabels", DEFAULTS.showLabels),
    showRoute: getBoolean("showRoute", DEFAULTS.showRoute),
    autoRefresh: getBoolean("autoRefresh", DEFAULTS.autoRefresh),
    showAllStops: getBoolean("showAllStops", DEFAULTS.showAllStops),
    fontSize: getString("fontSize", DEFAULTS.fontSize),
    highContrast: getBoolean("highContrast", DEFAULTS.highContrast),
    reducedMotion: getBoolean("reducedMotion", DEFAULTS.reducedMotion),
    elderlyMode: getBoolean("elderlyMode", DEFAULTS.elderlyMode),
  };

  const setSetting = useCallback((key: keyof Settings, value: boolean | string) => {
    if (typeof value === "boolean") {
      localStorage.setItem(key, value ? "1" : "0");
    } else {
      localStorage.setItem(key, value);
    }
    setRevision((r) => r + 1);
  }, []);

  const resetAll = useCallback(() => {
    [
      "showHasilat", "showLabels", "showRoute", "autoRefresh", "showAllStops",
      "fontSize", "highContrast", "reducedMotion", "elderlyMode",
      "theme", "cerezOnay", "userLoc", "hideInfoModal",
    ].forEach((k) => localStorage.removeItem(k));
    setRevision((r) => r + 1);
  }, []);

  // Yaşlı modu otomatik algılama (ilk yükleme)
  useEffect(() => {
    if (detectElderlyHints() && !settings.elderlyMode) {
      setSetting("elderlyMode", true);
      setSetting("fontSize", "xlarge");
      setSetting("reducedMotion", true);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // CSS sınıflarını <html>'e uygula
  useEffect(() => {
    const root = document.documentElement;

    // Font boyutu
    root.classList.remove("text-scale-normal", "text-scale-large", "text-scale-xlarge");
    const effectiveSize = settings.elderlyMode ? "xlarge" : settings.fontSize;
    root.classList.add(`text-scale-${effectiveSize}`);

    // Yüksek kontrast
    root.classList.toggle("high-contrast", settings.highContrast || settings.elderlyMode);

    // Azaltılmış hareket
    root.classList.toggle("force-reduced-motion", settings.reducedMotion || settings.elderlyMode);
  }, [settings.fontSize, settings.highContrast, settings.reducedMotion, settings.elderlyMode, revision]);

  return { settings, setSetting, resetAll };
};
