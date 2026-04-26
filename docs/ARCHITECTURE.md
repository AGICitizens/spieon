# Spieon — Architecture Diagrams

Visual companion to [PRD.md](PRD.md) (v2). Source of truth for behavior is the PRD; this file is for orientation.

## 1. Service topology

End-to-end view of components and where they run. Langfuse instruments every agent decision, tool call, memory operation, and chain interaction from day 1.

```mermaid
graph TB
    subgraph Browser
        UI[Next.js Frontend<br/>spieon.eth dashboard<br/>persistent-identity banner<br/>narration stream UI]
    end

    subgraph VPS["VPS — Docker Compose"]
        API[FastAPI Backend<br/>REST + WebSocket]
        WF[Scan Workflow<br/>LangGraph · adaptive]
        AGENT[Spieon Agent Runtime<br/>Letta + guard layer]
        CHAIN[Chain Service<br/>web3.py / viem patterns]
        DB[(Postgres + pgvector<br/>Memory Layer)]
        LF[Langfuse<br/>self-hosted observability]
    end

    subgraph Sandboxed["e2b Sandboxes"]
        HARNESS[Probe Safety Harness<br/>rate limits · blocklist<br/>stop conditions · attribution]
        ENGINES[Probe Engines<br/>garak · PyRIT · Snyk · native]
    end

    subgraph External
        BASE[Base Sepolia<br/>EAS · Safe · ERC-8004<br/>NameStone L2 resolver]
        ZG[ZeroG / IPFS<br/>encrypted bundles]
        TARGETS[Benchmark targets<br/>DVMCP · DVLA · Cybench<br/>AgentDojo · custom MCP]
    end

    UI <-->|REST + WS narration| API
    API --> WF
    WF <--> AGENT
    AGENT <--> DB
    WF -->|run probe| HARNESS
    HARNESS --> ENGINES
    ENGINES -->|x402 payable call| TARGETS
    AGENT -->|attest, payout| CHAIN
    CHAIN --> BASE
    WF -->|store bundle| ZG
    AGENT -.trace.-> LF
    WF -.trace.-> LF
    CHAIN -.trace.-> LF
```

## 2. Per-scan adaptive workflow

LangGraph nodes for a single scan. Every node is checkpointable, and every node emits narration events — a crashed scan resumes at the next node, not from scratch. The reflect / adapt-decision loop is the genuine "thinking" beat: the planner can mutate parameters, pivot to a new attack class, or continue the planned probe list based on what the previous probe revealed.

```mermaid
stateDiagram-v2
    [*] --> recon
    recon --> plan : introspect target<br/>fetch metadata<br/>recall memory<br/>narrate
    plan --> probe : ordered probe list<br/>+ budget allocation<br/>narrate plan
    probe --> reflect : execute via safety harness<br/>record cost · capture response<br/>narrate result
    reflect --> adapt : narrate reflection
    adapt --> probe : continue planned probe
    adapt --> probe : mutate params
    adapt --> plan : pivot to new attack class
    adapt --> verify : budget exhausted<br/>or convergent
    verify --> attest : dedupe across engines<br/>LLM-judge<br/>severity + OWASP/ATLAS/MAESTRO
    attest --> consolidate : sign EAS<br/>encrypt bundle<br/>emit FindingDisclosed<br/>narrate hash
    consolidate --> [*] : update procedural memory<br/>decay / promote / prune<br/>sync heuristics onchain
```

## 3. Reflection-as-narration

Every meaningful decision emits a structured narration event that fans out to four destinations. This is what makes the demo "watch the agent think" rather than "watch a progress bar."

```mermaid
graph LR
    Node[LangGraph node<br/>recon · plan · probe<br/>reflect · attest · consolidate] --> Narrate[narrate tool]
    Narrate --> Event[Structured event<br/>scan_id · phase · type<br/>content · context]
    Event --> WS[WebSocket stream<br/>→ dashboard live view]
    Event --> Mem[Memory layer<br/>→ scan trace + consolidation]
    Event --> LF[Langfuse trace]
    Event --> Report[Public scan report<br/>spieon.eth/scan/id]
```

## 4. Memory architecture

Three-tier consolidation with deferred pruning. Negative examples (failed probes) survive long enough to become diagnostic when paired with later positives. Procedural memory is public and hash-attested onchain per heuristic version.

