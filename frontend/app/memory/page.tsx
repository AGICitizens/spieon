import { api, type Heuristic } from "@/lib/api";
import { EmptyState, PageHeader, Panel, StatusPill } from "@/components/ui";

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

  const averageSuccess =
    heuristics.length > 0
      ? `${Math.round(
          heuristics.reduce((sum, heuristic) => sum + heuristic.success_rate, 0) /
            heuristics.length *
            100,
        )}%`
      : "—";

  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Procedural Memory"
        title={
          <>
            What the agent
            <br />
            learns should
            <br />
            stay auditable.
          </>
        }
        description={
          <>
            Heuristics derived from past scans are content-addressed and
            attested onchain so operators can inspect how Spieon adapts over
            time.
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <Stat label="versions" value={String(heuristics.length)} />
            <Stat label="avg success" value={averageSuccess} />
          </div>
        }
      />

      {error ? (
        <EmptyState title="Backend unreachable" description={error} />
      ) : heuristics.length === 0 ? (
        <EmptyState
          title="No heuristics yet"
          description="Run a few scans and Spieon will start deriving reusable heuristics that appear here."
        />
      ) : (
        <ul className="space-y-4">
          {heuristics.map((heuristic) => (
            <li key={heuristic.id}>
              <Panel>
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                  <div className="space-y-2">
                    <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
                      heuristic / {heuristic.heuristic_key}
                    </p>
                    <h2 className="font-editorial-sans text-2xl font-semibold uppercase">
                      Version {heuristic.version}
                    </h2>
                  </div>
                  <StatusPill tone="info">
                    {pct(heuristic.success_rate)} on {heuristic.sample_size} samples
                  </StatusPill>
                </div>

                <p className="mt-4 max-w-4xl text-sm leading-6 text-[var(--muted)]">
                  {heuristic.rule}
                </p>

                <dl className="mt-5 grid gap-x-6 gap-y-3 text-xs sm:grid-cols-3">
                  {heuristic.target_type ? (
                    <Field label="target" value={heuristic.target_type} />
                  ) : null}
                  {heuristic.probe_class ? (
                    <Field label="probe class" value={heuristic.probe_class} />
                  ) : null}
                  {heuristic.owasp_id ? (
                    <Field label="owasp" value={heuristic.owasp_id} />
                  ) : null}
                  {heuristic.atlas_technique_id ? (
                    <Field label="atlas" value={heuristic.atlas_technique_id} />
                  ) : null}
                  <Field
                    label="content hash"
                    value={`${heuristic.content_hash.slice(0, 12)}…`}
                    mono
                  />
                  {heuristic.eas_attestation_uid ? (
                    <Field
                      label="attestation"
                      value={`${heuristic.eas_attestation_uid.slice(0, 12)}…`}
                      mono
                    />
                  ) : null}
                </dl>
              </Panel>
            </li>
          ))}
        </ul>
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
      <dt className="font-editorial-mono uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </dt>
      <dd className={`mt-1 text-sm text-[var(--ink)] ${mono ? "font-editorial-mono" : ""}`}>
        {value}
      </dd>
    </div>
  );
}
