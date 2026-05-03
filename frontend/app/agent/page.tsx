import {
  api,
  type AgentStats,
  type KeeperHubRunsResponse,
  type KeeperHubStatus,
  type Scan,
} from "@/lib/api";
import { EmptyState, MetricCard, PageHeader, Panel, StatusPill } from "@/components/ui";

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

function shortAddress(value: string | null) {
  if (!value) return "agent.unset";
  return `${value.slice(0, 8)}…${value.slice(-6)}`;
}

function toneForScanStatus(status: Scan["status"]) {
  if (status === "done") return "success" as const;
  if (status === "failed" || status === "canceled") return "danger" as const;
  if (status === "pending") return "neutral" as const;
  return "info" as const;
}

function keeperHubLabel(status: KeeperHubStatus) {
  if (status.configured) return "live · paid per run via x402";
  if (status.api_key_present) return "api key set · workflow id missing";
  return "not configured";
}

function keeperHubTone(status: KeeperHubStatus) {
  if (status.configured) return "success" as const;
  if (status.api_key_present) return "warning" as const;
  return "neutral" as const;
}

export default async function AgentPage() {
  let stats: AgentStats | null = null;
  let scans: Scan[] = [];
  let khStatus: KeeperHubStatus | null = null;
  let khRuns: KeeperHubRunsResponse | null = null;
  let error: string | null = null;

  const [statsResult, scansResult, khStatusResult] = await Promise.allSettled([
    api.agentStats(),
    api.listScans(),
    api.keeperhubStatus(),
  ]);

  if (statsResult.status === "fulfilled") {
    stats = statsResult.value;
  } else {
    error = statsResult.reason instanceof Error ? statsResult.reason.message : String(statsResult.reason);
  }

  if (scansResult.status === "fulfilled") {
    scans = scansResult.value;
  } else if (!error) {
    error = scansResult.reason instanceof Error ? scansResult.reason.message : String(scansResult.reason);
  }

  if (khStatusResult.status === "fulfilled") {
    khStatus = khStatusResult.value;
    if (khStatus.configured) {
      khRuns = await api.keeperhubRuns(10).catch(() => null);
    }
  } else {
    khStatus = null;
  }

  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Agent Profile"
        title={
          <>
            One identity.
            <br />
            Persistent
            <br />
            telemetry.
          </>
        }
        description={
          <>
            The agent page is the operational snapshot: balances, scan volume,
            ENS identity, and payout workflow readiness in one glance.
          </>
        }
        aside={
          stats ? (
            <div className="space-y-4">
              <div>
                <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
                  Wallet
                </p>
                <p className="mt-3 font-editorial-mono text-lg text-[var(--ink)]">
                  {shortAddress(stats.address)}
                </p>
                {stats.ens_name || stats.ens_primary_name ? (
                  <p className="mt-2 text-sm text-[var(--muted)]">
                    {(stats.ens_primary_name ?? stats.ens_name) as string}
                    {" · "}chain {stats.ens_chain_id ?? "—"}
                  </p>
                ) : null}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <MetricCard label="ETH" value={formatEth(stats.balances.eth)} className="p-4" />
                <MetricCard
                  label="USDC"
                  value={formatUsdc(stats.balances.usdc)}
                  className="p-4"
                />
              </div>
            </div>
          ) : (
            <div className="text-sm leading-6 text-[var(--muted)]">
              Agent wallet and ENS data appear here when the backend is reachable.
            </div>
          )
        }
      />

      {error ? <EmptyState title="Backend unreachable" description={error} /> : null}

      {stats ? (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="scans" value={String(stats.scans)} />
          <MetricCard label="completed" value={String(stats.scans_completed)} />
          <MetricCard label="findings" value={String(stats.findings)} />
          <MetricCard
            label="heuristics"
            value={String(stats.heuristics_attested)}
            detail={`Spent ${formatUsdc(stats.spent_usdc)}`}
          />
        </section>
      ) : null}

      {khStatus ? (
        <Panel className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
                KeeperHub
              </p>
              <h2 className="mt-2 font-editorial-sans text-2xl font-semibold uppercase">
                Payout workflow
              </h2>
            </div>
            <StatusPill tone={keeperHubTone(khStatus)}>{keeperHubLabel(khStatus)}</StatusPill>
          </div>
          {khStatus.workflow_id ? (
            <p className="font-editorial-mono text-xs text-[var(--muted)]">
              workflow {khStatus.workflow_id.slice(0, 16)}…
            </p>
          ) : null}
          {khRuns?.executions?.length ? (
            <ul className="space-y-2">
              {khRuns.executions.slice(0, 5).map((run, index) => (
                <li
                  key={String(run.id ?? index)}
                  className="grid grid-cols-[1fr_auto] gap-4 border-t border-[var(--line)] pt-3 font-editorial-mono text-xs text-[var(--ink)] first:border-t-0 first:pt-0"
                >
                  <span>{String(run.id ?? "—").slice(0, 18)}…</span>
                  <span className="text-[var(--muted)]">{String(run.status ?? "")}</span>
                </li>
              ))}
            </ul>
          ) : khStatus.configured ? (
            <p className="text-sm text-[var(--muted)]">No executions yet.</p>
          ) : null}
        </Panel>
      ) : null}

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
              Recent scans
            </p>
            <h2 className="mt-2 font-editorial-sans text-2xl font-semibold uppercase">
              Execution history
            </h2>
          </div>
          <StatusPill tone="neutral">{scans.length} loaded</StatusPill>
        </div>

        {scans.length === 0 ? (
          <EmptyState
            title="No scans yet"
            description="Launch the first scan and the recent execution history will populate here."
          />
        ) : (
          <ul className="space-y-3">
            {scans.slice(0, 20).map((scan) => (
              <li key={scan.id}>
                <Panel className="flex flex-wrap items-center justify-between gap-4 p-4 text-sm">
                  <div className="space-y-1">
                    <a
                      href={`/scan/${scan.id}`}
                      className="font-editorial-mono text-sm text-[var(--ink)] underline decoration-[var(--line-strong)] underline-offset-4"
                    >
                      {scan.id.slice(0, 8)}…
                    </a>
                    <p className="text-sm text-[var(--muted)]">{scan.target_url}</p>
                  </div>
                  <StatusPill tone={toneForScanStatus(scan.status)}>
                    {scan.status}
                  </StatusPill>
                </Panel>
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
