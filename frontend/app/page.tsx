import Link from "next/link";
import { api, type AgentStats } from "@/lib/api";

function formatUsdc(value: string | null | undefined) {
  if (!value) return "—";
  const num = Number(value);
  if (Number.isNaN(num)) return value;
  return `${num.toFixed(num < 1 ? 6 : 2)} USDC`;
}

function shortAddress(addr: string | null) {
  if (!addr) return "agent.unset";
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}

export default async function HomePage() {
  let healthLine = "checking…";
  let stats: AgentStats | null = null;
  try {
    const [health, agentStats] = await Promise.all([api.health(), api.agentStats()]);
    healthLine = `${health.status} · db ${health.db ? "ok" : "down"}`;
    stats = agentStats;
  } catch (err) {
    healthLine = `unreachable: ${(err as Error).message}`;
  }

  return (
    <section className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Spieon</h1>
        <p className="text-zinc-400">
          Autonomous security agent for the agent economy. Scans MCP servers and
          x402 endpoints, attests findings on Base Sepolia, pays bounties to
          module authors.
        </p>
      </header>

      {stats ? <IdentityBanner stats={stats} /> : null}

      <div className="rounded-md border border-zinc-800 bg-zinc-950/40 p-4 text-sm text-zinc-300">
        <span className="text-zinc-500">backend:</span> {healthLine}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          href="/scan"
          className="rounded-md border border-zinc-800 p-4 hover:border-zinc-600"
        >
          <h2 className="font-medium text-zinc-100">Submit a scan</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Point Spieon at an x402 or MCP endpoint and watch it work.
          </p>
        </Link>
        <Link
          href="/findings"
          className="rounded-md border border-zinc-800 p-4 hover:border-zinc-600"
        >
          <h2 className="font-medium text-zinc-100">Findings feed</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Public metadata for every attested finding.
          </p>
        </Link>
      </div>
    </section>
  );
}

function IdentityBanner({ stats }: { stats: AgentStats }) {
  const items = [
    { label: "address", value: shortAddress(stats.address) },
    { label: "scans", value: String(stats.scans) },
    { label: "findings", value: String(stats.findings) },
    { label: "heuristics", value: String(stats.heuristics_attested) },
    { label: "spent", value: formatUsdc(stats.spent_usdc) },
    { label: "treasury", value: formatUsdc(stats.balances.usdc) },
  ];
  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-950/60 p-4">
      <ul className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3 lg:grid-cols-6">
        {items.map((item) => (
          <li key={item.label} className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-zinc-500">
              {item.label}
            </p>
            <p className="font-mono text-zinc-100">{item.value}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
