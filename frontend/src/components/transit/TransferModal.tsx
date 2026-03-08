import { motion } from "framer-motion";
import { X } from "lucide-react";
import { transferRules } from "@/data/mockData";

interface TransferModalProps {
  open: boolean;
  onClose: () => void;
}

const TransferModal = ({ open, onClose }: TransferModalProps) => {
  if (!open) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[90] flex items-center justify-center bg-foreground/20 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="glass-panel w-full max-w-md rounded-3xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-sora text-lg font-bold text-foreground">🔄 Aktarma Kuralları</h3>
          <button onClick={onClose} className="text-muted-foreground" aria-label="Kapat">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mb-4 flex flex-col gap-2 text-sm">
          <div className="flex justify-between text-muted-foreground">
            <span>Süre Limiti</span>
            <span className="font-mono font-semibold text-foreground">90 dakika</span>
          </div>
          <div className="flex justify-between text-muted-foreground">
            <span>Max Aktarma</span>
            <span className="font-mono font-semibold text-foreground">3</span>
          </div>
        </div>

        <div className="rounded-xl bg-accent/50 overflow-hidden">
          <div className="grid grid-cols-3 gap-px bg-border text-xs font-semibold text-muted-foreground px-3 py-2">
            <span>Kart Türü</span>
            <span className="text-center">İndirim</span>
            <span className="text-right">Ücret</span>
          </div>
          {transferRules.map((rule) => (
            <div key={rule.type} className="grid grid-cols-3 gap-px px-3 py-2.5 text-sm border-t border-border/50">
              <span className="font-medium text-foreground">{rule.type}</span>
              <span className="text-center text-muted-foreground">{rule.discount}</span>
              <span className="text-right font-mono font-semibold text-foreground">{rule.fare}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default TransferModal;
