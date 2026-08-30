"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";

const KIND_OPTIONS = [
  { value: "", label: "All" },
  { value: "FILM", label: "Films" },
  { value: "BOOK", label: "Books" },
  { value: "ANIME", label: "Anime" },
];

export function BrowseFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentKind = searchParams.get("kind") ?? "";
  const currentQ = searchParams.get("q") ?? "";

  const [searchInput, setSearchInput] = useState(currentQ);

  // Keep local state in sync with URL if user hits back button
  useEffect(() => {
    setSearchInput(currentQ);
  }, [currentQ]);

  function updateParams(updates: Record<string, string>) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    }
    // Any filter change resets to page 1
    params.delete("page");
    router.push(`/browse?${params.toString()}`);
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    updateParams({ q: searchInput.trim() });
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {KIND_OPTIONS.map((opt) => {
          const active = currentKind === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => updateParams({ kind: opt.value })}
              className={`px-3 py-1.5 border font-mono text-xs uppercase tracking-widest transition-colors ${
                active
                  ? "border-primary text-primary bg-primary/10"
                  : "border-border-strong text-foreground-muted hover:border-primary hover:text-primary"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="search titles..."
          className="flex-1 bg-surface border border-border-strong px-3 py-2 font-mono text-sm text-foreground placeholder:text-foreground-dim focus:border-primary focus:outline-none"
        />
        <button
          type="submit"
          className="px-4 py-2 border border-primary text-primary hover:bg-primary hover:text-background font-mono text-xs uppercase tracking-widest transition-colors"
        >
          search
        </button>
      </form>
    </div>
  );
}