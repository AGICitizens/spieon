import { api, type Heuristic } from "@/lib/api";

function pct(rate: number) {
  return `${Math.round(rate * 100)}%`;
}

export default async function MemoryPage() {
  let heuristics: Heuristic[] = [];
  let error: string | null = null;
  try {
    heuristics = await api.listHeuristics(100);
  } catch (err) {
    error = (err as Error).message;
  }

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Procedural memory</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Heuristics derived from past scans. Each version is content-addressed
          (sha256) and attested onchain so the public memory log can be checked
          against the agent's claim.
        </p>
      </header>

      {error ? (
        <p className="text-sm text-red-400">backend unreachable: {error}</p>
      ) : heuristics.length === 0 ? (
        <p className="text-sm text-zinc-500">
          The agent has not derived a heuristic yet. Run a few scans to populate
          this page.
        </p>
      ) : (
        <ul className="space-y-3">
          {heuristics.map((h) => (
            <li
              key={h.id}
              className="rounded-md border border-zinc-800 bg-zinc-950/40 p-4"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <h2 className="font-mono text-sm text-zinc-200">
                  {h.heuristic_key} <span className="text-zinc-500">v{h.version}</span>
                </h2>
                <span className="text-xs uppercase tracking-wide text-zinc-500">
                  {pct(h.success_rate)} on {h.sample_size} samples
                </span>
              </div>
              <p className="mt-2 text-sm text-zinc-300">{h.rule}</p>
              <dl className="mt-3 grid gap-x-6 gap-y-1 text-xs text-zinc-500 sm:grid-cols-3">
                {h.target_type ? (
                  <Field label="target" value={h.target_type} />
                ) : null}
                {h.probe_class ? (
                  <Field label="probe class" value={h.probe_class} />
                ) : null}
                {h.owasp_id ? <Field label="owasp" value={h.owasp_id} /> : null}
                {h.atlas_technique_id ? (
                  <Field label="atlas" value={h.atlas_technique_id} />
                ) : null}
                <Field label="content hash" value={`${h.content_hash.slice(0, 12)}…`} mono />
                {h.eas_attestation_uid ? (
                  <Field
                    label="attestation"
                    value={`${h.eas_attestation_uid.slice(0, 12)}…`}
                    mono
                  />
                ) : null}
              </dl>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-zinc-500">{label}</dt>
      <dd className={`text-zinc-300 ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}
