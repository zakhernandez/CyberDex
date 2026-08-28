import Link from "next/link";

import { auth, signIn, signOut } from "@/auth";

import { Button } from "./Button";
import { Container } from "./Container";

export async function AppHeader() {
  const session = await auth();

  return (
    <header className="border-b border-border bg-background sticky top-0 z-50 backdrop-blur">
      <Container>
        <div className="flex items-center justify-between h-14">
          <Link
            href="/"
            className="font-display text-2xl font-bold text-primary tracking-wide hover:text-primary/80 transition-colors"
          >
            CYBERDEX
          </Link>

          <nav className="flex items-center gap-6">
            <Link
              href="/browse"
              className="font-mono text-xs uppercase tracking-widest text-foreground-muted hover:text-primary transition-colors"
            >
              browse
            </Link>
            <Link
              href="/ratings"
              className="font-mono text-xs uppercase tracking-widest text-foreground-muted hover:text-primary transition-colors"
            >
              my ratings
            </Link>

            {session?.user ? (
              <form
                action={async () => {
                  "use server";
                  await signOut();
                }}
              >
                <Button variant="ghost">sign out</Button>
              </form>
            ) : (
              <form
                action={async () => {
                  "use server";
                  await signIn("google", { redirectTo: "/" });
                }}
              >
                <Button variant="primary">sign in</Button>
              </form>
            )}
          </nav>
        </div>
      </Container>
    </header>
  );
}