"use client";

import { useState } from "react";
import { type Finding } from "@/lib/api";
import { decryptBundleJson } from "@/lib/encryption";

export default function DecryptPanel({ finding }: { finding: Finding }) {
  const [identity, setIdentity] = useState("");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plaintext, setPlaintext] = useState<string | null>(null);

  if (!finding.encrypted_bundle_uri) {
    return null;
  }

  async function load() {
    setBusy(true);
    setError(null);
    setPlaintext(null);
    try {
      const ciphertext = await fetchBundle(finding.encrypted_bundle_uri!);
      const decoded = await decryptBundleJson(ciphertext, identity.trim());
      setPlaintext(JSON.stringify(decoded, null, 2));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-1 font-editorial-mono text-[0.72rem] uppercase tracking-[0.18em] text-[var(--muted)] underline decoration-[var(--line-strong)] underline-offset-4 hover:text-[var(--ink)]"
      >
        Decrypt bundle
      </button>
    );
  }

  return (
    <div className="editorial-card mt-3 space-y-3 p-4">
      <p className="text-xs leading-5 text-[var(--muted)]">
        Paste the AGE-SECRET-KEY-… from the file you downloaded at scan
        submission. The key never leaves the browser.
      </p>
      <textarea
        value={identity}
        onChange={(e) => setIdentity(e.target.value)}
        placeholder="AGE-SECRET-KEY-…"
        rows={2}
        className="editorial-textarea font-editorial-mono text-xs"
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={load}
          disabled={busy || !identity.trim()}
          className="editorial-button editorial-button-dark min-h-0 px-4 py-3 disabled:translate-x-0 disabled:translate-y-0 disabled:opacity-60"
        >
          {busy ? "Decrypting…" : "Decrypt"}
        </button>
        <button
          type="button"
          onClick={() => {
            setOpen(false);
            setPlaintext(null);
            setError(null);
          }}
          className="editorial-button editorial-button-light min-h-0 px-4 py-3"
        >
          Close
        </button>
      </div>
      {error ? <p className="text-xs text-[var(--danger)]">{error}</p> : null}
      {plaintext ? (
        <pre className="max-h-64 overflow-auto border border-[var(--line-strong)] bg-[var(--panel-strong)] p-3 font-editorial-mono text-xs text-[var(--ink)]">
          {plaintext}
        </pre>
      ) : null}
    </div>
  );
}

async function fetchBundle(uri: string): Promise<Uint8Array> {
  if (uri.startsWith("file://")) {
    throw new Error(
      "bundle is on the local filesystem — not browser-accessible. Configure ZeroG or IPFS.",
    );
  }
  if (uri.startsWith("null://")) {
    throw new Error("bundle storage is null:// (no upload performed).");
  }
  if (uri.startsWith("ipfs://")) {
    const cid = uri.slice("ipfs://".length);
    const url = `https://${cid}.ipfs.w3s.link`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`gateway ${res.status}`);
    return new Uint8Array(await res.arrayBuffer());
  }
  const res = await fetch(uri);
  if (!res.ok) throw new Error(`fetch ${res.status}`);
  return new Uint8Array(await res.arrayBuffer());
}
