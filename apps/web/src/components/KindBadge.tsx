import type { WorkKind } from "@/types/api.ts";

const labels: Record<WorkKind, string> = {
  FILM: "FILM",
  BOOK: "BOOK",
  ANIME: "ANIME",
};

const colors: Record<WorkKind, string> = {
  FILM: "text-film border-film",
  BOOK: "text-book border-book",
  ANIME: "text-anime border-anime",
};

export function KindBadge({ kind }: { kind: WorkKind }) {
  return (
    <span
      className={`inline-block border px-2 py-0.5 font-mono text-[10px] tracking-widest uppercase ${colors[kind]}`}
    >
      {labels[kind]}
    </span>
  );
}