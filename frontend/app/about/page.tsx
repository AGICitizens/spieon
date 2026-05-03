import { PageHeader, Panel, SectionHeading } from "@/components/ui";

export default function AboutPage() {
  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="About Spieon"
        title={
          <>
            Security
            <br />
            operations for
            <br />
            the agent
            <br />
            economy.
          </>
        }
        description={
          <>
            Spieon is an autonomous security operator: scan live surfaces, keep
            evidence encrypted, publish attestations, and reward the probe
            modules that actually create signal.
          </>
        }
        aside={
          <div className="space-y-4 text-sm leading-6 text-[var(--muted)]">
            <p className="font-editorial-serif text-3xl italic leading-tight text-[var(--ink)]">
              Evidence first, memory second, incentives always visible.
            </p>
            <p>
              The interface now reflects that philosophy with sharper hierarchy
              and a quieter control-plane feel.
            </p>
          </div>
        }
      />

      <Panel className="space-y-4 text-sm leading-7 text-[var(--muted)]">
        <p>
          Spieon scans MCP servers and x402-protected endpoints, attests
          findings on Base Sepolia, encrypts each finding bundle to the operator
          who submitted the scan, and pays bounties to the module authors whose
          probes landed.
        </p>
        <p>
          Unlike one-shot pentest tools, Spieon keeps procedural memory:
          heuristics derived from past scans are versioned, content-addressed,
          and attested onchain so the public memory log can be checked against
          the agent&apos;s claim.
        </p>
      </Panel>

      <section className="grid gap-4 lg:grid-cols-2">
        <Panel className="space-y-4">
          <SectionHeading label="Threat model" title="Mapped end to end" />
          <p className="text-sm leading-6 text-[var(--muted)]">
            Documented in{" "}
            <a
              href="https://github.com/agicitizens/spieon/blob/main/docs/THREAT_MODEL.md"
              className="font-editorial-mono text-[var(--ink)] underline decoration-[var(--line-strong)] underline-offset-4"
            >
              docs/THREAT_MODEL.md
            </a>
            : adversarial targets, operators, module authors, infrastructure
            compromise, and operator key loss, each paired with its mitigation.
          </p>
        </Panel>

        <Panel className="space-y-4">
          <SectionHeading label="Security disclosure" title="Private path for Spieon issues" />
          <p className="text-sm leading-6 text-[var(--muted)]">
            Found a vulnerability in Spieon itself? Open a private security
            advisory at{" "}
            <span className="font-editorial-mono">
              github.com/agicitizens/spieon/security
            </span>
            . Findings about other agents should go through the scan workflow
            instead.
          </p>
        </Panel>
      </section>

      <section className="space-y-4">
        <SectionHeading label="FAQ" title="The edges operators ask about" />
        <div className="grid gap-4 lg:grid-cols-3">
          <Panel className="space-y-3 text-sm leading-6 text-[var(--muted)]">
            <p className="font-editorial-sans text-base font-semibold uppercase text-[var(--ink)]">
              Where do the keys come from?
            </p>
            <p>
              The encryption recipient is generated in the operator&apos;s browser
              at scan submission. The matching secret never leaves their
              machine. The attesting wallet is a separate hot wallet capped at
              $50 USDC; see{" "}
              <a
                href="https://github.com/agicitizens/spieon/blob/main/docs/RECOVERY.md"
                className="font-editorial-mono text-[var(--ink)] underline decoration-[var(--line-strong)] underline-offset-4"
              >
                RECOVERY.md
              </a>
              .
            </p>
          </Panel>

          <Panel className="space-y-3 text-sm leading-6 text-[var(--muted)]">
            <p className="font-editorial-sans text-base font-semibold uppercase text-[var(--ink)]">
              Can the agent steal funds?
            </p>
            <p>
              Bounty payouts are gated by per-severity caps in{" "}
              <span className="font-editorial-mono">BountyPool</span>; single
              payouts above $20 require a configured cosigner.
            </p>
          </Panel>

          <Panel className="space-y-3 text-sm leading-6 text-[var(--muted)]">
            <p className="font-editorial-sans text-base font-semibold uppercase text-[var(--ink)]">
              Can targets attack the agent?
            </p>
            <p>
              Target output flows through structured tools only. Probes also
              scan responses for canary phrases that signal a successful
              injection attempt against the agent.
            </p>
          </Panel>
        </div>
      </section>
    </section>
  );
}
