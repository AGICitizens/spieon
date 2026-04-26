# Spieon — Product Requirements Document

## 1. Project overview

**Spieon** is the open-source XBOW for the agent economy. An autonomous AI agent that lives onchain, probes paid AI agents and MCP servers for vulnerabilities, settles every probe in real stablecoin via x402, and posts tamper-proof attestations of its findings on Base Sepolia. Module authors earn bounties when their attack code lands. The agent's learned heuristics are public and grow over time.

The name is Italian _spia_ (spy / warning indicator) + -eon. Both meanings apply: the agent infiltrates paid agents to probe them, and it signals that something is wrong when it finds something.

**Vision:** Be the canonical security primitive for the agent economy. Every paid AI agent should be able to point at a Spieon attestation and say "I've been probed, here's the evidence."

**Hackathon:** ETHGlobal Open Agents, April 26 – May 3 2026. Solo entry. Submission Sunday 11:59 ET; finalist Zoom Monday 12-2:30 ET.

**Success criteria, in priority order:**

1. **Live demo works:** the agent scans a vulnerable target during the Zoom call and finds at least one bug
2. **Onchain artifacts persist:** at least 5 attestations on Base Sepolia from real scans, viewable from the public dashboard
3. **The agent stays running for 60-90 days post-hackathon**, scanning publicly registered targets on its own schedule
4. Win at least one sponsor prize (most plausible: ENS, ZeroG, Keeperhub)
5. Reach finalist top-10

Failing 4-5 is acceptable; failing 1-3 is project failure regardless of prize outcome.

## 2. The single demo loop (4-minute video and Zoom narrative)

The video and Zoom both show the same loop. One beat, repeated with variations.

**Beat 1 — Setup (0:00 – 0:30):** Land on spieon.eth dashboard. Show recent scans, the agent's wallet balance, the leaderboard of attack-module authors, the heuristics file growing. One sentence: _"Spieon is an autonomous AI agent that hunts vulnerabilities in paid AI agents."_

**Beat 2 — Target (0:30 – 0:50):** Operator pastes a paid MCP server URL into the dashboard. Funds a small bounty pool ($5 USDC). Sets max scan budget ($2 USDC). Hits "scan."

**Beat 3 — Probing (0:50 – 2:30):** Live view of agent activity:

- Agent introspects target, discovers MCP tool list and x402 prices
- Agent loads relevant heuristics from procedural memory
- Wraps four engines: Snyk mcp-scan (static MCP analysis), garak (LLM probes), PyRIT (multi-turn attacks), Spieon's native x402 probes
- Each probe execution is a real x402 call. Cost ticks visibly upward
- Two findings emerge with different severities. Cross-engine deduplication merges related findings into one entry
- Each finding shows: severity, cost-of-exploit ($0.34), exploit pattern, deployable patch artifact (Colang rule for NeMo Guardrails or PolicyLayer rule)

**Beat 4 — Attestation (2:30 – 3:10):** Agent signs the findings, posts EAS attestation on Base Sepolia. Attestation hash appears live. Click-through to base-sepolia.easscan.org showing the attestation. Encrypted detail bundle hash referenced in attestation; sensitive details are NOT public, only the operator can decrypt.

**Beat 5 — Bounty (3:10 – 3:30):** Module author (whose probe found the bug) gets paid 0.5 USDC from the operator's bounty pool. Onchain transfer visible. Author's score on the leaderboard ticks up.

**Beat 6 — Memory (3:30 – 4:00):** Agent reflects on the scan, updates its procedural memory: _"MCP servers using transport X are vulnerable to probe Y; success rate now 67% across 12 attempts."_ New heuristic appears in the public memory artifact, signed by the agent's ENS identity.

**Closing (4:00):** _"Spieon is open source. Every scan public. Every probe paid. Module authors earn bounties when their code lands. The agent runs continuously at spieon.eth."_

The demo's center of gravity is **the live cost-coupling and onchain attestation**. Everything else is supporting structure. If anything in the video doesn't make those two beats clearer, it gets cut.

## 3. Architecture

### 3.1 Service topology

