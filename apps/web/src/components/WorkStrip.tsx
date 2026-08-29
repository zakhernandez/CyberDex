import Link from "next/link";
import type { WorkListItem } from "@/types/api";
import { WorkCard } from "./WorkCard";

export function WorkStrip({
  title,
  works,
  viewAllHref,
}: {
  title: string;
  works: WorkListItem[];
  viewAllHref?: string;
}) {
  if (works.length === 0) return null;

  return (
    <section>
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="font-display text-2xl font-bold uppercase tracking-wide">
          {title}
        </h2>
        {viewAllHref && (
          <Link
            href={viewAllHref}
            className="font-mono text-xs uppercase tracking-widest text-foreground-muted hover:text-primary transition-colors"
          >
            view all →
          </Link>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {works.slice(0, 6).map((work) => (
          <WorkCard key={work.id} work={work} />
        ))}
      </div>
    </section>
  );
}