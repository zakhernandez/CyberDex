import Image from "next/image";

async function getHealth() {
  const res = await fetch("http://localhost:8000/api/health", {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API responded ${res.status}`);
  }
  return res.json();
}



export default async function Home() {
  const data = await getHealth();

  return (
    <main className="flex min-h-screen items-center justify-center bg-black text-cyan-400 font-mono">
      <div className="text-center">
        <h1 className="text-5xl font-bold mb-4">CyberDex</h1>
        <p className="text-xl">// api status: {data.status}</p>
      </div>
    </main>
  );
}
