import { api, type ModuleEntry } from "@/lib/api";

function shorten(hash: string | null) {
  if (!hash) return "—";
  return `${hash.slice(0, 10)}…${hash.slice(-6)}`;
}

function formatUsdc(value: string) {
  const num = Number(value);
  if (Number.isNaN(num)) return value;
  return `${num.toFixed(num < 1 ? 4 : 2)} USDC`;
}

export default async function ModulesPage() {
  let modules: ModuleEntry[] = [];
  let error: string | null = null;
  try {
    modules = await api.listModules(100);
  } catch (err) {
    error = (err as Error).message;
  }

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Modules</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Probe modules and the bounties they have earned. On-chain registry
          counters synced via the agent.
        </p>
      </header>

      {error ? (
        <p className="text-sm text-red-400">backend unreachable: {error}</p>
      ) : modules.length === 0 ? (
        <p className="text-sm text-zinc-500">No modules registered yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-zinc-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-zinc-950/60 text-xs uppercase tracking-wide text-zinc-500">
              <tr>
                <th className="px-3 py-2">probe</th>
                <th className="px-3 py-2">module hash</th>
                <th className="px-3 py-2">severity cap</th>
                <th className="px-3 py-2 text-right">findings</th>
                <th className="px-3 py-2 text-right">bounties</th>
                <th className="px-3 py-2">owasp</th>
                <th className="px-3 py-2">atlas</th>
              </tr>
            </thead>
            <tbody>
              {modules.map((m) => (
                <tr
                  key={m.module_hash}
                  className="border-t border-zinc-900 hover:bg-zinc-950/40"
                >
                  <td className="px-3 py-2 font-mono text-zinc-200">
                    {m.probe_id ?? <span className="text-zinc-500">unknown</span>}
                  </td>
                  <td className="px-3 py-2 font-mono text-zinc-400">
                    {shorten(m.module_hash)}
                  </td>
                  <td className="px-3 py-2 capitalize text-zinc-300">
                    {m.severity_cap}
                  </td>
                  <td className="px-3 py-2 text-right text-zinc-100">
                    {m.findings_landed}
                  </td>
                  <td className="px-3 py-2 text-right text-zinc-300">
                    {formatUsdc(m.bounties_earned_usdc)}
                  </td>
                  <td className="px-3 py-2 text-zinc-400">{m.owasp_id ?? "—"}</td>
                  <td className="px-3 py-2 text-zinc-400">
                    {m.atlas_technique_id ?? "—"}
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
