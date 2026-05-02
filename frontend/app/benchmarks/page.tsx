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
      "Damn Vulnerable MCP Server — open-source benchmark of MCP-specific exploits.",
    status: "pending",
    notes:
      "Native probes mcp-tool-description-injection and mcp-schema-poisoning target this; numbers will land after a benchmark VPS run.",
  },
  {
    id: "dvla",
    name: "DVLA",
    description:
      "Damn Vulnerable LLM Application — prompt-injection-shaped CTF surface.",
    status: "pending",
    notes:
      "Reuses the prompt-injection probe surface; needs a benchmark host.",
  },
  {
    id: "cybench",
    name: "Cybench (subset)",
    description:
      "10–15 task subset of Cybench focused on the categories Spieon's probes can address.",
    status: "pending",
    notes: "Subset list is locked in PRD §11.",
  },
  {
    id: "custom",
    name: "Spieon-x402-target",
    description:
      "Custom vulnerable x402 endpoint that intentionally accepts replayed payment headers.",
    status: "pending",
    notes:
      "Smallest target — will be the first to ship and the cleanest demo number.",
  },
];

export default function BenchmarksPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Benchmarks</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Benchmarks are run on a separate VPS, not the agent's host. Spieon's
          own host is intentionally not exposed to benchmark traffic.
        </p>
      </header>

      <ul className="space-y-3">
        {BENCHES.map((b) => (
          <li
            key={b.id}
            className="rounded-md border border-zinc-800 bg-zinc-950/40 p-4"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <h2 className="font-medium text-zinc-100">{b.name}</h2>
              <span
                className={`rounded border px-2 py-0.5 text-xs uppercase tracking-wide ${
                  b.status === "deployed"
                    ? "border-emerald-700 bg-emerald-950/40 text-emerald-200"
                    : "border-zinc-700 bg-zinc-900 text-zinc-400"
                }`}
              >
                {b.status}
              </span>
            </div>
            <p className="mt-2 text-sm text-zinc-300">{b.description}</p>
            {b.score ? (
              <p className="mt-3 font-mono text-sm text-zinc-100">
                {b.score.detected} / {b.score.total} detections
              </p>
            ) : null}
            {b.notes ? (
              <p className="mt-2 text-xs text-zinc-500">{b.notes}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
