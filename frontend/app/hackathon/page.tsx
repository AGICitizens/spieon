import Link from "next/link";
import { PageHeader, Panel, SectionHeading, StatusPill } from "@/components/ui";

const VERIFY_LINKS = [
  {
    label: "AI usage log",
    href: "https://github.com/AGICitizens/spieon/blob/main/docs/AI_USAGE.md",
    detail: "Required disclosure for ETHGlobal Open Agents judges.",
  },
  {
    label: "Demo playbook",
    href: "https://github.com/AGICitizens/spieon/blob/main/docs/DEMO.md",
    detail: "Sponsor tracks, verification steps, and the judge cheat sheet.",
  },
  {
    label: "Threat model",
    href: "https://github.com/AGICitizens/spieon/blob/main/docs/THREAT_MODEL.md",
    detail: "Adversaries, mitigations, and payout abuse assumptions.",
  },
];

const SPONSORS = [
  {
    name: "ENS",
    track: "Best ENS Integration for AI Agents",
    summary:
      "The agent identity is anchored to spieon-agent.eth on Sepolia, and the app reads ENS records live instead of hardcoding them.",
    proof:
      "Surfaced in /.well-known/agent.json, /agent/stats, and the /agent profile with chain-backed text records and reverse resolution.",
  },
  {
    name: "KeeperHub",
    track: "Best Integration with KeeperHub",
    summary:
      "After a confirmed bounty payout, Spieon triggers a KeeperHub workflow paid via the same x402 client used during scans.",
    proof:
      "The payout response carries keeperhub execution metadata, and the /agent page shows the resulting workflow run.",
  },
];

export default function HackathonPage() {
  return (
    <section className="space-y-8">
      <PageHeader
        eyebrow="Hackathon Brief"
        title={
          <>
            Built for
            <br />
            judges, hosts,
            <br />
            and sponsor
            <br />
            reviewers.
          </>
        }
        description={
          <>
            This page packages the judge-facing context in one place: what AI
            assisted with, which sponsor tracks are live, how bounties flow,
            and where to verify each claim in the open-source repo.
          </>
        }
        actions={
          <>
            <a
              href="https://github.com/AGICitizens/spieon"
              target="_blank"
              rel="noreferrer"
              className="editorial-button editorial-button-dark"
            >
              Open OSS repo
            </a>
            <a
              href="https://github.com/AGICitizens/spieon/blob/main/docs/DEMO.md"
              target="_blank"
              rel="noreferrer"
              className="editorial-button editorial-button-light"
            >
              Judge playbook
            </a>
          </>
        }
        aside={
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <StatusPill tone="success">open source</StatusPill>
              <StatusPill tone="info">AI disclosed</StatusPill>
              <StatusPill tone="warning">sponsor-ready</StatusPill>
            </div>
            <p className="font-editorial-serif text-3xl italic leading-tight text-[var(--ink)]">
              Every claim here maps back to code, docs, or chain-visible proof.
            </p>
            <p className="text-sm leading-6 text-[var(--muted)]">
              Spieon is an ETHGlobal Open Agents submission focused on MCP and
              x402 security, attestation, and incentive alignment.
            </p>
          </div>
        }
      />

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <Panel className="space-y-5">
          <SectionHeading
            label="AI usage"
            title="Disclosed the way judges expect"
            description="Per the hackathon rules, AI is treated as a development assistant rather than an invisible co-author."
          />
          <div className="space-y-4 text-sm leading-7 text-[var(--muted)]">
            <p>
              The repository includes a dedicated{" "}
              <a
                href="https://github.com/AGICitizens/spieon/blob/main/docs/AI_USAGE.md"
                target="_blank"
                rel="noreferrer"
                className="font-editorial-mono text-[var(--ink)] underline decoration-[var(--line-strong)] underline-offset-4"
              >
                AI usage log
              </a>{" "}
              that explains where tools like Claude Code assisted with drafting,
              scaffolding, refactoring, and debugging.
            </p>
            <p>
              The same disclosure states what remained human-led: architecture,
              probe design, incentive model, threat model, and the demo
              narrative. The goal is a complete and honest record rather than a
              vague “AI was used” footnote.
            </p>
          </div>
        </Panel>

        <Panel className="space-y-5">
          <SectionHeading
            label="Verification"
            title="Fast links for review"
            description="Useful when a host or judge wants the shortest path from claim to evidence."
          />
          <div className="space-y-3">
            {VERIFY_LINKS.map((item) => (
              <a
                key={item.href}
                href={item.href}
                target="_blank"
                rel="noreferrer"
                className="block border border-[var(--line)] p-4 transition-transform duration-150 hover:-translate-x-1 hover:-translate-y-1"
              >
                <p className="font-editorial-sans text-lg font-semibold uppercase text-[var(--ink)]">
                  {item.label}
                </p>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{item.detail}</p>
              </a>
            ))}
          </div>
        </Panel>
      </section>

      <section className="space-y-4">
        <SectionHeading
          label="Sponsors"
          title="Tracks integrated into the product"
          description="These are not slide-only claims. Each integration has runtime behavior and a repo-level verification path."
        />
        <div className="grid gap-4 lg:grid-cols-2">
          {SPONSORS.map((sponsor) => (
            <Panel key={sponsor.name} className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
                    {sponsor.name}
                  </p>
                  <h3 className="mt-2 font-editorial-sans text-xl font-semibold uppercase leading-tight">
                    {sponsor.track}
                  </h3>
                </div>
                <StatusPill tone="success">integrated</StatusPill>
              </div>
              <p className="text-sm leading-6 text-[var(--muted)]">{sponsor.summary}</p>
              <p className="border-t border-[var(--line)] pt-4 text-sm leading-6 text-[var(--muted)]">
                {sponsor.proof}
              </p>
            </Panel>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Panel className="space-y-4">
          <SectionHeading label="Bounties" title="Real incentives, not fake points" />
          <p className="text-sm leading-6 text-[var(--muted)]">
            Findings can trigger bounty payouts to module authors. Severity caps
            and payout data are visible in the product, and seeded demo scans
            are ready for the attestation-to-payout proof path judges care
            about.
          </p>
        </Panel>

        <Panel className="space-y-4">
          <SectionHeading label="Attestations" title="Chain-visible evidence" />
          <p className="text-sm leading-6 text-[var(--muted)]">
            Confirmed findings are attested on Base Sepolia. The frontend links
            directly to the attestation explorer so a reviewer can move from UI
            claim to chain proof without leaving the demo trail.
          </p>
        </Panel>

        <Panel className="space-y-4">
          <SectionHeading label="Open review" title="Repo-first judging" />
          <p className="text-sm leading-6 text-[var(--muted)]">
            Judges can inspect the app, contracts, docs, and deployment notes in
            the public repository, then trace those claims through the live
            interface rather than relying on a pitch-only narrative.
          </p>
        </Panel>
      </section>

      <Panel className="space-y-5">
        <SectionHeading
          label="Next steps"
          title="Where to go from here"
          description="A compact route for someone evaluating the project under time pressure."
        />
        <div className="grid gap-3 lg:grid-cols-3">
          <Link href="/agent" className="editorial-button editorial-button-light justify-center">
            Inspect agent profile
          </Link>
          <Link href="/leaderboard" className="editorial-button editorial-button-light justify-center">
            Review bounty outcomes
          </Link>
          <a
            href="https://github.com/AGICitizens/spieon"
            target="_blank"
            rel="noreferrer"
            className="editorial-button editorial-button-dark justify-center text-center"
          >
            Read the repo
          </a>
        </div>
      </Panel>
    </section>
  );
}
