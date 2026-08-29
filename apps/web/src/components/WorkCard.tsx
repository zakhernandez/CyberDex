import Image from "next/image";
import Link from "next/link";

import type { WorkListItem } from "@/types/api";

import { KindBadge } from "./KindBadge";

export function WorkCard({ work }: { work: WorkListItem }) {
  return (
    <Link
      href={`/works/${work.slug}`}
      className="group block bg-surface border border-border hover:border-primary transition-colors duration-[var(--duration-med)] ease-[var(--ease-sharp)]"
    >
      <div className="relative aspect-[2/3] bg-background overflow-hidden">
        {work.cover_url ? (
          <Image
            src={work.cover_url}
            alt={work.title}
            fill
            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 25vw, 200px"
            className="object-cover transition-opacity duration-[var(--duration-med)] group-hover:opacity-90"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-foreground-dim font-mono text-xs">
            no cover
          </div>
        )}
        <div className="absolute top-2 left-2">
          <KindBadge kind={work.kind} />
        </div>
      </div>

      <div className="p-3">
        <h3 className="font-display text-base font-semibold leading-tight text-foreground group-hover:text-primary transition-colors line-clamp-2">
          {work.title}
        </h3>
        {work.year && (
          <p className="mt-1 font-mono text-xs text-foreground-muted">
            {work.year}
          </p>
        )}
      </div>
    </Link>
  );
}