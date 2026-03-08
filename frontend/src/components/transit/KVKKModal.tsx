import { motion, AnimatePresence } from "framer-motion";
import { useTransit } from "@/contexts/TransitContext";
import { APP_CONFIG } from "@/contexts/TransitContext";

const KVKKModal = () => {
  const { showKVKK, setShowKVKK } = useTransit();

  return (
    <AnimatePresence>
      {showKVKK && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowKVKK(false)} />
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="relative z-10 w-full max-w-lg max-h-[80vh] overflow-y-auto glass-panel rounded-2xl p-6 border border-border/50 scrollbar-hide"
          >
            <h2 className="font-sora text-lg font-bold text-foreground mb-1">🔒 KVKK Aydınlatma Metni</h2>
            <p className="text-xs text-muted-foreground mb-4">6698 Sayılı Kişisel Verilerin Korunması Kanunu</p>

            <section className="mb-4">
              <h3 className="font-sora text-sm font-semibold text-foreground mb-1">Veri Sorumlusu</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                <strong>{APP_CONFIG.name}</strong> uygulaması<br />
                Veri Sorumlusu: <strong>{APP_CONFIG.author}</strong> (Bireysel Geliştirici)<br />
                <a href={APP_CONFIG.github} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">github.com/tarihcituranx</a> · {APP_CONFIG.website.replace("https://", "")}<br />
                Son Güncelleme: Mart 2026
              </p>
            </section>

            <section className="mb-4">
              <h3 className="font-sora text-sm font-semibold text-foreground mb-2">İşlenen Veriler</h3>
              <div className="flex flex-col gap-2">
                <div className="glass-panel rounded-xl p-3">
                  <p className="text-xs font-semibold text-foreground mb-1">📍 Konum Verisi</p>
                  <p className="text-xs text-muted-foreground">Yalnızca oturum süresince tarayıcı belleğinde tutulur, sunucuya GÖNDERİLMEZ.</p>
                </div>
                <div className="glass-panel rounded-xl p-3">
                  <p className="text-xs font-semibold text-foreground mb-1">💾 localStorage Anahtarları</p>
                  <p className="text-xs text-muted-foreground">Tema, bildirim gizleme, uygulama ayarları — yalnızca cihazda saklanır.</p>
                </div>
                <div className="glass-panel rounded-xl p-3">
                  <p className="text-xs font-semibold text-foreground mb-1">🌐 Üçüncü Taraf Hizmetler</p>
                  <ul className="text-xs text-muted-foreground space-y-1 mt-1">
                    <li>• <strong>OpenStreetMap / CartoDB:</strong> Harita görselleri</li>
                    <li>• <strong>Nominatim / OSM:</strong> Adres çözümleme (koordinat gönderilir)</li>
                    <li>• <strong>OSRM:</strong> Rota hesaplama (koordinatlar gönderilir)</li>
                    <li>• <strong>Google Fonts:</strong> Yazı tipi yükleme (IP adresi Google'a iletilir)</li>
                  </ul>
                </div>
              </div>
            </section>

            <section className="mb-4">
              <h3 className="font-sora text-sm font-semibold text-foreground mb-1">Haklarınız (KVKK Md. 11)</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Bilgi alma, düzeltme, silme hakları bulunmaktadır. Uygulama kişisel veri depolamadığından
                localStorage'ı tarayıcı ayarlarından silebilirsiniz.
              </p>
            </section>

            <section className="mb-5">
              <h3 className="font-sora text-sm font-semibold text-foreground mb-1">Yasal Dayanak</h3>
              <p className="text-xs text-muted-foreground">6698 sayılı Kişisel Verilerin Korunması Kanunu</p>
            </section>

            <button
              onClick={() => setShowKVKK(false)}
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

export default KVKKModal;