import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import { Container } from "@/components/Container";
import { KindBadge } from "@/components/KindBadge";
import { RatingWidget } from "@/components/RatingWidget";
import { apiFetch } from "@/lib/api";
import type { RatingWithWork, WorkDetail } from "@/types/api";

interface WorkPageProps {
  params: Promise<{ slug: string }>;
}

async function getWork(slug: string): Promise<WorkDetail | null> {
  try {
    const res = await apiFetch(`/api/works/${slug}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`API ${res.status}`);
    return res.json();
  } catch {
    return null;
  }
}

async function getMyRatingForWork(workId: number): Promise<number | null> {
  try {
    const res = await apiFetch("/api/ratings?limit=200");
    if (!res.ok) return null;
    const ratings: RatingWithWork[] = await res.json();
    const found = ratings.find((r) => r.work.id === workId);
    return found ? found.score : null;
  } catch {
    return null;
  }
}

function formatRuntime(minutes: number | null | undefined): string | null {
  if (!minutes) return null;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

function groupCreatorsByRole(work: WorkDetail) {
  const groups: Record<string, string[]> = {};
  for (const wc of work.creators) {
    const role = wc.role.toLowerCase();
    if (!groups[role]) groups[role] = [];
    groups[role].push(wc.creator.name);
  }
  return groups;
}

const ROLE_LABELS: Record<string, string> = {
  director: "directed by",
  screenwriter: "written by",
  author: "written by",
  studio: "studio",
  mangaka: "mangaka",
  novelist: "novelist",
  composer: "score by",
};

export default async function WorkPage({ params }: WorkPageProps) {
  const { slug } = await params;
  const work = await getWork(slug);
  if (!work) notFound();

  const session = await auth();
  const myScore = session ? await getMyRatingForWork(work.id) : null;

  const creatorsByRole = groupCreatorsByRole(work);
  const runtime = formatRuntime(work.film?.runtime_minutes);

  return (
    <Container className="py-8">
      <Link
        href="/browse"
        className="font-mono text-xs uppercase tracking-widest text-foreground-muted hover:text-primary transition-colors"
      >
        ← back to catalog
      </Link>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-[280px_1fr] gap-8">
        <div>
          <div className="relative aspect-[2/3] bg-surface border border-border">
            {work.cover_url ? (
              <Image
                src={work.cover_url}
                alt={work.title}
                fill
                sizes="280px"
                className="object-cover"
                priority
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-foreground-dim font-mono text-xs">
                no cover
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <KindBadge kind={work.kind} />
              {work.year && (
                <span className="font-mono text-xs text-foreground-muted">
                  {work.year}
                </span>
              )}
              {work.original_language && (
                <span className="font-mono text-xs text-foreground-muted uppercase">
                  {work.original_language}
                </span>
              )}
            </div>
            <h1 className="font-display text-4xl font-bold leading-tight">
              {work.title}
            </h1>
            {work.original_title && work.original_title !== work.title && (
              <p className="mt-1 text-foreground-muted italic">
                {work.original_title}
              </p>
            )}
          </div>

          {work.film?.tagline && (
            <p className="font-display text-xl text-foreground-muted italic">
              &ldquo;{work.film.tagline}&rdquo;
            </p>
          )}

          {work.synopsis && (
            <div className="text-foreground leading-relaxed max-w-2xl whitespace-pre-line">
              {work.synopsis}
            </div>
          )}

          <div className="border-t border-border pt-6 space-y-3">
            {Object.entries(creatorsByRole).map(([role, names]) => (
              <div key={role} className="flex gap-4 text-sm">
                <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted w-32 shrink-0 pt-0.5">
                  {ROLE_LABELS[role] ?? role}
                </span>
                <span className="text-foreground">{names.join(", ")}</span>
              </div>
            ))}

            {runtime && (
              <div className="flex gap-4 text-sm">
                <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted w-32 shrink-0 pt-0.5">
                  runtime
                </span>
                <span className="text-foreground font-mono">{runtime}</span>
              </div>
            )}

            {work.book?.page_count && (
              <div className="flex gap-4 text-sm">
                <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted w-32 shrink-0 pt-0.5">
                  pages
                </span>
                <span className="text-foreground font-mono">
                  {work.book.page_count}
                </span>
              </div>
            )}

            {work.book?.isbn_13 && (
              <div className="flex gap-4 text-sm">
                <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted w-32 shrink-0 pt-0.5">
                  isbn
                </span>
                <span className="text-foreground font-mono">
                  {work.book.isbn_13}
                </span>
              </div>
            )}

            {work.anime?.episodes && (
              <div className="flex gap-4 text-sm">
                <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted w-32 shrink-0 pt-0.5">
                  episodes
                </span>
                <span className="text-foreground font-mono">
                  {work.anime.episodes}
                </span>
              </div>
            )}

            {work.anime?.format && (
              <div className="flex gap-4 text-sm">
                <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted w-32 shrink-0 pt-0.5">
                  format
                </span>
                <span className="text-foreground font-mono uppercase">
                  {work.anime.format}
                </span>
              </div>
            )}

            {work.anime?.source && work.anime.source !== "ORIGINAL" && (
              <div className="flex gap-4 text-sm">
                <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted w-32 shrink-0 pt-0.5">
                  adapted from
                </span>
                <span className="text-foreground font-mono uppercase">
                  {work.anime.source.replace("_", " ")}
                </span>
              </div>
            )}
          </div>

          <div className="border-t border-border pt-6">
            <RatingWidget
              workId={work.id}
              initialScore={myScore}
              isSignedIn={!!session}
            />
          </div>

          {work.external_ids.length > 0 && (
            <div className="border-t border-border pt-6">
              <div className="font-mono text-xs uppercase tracking-widest text-foreground-muted mb-3">
                external links
              </div>
              <div className="flex flex-wrap gap-3">
                {work.external_ids.map((ext) => (
                  <a
                    key={`${ext.source}-${ext.external_id}`}
                    href={ext.url ?? "#"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1.5 border border-border-strong text-foreground-muted hover:border-primary hover:text-primary font-mono text-xs uppercase tracking-widest transition-colors"
                  >
                    {ext.source} ↗
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Container>
  );
}