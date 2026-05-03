import { api, type ModuleEntry } from "@/lib/api";
import { EmptyState, PageHeader, Panel } from "@/components/ui";

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
    .filter((module) => module.findings_landed > 0 || module.success_count > 0)
    .slice(0, 25);

  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Module Leaderboard"
        title={
          <>
            Reward the
            <br />
            authors whose
            <br />
            probes produce
            <br />
            real signal.
          </>
        }
        description={
          <>
            Rankings combine landed findings, successful executions, and bounty
            earnings so the highest-value module authors are immediately visible.
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <Stat label="ranked" value={String(ranked.length)} />
            <Stat
              label="earning"
              value={String(
                ranked.filter((module) => Number(module.bounties_earned_usdc) > 0).length,
              )}
            />
          </div>
        }
      />

      {error ? (
        <EmptyState title="Backend unreachable" description={error} />
      ) : ranked.length === 0 ? (
        <EmptyState
          title="Leaderboard empty"
          description="Once authors start landing findings and collecting bounties, the leaderboard will rank them here."
        />
      ) : (
        <Panel className="overflow-x-auto p-0">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-[var(--line-strong)] bg-[var(--panel-strong)] font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
              <tr>
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">probe</th>
                <th className="px-4 py-3">author</th>
                <th className="px-4 py-3 text-right">findings</th>
                <th className="px-4 py-3 text-right">success</th>
                <th className="px-4 py-3 text-right">bounties</th>
              </tr>
            </thead>
            <tbody>
              {ranked.map((module, index) => (
                <tr
                  key={module.module_hash}
                  className="border-t border-[var(--line)] bg-[var(--panel)] hover:bg-[var(--panel-strong)]"
                >
                  <td className="px-4 py-3 font-editorial-mono text-[var(--muted)]">
                    {index + 1}
                  </td>
                  <td className="px-4 py-3 font-editorial-mono text-[var(--ink)]">
                    {module.probe_id ?? "—"}
                  </td>
                  <td className="px-4 py-3 font-editorial-mono text-[var(--muted)]">
                    {shorten(module.author_address)}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--ink)]">
                    {module.findings_landed}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--muted)]">
                    {module.success_count}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--muted)]">
                    {formatUsdc(module.bounties_earned_usdc)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="editorial-card space-y-2 p-4">
      <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </p>
      <p className="font-editorial-mono text-lg text-[var(--ink)]">{value}</p>
    </div>
  );
}
