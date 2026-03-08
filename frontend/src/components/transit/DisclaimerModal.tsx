import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";

const DisclaimerModal = () => {
  const [open, setOpen] = useState(false);
  const [hideForever, setHideForever] = useState(false);
  const { setShowKVKK, setShowCookie } = useTransit();

  useEffect(() => {
    if (localStorage.getItem("hideInfoModal") !== "true") {
      setOpen(true);
    }
  }, []);

  const handleClose = () => {
    if (hideForever) {
      localStorage.setItem("hideInfoModal", "true");
    }
    setOpen(false);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleClose} />
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="relative z-10 w-full max-w-md glass-panel rounded-2xl p-6 border border-border/50"
          >
            <h2 className="font-sora text-lg font-bold text-primary mb-3">⚠️ Önemli Bilgilendirme</h2>

            <p className="text-sm text-foreground leading-relaxed mb-3">
              <strong>{APP_CONFIG.name}</strong>, <strong>{APP_CONFIG.author}</strong> tarafından geliştirilen,{" "}
              <strong>Samsun Büyükşehir Belediyesi veya Samulaş ile hiçbir resmi bağlantısı bulunmayan</strong>{" "}
              bağımsız bir vatandaş projesidir.
            </p>

            <p className="text-sm text-muted-foreground leading-relaxed mb-4">
              Gösterilen fiyatlar, sefer saatleri ve araç konumları tahmini veya gecikmiş olabilir.
            </p>

            <div className="flex flex-col gap-2 mb-4">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <span>📞</span>
                <a href="tel:153" className="text-primary hover:underline font-medium">Samsun içi: 153</a>
                <span className="text-muted-foreground">|</span>
                <a href="tel:03624311012" className="text-primary hover:underline font-medium">0362 431 10 12</a>
              </div>
            </div>

            <div className="flex gap-2 mb-4">
              <button
                onClick={() => { setOpen(false); setShowKVKK(true); }}
                className="text-xs text-primary hover:underline font-medium"
              >
                KVKK Aydınlatma
              </button>
              <span className="text-muted-foreground">•</span>
              <button
                onClick={() => { setOpen(false); setShowCookie(true); }}
                className="text-xs text-primary hover:underline font-medium"
              >
                Çerez Politikası
              </button>
            </div>

            <label className="flex items-center gap-2 mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={hideForever}
                onChange={(e) => setHideForever(e.target.checked)}
                className="h-4 w-4 rounded border-border accent-primary"
              />
              <span className="text-xs text-muted-foreground">Bir daha gösterme</span>
            </label>

            <button
              onClick={handleClose}
              className="w-full rounded-xl bg-primary py-2.5 text-sm font-semibold text-primary-foreground"
            >
              Anladım
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default DisclaimerModal;