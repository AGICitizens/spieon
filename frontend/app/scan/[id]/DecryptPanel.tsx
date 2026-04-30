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
        className="mt-2 text-xs text-zinc-400 underline-offset-2 hover:text-zinc-200 hover:underline"
      >
        Decrypt bundle
      </button>
    );
  }

  return (
    <div className="mt-3 space-y-2 rounded-md border border-zinc-800 bg-zinc-950/40 p-3">
      <p className="text-xs text-zinc-400">
        Paste the AGE-SECRET-KEY-… from the file you downloaded at scan
        submission. The key never leaves the browser.
      </p>
      <textarea
        value={identity}
        onChange={(e) => setIdentity(e.target.value)}
        placeholder="AGE-SECRET-KEY-…"
        rows={2}
        className="w-full rounded-md border border-zinc-800 bg-zinc-950 p-2 font-mono text-xs text-zinc-100 outline-none focus:border-zinc-600"
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={load}
          disabled={busy || !identity.trim()}
          className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1 text-xs text-zinc-100 hover:border-zinc-500 disabled:opacity-50"
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
          className="rounded-md border border-zinc-800 px-3 py-1 text-xs text-zinc-400 hover:text-zinc-100"
        >
          Close
        </button>
      </div>
      {error ? <p className="text-xs text-red-400">{error}</p> : null}
      {plaintext ? (
        <pre className="max-h-64 overflow-auto rounded-md border border-zinc-800 bg-black/40 p-2 text-xs text-zinc-200">
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
