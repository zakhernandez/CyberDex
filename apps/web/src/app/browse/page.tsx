import { BrowseFilters } from "@/components/BrowseFilters";
import { Container } from "@/components/Container";
import { Pagination } from "@/components/Pagination";
import { WorkCard } from "@/components/WorkCard";
import { apiFetch } from "@/lib/api";
import type { WorkKind, WorkListResponse } from "@/types/api";

const PER_PAGE = 24;

interface BrowsePageProps {
  searchParams: Promise<{
    kind?: string;
    q?: string;
    page?: string;
  }>;
}

async function getWorks(params: {
  kind?: string;
  q?: string;
  page: number;
}): Promise<WorkListResponse | null> {
  const query = new URLSearchParams({
    page: String(params.page),
    per_page: String(PER_PAGE),
  });
  if (params.kind) query.set("kind", params.kind);
  if (params.q) query.set("q", params.q);

  try {
    const res = await apiFetch(`/api/works?${query.toString()}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function BrowsePage({ searchParams }: BrowsePageProps) {
  const params = await searchParams;
  const page = Math.max(1, parseInt(params.page ?? "1", 10) || 1);
  const kind = params.kind as WorkKind | undefined;
  const q = params.q;

  const data = await getWorks({ kind, q, page });

  return (
    <Container className="py-8 space-y-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-foreground-muted mb-2">
          &gt; catalog
        </p>
        <h1 className="font-display text-4xl font-bold mb-6">Browse</h1>

        <BrowseFilters />
      </div>

      {data ? (
        <>
          <div className="flex items-center justify-between font-mono text-xs uppercase tracking-widest text-foreground-muted">
            <span>
              {data.total.toLocaleString()} works
              {kind ? ` · ${kind.toLowerCase()}` : ""}
              {q ? ` · matching "${q}"` : ""}
            </span>
            <span>
              page {data.page}
            </span>
          </div>

          {data.items.length === 0 ? (
            <div className="border border-border bg-surface p-12 text-center">
              <p className="font-mono text-foreground-muted">
                no works match these filters
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {data.items.map((work) => (
                <WorkCard key={work.id} work={work} />
              ))}
            </div>
          )}

          {data.items.length > 0 && (
            <Pagination currentPage={data.page} hasNext={data.has_next} />
          )}
        </>
      ) : (
        <div className="border border-border bg-surface p-12 text-center">
          <p className="font-mono text-red-400">
            failed to load catalog
          </p>
        </div>
      )}
    </Container>
  );
}