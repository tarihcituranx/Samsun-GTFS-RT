import { motion, AnimatePresence } from "framer-motion";
import { useTransit } from "@/contexts/TransitContext";

const cookieTable = [
  { key: "theme", purpose: "Aydınlık/Karanlık tema tercihi", duration: "Süresiz" },
  { key: "hideInfoModal", purpose: "Açılış bildirimini gizle", duration: "Süresiz" },
  { key: "userLoc", purpose: "Son bilinen konum", duration: "Süresiz" },
  { key: "cerezOnay", purpose: "Çerez onay durumu", duration: "Süresiz" },
];

const thirdParty = [
  { name: "CartoDB", desc: "Harita tile sunucusu" },
  { name: "Nominatim (OSM)", desc: "Adres çözümleme — koordinat gönderilir" },
  { name: "OSRM", desc: "Rota hesaplama — koordinatlar gönderilir" },
  { name: "Google Fonts", desc: "Yazı tipi — IP adresi iletilir" },
];

const CookieModal = () => {
  const { showCookie, setShowCookie } = useTransit();

  return (
    <AnimatePresence>
      {showCookie && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowCookie(false)} />
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="relative z-10 w-full max-w-lg max-h-[80vh] overflow-y-auto glass-panel rounded-2xl p-6 border border-border/50 scrollbar-hide"
          >
            <h2 className="font-sora text-lg font-bold text-foreground mb-3">🍪 Çerez Politikası</h2>

            <p className="text-sm text-muted-foreground leading-relaxed mb-4">
              <strong className="text-foreground">Kentli</strong>, HTTP çerezi <strong className="text-foreground">kullanmamaktadır</strong>. Yalnızca <code className="text-xs bg-accent px-1 py-0.5 rounded">localStorage</code> kullanılır.
            </p>

            <div className="overflow-x-auto mb-4">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 px-2 font-semibold text-foreground">Anahtar</th>
                    <th className="text-left py-2 px-2 font-semibold text-foreground">Amaç</th>
                    <th className="text-left py-2 px-2 font-semibold text-foreground">Süre</th>
                  </tr>
                </thead>
                <tbody>
                  {cookieTable.map((row) => (
                    <tr key={row.key} className="border-b border-border/50">
                      <td className="py-2 px-2 font-mono text-primary">{row.key}</td>
                      <td className="py-2 px-2 text-muted-foreground">{row.purpose}</td>
                      <td className="py-2 px-2 text-muted-foreground">{row.duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <section className="mb-4">
              <h3 className="font-sora text-sm font-semibold text-foreground mb-2">Üçüncü Taraf Transferleri</h3>
              <div className="flex flex-col gap-1.5">
                {thirdParty.map((tp) => (
                  <div key={tp.name} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <span className="text-primary">•</span>
                    <span><strong className="text-foreground">{tp.name}:</strong> {tp.desc}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="mb-5">
              <h3 className="font-sora text-sm font-semibold text-foreground mb-1">Verileri Nasıl Silersiniz?</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Tarayıcı Ayarları → Gizlilik → Çerezler ve Site Verileri → Tüm verileri temizle. Veya tarayıcı konsolunda{" "}
                <code className="bg-accent px-1 py-0.5 rounded">localStorage.clear()</code> komutunu çalıştırın.
              </p>
            </section>

            <button
              onClick={() => setShowCookie(false)}
              className="w-full rounded-xl bg-primary py-2.5 text-sm font-semibold text-primary-foreground"
            >
              Anladım, Kapat
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default CookieModal;