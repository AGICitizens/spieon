import Link from "next/link";
import { api, type AgentStats } from "@/lib/api";
import {
  ActionCard,
  MetricCard,
  PageHeader,
  Panel,
  StatusPill,
} from "@/components/ui";

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

function formatTimestamp(value: string | null | undefined) {
  if (!value) return "live";
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function HomePage() {
  let healthLine = "checking…";
  let stats: AgentStats | null = null;
  let backendTone: "neutral" | "success" | "danger" = "neutral";
  try {
    const [health, agentStats] = await Promise.all([api.health(), api.agentStats()]);
    healthLine = `${health.status} · db ${health.db ? "ok" : "down"}`;
    stats = agentStats;
    backendTone = health.status === "ok" && health.db ? "success" : "danger";
  } catch (err) {
    healthLine = `unreachable: ${(err as Error).message}`;
    backendTone = "danger";
  }

  return (
    <section className="space-y-10">
      <PageHeader
        eyebrow="Autonomous Security Agent"
        title={
          <>
            Trust every
            <br />
            agent endpoint
            <br />
            only after it
            <br />
            survives contact.
          </>
        }
        description={
          <>
            Spieon runs adversarial scans against MCP servers and x402
            endpoints, attests what it finds, and routes rewards back to the
            module authors whose probes actually landed. The interface stays
            minimal so operators can move from signal to action fast.
          </>
        }
        actions={
          <>
            <Link href="/scan" className="editorial-button editorial-button-dark">
              Launch a scan
            </Link>
            <Link href="/findings" className="editorial-button editorial-button-light">
              Review findings
            </Link>
          </>
        }
        aside={
          <div className="space-y-5">
            <div className="flex items-center justify-between gap-3">
              <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
                System posture
              </p>
              <StatusPill tone={backendTone}>backend {healthLine}</StatusPill>
            </div>
            {stats ? (
              <div className="grid grid-cols-2 gap-3">
                <MetricCard label="scans" value={stats.scans} className="p-4" />
                <MetricCard
                  label="findings"
                  value={stats.findings}
                  className="p-4"
                />
                <MetricCard
                  label="wallet"
                  value={
                    <span className="font-editorial-mono text-lg">
                      {shortAddress(stats.address)}
                    </span>
                  }
                  className="p-4"
                />
                <MetricCard
                  label="treasury"
                  value={
                    <span className="font-editorial-mono text-lg">
                      {formatUsdc(stats.balances.usdc)}
                    </span>
                  }
                  className="p-4"
                />
              </div>
            ) : (
              <p className="text-sm leading-6 text-[var(--muted)]">
                The shell is live even if the backend is unavailable. Once the
                agent is reachable, current wallet and scan telemetry appears
                here.
              </p>
            )}
            <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
              Refreshed {formatTimestamp(stats?.as_of)}
            </p>
          </div>
        }
      />

      <section className="grid gap-4 lg:grid-cols-3">
        <ActionCard
          href="/scan"
          label="01"
          title="Submit a target"
          description="Generate an operator-held recipient key, assign a bounty budget, and start an adversarial scan without leaving the browser."
        />
        <ActionCard
          href="/findings"
          label="02"
          title="Review what landed"
          description="Track attested findings as they appear, including severity, cost, and the public evidence trail for each scan."
        />
        <ActionCard
          href="/modules"
          label="03"
          title="See which probes win"
          description="Measure the modules earning bounties, their severity caps, and the authors producing repeatable signal."
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Panel className="editorial-grid overflow-hidden">
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-3">
              <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
                Operating loop
              </p>
              <h2 className="max-w-[12ch] font-editorial-sans text-2xl font-semibold uppercase leading-tight">
                Scan, attest, reward, remember.
              </h2>
            </div>
            <div className="space-y-4 border-t border-[var(--line)] pt-4 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
              <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
                01 / Recon
              </p>
              <p className="text-sm leading-6 text-[var(--muted)]">
                Target an x402 or MCP surface, set operator consent, and let
                Spieon plan the cheapest useful probes first.
              </p>
            </div>
            <div className="space-y-4 border-t border-[var(--line)] pt-4 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
              <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
                02 / Evidence
              </p>
              <p className="text-sm leading-6 text-[var(--muted)]">
                Findings are encrypted to the operator, while public metadata
                and attestations keep the system auditable for everyone else.
              </p>
            </div>
          </div>
        </Panel>

        <Panel>
          <p className="font-editorial-serif text-4xl italic leading-none">
            Enterprise-grade means less dashboard noise and more immediate
            operator confidence.
          </p>
          <div className="mt-6 space-y-4 text-sm leading-6 text-[var(--muted)]">
            <p>
              The UX now prioritizes state clarity, obvious primary actions, and
              mono-typed telemetry instead of generic dark cards.
            </p>
            <p>
              The visual language intentionally mirrors a security control plane:
              paper, ink, evidence, and crisp borders rather than soft consumer
              gradients.
            </p>
          </div>
        </Panel>
      </section>
    </section>
  );
}