```
┌──────────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                          │
│   spieon.eth | dashboard | scan input | leaderboard           │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST + WebSocket
┌────────────────────────▼─────────────────────────────────────┐
│              Backend API (FastAPI, Python)                    │
│   POST /scans  GET /scans/{id}  GET /findings  GET /agent     │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────────┐
│  Scan       │    │  Spieon     │    │  Chain          │
│  Workflow   │    │  Agent      │    │  Service        │
│  (LangGraph)│◄───┤  Runtime    ├───►│  (viem-py)      │
│             │    │  (Letta)    │    │                 │
└──────┬──────┘    └──────┬──────┘    └──────┬──────────┘
       │                  │                  │
┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────────┐
│  Probe      │    │  Memory     │    │  Base Sepolia   │
│  Engines    │    │  Layer      │    │  EAS / Safe /   │
│  (e2b)      │    │  (pgvector) │    │  ERC-8004       │
└─────────────┘    └─────────────┘    └─────────────────┘
```

### 3.2 Components

**Frontend (Next.js + Tailwind + viem):** dashboard, scan input, public scan reports, agent profile page, leaderboard, module registry, memory viewer. Server-rendered for the public report URLs.

**Backend API (FastAPI):** REST + WebSocket. Auth-light — operator session for scan submission, public read for everything else. WebSocket pushes scan progress to the dashboard live.

**Scan Workflow (LangGraph):** per-scan state machine. Recon → plan → probe → verify → attest → reflect. Checkpointed; survives process restarts. One graph instance per scan.

**Spieon Agent Runtime (Letta):** the persistent agent. Lives across all scans. Holds tiered memory (core/recall/archival). Decides which probes to run based on memory and target. Issues procedural-memory updates after each scan.

**Probe Engines:** four wrapped engines + native probe library, each running in e2b sandbox.

1. Snyk mcp-scan (Python subprocess)
2. garak (Python subprocess via REST target)
3. PyRIT (Python library, lifted Crescendo + TAP orchestrator patterns)
4. Spieon's native x402/MCP probes (Python module, 5-7 probes)

**Memory Layer (pgvector + Letta):** Three-tier consolidation. Hot buffer → working memory (deferred review) → long-term store. Procedural memory lives here as a separate artifact, periodically synced to onchain.

**Chain Service (viem-py / web3.py):** signs and broadcasts EAS attestations, registers ERC-8004 entries, manages the Safe-controlled bounty pool, posts module-author payouts. Stateless service called by other components.

### 3.3 Hosting

- Backend, scan workflow, agent runtime, probe sandboxes: single VPS for V1 (Hetzner/Linode), 8 vCPU / 16GB / SSD. Docker Compose.
- Postgres + pgvector: same host, persisted volume.
- e2b sandboxes: hosted e2b service, called via API.
- Frontend: Vercel.
- ENS: spieon.eth resolves via custom resolver to a JSON profile + the dashboard URL.

Estimated V1 hosting cost: $50-100/month. Acceptable for 60-90 day post-hackathon run.

## 4. The agent's tool palette and decision loop

### 4.1 Tools available to the agent

The Spieon agent (Letta) has a fixed tool palette. Each tool call is logged, costed, and may incur real x402 expense.

| Tool                                   | What it does                                            | Cost-bearing?                           |
| -------------------------------------- | ------------------------------------------------------- | --------------------------------------- |
| `target.introspect()`                  | Discover MCP tool list, schemas, x402 endpoints, prices | Yes (x402 calls to discovery endpoints) |
| `target.fetch_metadata()`              | Pull from x402scan registry, prior scan history         | No                                      |
| `memory.recall(query)`                 | Retrieve relevant past experience and heuristics        | No                                      |
| `garak.run(probes)`                    | Subprocess garak with selected probes                   | Yes                                     |
| `pyrit.run(orchestrator, target)`      | Invoke PyRIT orchestrator (Crescendo, TAP)              | Yes                                     |
| `mcp_scan.run(target)`                 | Snyk mcp-scan static analysis                           | No (static)                             |
| `native.run(probe_id, params)`         | Run one of Spieon's 5-7 native probes                   | Yes                                     |
| `verify.judge(attempt, response)`      | LLM-as-judge to confirm finding                         | No                                      |
| `correlate.dedup(findings)`            | Merge related findings across engines                   | No                                      |
| `cost.record(probe_id, usd)`           | Log cost-of-exploit for a finding                       | No                                      |
| `attest.sign(finding)`                 | Sign and post EAS attestation                           | Gas only                                |
| `bounty.payout(module_author, amount)` | Distribute bounty                                       | Gas + USDC                              |
| `memory.update(heuristic)`             | Update procedural memory with learned pattern           | No                                      |
| `target.give_up()`                     | Abort scan if budget exceeded or no progress            | No                                      |

