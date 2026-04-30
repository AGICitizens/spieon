"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Finding } from "@/lib/api";

const DEFAULT_AMOUNT: Record<Finding["severity"], string> = {
  low: "0.10",
  medium: "0.50",
  high: "2.00",
  critical: "5.00",
};

export default function PayoutButton({ finding }: { finding: Finding }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [recipient, setRecipient] = useState(finding.bounty_recipient ?? "");
  const [amount, setAmount] = useState(
    finding.bounty_amount_usdc ?? DEFAULT_AMOUNT[finding.severity],
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (finding.bounty_tx_hash) {
    return (
      <p className="mt-2 text-xs text-zinc-400">
        Paid <span className="font-mono text-zinc-200">{amount} USDC</span> →{" "}
        <span className="font-mono text-zinc-300">
          {(finding.bounty_recipient ?? "").slice(0, 10)}…
        </span>{" "}
        · tx{" "}
        <span className="font-mono text-zinc-300">
          {finding.bounty_tx_hash.slice(0, 10)}…
        </span>
      </p>
    );
  }

  if (!finding.eas_attestation_uid) {
    return (
      <p className="mt-2 text-xs text-zinc-500">
        Not attested yet — waiting on the agent.
      </p>
    );
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 hover:border-zinc-500"
      >
        Pay bounty
      </button>
    );
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.payFinding(finding.id, {
        recipient: recipient.trim(),
        amount_usdc: amount,
      });
      router.refresh();
      setOpen(false);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="mt-3 space-y-2 rounded-md border border-zinc-800 bg-zinc-950/40 p-3"
    >
      <label className="block text-xs text-zinc-400">
        Recipient address
        <input
          type="text"
          required
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
          placeholder="0x…"
          className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 font-mono text-sm text-zinc-100 outline-none focus:border-zinc-600"
        />
      </label>
      <label className="block text-xs text-zinc-400">
        Amount (USDC)
        <input
          type="text"
          required
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 text-sm text-zinc-100 outline-none focus:border-zinc-600"
        />
      </label>
      {error ? <p className="text-xs text-red-400">{error}</p> : null}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1 text-xs text-zinc-100 hover:border-zinc-500 disabled:opacity-50"
        >
          {submitting ? "Paying…" : "Confirm payout"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-md border border-zinc-800 px-3 py-1 text-xs text-zinc-400 hover:text-zinc-100"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
