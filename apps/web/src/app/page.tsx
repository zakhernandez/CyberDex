import Link from "next/link";

import { Button } from "@/components/Button";
import { Container } from "@/components/Container";
import { StatsPanel } from "@/components/StatsPanel";
import { WorkStrip } from "@/components/WorkStrip";
import { apiFetch } from "@/lib/api";
import type {
  CatalogStats,
  WorkListItem,
} from "@/types/api";

async function getStats(): Promise<CatalogStats | null> {
  try {
    const res = await apiFetch("/api/stats");
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function getRecent(kind?: string): Promise<WorkListItem[]> {
  try {
    const query = kind ? `?kind=${kind}&limit=6` : "?limit=6";
    const res = await apiFetch(`/api/works/recent${query}`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function Home() {
  const [stats, recentFilms, recentBooks, recentAnime] = await Promise.all([
    getStats(),
    getRecent("FILM"),
    getRecent("BOOK"),
    getRecent("ANIME"),
  ]);

  return (
    <Container className="py-12 space-y-12">
      <section>
        <p className="font-mono text-xs uppercase tracking-widest text-foreground-muted mb-4">
          &gt; system online
        </p>
        <h1 className="font-display text-5xl font-bold leading-none mb-4">
          Welcome to <span className="text-primary">CyberDex</span>.
        </h1>
        <p className="text-foreground-muted text-lg max-w-xl mb-6">
          A private catalog of cyberpunk films, books, and anime.
        </p>
        <Link href="/browse">
          <Button variant="primary">enter catalog</Button>
        </Link>
      </section>

      {stats && <StatsPanel stats={stats} />}

      <WorkStrip
        title="Recent Films"
        works={recentFilms}
        viewAllHref="/browse?kind=FILM"
      />
      <WorkStrip
        title="Recent Books"
        works={recentBooks}
        viewAllHref="/browse?kind=BOOK"
      />
      <WorkStrip
        title="Recent Anime"
        works={recentAnime}
        viewAllHref="/browse?kind=ANIME"
      />
    </Container>
  );
}