import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { mockLines } from "@/data/mockData";

const TOAST_MESSAGES = [
  { type: "delay" as const, lineCode: "E1", message: "hattında 5 dk gecikme" },
  { type: "arrival" as const, lineCode: "T1", message: "durağınıza 2 dakikada ulaşıyor" },
  { type: "info" as const, lineCode: "V1", message: "sefer saatleri güncellendi" },
  { type: "delay" as const, lineCode: "19", message: "hattında yoğunluk var" },
  { type: "arrival" as const, lineCode: "E2", message: "durağınıza yaklaşıyor" },
  { type: "info" as const, lineCode: "R1", message: "hattı normal seferlere döndü" },
];

const ToastSystem = () => {
  const indexRef = useRef(0);

  useEffect(() => {
    // Fire first toast after 15s, then every 20–40s
    const firstTimeout = setTimeout(() => {
      fireToast();
      const interval = setInterval(fireToast, 20000 + Math.random() * 20000);
      return () => clearInterval(interval);
    }, 15000);

    return () => clearTimeout(firstTimeout);
  }, []);

  const fireToast = () => {
    const msg = TOAST_MESSAGES[indexRef.current % TOAST_MESSAGES.length];
    indexRef.current++;
    const line = mockLines.find((l) => l.code === msg.lineCode);

    if (msg.type === "delay") {
      toast.error(`🚨 ${msg.lineCode} ${msg.message}`, {
        description: line?.name,
        duration: 4000,
      });
    } else if (msg.type === "arrival") {
      toast.success(`🟢 ${msg.lineCode} ${msg.message}`, {
        description: line?.name,
        duration: 4000,
      });
    } else {
      toast.info(`ℹ️ ${msg.lineCode} ${msg.message}`, {
        description: line?.name,
        duration: 4000,
      });
    }
  };

  return null;
};

export default ToastSystem;
