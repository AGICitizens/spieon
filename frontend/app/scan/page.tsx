"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { PageHeader, Panel, StatusPill } from "@/components/ui";
import {
  type ScanIdentity,
  downloadIdentityFile,
  generateScanIdentity,
} from "@/lib/encryption";

export default function ScanSubmissionPage() {
  const router = useRouter();

  const [targetUrl, setTargetUrl] = useState("");
  const [operatorAddress, setOperatorAddress] = useState("");
  const [budget, setBudget] = useState("1.00");
  const [bounty, setBounty] = useState("5.00");
  const [identity, setIdentity] = useState<ScanIdentity | null>(null);
  const [identityDownloaded, setIdentityDownloaded] = useState(false);
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setError(null);
    try {
      const next = await generateScanIdentity();
      setIdentity(next);
      setIdentityDownloaded(false);
    } catch (err) {
      setError(`could not generate keypair: ${(err as Error).message}`);
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!identity) {
      setError("Generate a recipient key before submitting.");
      return;
    }
    if (!identityDownloaded) {
      setError(
        "Download the recipient key first — the backend cannot recover it."
      );
      return;
    }
    if (!consent) {
      setError("Operator consent is required.");
      return;
    }
    setSubmitting(true);
    try {
      const scan = await api.createScan({
        target_url: targetUrl,
        operator_address: operatorAddress,
        recipient_pubkey: identity.recipient,
        budget_usdc: budget,
        bounty_usdc: bounty,
        consent: true,
      });
      router.push(`/scan/${scan.id}`);
    } catch (err) {
      setError(`submission failed: ${(err as Error).message}`);
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Scan Intake"
        title={
          <>
            Start one
            <br />
            deliberate
            <br />
            scan.
          </>
        }
        description={
          <>
            Spieon encrypts every evidence bundle to a recipient key you
            generate locally. The private half never leaves the browser, so the
            operator stays in control of sensitive findings.
          </>
        }
        aside={
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
                Operator flow
              </p>
              <StatusPill tone="info">local key custody</StatusPill>
            </div>
            <ol className="space-y-3">
              {[
                "Generate a recipient keypair in-browser.",
                "Set the target, budget, and bounty parameters.",
                "Download the key file before you dispatch the scan.",
              ].map((step, index) => (
                <li
                  key={step}
                  className="grid grid-cols-[1.75rem_1fr] gap-3 border-t border-[var(--line)] pt-3 text-sm leading-6 text-[var(--muted)] first:border-t-0 first:pt-0"
                >
                  <span className="font-editorial-mono text-[0.72rem] font-bold text-[var(--ink)]">
                    0{index + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        }
      />

      <Panel>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,22rem)]">
            <div className="space-y-5">
              <Field
                label="Target URL"
                hint="x402-protected endpoint or MCP server."
              >
                <input
                  type="url"
                  required
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder="https://example.invalid/mcp"
                  className="editorial-input"
                />
              </Field>

              <Field
                label="Operator address"
                hint="Used for attribution and bounty escrow."
              >
                <input
                  type="text"
                  required
                  value={operatorAddress}
                  onChange={(e) => setOperatorAddress(e.target.value)}
                  placeholder="0x…"
                  className="editorial-input font-editorial-mono"
                />
              </Field>

              <div className="grid gap-4 sm:grid-cols-2">
                <Field
                  label="Budget (USDC)"
                  hint="Maximum spend reserved for probes."
                >
                  <input
                    type="text"
                    required
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    className="editorial-input"
                  />
                </Field>
                <Field
                  label="Bounty (USDC)"
                  hint="Per-finding payout pool available to winning modules."
                >
                  <input
                    type="text"
                    required
                    value={bounty}
                    onChange={(e) => setBounty(e.target.value)}
                    className="editorial-input"
                  />
                </Field>
              </div>

              <label className="editorial-card flex items-start gap-3 p-4 text-sm leading-6 text-[var(--muted)]">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  className="mt-1 h-4 w-4 accent-[var(--ink)]"
                />
                <span>
                  I authorize Spieon to probe this endpoint with adversarial
                  inputs and I understand those probes may cause temporary
                  service disruption.
                </span>
              </label>
            </div>

            <div className="space-y-5">
              <RecipientKeyPanel
                identity={identity}
                downloaded={identityDownloaded}
                onGenerate={handleGenerate}
                onDownload={() => {
                  if (!identity) return;
                  downloadIdentityFile(identity);
                  setIdentityDownloaded(true);
                }}
              />

              <div className="editorial-card p-5">
                <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
                  Why it matters
                </p>
                <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
                  Scan evidence can include sensitive payloads, operator details,
                  and exploit traces. Downloading the key first ensures only the
                  operator can decrypt the full bundle later.
                </p>
              </div>
            </div>
          </div>

          {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="submit"
              disabled={submitting}
              className="editorial-button editorial-button-dark disabled:translate-x-0 disabled:translate-y-0 disabled:opacity-60"
            >
              {submitting ? "Submitting…" : "Dispatch scan"}
            </button>
            <p className="max-w-xl text-sm leading-6 text-[var(--muted)]">
              Submissions redirect directly into the live scan view so operators
              can watch narration events and findings appear in real time.
            </p>
          </div>
        </form>
      </Panel>
    </section>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-2">
      <span className="font-editorial-mono text-[0.72rem] font-bold uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </span>
      {children}
      {hint ? (
        <span className="block text-xs leading-5 text-[var(--muted)]">{hint}</span>
      ) : null}
    </label>
  );
}

function RecipientKeyPanel({
  identity,
  downloaded,
  onGenerate,
  onDownload,
}: {
  identity: ScanIdentity | null;
  downloaded: boolean;
  onGenerate: () => void;
  onDownload: () => void;
}) {
  return (
    <div className="editorial-card space-y-4 p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
            Recipient key
          </p>
          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
            X25519 keypair generated locally. Spieon only sees the public part.
          </p>
        </div>
        <button
          type="button"
          onClick={onGenerate}
          className="editorial-button editorial-button-light min-h-0 px-4 py-3"
        >
          {identity ? "Regenerate" : "Generate"}
        </button>
      </div>

      {identity ? (
        <div className="space-y-3 text-xs">
          <div className="border border-[var(--line-strong)] bg-[var(--panel-strong)] p-3 font-editorial-mono break-all text-[var(--ink)]">
            <span className="text-[var(--muted)]">recipient:</span> {identity.recipient}
          </div>
          <button
            type="button"
            onClick={onDownload}
            className="editorial-button editorial-button-dark min-h-0 px-4 py-3"
          >
            {downloaded ? "Re-download key file" : "Download key file"}
          </button>
          {!downloaded ? (
            <p className="leading-5 text-[var(--warning)]">
              Download required before submitting — there is no recovery path.
            </p>
          ) : (
            <p className="leading-5 text-[var(--success)]">
              Key saved. Keep the file somewhere safe.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
