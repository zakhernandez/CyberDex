import { auth, signIn, signOut } from "@/auth";

export default async function Home() {
  const session = await auth();

  return (
    <main className="flex min-h-screen items-center justify-center bg-black text-cyan-400 font-mono p-8">
      <div className="max-w-md w-full space-y-6">
        <h1 className="text-5xl font-bold text-center">CyberDex</h1>

        {session?.user ? (
          <div className="space-y-4 text-center">
            <p>Signed in as {session.user.email}</p>
            <p className="text-xs opacity-60">
              Google ID: {session.user.googleId}
            </p>
            <form
              action={async () => {
                "use server";
                await signOut();
              }}
            >
              <button
                type="submit"
                className="px-4 py-2 border border-cyan-400 hover:bg-cyan-400 hover:text-black transition-colors"
              >
                sign out
              </button>
            </form>
          </div>
        ) : (
          <div className="text-center">
            <form
              action={async () => {
                "use server";
                await signIn("google", { redirectTo: "/" });
              }}
            >
              <button
                type="submit"
                className="px-6 py-3 border border-cyan-400 hover:bg-cyan-400 hover:text-black transition-colors"
              >
                &gt; sign in with google
              </button>
            </form>
          </div>
        )}
      </div>
    </main>
  );
}