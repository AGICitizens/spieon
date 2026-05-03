import { api, type Finding, type NarrationEvent, type Scan } from "@/lib/api";
import { EmptyState, PageHeader, Panel, StatusPill } from "@/components/ui";
import DecryptPanel from "./DecryptPanel";
import LiveRefresh from "./LiveRefresh";
import NarrationStream from "./NarrationStream";
import PayoutButton from "./PayoutButton";

const STATUS_STYLE: Record<
  Scan["status"],
  "neutral" | "warning" | "info" | "success" | "danger"
> = {
  pending: "neutral",
  running: "warning",
  verifying: "info",
  attesting: "info",
  done: "success",
  failed: "danger",
  canceled: "neutral",
};

const SEVERITY_STYLE: Record<
  Finding["severity"],
  "neutral" | "warning" | "danger"
> = {
  low: "neutral",
  medium: "warning",
  high: "warning",
  critical: "danger",
};

type Params = { id: string };

export default async function ScanDetailPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { id } = await params;

  let findings: Finding[] = [];
  let narration: NarrationEvent[] = [];
  let scan: Scan | null = null;
  let scanError: string | null = null;
  try {
    [findings, scan, narration] = await Promise.all([
      api.listFindings({ scanId: id }),
      api.getScan(id).catch(() => null),
      api.listNarration(id).catch(() => []),
    ]);
  } catch (err) {
    scanError = (err as Error).message;
  }

  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Scan Detail"
        title={
          <>
            Watch one
            <br />
            target move
            <br />
            from recon
            <br />
            to attestation.
          </>
        }
        description={
          <>
            The detail view shows live narration, public findings, and payout
            controls without breaking the evidence chain.
          </>
        }
        aside={
          scan ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
                  Scan status
                </p>
                <StatusPill tone={STATUS_STYLE[scan.status]}>{scan.status}</StatusPill>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Stat label="budget" value={scan.budget_usdc} />
                <Stat label="spent" value={scan.spent_usdc} />
                <Stat label="findings" value={String(findings.length)} />
                <Stat label="adapt" value={String(scan.adapt_iterations)} />
              </div>
              <p className="font-editorial-mono text-xs leading-5 text-[var(--muted)]">
                {scan.target_url}
              </p>
            </div>
          ) : (
            <div className="text-sm leading-6 text-[var(--muted)]">
              Scan metadata appears here once the backend returns the record.
            </div>
          )
        }
      />

      {scan && (scan.status === "running" || scan.status === "pending") ? (
        <LiveRefresh intervalMs={3000} />
      ) : null}

      {scanError ? (
        <EmptyState title="Backend unreachable" description={scanError} />
      ) : null}

      {scan ? (
        <Panel className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
              Target
            </p>
            {scan.error ? <StatusPill tone="danger">{scan.error}</StatusPill> : null}
          </div>
          <p className="font-editorial-mono text-sm text-[var(--ink)]">{scan.id}</p>
          <p className="text-sm leading-6 text-[var(--muted)]">{scan.target_url}</p>
        </Panel>
      ) : null}

      <NarrationStream
        scanId={id}
        scanStatus={scan?.status ?? null}
        initialEvents={narration}
      />

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
              Findings
            </p>
            <h2 className="mt-2 font-editorial-sans text-2xl font-semibold uppercase">
              {findings.length} public records
            </h2>
          </div>
          <StatusPill tone="neutral">{findings.length} items</StatusPill>
        </div>

        {findings.length === 0 ? (
          <EmptyState
            title="No findings yet"
            description="Findings will appear here as the agent verifies and attests them."
          />
        ) : (
          <ul className="space-y-4">
            {findings.map((finding) => (
              <li key={finding.id}>
                <Panel className="space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-2">
                      <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
                        finding / {finding.id.slice(0, 8)}
                      </p>
                      <h3 className="font-editorial-sans text-2xl font-semibold uppercase leading-tight">
                        {finding.title}
                      </h3>
                    </div>
                    <StatusPill tone={SEVERITY_STYLE[finding.severity]}>
                      {finding.severity}
                    </StatusPill>
                  </div>

                  <p className="text-sm leading-6 text-[var(--muted)]">
                    {finding.summary}
                  </p>

                  <dl className="grid gap-x-6 gap-y-3 text-xs sm:grid-cols-2 lg:grid-cols-4">
                    {finding.owasp_id ? <Field label="owasp" value={finding.owasp_id} /> : null}
                    {finding.atlas_technique_id ? (
                      <Field label="atlas" value={finding.atlas_technique_id} />
                    ) : null}
                    {finding.eas_attestation_uid ? (
                      <Field
                        label="attestation"
                        value={`${finding.eas_attestation_uid.slice(0, 10)}…`}
                        mono
                      />
                    ) : null}
                    {finding.ciphertext_sha256 ? (
                      <Field
                        label="ciphertext"
                        value={`${finding.ciphertext_sha256.slice(0, 10)}…`}
                        mono
                      />
                    ) : null}
                  </dl>

                  <PayoutButton finding={finding} />
                  <DecryptPanel finding={finding} />
                </Panel>
              </li>
            ))}
          </ul>
        )}
      </section>
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
