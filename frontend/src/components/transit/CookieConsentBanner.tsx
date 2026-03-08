import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTransit } from "@/contexts/TransitContext";

const CookieConsentBanner = () => {
  const [visible, setVisible] = useState(false);
  const { setShowKVKK, setShowCookie } = useTransit();

  useEffect(() => {
    if (!localStorage.getItem("cerezOnay")) {
      setVisible(true);
    }
  }, []);

  const handleAccept = (value: string) => {
    localStorage.setItem("cerezOnay", value);
    setVisible(false);
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className="fixed bottom-20 left-4 right-4 z-[9998] glass-panel rounded-2xl p-4 border border-border/50 md:bottom-6 md:left-auto md:right-6 md:max-w-sm"
        >
          <p className="text-xs text-foreground leading-relaxed mb-3">
            🍪 Bu uygulama yalnızca işlevsellik için localStorage kullanır. Kişisel veriniz sunucuya aktarılmaz.
          </p>

          <div className="flex items-center gap-2 mb-3">
            <button
              onClick={() => setShowCookie(true)}
              className="text-[10px] text-primary hover:underline font-medium"
            >
              Çerez Politikası
            </button>
            <span className="text-muted-foreground text-[10px]">•</span>
            <button
              onClick={() => setShowKVKK(true)}
              className="text-[10px] text-primary hover:underline font-medium"
            >
              KVKK
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => handleAccept("zorunlu")}
              className="flex-1 rounded-xl border border-border py-2 text-xs font-medium text-foreground"
            >
              Yalnızca Zorunlu
            </button>
            <button
              onClick={() => handleAccept("1")}
              className="flex-1 rounded-xl bg-primary py-2 text-xs font-semibold text-primary-foreground"
            >
              Tamam, Anladım
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default CookieConsentBanner;
