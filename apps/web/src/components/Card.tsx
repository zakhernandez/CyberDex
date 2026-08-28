import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
  accent,
}: {
  children: ReactNode;
  className?: string;
  accent?: "film" | "book" | "anime";
}) {
  const accentBorder =
    accent === "film"
      ? "border-l-film"
      : accent === "book"
      ? "border-l-book"
      : accent === "anime"
      ? "border-l-anime"
      : "border-l-border-strong";

  return (
    <div
      className={`bg-surface border border-border border-l-2 ${accentBorder} ${className}`}
    >
      {children}
    </div>
  );
}