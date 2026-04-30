import Link from "next/link";
import { api, type Finding } from "@/lib/api";

const SEVERITY_STYLE: Record<Finding["severity"], string> = {
  low: "bg-zinc-900 text-zinc-300 border-zinc-700",
  medium: "bg-amber-950/40 text-amber-200 border-amber-700",
  high: "bg-orange-950/40 text-orange-200 border-orange-700",
  critical: "bg-red-950/40 text-red-200 border-red-700",
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

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Findings</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Global metadata feed. Bundles stay encrypted to the operator's age
          recipient — only the cipher digest is published.
        </p>
      </header>

      {error ? (
        <p className="text-sm text-red-400">backend unreachable: {error}</p>
      ) : findings.length === 0 ? (
        <p className="text-sm text-zinc-500">No findings yet.</p>
      ) : (
        <ul className="space-y-3">
          {findings.map((f) => (
            <li
              key={f.id}
              className="rounded-md border border-zinc-800 bg-zinc-950/40 p-4"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <h2 className="font-medium text-zinc-100">{f.title}</h2>
                <span
                  className={`rounded border px-2 py-0.5 text-xs uppercase tracking-wide ${SEVERITY_STYLE[f.severity]}`}
                >
                  {f.severity}
                </span>
              </div>
              <p className="mt-2 text-sm text-zinc-400">{f.summary}</p>
              <dl className="mt-3 grid gap-x-6 gap-y-2 text-xs text-zinc-500 sm:grid-cols-2 lg:grid-cols-4">
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
                      className="font-mono text-zinc-300 hover:text-zinc-100"
                    >
                      {f.scan_id.slice(0, 8)}…
                    </Link>
                  }
                />
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
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-zinc-500">{label}</dt>
      <dd className={`text-zinc-300 ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}
