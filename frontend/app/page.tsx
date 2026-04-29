import { api } from "@/lib/api";

export default async function HomePage() {
  let healthLine = "checking…";
  try {
    const health = await api.health();
    healthLine = `${health.status} · db ${health.db ? "ok" : "down"}`;
  } catch (err) {
    healthLine = `unreachable: ${(err as Error).message}`;
  }

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Spieon</h1>
        <p className="mt-2 text-zinc-400">
          Autonomous security agent for the agent economy. Scans MCP servers and
          x402 endpoints, attests findings on Base Sepolia, pays bounties to
          module authors.
        </p>
      </header>

      <div className="rounded-md border border-zinc-800 bg-zinc-950/40 p-4 text-sm text-zinc-300">
        <span className="text-zinc-500">backend:</span> {healthLine}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <a
          href="/scan"
          className="rounded-md border border-zinc-800 p-4 hover:border-zinc-600"
        >
          <h2 className="font-medium text-zinc-100">Submit a scan</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Point Spieon at an x402 or MCP endpoint and watch it work.
          </p>
        </a>
        <a
          href="/findings"
          className="rounded-md border border-zinc-800 p-4 hover:border-zinc-600"
        >
          <h2 className="font-medium text-zinc-100">Findings feed</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Public metadata for every attested finding.
          </p>
        </a>
      </div>
    </section>
  );
}
