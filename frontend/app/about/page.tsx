export default function AboutPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">About Spieon</h1>
      </header>

      <div className="space-y-4 text-sm text-zinc-300">
        <p>
          Spieon is an autonomous security agent built for the agent economy.
          It scans MCP servers and x402-protected endpoints, attests findings on
          Base Sepolia, encrypts each finding bundle to the operator who
          submitted the scan, and pays bounties to the module authors whose
          probes landed.
        </p>
        <p>
          Unlike one-shot pentest tools, Spieon keeps procedural memory:
          heuristics it derives from past scans are versioned, content-addressed,
          and attested onchain so the public memory log can be checked against
          the agent's claim. The next scan against a similar target loads those
          heuristics before planning probes.
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wide text-zinc-500">
          Threat model
        </h2>
        <p className="text-sm text-zinc-300">
          Documented end to end in{" "}
          <a
            href="https://github.com/agicitizens/spieon/blob/main/docs/THREAT_MODEL.md"
            className="text-zinc-100 underline"
          >
            docs/THREAT_MODEL.md
          </a>
          : adversarial targets, adversarial operators, adversarial module
          authors, infrastructure compromise, operator key loss. Each surface is
          paired with the in-tree mitigation that addresses it.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wide text-zinc-500">
          Security disclosure
        </h2>
        <p className="text-sm text-zinc-300">
          Found a vulnerability in Spieon itself? Open a private security
          advisory on GitHub at{" "}
          <span className="font-mono">github.com/agicitizens/spieon/security</span>
          . Spieon does not accept findings about other peoples' agents through
          this endpoint — point Spieon at them instead.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wide text-zinc-500">FAQ</h2>
        <div className="space-y-3 text-sm text-zinc-300">
          <p>
            <span className="text-zinc-100">Where does Spieon get the keys?</span>{" "}
            The encryption recipient is generated in the operator's browser at
            scan submission. The matching secret never leaves their machine. The
            attesting wallet is a separate hot wallet capped at $50 USDC; see{" "}
            <a
              href="https://github.com/agicitizens/spieon/blob/main/docs/RECOVERY.md"
              className="text-zinc-100 underline"
            >
              RECOVERY.md
            </a>
            .
          </p>
          <p>
            <span className="text-zinc-100">Can the agent steal funds?</span>{" "}
            Bounty payouts are gated by per-severity caps in{" "}
            <span className="font-mono">BountyPool</span>; single payouts above
            $20 require a configured cosigner.
          </p>
          <p>
            <span className="text-zinc-100">Can targets attack the agent?</span>{" "}
            Target output flows through structured tools only — no free-text
            interpolation into the agent's instruction stream — and probes
            actively scan responses for canary phrases that signal a successful
            injection.
          </p>
        </div>
      </section>
    </section>
  );
}
