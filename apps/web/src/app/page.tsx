import Link from "next/link";

import { Button } from "@/components/Button";
import { Container } from "@/components/Container";
import { KindBadge } from "@/components/KindBadge";

export default function Home() {
  return (
    <Container>
      <section className="py-24 max-w-3xl">
        <p className="font-mono text-xs uppercase tracking-widest text-foreground-muted mb-6">
          &gt; system online
        </p>
        <h1 className="font-display text-6xl font-bold leading-none mb-6">
          A catalog for{" "}
          <span className="text-primary">cyberpunk</span> media.
        </h1>
        <p className="text-foreground-muted text-lg mb-8 max-w-xl">
          Films, books, and anime — rated, cross-referenced, and
          recommended. A private database for the low-life
          high-tech connoisseur.
        </p>

        <div className="flex items-center gap-4 mb-16">
          <Link href="/browse">
            <Button variant="primary">enter catalog</Button>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <KindBadge kind="FILM" />
          <KindBadge kind="BOOK" />
          <KindBadge kind="ANIME" />
        </div>
      </section>
    </Container>
  );
}