The agent does NOT have arbitrary code execution, arbitrary HTTP fetch, or wallet-transfer-to-anywhere tools. Every tool is bounded.

### 4.2 Per-scan decision loop

LangGraph encodes the workflow:

```
START
  ↓
[recon]  introspect target, fetch metadata, recall relevant memory
  ↓
[plan]   given budget B, target type T, memory M:
         select ordered probe list with budget allocation
  ↓
[probe]  for each planned probe:
           execute in sandbox, record cost, capture response
           if budget exceeded: break to verify
  ↓
[verify] dedupe across engines, run LLM-judge on each candidate
         drop false positives, assign severity
  ↓
[attest] for each verified finding:
           generate patch artifact
           encrypt detail bundle to operator key
           sign attestation, post to EAS
           emit FindingDisclosed event
  ↓
[reflect] summarize what worked vs didn't
          update procedural memory
          decay/promote/prune memory items
  ↓
END
```

Every node can checkpoint. A scan that crashes mid-probe resumes at the next probe, not from scratch.

## 5. Memory architecture

### 5.1 Three-tier consolidation with deferred pruning

**Layer 1 — Hot buffer:**

- All raw scan events: probe attempts, target responses, costs, errors
- No filtering
- Retention: last 50 scans or 7 days, whichever larger
- Storage: pgvector with cheap embeddings, indexed by scan_id and timestamp

**Layer 2 — Working memory (the "temp dump"):**

- Items moved here from Layer 1 by periodic consolidation pass
- Each item has: usefulness_score (init 0), cycles_unused (init 0), last_retrieved timestamp
- Items here have NOT yet been judged. They wait.
- Storage: same pgvector instance, separate table

**Layer 3 — Long-term store:**

- Items promoted from Layer 2 with usefulness_score > threshold
- Periodically summarized to compress related entries
- Storage: pgvector + structured metadata (target_type, probe_class, outcome)
- This is what feeds into procedural memory

**Procedural memory (separate, public):**

- Heuristics learned from Layer 3
- Format: `{ rule, evidence_scan_ids, success_rate, sample_size, last_updated }`
- Synced to onchain via EAS attestation (one attestation per heuristic version)
- Public file at `spieon.eth/memory.json`, hash-attested
- Other agents can read this; researchers can audit

### 5.2 Consolidation pass

Runs every 10 scans, or nightly, whichever fires first.

```
For each item in Layer 2:
  if item was retrieved during recent scans:
    usefulness_score += retrieval_count
    cycles_unused = 0
  else:
    cycles_unused += 1

  if cycles_unused >= PRUNE_THRESHOLD (default 5):
    drop item
  elif usefulness_score >= PROMOTE_THRESHOLD (default 3):
    promote to Layer 3
    if procedural pattern detected (same probe class succeeding on similar targets):
      generate or update heuristic in procedural memory
      sync new heuristic version onchain

For each item in Layer 1 older than 7 days:
  move to Layer 2 with reset counters
```

The agent itself runs the consolidation as a periodic Letta task. The agent decides via reflection what counts as "similar targets" and "successful pattern."

### 5.3 Why this matters for security work specifically

Negative examples (probes that failed) carry diagnostic information. Pure recency-based pruning would lose them. Deferred pruning preserves them long enough to become diagnostic when paired with later positive examples.

## 6. Probe library

### 6.1 Wrapped engines

V1 ships with three wrapped external engines, called via subprocess or library import inside e2b sandbox.

