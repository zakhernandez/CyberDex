export function RatingDisplay({
  score,
  size = "md",
}: {
  score: number | null | undefined;
  size?: "sm" | "md" | "lg";
}) {
  const sizeClasses = {
    sm: "text-sm",
    md: "text-lg",
    lg: "text-3xl",
  }[size];

  if (score == null) {
    return (
      <span className={`${sizeClasses} font-mono text-foreground-dim`}>
        —
      </span>
    );
  }

  const colorClass =
    score >= 9
      ? "text-success"
      : score >= 7
      ? "text-primary"
      : score >= 5
      ? "text-foreground"
      : "text-foreground-muted";

  return (
    <span className={`${sizeClasses} font-mono ${colorClass}`}>
      {score}
      <span className="text-foreground-dim text-[0.6em]">/10</span>
    </span>
  );
}