```mermaid
graph LR
    Events[Raw scan events<br/>probes · responses · costs<br/>errors · narration] --> L1

    subgraph L1["Layer 1 — Hot Buffer"]
        H[All events<br/>last 50 scans / 7 days<br/>no filtering]
    end

    subgraph L2["Layer 2 — Working Memory"]
        W[usefulness_score<br/>cycles_unused<br/>last_retrieved]
    end

    subgraph L3["Layer 3 — Long-term"]
        T[Promoted items<br/>summarized<br/>indexed by target_type / probe_class]
    end

    subgraph PM["Procedural Memory — public"]
        P[Heuristics with<br/>OWASP/ATLAS mapping<br/>spieon.eth/memory.json]
    end

    L1 -->|age > 7d<br/>reset counters| L2
    L2 -->|usefulness ≥ 3| L3
    L2 -->|cycles_unused ≥ 5| Drop[/dropped/]
    L3 -->|pattern detected| PM
    PM -->|hash attestation per version| EAS[(EAS on Base Sepolia)]

    Recall[memory.recall query] -.-> L3
    Recall -.-> L2
```

## 5. Cost-of-exploit measurement

Every probe is wrapped in a `CostMeter` so the headline metric — *how cheaply could an attacker have found this* — is grounded in real on-chain spend. Aggregate cost includes failed precursor probes that contributed to the finding.

```mermaid
sequenceDiagram
    participant Agent
    participant Meter as CostMeter
    participant Harness as Safety Harness
    participant Probe
    participant X402 as x402 Client
    participant Target
    participant Wallet

    Agent->>Meter: enter(probe_id)
    Meter->>Wallet: read balance (pre)
    Agent->>Harness: execute(probe, params)
    Harness->>Harness: rate-limit · blocklist · stop check
    Harness->>Probe: execute(params)
    Probe->>X402: payable call
    X402->>Target: HTTP + X-PAYMENT<br/>+ User-Agent: Spieon-Pentest/1.0<br/>+ X-Spieon-Scan-Id
    Target-->>X402: response
    X402-->>Probe: result
    Probe-->>Harness: response, signal
    Harness-->>Agent: response, signal
    Meter->>Wallet: read balance (post)
    Meter->>Agent: cost = pre − post
    Note over Agent: attach cost to finding<br/>aggregate across precursor probes
```

## 6. Defense layers — protecting Spieon and targets

Spieon's threat model is two-sided. Hostile target responses can try to manipulate Spieon; Spieon's probes can damage targets. Both defenses are built day 1–5, not bolted on.

```mermaid
graph TB
    subgraph Inbound["Inbound — defending Spieon"]
        TR[Target response] --> LG[LLM Guard scanner]
        LG --> Strip[Strip-and-flag<br/>known injection patterns]
        Strip --> Cap[Length caps]
        Cap --> Sub[Isolated sub-agent context<br/>cannot call tools directly]
        Sub --> Main[Main agent<br/>structured tool calls only]
        Main --> Validate[Tool-call validation<br/>· payouts only to registered modules<br/>· attestations only for recorded probes<br/>· memory writes scoped to scan]
    end

    subgraph Outbound["Outbound — protecting targets"]
        Plan[Planned probe] --> Rate[Rate limit<br/>60/min · 1000/hr per target]
        Rate --> Block[Destructive blocklist<br/>no DoS · no auth-brute >3<br/>no destructive writes]
        Block --> Stop[Auto-stop conditions<br/>· 5 consecutive 5xx<br/>· budget exhausted<br/>· max attempts reached]
        Stop --> Attr[Attribution headers<br/>User-Agent · X-Spieon-Scan-Id]
        Attr --> Exec[Probe executes]
    end

    subgraph Operator["Adversarial-operator mitigations"]
        Cap1[Per-finding bounty caps<br/>crit $5 · high $2 · med $0.50 · low $0.10]
        Cap2[Per-module daily cap $10]
        Review[Outsized payout review<br/>>$20 flagged]
        Hist[Operator history tracking<br/>FP rate → rate limit]
    end
```

## 7. Onchain disclosure timeline

The contract enforces the *timeline* of disclosure, not the *publication* of contents. Attestations carry full taxonomy (OWASP Agentic Top 10, MITRE ATLAS, MAESTRO). Auto-publish is V2.

