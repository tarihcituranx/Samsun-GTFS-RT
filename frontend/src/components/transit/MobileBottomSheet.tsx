import React, { useRef, useState, useCallback } from "react";
import { motion, PanInfo, useMotionValue, useTransform, animate } from "framer-motion";

interface MobileBottomSheetProps {
  children: React.ReactNode;
}

// Bottom nav height + safe area
const BOTTOM_NAV = 60;
// Snap percentages of viewport
const SNAPS = [0.22, 0.5, 0.92];

const MobileBottomSheet: React.FC<MobileBottomSheetProps> = ({ children }) => {
  const [snapIdx, setSnapIdx] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  const getVH = () => window.visualViewport?.height ?? window.innerHeight;

  const snapHeight = (i: number) => getVH() * SNAPS[i];

  const handleDragEnd = useCallback(
    (_: any, info: PanInfo) => {
      const vy = info.velocity.y;
      const oy = info.offset.y;

      let next = snapIdx;
      if (vy < -400 || oy < -80) {
        next = Math.min(2, snapIdx + 1);
      } else if (vy > 400 || oy > 80) {
        next = Math.max(0, snapIdx - 1);
      }
      setSnapIdx(next);

      // Reset scroll when collapsing
      if (next < snapIdx && scrollRef.current) {
        scrollRef.current.scrollTop = 0;
      }
    },
    [snapIdx]
  );

  const handleSnapClick = () => {
    // Tap on handle cycles: 0→1, 1→2, 2→0
    setSnapIdx((prev) => (prev + 1) % 3);
  };

  return (
    <motion.div
      className="fixed left-0 right-0 z-30 flex flex-col rounded-t-3xl md:hidden"
      style={{
        bottom: `calc(${BOTTOM_NAV}px + env(safe-area-inset-bottom, 0px))`,
        background: "hsl(var(--surface-glass) / 0.95)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderTop: "1px solid hsl(var(--border) / 0.2)",
        boxShadow: "0 -4px 30px hsl(var(--background) / 0.3)",
      }}
      animate={{ height: snapHeight(snapIdx) }}
      transition={{ type: "spring", stiffness: 380, damping: 38 }}
    >
      {/* ─── Drag Handle ─── */}
      <motion.div
        className="flex shrink-0 cursor-grab items-center justify-center py-3 active:cursor-grabbing"
        drag="y"
        dragConstraints={{ top: 0, bottom: 0 }}
        dragElastic={0}
        onDragEnd={handleDragEnd}
        onClick={handleSnapClick}
      >
        <div className="h-[5px] w-10 rounded-full bg-muted-foreground/30" />
      </motion.div>

      {/* ─── Scrollable Content ─── */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto overscroll-contain scrollbar-hide"
        style={{ paddingBottom: 24 }}
      >
        {children}
      </div>
    </motion.div>
  );
};

export default MobileBottomSheet;
