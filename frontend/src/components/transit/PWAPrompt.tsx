import { useRegisterSW } from 'virtual:pwa-register/react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, X } from 'lucide-react';

const PWAPrompt = () => {
    const {
        needRefresh: [needRefresh, setNeedRefresh],
        updateServiceWorker,
    } = useRegisterSW({
        onRegistered(r) {
            console.log('SW Registered: ' + r);
        },
        onRegisterError(error) {
            console.log('SW registration error', error);
        },
    });

    const close = () => {
        setNeedRefresh(false);
    };

    return (
        <AnimatePresence>
            {needRefresh && (
                <motion.div
                    initial={{ opacity: 0, y: 50, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 50, scale: 0.9 }}
                    className="fixed bottom-20 left-1/2 -translate-x-1/2 z-[100] w-[90%] max-w-sm rounded-2xl bg-primary text-primary-foreground p-4 shadow-2xl shadow-primary/30 flex items-center justify-between gap-3"
                >
                    <div className="flex items-center gap-3">
                        <div className="bg-primary-foreground/20 p-2 rounded-full animate-spin-slow">
                            <RefreshCw className="h-5 w-5" />
                        </div>
                        <div>
                            <p className="font-sora font-bold text-sm">Yeni Güncelleme!</p>
                            <p className="text-xs opacity-90 mt-0.5">Uygulama güncellendi. Yeni özellikleri görmek için yenileyin.</p>
                        </div>
                    </div>
                    <div className="flex flex-col gap-2 shrink-0">
                        <button
                            onClick={() => updateServiceWorker(true)}
                            className="bg-primary-foreground text-primary text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-primary-foreground/90 transition-colors"
                        >
                            Yenile
                        </button>
                        <button
                            onClick={close}
                            className="text-primary-foreground/70 hover:text-primary-foreground text-xs p-1"
                        >
                            Sonra
                        </button>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default PWAPrompt;
