import { api, type ModuleEntry } from "@/lib/api";

function shorten(addr: string | null) {
  if (!addr) return "—";
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}

function formatUsdc(value: string) {
  const num = Number(value);
  if (Number.isNaN(num)) return value;
  return `${num.toFixed(num < 1 ? 4 : 2)} USDC`;
}

export default async function LeaderboardPage() {
  let modules: ModuleEntry[] = [];
  let error: string | null = null;
  try {
    modules = await api.listModules(100);
  } catch (err) {
    error = (err as Error).message;
  }

  const ranked = modules
    .filter((m) => m.findings_landed > 0 || m.success_count > 0)
    .slice(0, 25);

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Leaderboard</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Module authors ranked by findings landed and bounties earned.
        </p>
      </header>

      {error ? (
        <p className="text-sm text-red-400">backend unreachable: {error}</p>
      ) : ranked.length === 0 ? (
        <p className="text-sm text-zinc-500">
          No author has earned a bounty yet — leaderboard will fill in after the
          first paid finding lands.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-zinc-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-zinc-950/60 text-xs uppercase tracking-wide text-zinc-500">
              <tr>
                <th className="px-3 py-2">#</th>
                <th className="px-3 py-2">probe</th>
                <th className="px-3 py-2">author</th>
                <th className="px-3 py-2 text-right">findings</th>
                <th className="px-3 py-2 text-right">success</th>
                <th className="px-3 py-2 text-right">bounties</th>
              </tr>
            </thead>
            <tbody>
              {ranked.map((m, i) => (
                <tr
                  key={m.module_hash}
                  className="border-t border-zinc-900 hover:bg-zinc-950/40"
                >
                  <td className="px-3 py-2 text-zinc-500">{i + 1}</td>
                  <td className="px-3 py-2 font-mono text-zinc-200">
                    {m.probe_id ?? "—"}
                  </td>
                  <td className="px-3 py-2 font-mono text-zinc-400">
                    {shorten(m.author_address)}
                  </td>
                  <td className="px-3 py-2 text-right text-zinc-100">
                    {m.findings_landed}
                  </td>
                  <td className="px-3 py-2 text-right text-zinc-300">
                    {m.success_count}
                  </td>
                  <td className="px-3 py-2 text-right text-zinc-300">
                    {formatUsdc(m.bounties_earned_usdc)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
