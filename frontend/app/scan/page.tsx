"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
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
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Submit a scan</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Spieon encrypts every finding bundle to a recipient key you generate
          here. The matching private key never leaves your browser.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-5">
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
            className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-zinc-600"
          />
        </Field>

        <Field
          label="Operator address"
          hint="Your wallet — used for attribution and the bounty escrow."
        >
          <input
            type="text"
            required
            value={operatorAddress}
            onChange={(e) => setOperatorAddress(e.target.value)}
            placeholder="0x…"
            className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-sm text-zinc-100 outline-none focus:border-zinc-600"
          />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Budget (USDC)" hint="Max Spieon may spend on probes.">
            <input
              type="text"
              required
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-zinc-600"
            />
          </Field>
          <Field
            label="Bounty (USDC)"
            hint="Reserved per-finding payout pool."
          >
            <input
              type="text"
              required
              value={bounty}
              onChange={(e) => setBounty(e.target.value)}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-zinc-600"
            />
          </Field>
        </div>

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

        <label className="flex items-start gap-3 rounded-md border border-zinc-800 bg-zinc-950/40 p-3 text-sm text-zinc-300">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-1"
          />
          <span>
            I authorize Spieon to probe this endpoint with adversarial inputs.
            Probes may cause temporary service disruption. I take responsibility
            for ensuring the target is appropriate for testing.
          </span>
        </label>

        {error ? <p className="text-sm text-red-400">{error}</p> : null}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-100 hover:border-zinc-500 disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Submit scan"}
        </button>
      </form>
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
    <label className="block space-y-1">
      <span className="text-sm text-zinc-300">{label}</span>
      {children}
      {hint ? <span className="block text-xs text-zinc-500">{hint}</span> : null}
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
    <div className="space-y-2 rounded-md border border-zinc-800 bg-zinc-950/40 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-zinc-300">Recipient key</p>
          <p className="text-xs text-zinc-500">
            X25519 keypair generated locally. Spieon only sees the public part.
          </p>
        </div>
        <button
          type="button"
          onClick={onGenerate}
          className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 hover:border-zinc-500"
        >
          {identity ? "Regenerate" : "Generate"}
        </button>
      </div>

      {identity ? (
        <div className="space-y-2 text-xs">
          <div className="rounded border border-zinc-800 bg-black/40 p-2 font-mono break-all text-zinc-300">
            <span className="text-zinc-500">recipient:</span> {identity.recipient}
          </div>
          <button
            type="button"
            onClick={onDownload}
            className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-zinc-200 hover:border-zinc-500"
          >
            {downloaded ? "Re-download key file" : "Download key file"}
          </button>
          {!downloaded ? (
            <p className="text-zinc-500">
              Download required before submitting — there is no recovery path.
            </p>
          ) : (
            <p className="text-zinc-500">
              Key saved. Keep the file somewhere safe.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
