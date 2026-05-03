import Link from "next/link";
import { api, type Finding } from "@/lib/api";
import { EmptyState, PageHeader, Panel, StatusPill } from "@/components/ui";

const SEVERITY_STYLE: Record<
  Finding["severity"],
  "neutral" | "warning" | "danger"
> = {
  low: "neutral",
  medium: "warning",
  high: "warning",
  critical: "danger",
};

function formatUsdc(value: string) {
  const num = Number(value);
  if (Number.isNaN(num)) return value;
  return `${num.toFixed(num < 1 ? 6 : 2)} USDC`;
}

export default async function FindingsPage() {
  let findings: Finding[] = [];
  let error: string | null = null;
  try {
    findings = await api.listFindings({ limit: 100 });
  } catch (err) {
    error = (err as Error).message;
  }

  const critical = findings.filter((finding) => finding.severity === "critical").length;
  const totalCost = findings.reduce((sum, finding) => {
    const num = Number(finding.cost_usdc);
    return Number.isNaN(num) ? sum : sum + num;
  }, 0);

  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Attested Findings"
        title={
          <>
            Review the
            <br />
            signal that
            <br />
            survived
            <br />
            verification.
          </>
        }
        description={
          <>
            This feed exposes only public metadata. Full evidence bundles stay
            encrypted to the operator who submitted the scan, while the
            attestation trail remains visible for everyone else.
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <Stat label="total" value={String(findings.length)} />
            <Stat label="critical" value={String(critical)} />
            <Stat label="cost" value={formatUsdc(String(totalCost))} />
            <Stat label="window" value="100 rows" />
          </div>
        }
      />

      {error ? (
        <EmptyState
          title="Backend unreachable"
          description={error}
        />
      ) : findings.length === 0 ? (
        <EmptyState
          title="No findings yet"
          description="Run scans first and attested findings will accumulate here with severity, cost, and the public evidence trail."
        />
      ) : (
        <ul className="space-y-4">
          {findings.map((f) => (
            <li key={f.id}>
              <Panel>
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <div className="space-y-2">
                  <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
                    finding / {f.id.slice(0, 8)}
                  </p>
                  <h2 className="font-editorial-sans text-2xl font-semibold uppercase leading-tight">
                    {f.title}
                  </h2>
                </div>
                <StatusPill tone={SEVERITY_STYLE[f.severity]}>
                  {f.severity}
                </StatusPill>
              </div>
              <p className="mt-4 max-w-4xl text-sm leading-6 text-[var(--muted)]">
                {f.summary}
              </p>
              <dl className="mt-5 grid gap-x-6 gap-y-3 text-xs sm:grid-cols-2 lg:grid-cols-4">
                {f.target_url ? (
                  <Field label="target" value={f.target_url} mono />
                ) : null}
                <Field label="cost" value={formatUsdc(f.cost_usdc)} />
                {f.owasp_id ? <Field label="owasp" value={f.owasp_id} /> : null}
                {f.atlas_technique_id ? (
                  <Field label="atlas" value={f.atlas_technique_id} />
                ) : null}
                {f.eas_attestation_uid ? (
                  <Field
                    label="attestation"
                    value={`${f.eas_attestation_uid.slice(0, 10)}…`}
                    mono
                  />
                ) : null}
                {f.ciphertext_sha256 ? (
                  <Field
                    label="ciphertext"
                    value={`${f.ciphertext_sha256.slice(0, 10)}…`}
                    mono
                  />
                ) : null}
                <Field
                  label="scan"
                  value={
                    <Link
                      href={`/scan/${f.scan_id}`}
                      className="font-editorial-mono text-[var(--ink)] underline decoration-[var(--line-strong)] underline-offset-4"
                    >
                      {f.scan_id.slice(0, 8)}…
                    </Link>
                  }
                />
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
  value: React.ReactNode;
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