**Snyk mcp-scan:** static analysis of MCP server source/configs. Detects tool poisoning, shadowing, rug-pull patterns, suspicious tool descriptions. Does not require live target — works from URL or source. Output normalized to Spieon's finding schema.

**garak:** LLM probes via REST target adapter. Spieon ships a custom garak generator that speaks x402 — pays for each probe, captures response. Probe selection: subset of garak's catalog matched to target type (15-25 probes per scan, not all 150).

**PyRIT:** lift Crescendo and TAP orchestrators. Each runs as a Python coroutine. Targets the agent layer of paid agents (multi-turn attacks). Costs per turn tracked.

V2 extensions (post-hackathon): promptfoo Hydra strategy, Cisco mcp-scanner, agentic_security.

### 6.2 Native x402/MCP probes

Five probes shipped in V1. Each probe is a Python module conforming to a `Probe` interface.

1. **x402-replay-attack:** capture a successful x402 payment payload, attempt to replay it after settlement. Tests whether server validates nonce/timestamp/X-PAYMENT header uniqueness.

2. **payment-retry-bypass:** send 402 response request, retry without payment, retry with malformed payment, retry with expired payment. Tests whether server's retry logic enforces payment in all paths.

3. **settlement-skip:** send valid payment payload but disconnect before settlement confirmation. Test whether server delivers resource without confirming settlement.

4. **mcp-tool-description-injection:** for MCP targets, send tool descriptions containing prompt injection payloads designed to make the calling agent perform unauthorized actions. Tests whether the target validates tool descriptions before passing to its LLM.

5. **mcp-schema-poisoning:** craft tool schemas with unicode confusables, hidden instructions in description fields, tool name shadowing. Tests whether the target's MCP client sanitizes schemas.

V1 stretch (if time): two more probes — **payment-amount-manipulation** (race condition between price quote and settlement) and **agent-impersonation** (forge ERC-8004 identity in payment context).

