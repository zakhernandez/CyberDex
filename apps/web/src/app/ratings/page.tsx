import { auth } from "@/auth";
import { Container } from "@/components/Container";
import { WorkCard } from "@/components/WorkCard";
import { apiFetch } from "@/lib/api";
import type { RatingWithWork } from "@/types/api";

async function getRatings(): Promise<RatingWithWork[]> {
  try {
    const res = await apiFetch("/api/ratings?limit=200");
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function RatingsPage() {
  const session = await auth();
  if (!session) {
    return (
      <Container className="py-16 text-center">
        <p className="font-mono text-foreground-muted uppercase tracking-widest">
          sign in to see your ratings
        </p>
      </Container>
    );
  }

  const ratings = await getRatings();

  return (
    <Container className="py-8 space-y-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-foreground-muted mb-2">
          &gt; user log
        </p>
        <h1 className="font-display text-4xl font-bold">My Ratings</h1>
        <p className="mt-2 font-mono text-sm text-foreground-muted">
          {ratings.length} work{ratings.length === 1 ? "" : "s"} rated
        </p>
      </div>

      {ratings.length === 0 ? (
        <div className="border border-border bg-surface p-12 text-center">
          <p className="font-mono text-foreground-muted">
            nothing rated yet — browse the catalog and start rating
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {ratings.map((r) => (
            <div key={r.id} className="relative">
              <WorkCard work={r.work} />
              <div className="absolute top-2 right-2 bg-background/95 border border-primary px-2 py-1 font-mono text-sm text-primary">
                {r.score}
              </div>
            </div>
          ))}
        </div>
      )}
    </Container>
  );
}