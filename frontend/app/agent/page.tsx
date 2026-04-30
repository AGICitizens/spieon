import { api, type AgentStats, type Scan } from "@/lib/api";

function formatUsdc(value: string | null | undefined) {
  if (!value) return "—";
  const num = Number(value);
  if (Number.isNaN(num)) return value;
  return `${num.toFixed(num < 1 ? 6 : 2)} USDC`;
}

function formatEth(value: string | null) {
  if (!value) return "—";
  const num = Number(value);
  if (Number.isNaN(num)) return value;
  return `${num.toFixed(4)} ETH`;
}

export default async function AgentPage() {
  let stats: AgentStats | null = null;
  let scans: Scan[] = [];
  let error: string | null = null;
  try {
    [stats, scans] = await Promise.all([api.agentStats(), api.listScans()]);
  } catch (err) {
    error = (err as Error).message;
  }

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Agent profile</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Persistent identity for the Spieon agent. Stats and balances refresh
          on every page load.
        </p>
      </header>

      {error ? (
        <p className="text-sm text-red-400">backend unreachable: {error}</p>
      ) : null}

      {stats ? (
        <section className="space-y-4">
          <div className="rounded-md border border-zinc-800 bg-zinc-950/40 p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">
              wallet
            </p>
            <p className="mt-1 font-mono text-sm text-zinc-100">
              {stats.address ?? "agent.unset"}
            </p>
            <dl className="mt-4 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-4">
              <Stat label="ETH" value={formatEth(stats.balances.eth)} />
              <Stat label="USDC" value={formatUsdc(stats.balances.usdc)} />
              <Stat label="spent" value={formatUsdc(stats.spent_usdc)} />
              <Stat label="heuristics" value={String(stats.heuristics_attested)} />
            </dl>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <Card label="scans" value={String(stats.scans)} />
            <Card label="completed" value={String(stats.scans_completed)} />
            <Card label="findings" value={String(stats.findings)} />
          </div>
        </section>
      ) : null}

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-wide text-zinc-500">
          Recent scans
        </h2>
        {scans.length === 0 ? (
          <p className="text-sm text-zinc-500">No scans yet.</p>
        ) : (
          <ul className="space-y-2">
            {scans.slice(0, 20).map((scan) => (
              <li
                key={scan.id}
                className="flex flex-wrap items-baseline justify-between gap-3 rounded-md border border-zinc-800 bg-zinc-950/40 p-3 text-sm"
              >
                <a
                  href={`/scan/${scan.id}`}
                  className="font-mono text-zinc-200 hover:text-zinc-100"
                >
                  {scan.id.slice(0, 8)}…
                </a>
                <span className="text-zinc-300">{scan.target_url}</span>
                <span className="text-xs uppercase tracking-wide text-zinc-500">
                  {scan.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="font-mono text-zinc-100">{value}</p>
    </div>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-950/40 p-4">
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-zinc-100">{value}</p>
    </div>
  );
}
