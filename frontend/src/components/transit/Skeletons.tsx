const SkeletonCard = ({ className = "" }: { className?: string }) => (
  <div className={`glass-panel rounded-2xl p-4 animate-pulse ${className}`}>
    <div className="flex items-center gap-3">
      <div className="h-12 w-12 rounded-xl bg-muted" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-3/4 rounded bg-muted" />
        <div className="h-3 w-1/2 rounded bg-muted" />
      </div>
    </div>
    <div className="mt-3 h-1.5 w-full rounded-full bg-muted" />
  </div>
);

const SkeletonList = ({ count = 5 }: { count?: number }) => (
  <div className="flex flex-col gap-2">
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonCard key={i} />
    ))}
  </div>
);

const SkeletonStats = () => (
  <div className="grid grid-cols-3 gap-2 animate-pulse">
    {[1, 2, 3].map((i) => (
      <div key={i} className="glass-panel rounded-xl p-3 text-center">
        <div className="h-7 w-12 mx-auto rounded bg-muted" />
        <div className="h-3 w-16 mx-auto mt-2 rounded bg-muted" />
      </div>
    ))}
  </div>
);

export { SkeletonCard, SkeletonList, SkeletonStats };
