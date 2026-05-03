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
      <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
        Paid <span className="font-editorial-mono text-[var(--ink)]">{amount} USDC</span> →{" "}
        <span className="font-editorial-mono text-[var(--ink)]">
          {(finding.bounty_recipient ?? "").slice(0, 10)}…
        </span>{" "}
        · tx{" "}
        <span className="font-editorial-mono text-[var(--ink)]">
          {finding.bounty_tx_hash.slice(0, 10)}…
        </span>
      </p>
    );
  }

  if (!finding.eas_attestation_uid) {
    return (
      <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
        Not attested yet — waiting on the agent.
      </p>
    );
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="editorial-button editorial-button-dark mt-3 min-h-0 px-4 py-3"
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
      className="editorial-card mt-3 space-y-3 p-4"
    >
      <label className="block text-xs text-[var(--muted)]">
        Recipient address
        <input
          type="text"
          required
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
          placeholder="0x…"
          className="editorial-input mt-2 font-editorial-mono text-sm"
        />
      </label>
      <label className="block text-xs text-[var(--muted)]">
        Amount (USDC)
        <input
          type="text"
          required
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="editorial-input mt-2 text-sm"
        />
      </label>
      {error ? <p className="text-xs text-[var(--danger)]">{error}</p> : null}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="editorial-button editorial-button-dark min-h-0 px-4 py-3 disabled:translate-x-0 disabled:translate-y-0 disabled:opacity-60"
        >
          {submitting ? "Paying…" : "Confirm payout"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="editorial-button editorial-button-light min-h-0 px-4 py-3"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
