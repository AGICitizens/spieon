import { api, type ModuleEntry } from "@/lib/api";
import { EmptyState, PageHeader, Panel } from "@/components/ui";

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

  const totalBounties = modules.reduce((sum, module) => {
    const num = Number(module.bounties_earned_usdc);
    return Number.isNaN(num) ? sum : sum + num;
  }, 0);

  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Probe Modules"
        title={
          <>
            The registry of
            <br />
            probes and the
            <br />
            rewards they
            <br />
            earn.
          </>
        }
        description={
          <>
            Track module hashes, severity caps, findings landed, and the bounty
            totals that justify keeping a probe in rotation.
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <Stat label="modules" value={String(modules.length)} />
            <Stat label="bounties" value={formatUsdc(String(totalBounties))} />
          </div>
        }
      />

      {error ? (
        <EmptyState title="Backend unreachable" description={error} />
      ) : modules.length === 0 ? (
        <EmptyState
          title="No modules registered yet"
          description="Once modules are synced onchain, this registry will show performance and earnings."
        />
      ) : (
        <Panel className="overflow-x-auto p-0">
          <table className="w-full min-w-[780px] text-left text-sm">
            <thead className="border-b border-[var(--line-strong)] bg-[var(--panel-strong)] font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
              <tr>
                <th className="px-4 py-3">probe</th>
                <th className="px-4 py-3">module hash</th>
                <th className="px-4 py-3">severity cap</th>
                <th className="px-4 py-3 text-right">findings</th>
                <th className="px-4 py-3 text-right">bounties</th>
                <th className="px-4 py-3">owasp</th>
                <th className="px-4 py-3">atlas</th>
              </tr>
            </thead>
            <tbody>
              {modules.map((module) => (
                <tr
                  key={module.module_hash}
                  className="border-t border-[var(--line)] bg-[var(--panel)] transition-colors hover:bg-[var(--panel-strong)]"
                >
                  <td className="px-4 py-3 font-editorial-mono text-[var(--ink)]">
                    {module.probe_id ?? <span className="text-[var(--muted)]">unknown</span>}
                  </td>
                  <td className="px-4 py-3 font-editorial-mono text-[var(--muted)]">
                    {shorten(module.module_hash)}
                  </td>
                  <td className="px-4 py-3 capitalize text-[var(--ink)]">
                    {module.severity_cap}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--ink)]">
                    {module.findings_landed}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--muted)]">
                    {formatUsdc(module.bounties_earned_usdc)}
                  </td>
                  <td className="px-4 py-3 text-[var(--muted)]">{module.owasp_id ?? "—"}</td>
                  <td className="px-4 py-3 text-[var(--muted)]">
                    {module.atlas_technique_id ?? "—"}
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
