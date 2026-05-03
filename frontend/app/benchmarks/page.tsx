import { PageHeader, Panel, StatusPill } from "@/components/ui";

type Bench = {
  id: string;
  name: string;
  description: string;
  status: "deployed" | "pending";
  score?: { detected: number; total: number };
  notes?: string;
};

const BENCHES: Bench[] = [
  {
    id: "dvmcp",
    name: "DVMCP",
    description:
      "Damn Vulnerable MCP Server, an open-source benchmark focused on MCP-specific exploits.",
    status: "pending",
    notes:
      "Native probes mcp-tool-description-injection and mcp-schema-poisoning will target this first.",
  },
  {
    id: "dvla",
    name: "DVLA",
    description:
      "Damn Vulnerable LLM Application, used here as a prompt-injection-shaped benchmark surface.",
    status: "pending",
    notes: "Reuses the prompt-injection probe family and needs a benchmark host.",
  },
  {
    id: "cybench",
    name: "Cybench subset",
    description:
      "A 10 to 15 task slice of Cybench aligned to the categories Spieon can meaningfully address.",
    status: "pending",
    notes: "Subset list is locked in PRD section 11.",
  },
  {
    id: "custom",
    name: "Spieon x402 target",
    description:
      "Custom vulnerable x402 endpoint that intentionally accepts replayed payment headers.",
    status: "pending",
    notes: "This is expected to be the first benchmark to ship for demos.",
  },
];

export default function BenchmarksPage() {
  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Benchmarks"
        title={
          <>
            Prove the
            <br />
            agent on
            <br />
            dedicated
            <br />
            targets.
          </>
        }
        description={
          <>
            Benchmark traffic runs on separate infrastructure, not the agent&apos;s
            own host, so measurement stays realistic without exposing the
            control plane itself.
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <Stat label="tracks" value={String(BENCHES.length)} />
            <Stat
              label="deployed"
              value={String(BENCHES.filter((bench) => bench.status === "deployed").length)}
            />
          </div>
        }
      />

      <ul className="grid gap-4 lg:grid-cols-2">
        {BENCHES.map((bench) => (
          <li key={bench.id}>
            <Panel className="h-full">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-2">
                  <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
                    benchmark / {bench.id}
                  </p>
                  <h2 className="font-editorial-sans text-2xl font-semibold uppercase leading-tight">
                    {bench.name}
                  </h2>
                </div>
                <StatusPill tone={bench.status === "deployed" ? "success" : "neutral"}>
                  {bench.status}
                </StatusPill>
              </div>
              <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
                {bench.description}
              </p>
              {bench.score ? (
                <p className="mt-4 font-editorial-mono text-sm text-[var(--ink)]">
                  {bench.score.detected} / {bench.score.total} detections
                </p>
              ) : null}
              {bench.notes ? (
                <p className="mt-4 text-xs leading-5 text-[var(--muted)]">
                  {bench.notes}
                </p>
              ) : null}
            </Panel>
          </li>
        ))}
      </ul>
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