```mermaid
sequenceDiagram
    participant Agent as Spieon Agent
    participant EAS as EAS (Base Sepolia)
    participant Bundle as ZeroG / IPFS
    participant Op as Operator
    participant Pool as Bounty Pool (Safe)
    participant Author as Module Author

    Agent->>Bundle: upload encrypted detail bundle
    Agent->>EAS: attest(scanId, target, severity,<br/>moduleHash, cost, bundleURI,<br/>owaspId, atlasTechniqueId, maestroId)
    EAS-->>Agent: FindingDisclosed
    Op->>Bundle: fetch + decrypt locally
    Op-->>EAS: OperatorAcknowledged (optional)
    Op-->>EAS: OperatorPatched
    EAS->>Pool: trigger payoutForFinding
    Pool->>Pool: enforce severity cap<br/>+ daily cap + outsized review
    Pool->>Author: USDC, severity-capped
    Pool-->>EAS: BountyPaid
    Note over Op,EAS: after RevealAfter window (default 90d)<br/>operator MAY publish decryption key<br/>(manual, not automatic)
```

## 8. Bounty flow

V1 simplification: one shared pool, severity-capped payouts, daily per-module cap as anti-spam. Module authors registered via NameStone L2 subnames where shipped, raw addresses otherwise.

```mermaid
graph LR
    Op[Operator] -->|deposit USDC<br/>+ encryption pubkey<br/>+ target tag| Pool[Shared Bounty Pool<br/>Safe + custom Module]
    Agent[Spieon Agent] -.signer.-> Pool
    Agent -->|recordUse| Reg[(ModuleRegistry<br/>+ OWASP/ATLAS IDs)]
    Reg -->|moduleHash → author| Lookup[ENS / NameStone L2<br/>resolution]

    Op -->|signs OperatorPatched| Pool
    Pool -->|payoutForFinding<br/>capped by severity<br/>+ deposit balance<br/>+ daily cap<br/>+ outsized review| Balance[Author balance]
    Lookup --> Balance
    Balance -->|withdraw| Wallet[Author wallet<br/>name.spieon.base.eth]
```

## 9. Probe library composition

Four engine families feed a single normalized finding pipeline. Every engine runs inside an e2b sandbox wrapped by the safety harness. Each finding ships with a deployable patch artifact.

```mermaid
graph TB
    subgraph Engines["Engines (in e2b + safety harness)"]
        Snyk[Snyk mcp-scan<br/>static analysis]
        Garak[garak<br/>LLM probes via x402 adapter<br/>15-25 selected per scan]
        PyRIT[PyRIT<br/>Crescendo · TAP orchestrators]
        Native[Spieon native probes<br/>1. x402-replay<br/>2. payment-retry-bypass<br/>3. settlement-skip<br/>4. mcp-tool-description-injection<br/>5. mcp-schema-poisoning<br/>stretch: amount-manipulation, agent-impersonation]
    end

    Snyk --> Norm[Finding normalizer<br/>+ taxonomy mapping]
    Garak --> Norm
    PyRIT --> Norm
    Native --> Norm

    Norm --> Dedup[Cross-engine dedupe<br/>correlate.dedup]
    Dedup --> Judge[LLM-as-judge<br/>verify.judge]
    Judge --> Sev[Severity normalization]
    Sev --> Patch[Patch artifact generator]
    Patch --> NeMo[NeMo Guardrails<br/>Colang rule]
    Patch --> Pol[PolicyLayer rule]
    Patch --> JSON[Generic JSON config]
```

## 10. Identity and public artifacts

How Spieon presents itself to other agents and to humans. Module authors get NameStone L2 subnames (V1 if slack, V2 fallback to address mapping).

```mermaid
graph LR
    subgraph Identity
        Base[spieon.base.eth<br/>Coinbase Basenames] --> Resolver[Custom resolver]
        Resolver --> Wallet[Hot agent wallet<br/>max $50 USDC]
        Resolver --> ProfileJSON[profile.json<br/>ERC-8004 agentURI]
        Resolver --> MemJSON[memory.json<br/>procedural memory]
        Resolver --> Dash[Dashboard URL<br/>spieon.eth]
    end

    subgraph Recovery["Recovery posture"]
        Wallet -->|auto-sweep overflow| Cold[Cold Safe<br/>multi-sig]
        Wallet -.rotation procedure.-> NewKey[Replacement key<br/>ERC-8004 entry updated]
    end

    subgraph "ERC-8004 Registries"
        IDR[Identity Registry] --> RR[Reputation Registry]
        RR -.V2.-> VR[Validation Registry]
    end

    ProfileJSON --> IDR
    Op[Operator post-scan] -->|giveFeedback| RR

    subgraph Subdomains["NameStone L2 subnames"]
        Sub1[alice.spieon.base.eth]
        Sub2[bob.spieon.base.eth]
    end
    Resolver --> Sub1
    Resolver --> Sub2
    Sub1 -.module attribution.-> EAS[(Finding attestations<br/>+ OWASP/ATLAS/MAESTRO)]
    Sub2 -.module attribution.-> EAS
```
