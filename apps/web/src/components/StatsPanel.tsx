import type { CatalogStats } from "@/types/api";

const kindLabels: Record<string, string> = {
  FILM: "films",
  BOOK: "books",
  ANIME: "anime",
};

export function StatsPanel({ stats }: { stats: CatalogStats }) {
  return (
    <div className="border border-border bg-surface p-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div>
          <div className="font-mono text-xs uppercase tracking-widest text-foreground-muted mb-2">
            works
          </div>
          <div className="font-display text-3xl font-bold text-primary">
            {stats.total_works.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="font-mono text-xs uppercase tracking-widest text-foreground-muted mb-2">
            creators
          </div>
          <div className="font-display text-3xl font-bold text-foreground">
            {stats.total_creators.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="font-mono text-xs uppercase tracking-widest text-foreground-muted mb-2">
            ratings
          </div>
          <div className="font-display text-3xl font-bold text-foreground">
            {stats.total_ratings.toLocaleString()}
          </div>
        </div>
      </div>

      {stats.by_kind.length > 0 && (
        <div className="mt-6 pt-6 border-t border-border">
          <div className="flex flex-wrap gap-6">
            {stats.by_kind.map((row) => (
              <div key={row.kind} className="flex items-baseline gap-2">
                <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted">
                  {kindLabels[row.kind] ?? row.kind.toLowerCase()}
                </span>
                <span className="font-mono text-sm text-foreground">
                  {row.count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}