Each probe ships with: code, expected attack signature, severity rating, suggested patch artifact, OWASP/MAESTRO mapping, author identity (Spieon's ENS for V1; community-contributed for V2).

### 6.3 Patch artifact generation

Every finding ships with a deployable defense. The agent generates this as part of the verify step. Three target formats:

- **NeMo Guardrails Colang rule:** for prompt-injection and tool-poisoning findings
- **PolicyLayer rule:** for x402-specific findings (payment retry, replay, settlement)
- **Generic JSON config:** describing the finding pattern in detector-agnostic form

Operators copy-paste the patch into their stack. This is what makes Spieon useful, not just informative.

## 7. Cost-of-exploit measurement

Every probe execution wraps the underlying call in a `CostMeter` context manager that:

1. Records pre-probe wallet balance
2. Allows probe to make x402 calls
3. Records post-probe wallet balance
4. Logs probe_id → USDC_spent
5. If a finding emerges, attaches the cost number to the finding

The aggregate cost-of-exploit for a finding = sum of probe costs across all probes that contributed to its discovery (including failed precursor attempts that informed the successful probe).

Reported in the attestation: `(severity, cost_to_discover, probe_class, sample_size)`.

This is the headline metric Spieon adds to the field. Severity tells you how bad a bug is. Cost tells you how cheap it is for an attacker to find it.

## 8. Onchain components

### 8.1 Network

Base Sepolia. Free testnet, fast, EAS deployed, easy faucet, x402 reference deployments live.

### 8.2 Contracts

**ModuleRegistry** (custom):

```solidity
struct Module {
    bytes32 moduleHash;       // hash of probe code
    address author;            // ENS-resolved address
    string metadataURI;        // IPFS or ZeroG
    uint8 severityCap;         // max severity this module can claim
    uint256 timesUsed;
    uint256 successCount;
}
mapping(bytes32 => Module) public modules;
function register(bytes32 hash, address author, string memory uri, uint8 cap) external;
function recordUse(bytes32 hash, bool success) external onlyAgent;
```

**FindingsLog** (uses EAS, not custom contract):

- EAS schema: `bytes32 scanId, address target, uint8 severity, bytes32 moduleHash, uint256 costInUSDC, string encryptedBundleURI, uint64 disclosedAt, uint64 acknowledgedAt, uint64 patchedAt`
- Each finding = one EAS attestation
- Attester = Spieon agent's wallet (signed by its private key, identity rooted in ERC-8004)
- Public attestation contains metadata; sensitive details encrypted in `encryptedBundleURI`

**BountyPool** (Safe + custom Module):

- Operator deposits USDC into a per-target Safe
- Spieon agent is a signer on the Safe
- Custom Safe Module: `payoutForFinding(scanId, moduleHash, amount)` — payable only by the Spieon agent, only for findings whose `scanId` matches a registered scan against this target, only up to per-finding cap
- Researchers withdraw earned bounties via `withdraw(moduleHash)` aggregated across all targets

V1 simplification: one shared bounty pool, not per-target. Per-target Safes are V2.

### 8.3 ERC-8004 registration

Spieon agent registers itself in the Identity Registry on first deploy:

- `agentURI` JSON: `{ name: "spieon", description, capabilities: ["mcp-scan", "x402-probe", ...], website: "spieon.eth", basename: "spieon.base.eth" }`
- The Reputation Registry receives `giveFeedback` from operators after each scan (operator signs that the scan was useful)
- The Validation Registry is V2 (TEE-backed validation hooks)

### 8.4 ENS / Basenames identity

- Primary: `spieon.base.eth` via Coinbase Basenames
- Profile and resolver point to: agent wallet address, agentURI, public dashboard, public memory.json hash
- Module authors register `<their-name>.spieon.base.eth` subdomains via a custom resolver
- Module attribution in attestations uses ENS names, not raw addresses

### 8.5 Disclosure model — audit trail, not auto-publish

Two-tier:

**Public:** EAS attestation with metadata only. Severity, cost, module used, target, timestamps. No exploit details.

**Private:** the actual exploit details, PoC, reproduction steps. Encrypted to the operator's public key (provided when they fund the bounty pool). Stored on ZeroG (sponsor fit) or IPFS. Hash referenced in the public attestation.

**Disclosure events emitted (via EAS) but no auto-publication:**

- `FindingDisclosed` (immediate, when scan completes)
- `OperatorAcknowledged` (operator signs receipt, optional)
- `OperatorPatched` (operator signs that fix is deployed, triggers bounty payout)
- `RevealAfter` field in attestation: configurable by operator, default 90 days, after which operator may choose to make the encrypted bundle's key publicly fetchable (manual step, not automatic)

The contract enforces the _timeline of disclosure_, not the _publication of contents_. Auto-publication is V2 with significant additional design work.

## 9. Bounty mechanics

### 9.1 Pool model

- One shared pool in V1
- Operators deposit USDC into the pool, tagged to a specific target URL + scan ID range
- Tag determines which findings can claim from this deposit

### 9.2 Payout rule

When a finding's `OperatorPatched` event fires:

1. Look up the finding's `moduleHash`
2. Look up `Module.author`
3. Pay author from operator's deposit, bounded by:
   - severity-based cap (critical: $5, high: $2, medium: $0.50, low: $0.10 in V1 — small for testnet)
   - operator's deposit balance
   - per-module daily cap (anti-spam)
4. Emit `BountyPaid(scanId, moduleHash, author, amount)`
5. Author can withdraw aggregated balance any time

### 9.3 Module submission

V1: only Spieon team submits modules. Module submission UX is V2.

V2 (within 60-90 days post-hackathon): researchers submit modules via PR to a public repo. Spieon team reviews, registers approved modules onchain. Authors get ENS subdomain `<name>.spieon.base.eth` and start earning when their modules fire.

## 10. Web app

### 10.1 Pages

- `/` — landing + quick scan input + recent activity feed
- `/scan` — full scan submission form (target URL, budget, bounty deposit, encryption pubkey)
- `/scan/{id}` — live or historical scan view, all findings, costs, attestation links
- `/agent` — Spieon's profile: stats, total scans, total findings, treasury balance, ERC-8004 reputation
- `/leaderboard` — module authors ranked by findings landed, bounties earned
- `/modules` — registry of attack modules with metadata
- `/memory` — viewable procedural memory file, growing over time
- `/findings` — global feed of all findings (metadata only)
- `/about` — what spieon is, how it works, FAQ, security disclosure

### 10.2 Key flows

**Operator flow:**

1. Land on `/scan`
2. Enter target URL, scan budget, bounty amount, encryption public key
3. Connect wallet, sign deposit + scan request
4. Get redirected to `/scan/{id}` with live progress
5. After scan completes: download encrypted bundle, decrypt locally, view full findings
6. Optionally: sign `OperatorAcknowledged`, deploy patches, sign `OperatorPatched` to release bounties

**Public viewer flow:**

1. Land on `/` or any scan URL
2. See public metadata: severity, cost, attestation hash, no exploit details
3. Click through to base-sepolia.easscan.org for raw attestation
4. Click through to ENS profile for module author

### 10.3 Public artifacts

- `spieon.eth/memory.json` — procedural memory, hash-attested
- `spieon.eth/profile.json` — ERC-8004 agentURI
- Every `/scan/{id}` is a permanent public URL
- All attestations on Base Sepolia, queryable by anyone

## 11. Vulnerable benchmark targets

Three targets shipped for the demo. All run on a separate VPS to avoid any liability mixing with Spieon infrastructure.

1. **DVMCP (Damn Vulnerable MCP Server)** — pulled from harishsg993010/damn-vulnerable-MCP-server. Ships with 10 graded vulnerability classes. We pre-scan it once and ensure the agent finds at least 3 of the 10 in V1.

2. **Spieon's own vulnerable target** — a paid MCP server (FastMCP-based) deliberately containing 3 of our native probe classes' vulnerabilities. We control this fully, can guarantee the demo finds something.

3. **An x402-only target** — a non-MCP paid HTTP endpoint with x402 retry-bypass and replay vulnerabilities. Tests Spieon against the simpler shape.

For the live Zoom demo: target #2 is the safe bet. Target #1 is the credibility play. Target #3 is the variety play.

## 12. 10-day plan with cut rules

10 days. Solo. Days are 12-14 effective hours of work each, accepting some slippage.

### Day 1 (today, April 26) — Setup and skeleton

- [ ] Repo initialized, Python project, Docker Compose, env vars
- [ ] Postgres + pgvector running locally
- [ ] FastAPI skeleton with `/scans` POST and GET
- [ ] Letta installed, basic agent instantiated, can hold conversation
- [ ] LangGraph installed, hello-world graph compiles
- [ ] e2b SDK working, can spin up sandbox
- [ ] Base Sepolia wallet created, faucet funded, viem-py client connecting
- [ ] EAS schema for findings registered on Base Sepolia
- [ ] Next.js scaffold with placeholder pages
- [ ] Decision: agent's wallet address generated, ENS lookup considered (Basenames registration is Day 2)

**Cut rule day 1:** if any of (Letta, LangGraph, e2b, EAS schema) takes more than 3 hours, swap for simpler. Letta could be replaced with raw LangGraph + pgvector if Letta integration is rough.

### Day 2 — Probe wrappers and one end-to-end scan

- [ ] garak wrapper: subprocess call, REST target adapter, output parser
- [ ] PyRIT wrapper: import, Crescendo orchestrator, output parser
- [ ] Snyk mcp-scan wrapper: subprocess, output parser
- [ ] One native probe written and tested: `x402-replay-attack`
- [ ] LangGraph scan workflow runs end-to-end on a single test target (no real x402 yet, mock client)
- [ ] First finding written to Postgres
- [ ] Basenames registered: `spieon.base.eth`

**Cut rule day 2:** if all three wrappers don't fit in the day, ship two (PyRIT + native probes minimum). Snyk mcp-scan is V2 if necessary.

### Day 3 — Real x402 + cost coupling + first attestation

- [ ] x402 client integrated, real testnet payments going through Coinbase facilitator
- [ ] CostMeter wraps every probe, records USDC spent
- [ ] EAS attestation pipeline: agent signs, posts, returns hash
- [ ] First end-to-end scan against DVMCP with real x402 payments and an attestation posted
- [ ] Encryption: detail bundles encrypted to operator pubkey, IPFS upload, hash in attestation

**🚦 Day 3 checkpoint:**

- A scan runs end-to-end, real money spent, attestation on chain, encrypted bundle on IPFS. **If this isn't true on day 3, scope must cut.** Cut candidates: drop ZeroG (use IPFS only), drop PyRIT (garak + native only), drop one of the three benchmark targets.

### Day 4 — Memory, reflection, procedural memory v1

- [ ] Three-tier memory schema in Postgres
- [ ] Hot buffer / working memory / long-term store separation
- [ ] Consolidation pass implemented as Letta tool
- [ ] First procedural memory entry written after a real scan
- [ ] Procedural memory file synced to onchain (via EAS attestation containing the file hash)
- [ ] Cross-scan retrieval working: agent recalls relevant memory before a new scan

### Day 5 — Native probes 2-5 + correlation/dedup

- [ ] Probe `payment-retry-bypass` written and tested
- [ ] Probe `settlement-skip` written and tested
- [ ] Probe `mcp-tool-description-injection` written and tested
- [ ] Probe `mcp-schema-poisoning` written and tested
- [ ] Cross-engine deduplication: if garak and a native probe report similar findings, merge into one
- [ ] Severity normalization across engines

### Day 6 — Bounty contracts + ERC-8004 + patch artifacts

- [ ] BountyPool contract deployed (V1 simplified: shared pool, not per-target)
- [ ] Safe deployed, agent set as signer
- [ ] Module registry contract deployed, V1 modules registered
- [ ] ERC-8004 registration completed; agent has Identity Registry entry on Base Sepolia
- [ ] Patch artifact generation: every finding now ships with Colang rule or PolicyLayer rule
- [ ] First successful bounty payout in test (operator confirms patch → module author paid)

**🚦 Day 6 checkpoint:**

- Backend complete, contracts deployed, end-to-end loop including bounty payouts works against the test target. **If this isn't true, all V2 features get cut and remaining days go to frontend + demo.**

### Day 7 — Frontend dashboard + scan submission

- [ ] Landing page with recent activity
- [ ] Scan submission form
- [ ] Live scan view with WebSocket updates
- [ ] Public scan report pages
- [ ] Agent profile page
- [ ] Leaderboard (placeholder data acceptable)

### Day 8 — Frontend polish + memory page + module registry page

- [ ] Memory viewer page
- [ ] Module registry page
- [ ] FAQ / about page with how-it-works
- [ ] Mobile responsive
- [ ] ENS resolution: spieon.eth resolves to dashboard
- [ ] Embed all attestation hashes link to base-sepolia.easscan.org
- [ ] Dry-run the demo end-to-end

**🚦 Day 8 checkpoint:**

- The demo can be performed end-to-end without manual intervention or visible errors. **If anything is broken, day 9 fixes it; day 10 is video.**

### Day 9 — Demo dry-run + benchmark targets + bug-fix

- [ ] Three benchmark targets deployed and verified scannable
- [ ] Run the full demo at least 3 times start-to-finish, recording timing
- [ ] Fix anything that breaks, anything that's slow, anything that's confusing
- [ ] Write submission text, devpost description
- [ ] Tweet thread / Farcaster cast drafted (post on day 10)

### Day 10 — Video + submission + buffer

- [ ] Record 4-minute demo video
- [ ] Edit, voiceover, submit
- [ ] Post submission text on devpost
- [ ] Submit to ETHGlobal Showcase by 11:59 ET
- [ ] Buffer time for last-minute fixes

### Cuts already on the table

V1 ships without:

- DSPy, Graphiti, Hats roles, ZK proofs
- Cisco mcp-scanner, agentic_security, promptfoo Hydra
- Auto-publish disclosure, per-target Safe pools, multi-pool bounty
- Module submission UX (V2)
- Validation Registry / TEE hooks
- Continuous scheduled scanning (V2 with Keeperhub)
- Multi-chain support (Base Sepolia only)
- TS or Mastra alternative (Python only)

If day 6 checkpoint fails, additional cuts:

- Ship with 3 native probes instead of 5
- One benchmark target instead of three
- Frontend simplified to single-page dashboard
- No memory page / module page / about page

## 13. Risks and mitigations

| Risk                                       | Probability | Impact   | Mitigation                                                                                                                                                                            |
| ------------------------------------------ | ----------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Letta integration too fiddly for Day 1     | Medium      | High     | Fallback: LangGraph + pgvector + custom memory layer. -1 day                                                                                                                          |
| x402 testnet flakiness during demo         | Medium      | High     | Run x402 facilitator locally as fallback; pre-record demo backup                                                                                                                      |
| EAS attestation cost / rate limit          | Low         | Medium   | Batch attestations if rate limited; testnet has been generous                                                                                                                         |
| e2b sandbox failures during live scan      | Medium      | High     | Local Docker sandbox as fallback; pre-warm sandboxes                                                                                                                                  |
| BugBuzzer overlap concern resurfaces       | Low         | Medium   | Document architectural distinction in repo: BugBuzzer is static website scanning, Spieon is LLM-driven probing of paid agents. Different surfaces, different methods, no code overlap |
| Submission flagged for "from scratch" rule | Low         | High     | Repo commit history is auditable; all code authored during hackathon window. Wrapping garak/PyRIT/Snyk is normal use of dependencies, not carryover                                   |
| Demo finds zero bugs in front of judges    | Low         | Critical | Three benchmark targets, at least one (#2) under our full control with seeded vulnerabilities                                                                                         |
| Burnout / fatigue compromises day 7-9      | Medium      | High     | Day 5 evening checkpoint: am I OK? If not, cut frontend to minimum. Sleep wins over feature parity                                                                                    |
| Sponsor fit insufficient for any prize     | Medium      | Medium   | Cover ENS (Basenames + subdomains) and ZeroG (encrypted bundles) explicitly. If Keeperhub is included as scheduled scans, mention it in submission as forward path                    |

## 14. Post-hackathon (60-90 day commitment)

**Days 11-30:**

- Spieon agent runs continuously, scanning publicly registered targets via x402scan
- Procedural memory grows. Public dashboard updates daily.
- Module submission opens for one or two trusted contributors first
- Begin writing technical blog posts on niravjoshi.dev about findings
- Post agent activity to Farcaster (now that we're past the hackathon)

**Days 30-60:**

- Module submission opens broadly via PR + review
- Validation Registry integration (TEE hooks)
- Per-target bounty pools
- Migrate from testnet to Base mainnet for real bounties
- Reach out to MerchantGuard, zauth, PaySentry — see if any partnership shape fits

**Days 60-90:**

- Decide: continue solo, recruit co-maintainer, or open as community project under a foundation
- Submit talk proposals to AI security conferences referencing the public dataset
- If usage justifies it, consider funded version (consulting / paid scans / certification badges)

## 15. Sponsor fit

**ENS ($5K):** Basenames identity, subdomains for module authors, profile JSON resolved via ENS. _Strongest fit._

**ZeroG ($5K):** encrypted finding bundles stored on ZeroG. _Real use case, not decoration._

**Keeperhub ($5K):** scheduled re-scanning of registered targets. _V2 explicitly, mentioned as forward path. May qualify if even basic integration done by day 8._

**Uniswap Foundation ($15K):** less direct fit. Could rationalize via "agent settles bounties using stablecoins routed through Uniswap." Honest assessment: weakest fit; don't optimize for this prize.

**Jensen ($5K):** unclear without more sponsor info. Worth checking sponsor docs day 1.

**Finalist track ($1K + flight + dev credits):** primary target if no sponsor prize lands.

## 16. Open decisions before day 1

1. Operator pubkey for testing (own EVM address is fine for dev)
2. ENS choice: `spieon.base.eth`, or a subdomain like `agent.spieon.base.eth`
3. Primary sponsor prize target (default: ENS)
4. VPS host: Hetzner / Linode / other
5. x402 facilitator: Coinbase vs self-hosted
