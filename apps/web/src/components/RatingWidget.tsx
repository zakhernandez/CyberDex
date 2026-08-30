"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface RatingWidgetProps {
  workId: number;
  initialScore: number | null;
  isSignedIn: boolean;
}

const SCORES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

export function RatingWidget({
  workId,
  initialScore,
  isSignedIn,
}: RatingWidgetProps) {
  const [score, setScore] = useState<number | null>(initialScore);
  const [hoverScore, setHoverScore] = useState<number | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function submit(newScore: number) {
    if (pending) return;
    setPending(true);
    setError(null);

    try {
      const res = await fetch("/api/proxy/ratings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ work_id: workId, score: newScore }),
      });

      if (!res.ok) {
        const body = await res.text();
        throw new Error(`Rating failed: ${res.status} ${body}`);
      }

      setScore(newScore);
      router.refresh();
    } catch (e: any) {
      setError(e.message ?? "Rating failed");
    } finally {
      setPending(false);
    }
  }

  async function remove() {
    if (pending || score === null) return;
    setPending(true);
    setError(null);

    try {
      const res = await fetch(`/api/proxy/ratings/${workId}`, {
        method: "DELETE",
      });
      if (!res.ok && res.status !== 404) {
        throw new Error(`Delete failed: ${res.status}`);
      }
      setScore(null);
      router.refresh();
    } catch (e: any) {
      setError(e.message ?? "Delete failed");
    } finally {
      setPending(false);
    }
  }

  if (!isSignedIn) {
    return (
      <div className="border border-border bg-surface p-4">
        <p className="font-mono text-xs uppercase tracking-widest text-foreground-muted">
          sign in to rate
        </p>
      </div>
    );
  }

  const displayScore = hoverScore ?? score;

  return (
    <div className="border border-border bg-surface p-4 space-y-3">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-xs uppercase tracking-widest text-foreground-muted">
          your rating
        </span>
        {score !== null && (
          <button
            onClick={remove}
            disabled={pending}
            className="font-mono text-[10px] uppercase tracking-widest text-foreground-dim hover:text-accent transition-colors disabled:opacity-40"
          >
            remove
          </button>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span
          className={`font-display text-4xl font-bold ${
            displayScore === null
              ? "text-foreground-dim"
              : displayScore >= 9
              ? "text-success"
              : displayScore >= 7
              ? "text-primary"
              : displayScore >= 5
              ? "text-foreground"
              : "text-foreground-muted"
          }`}
        >
          {displayScore ?? "—"}
        </span>
        <span className="font-mono text-foreground-dim text-sm">/10</span>
      </div>

      <div
        className="flex gap-1"
        onMouseLeave={() => setHoverScore(null)}
      >
        {SCORES.map((n) => (
          <button
            key={n}
            onMouseEnter={() => setHoverScore(n)}
            onClick={() => submit(n)}
            disabled={pending}
            className={`flex-1 h-8 border font-mono text-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
              (hoverScore !== null && n <= hoverScore) ||
              (hoverScore === null && score !== null && n <= score)
                ? "border-primary bg-primary/10 text-primary"
                : "border-border-strong text-foreground-muted hover:border-primary"
            }`}
          >
            {n}
          </button>
        ))}
      </div>

      {error && (
        <p className="font-mono text-xs text-accent">{error}</p>
      )}
    </div>
  );
}