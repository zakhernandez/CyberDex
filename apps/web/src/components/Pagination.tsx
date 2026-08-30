"use client";

import { useRouter, useSearchParams } from "next/navigation";

export function Pagination({
  currentPage,
  hasNext,
}: {
  currentPage: number;
  hasNext: boolean;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();

  function goToPage(page: number) {
    const params = new URLSearchParams(searchParams.toString());
    if (page === 1) {
      params.delete("page");
    } else {
      params.set("page", String(page));
    }
    router.push(`/browse?${params.toString()}`);
  }

  return (
    <div className="flex items-center justify-between font-mono text-sm">
      <button
        onClick={() => goToPage(currentPage - 1)}
        disabled={currentPage <= 1}
        className="px-4 py-2 border border-border-strong text-foreground hover:border-primary hover:text-primary transition-colors uppercase text-xs tracking-widest disabled:opacity-30 disabled:pointer-events-none"
      >
        ← prev
      </button>

      <span className="text-foreground-muted uppercase text-xs tracking-widest">
        page {currentPage}
      </span>

      <button
        onClick={() => goToPage(currentPage + 1)}
        disabled={!hasNext}
        className="px-4 py-2 border border-border-strong text-foreground hover:border-primary hover:text-primary transition-colors uppercase text-xs tracking-widest disabled:opacity-30 disabled:pointer-events-none"
      >
        next →
      </button>
    </div>
  );
}