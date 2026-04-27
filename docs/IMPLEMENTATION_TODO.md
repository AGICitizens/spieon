# Spieon — Implementation TODO

Granular checklist derived from [PRD §12](PRD.md) and [ARCHITECTURE.md](ARCHITECTURE.md). Today is **2026-04-26 (Day 1)**. Submission **2026-05-03 23:59 ET**.

Conventions: `[ ]` open, `[x]` done, `[~]` partial/blocked. Add a one-line note inline when blocked. Cut rules from the PRD apply at each daily checkpoint — don't push past a checkpoint just to complete a checklist.

---

## Pre-day-1 — Decisions locked (PRD §16)

- [x] Operator test wallet: own EVM address. **Encryption is decoupled from the wallet** — operator generates a separate X25519 recipient key in the browser at scan submission (see encryption decision below).
- [x] **ENS deferred** — Basenames `spieon.base.eth` not registered V1. $5K sponsor prize accepted as a knowing cut. Module attribution falls back to raw addresses.
- [x] VPS: **Hostinger** (KVM 4 / KVM 8 per PRD §3.3 sizing). Confirm Docker is allowed on chosen plan.
- [x] x402 facilitator: **Coinbase reference facilitator** (`https://x402.org/facilitator`). Supports Base Sepolia + USDC.
- [x] AI accelerator: **Claude Code**.
- [x] **AgentDojo: dropped from V1.** AGPL-3.0 makes "read source + port" risky; clean-room reimplementation eats Day 8 budget. DVMCP + DVLA + Cybench subset + custom = four benchmark numbers, sufficient.

## Architecture decisions locked (post-walkthrough)

- [x] **Drop Letta.** Use **LangGraph + LangMem + pgvector**. [DOMAIN_LANDSCAPE §16](DOMAIN_LANDSCAPE.md) recommends this combination explicitly; LangMem owns "agent rewrites its own heuristics" which is what PRD §5 procedural memory describes. No Letta runtime daemon — the agent IS the LangGraph workflow + LangMem state + system prompt. Removes a day-1 dependency-risk bucket.
- [x] **CostMeter consumes x402 receipts, not balance diffs.** Parse `X-PAYMENT-RESPONSE` header → tx hash → `eth_getTransactionReceipt` for actual USDC delta. Synchronous, deterministic, immune to async settlement timing. CostMeter takes a `PaymentReceiptParser` interface; V1 ships `X402ReceiptParser`, MPP/MCPay etc. are V2 adapters.
- [x] **Encryption: age with X25519 recipient.** Operator generates X25519 keypair in browser (js-age / libsodium WASM); private key never leaves browser, pubkey sent to backend. Agent encrypts each finding bundle via `age -e -r <pubkey>`, uploads ciphertext to ZeroG, zeroizes cleartext. **No decryption key ever exists in agent state.** EAS attestation commits to `sha256(ciphertext)` for auditability. Forward-secret against agent DB/RAM compromise: past scans cannot be retroactively decrypted.
- [x] **Narration: inline LLM with structured JSON output.** Anthropic tool_use with strict Pydantic schema: `narrate_decision(phase, success_signal, target_observations, decision, next_action, content)`. Malformed-JSON fallback → deterministic template from structured node state; log to Langfuse, never stall workflow.
- [x] **ORM: SQLModel** (Pydantic + SQLAlchemy 2.0, async via `asyncpg`, Alembic for migrations, pgvector via `Field(sa_column=Column(Vector(...)))`. One class = DB row + API schema, eliminating the model/schema duplication that plain SQLAlchemy forces.

---

## Day 1 — Setup, skeleton, Langfuse from start (2026-04-26)

### Repo + tooling

- [ ] Add `.env.example` at repo root with: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `LETTA_API_KEY`, `E2B_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, `BASE_SEPOLIA_RPC_URL`, `AGENT_PRIVATE_KEY`, `EAS_SCHEMA_UID`, `OPERATOR_TEST_PUBKEY`, `DATABASE_URL`, `X402_FACILITATOR_URL`
- [ ] Add `.gitignore` entries for `.env`, `.venv`, `node_modules`, `.next`, `langfuse-data/`, `pgdata/`
- [ ] Decide package manager — `uv` for Python (ships with `pyproject.toml`), `pnpm` or `npm` for frontend; document in root `README.md`
- [ ] Add Makefile or `scripts/` with `make up`, `make down`, `make backend`, `make frontend`, `make test`

### Docker Compose (root `docker-compose.yml`)

- [ ] Service: `postgres` with `pgvector/pgvector:pg16` image, named volume `pgdata`, exposed on `5432`
- [ ] Service: `langfuse` (self-hosted) + its `clickhouse` + `minio` deps per Langfuse self-host docs, exposed on `3001` (avoid clash with Next.js 3000)
- [ ] Service: `backend` (build from `./backend`, mounts `./backend` for hot reload), depends on `postgres`, `langfuse`
- [ ] Healthchecks on `postgres` and `langfuse` so `backend` waits for them
- [ ] `make up` confirmed to bring everything up green

### Backend (`backend/`)

- [ ] Add deps to `pyproject.toml`: `sqlmodel`, `asyncpg`, `alembic`, `pgvector`, `langgraph`, `langgraph-checkpoint-postgres`, `langmem`, `langchain-anthropic`, `langchain-openai`, `e2b-code-interpreter`, `web3`, `eth-account`, `httpx`, `websockets`, `langfuse`, `structlog`, `python-dotenv`, `pyrage` (age encryption)
- [ ] `app/config.py` — `pydantic-settings` `Settings` reading the `.env` keys above
- [ ] `app/db.py` — async engine via `sqlmodel.ext.asyncio`, session factory, `get_session` FastAPI dependency
- [ ] `app/models/` — SQLModel tables: `Scan`, `Finding`, `MemoryEvent` (Layer 1), `MemoryItem` (Layer 2/3), `Heuristic`, `Module`, `NarrationEvent`, `ProbeRun`. Each `table=True` model also serves as API response schema where appropriate; separate `*Create` / `*Read` SQLModels for input/output where shapes differ.
- [ ] `app/models/finding.py` includes taxonomy fields: `owasp_id`, `atlas_technique_id`, `maestro_id`, `cost_usdc`, `module_hash`, `severity`, `encrypted_bundle_uri`, `ciphertext_sha256`, `eas_attestation_uid`
- [ ] Alembic initialized against SQLModel metadata; first migration creates tables + enables `vector` extension; pgvector columns declared via `Field(sa_column=Column(Vector(1536)))`
- [ ] `app/api/scans.py` — `POST /scans`, `GET /scans/{id}` (stub returning DB rows)
- [ ] `app/api/health.py` — extends `/health` to also report DB connectivity
- [ ] Wire routers into `app/main.py`
- [ ] `app/observability/langfuse.py` — Langfuse client init, decorator/helper for tracing graph nodes and tool calls
- [ ] Smoke test: `uv run pytest` with one test hitting `/health`

### Agent + workflow scaffolding

- [ ] `app/agent/llm.py` — Anthropic client factory with structured-output (`tool_use` + Pydantic schemas)
- [ ] `app/agent/prompts.py` — system prompt with PRD §8.1 guard text
- [ ] `app/agent/tools/narrate.py` — `narrate_decision(phase, success_signal, target_observations, decision, next_action, content)` Pydantic schema; writes to `narration_events`, fans out to WebSocket pubsub, Langfuse trace, and memory event log; deterministic template fallback if JSON malformed
- [ ] `app/memory/langmem.py` — LangMem store wired to pgvector; procedural-memory namespace per agent identity
- [ ] `app/workflow/graph.py` — LangGraph `StateGraph` with placeholder nodes `recon → plan → probe → reflect → adapt → verify → attest → consolidate`; Postgres checkpointer enabled
- [ ] `app/workflow/state.py` — typed `ScanState` (scan_id, target_url, budget_usdc, spent_usdc, planned_probes, findings, memory_refs, adapt_iterations)
- [ ] Hello-world graph compiles and runs end-to-end against a fake target, persists checkpoints, recovers on restart

### e2b

- [ ] `app/sandbox/e2b_client.py` — wrapper that opens a sandbox, runs a command, returns stdout/stderr/exit
- [ ] Smoke test: run `python -c 'print(1+1)'` in e2b sandbox from a pytest

### Chain (Base Sepolia)

- [ ] Generate agent wallet, store private key in `.env` (NEVER commit), record address
- [ ] Fund from Base Sepolia faucet; confirm balance via `web3.py`
- [ ] `app/chain/client.py` — `web3.py` client, signer, helpers `get_balance()`, `current_block()`
- [ ] EAS schema registered on Base Sepolia with full taxonomy fields per PRD §9.2; record schema UID in `.env` as `EAS_SCHEMA_UID`
- [ ] `app/chain/eas.py` — `attest(finding) -> attestation_uid` stub (real implementation Day 3)

### Frontend (`frontend/`)

- [ ] Install deps: `tailwindcss`, `@tailwindcss/postcss`, `viem`, `wagmi`, `@tanstack/react-query`, `lucide-react`, `clsx`, `class-variance-authority`
- [ ] Tailwind configured (`tailwind.config.ts`, `postcss.config.mjs`, globals.css with `@tailwind` directives)
- [ ] App-router placeholders for: `/`, `/scan`, `/scan/[id]`, `/agent`, `/leaderboard`, `/modules`, `/memory`, `/findings`, `/benchmarks`, `/about`
- [ ] `lib/api.ts` — typed fetch wrapper hitting `NEXT_PUBLIC_API_URL`
- [ ] `pnpm dev` shows landing page hitting `/health` from backend

### ENS / Basenames

- [~] **Deferred per pre-day-1 decision.** Skipped V1. If reversed: 5-min Basenames claim only; no NameStone, no custom resolver.

### Day-1 cut rule check

- [ ] If any of (LangGraph + LangMem, e2b, EAS schema, Langfuse) took **>3h**, swap for simpler. Note the swap in this file inline. (Letta-or-not risk now eliminated.)

---

## Day 2 — Probe wrappers + first native probe + Spieon prompt-injection defense (2026-04-27)

### Probe wrappers (`app/probes/wrappers/`)

- [ ] `garak.py` — subprocess garak with custom REST target adapter that speaks x402; output parser → normalized finding
- [ ] `pyrit.py` — import PyRIT, run Crescendo orchestrator against test target, parse output
- [ ] `mcp_scan.py` — subprocess Snyk mcp-scan against MCP server source; parse JSON output
- [ ] Common normalizer `app/probes/normalize.py` — maps engine output → `Finding` with taxonomy fields

### First native probe (`app/probes/native/`)

- [ ] `x402_replay.py` — capture x402 payment from one call, replay nonce/timestamp, classify response as vulnerable/not
- [ ] Probe registry: `app/probes/registry.py` listing all probes with `id`, `class`, `cost_estimate`, `severity_cap`, `owasp_id`, `atlas_technique_id`

### Spieon prompt-injection defense (PRD §8.1) — built day 2, hardened day 6

- [ ] `app/defense/llm_guard.py` — install `llm-guard`, wrap target responses through prompt-injection scanner before they reach the agent
- [ ] `app/defense/sanitize.py` — strip-and-flag known injection patterns (instruction overrides, role plays, system-prompt extraction); enforce length caps
- [ ] `app/agent/prompts.py` — system prompt with the explicit guard text from PRD §8.1
- [ ] `app/defense/sub_agent.py` — isolated sub-agent context for analysing target responses; returns analysis only, not raw text, to main agent
- [ ] `app/defense/tool_validation.py` — pre-execution validators: payouts only to registered modules, attestations only for recorded probes, memory writes scoped to current scan
- [ ] Confirm structured tool calls only — no free-text target output is ever interpolated into the agent's instruction stream

### LangGraph workflow E2E

- [ ] Scan workflow runs end-to-end on a mock x402 target; produces one `Finding` row with taxonomy fields populated

### Day-2 cut rule check

- [ ] If all three engine wrappers don't fit, ship two minimum (PyRIT + native probes); slip Snyk mcp-scan to day 3.

---

## Day 3 — Real x402 + cost coupling + first attestation (2026-04-28)

### x402

- [ ] `app/x402/client.py` — real x402 payment client via Coinbase facilitator (testnet)
- [ ] Garak REST adapter switched from mock → real x402 client
- [ ] Native probe `x402-replay-attack` wired through real client

### Cost coupling

- [ ] `app/cost/receipts.py` — `PaymentReceiptParser` interface; `X402ReceiptParser` reads `X-PAYMENT-RESPONSE` header, extracts tx hash, fetches receipt via `eth_getTransactionReceipt`, parses USDC `Transfer` log → exact amount
- [ ] `app/cost/meter.py` — `CostMeter` async context manager wrapping a probe; consumes receipts emitted by the probe's HTTP client; aggregates across probes per finding (PRD §7)
- [ ] Every probe call wrapped in `CostMeter`
- [ ] `cost_to_discover` populated on each `Finding`

### Attestation pipeline

- [ ] `app/chain/eas.py` — real `attest()` posts EAS attestation with `(scanId, target, severity, moduleHash, costInUSDC, encryptedBundleURI, owaspId, atlasTechniqueId, maestroId)`
- [ ] `app/chain/encrypt.py` — `age` encryption to operator's X25519 pubkey via `pyrage`; zeroize cleartext on bundle close; persist only `{bundle_uri, ciphertext_sha256, recipient_pubkey}`; upload to ZeroG → bundle URI; `sha256(ciphertext)` written to EAS attestation
- [ ] `frontend/lib/encryption.ts` — browser-side X25519 keypair generation (libsodium WASM or `js-age`); pubkey to backend, private key shown for download/save with warning; never sent to server
- [ ] First end-to-end real scan against DVMCP: x402 payments occur → finding emitted → bundle on ZeroG → attestation hash visible on base-sepolia.easscan.org

### 🚦 Day 3 checkpoint (gate)

- [ ] Scan runs end-to-end, real money spent, attestation on chain with taxonomy fields, encrypted bundle on ZeroG.
- If failing: candidate cuts — drop ZeroG (use IPFS), drop PyRIT, drop one benchmark target. Note cut inline.

---

## Day 4 — Memory, reflection, narration stream, procedural memory v1 (2026-04-29)

### Three-tier memory (PRD §5)

- [ ] Tables / pgvector indexes for: Layer 1 hot buffer (`memory_events`), Layer 2 working memory (`memory_items` with `usefulness_score`, `cycles_unused`, `last_retrieved`), Layer 3 long-term (`memory_longterm`)
- [ ] `app/memory/recall.py` — `memory.recall(query)` tool: vector search across L2 + L3 with filters by target_type / probe_class
- [ ] `app/memory/consolidate.py` — consolidation pass:
  - L1 events older than 7 days → L2 with reset counters
  - L2 items: `usefulness_score >= 3` → L3, `cycles_unused >= 5` → drop
  - L3 pattern detection → procedural heuristic
- [ ] Schedule consolidation as a Letta task, also runs after every 10 scans
- [ ] First procedural heuristic generated and persisted

### Procedural memory onchain

- [ ] `app/memory/procedural.py` — `Heuristic` rows include `rule`, `evidence_scan_ids`, `success_rate`, `sample_size`, `last_updated`, `owasp_mapping`, `atlas_technique`
- [ ] EAS attestation per heuristic version; published as `spieon.eth/memory.json` (served by frontend or static export)

### Narration stream

- [ ] `app/api/ws.py` — WebSocket endpoint `/ws/scans/{scan_id}` pushes narration events
- [ ] Narration events emitted from every LangGraph node (recon, plan, probe, reflect, adapt, verify, attest, consolidate)
- [ ] Frontend `app/scan/[id]/page.tsx` subscribes to WS and renders streaming feed, color-coded by phase
- [ ] Narration events also persisted to DB and traced to Langfuse

### Cross-scan retrieval

- [ ] Run two scans against the same target type; second scan's `recon` retrieves heuristics from first

---

## Day 5 — Native probes 2-5 + adaptive attacker + probe safety harness (2026-04-30)

### Native probes (`app/probes/native/`)

- [ ] `payment_retry_bypass.py` — 402 response then retry without/malformed/expired payment
- [ ] `settlement_skip.py` — valid payment then disconnect before settlement
- [ ] `mcp_tool_description_injection.py` — tool descriptions with prompt-injection payloads
- [ ] `mcp_schema_poisoning.py` — schemas with unicode confusables, hidden instructions, name shadowing

### Adaptive attacker (`app/workflow/adapt.py`) — PRD §4.2

- [ ] `reflect` node returns structured signal: `{success, target_strength_signals, suggested_next}`
- [ ] `adapt` node decides between: `continue planned probe` / `mutate params` / `pivot to new attack class` / `forward to verify`
- [ ] Planner can re-enter `plan` with updated context to reorder probes
- [ ] Adaptive loop has max-iteration cap to prevent runaway

### Probe safety harness (`app/safety/harness.py`) — PRD §8.2

- [ ] Per-target rate limit: 60 req/min, 1000 req/hr (token bucket keyed by target host)
- [ ] Destructive blocklist: no DoS-class probes, no auth-brute >3, no destructive writes
- [ ] Auto-stop conditions: 5 consecutive 5xx, budget exhausted, operator wallet insufficient, max attempts reached
- [ ] Attribution headers injected on every outbound request: `User-Agent: Spieon-Pentest/1.0 (+spieon.eth)`, `X-Spieon-Scan-Id: <scan_id>`
- [ ] Consent checkbox added to scan submission form (frontend); backend rejects scans without consent

### Verification

- [ ] `app/probes/dedup.py` — cross-engine dedupe via signature hashing + LLM-judge merge
- [ ] `app/probes/judge.py` — LLM-as-judge confirms finding, drops false positives
- [ ] `app/probes/severity.py` — normalize severities across engines (CVSS-ish 0–10 → low/med/high/critical)

### Day-5 cut rule check

- [ ] If adaptive mutation logic broken: fall back to deterministic probe-list executor; label as "deterministic mode" honestly.

---

## Day 6 — Bounty contracts + ERC-8004 + patch artifacts + adversarial-operator mitigations (2026-05-01)

### Contracts (`contracts/` — Foundry or Hardhat)

- [ ] `ModuleRegistry.sol` per PRD §9.2 with taxonomy fields, deployed to Base Sepolia
- [ ] V1 modules registered (one per native probe + one per wrapped engine class)
- [ ] `BountyPool` Safe deployed; agent address added as signer
- [ ] Custom Safe Module `BountyPayoutModule.sol` with `payoutForFinding(scanId, moduleHash, amount)` enforcing per-finding caps (`crit $5, high $2, med $0.50, low $0.10`)
- [ ] Frontend ABI bindings generated via `wagmi cli` or `viem` `parseAbi`
- [ ] Backend `app/chain/contracts.py` with typed wrappers

### ERC-8004

- [ ] Identity Registry entry created for Spieon
  - `agentURI` JSON: name, description, capabilities, website `spieon.eth`, basename `spieon.base.eth`
- [ ] Reputation Registry: handler for `giveFeedback` from operators after scan completion
- [ ] Validation Registry: skipped (V2)

### Patch artifact generation (`app/probes/patches/`)

- [ ] `colang.py` — generate NeMo Guardrails Colang rule for prompt-injection / tool-poisoning findings
- [ ] `policylayer.py` — generate PolicyLayer rule for x402-specific findings
- [ ] `generic.py` — generic JSON config describing pattern
- [ ] Every finding ships at least one patch artifact; attached to encrypted bundle

### Adversarial-operator mitigations (PRD §8.3)

- [ ] Per-finding bounty caps enforced in Safe Module (already above)
- [ ] Per-module daily cap $10/day enforced in `BountyPayoutModule` or a backend gate before calling Safe Module
- [ ] Outsized payout (>$20) flag: agent halts payout, emits operator notification (placeholder email/log)
- [ ] Operator history tracking — `operator_stats` table with `false_positive_rate`; high-FP operators rate-limited on submission

### Recovery posture (PRD §8.4)

- [ ] `docs/RECOVERY.md` documents:
  - Hot wallet max $50 USDC; auto-sweep overflow to cold Safe
  - Private-key rotation procedure
  - Letta memory snapshot daily backup to encrypted offsite (S3 or local for V1)
- [ ] Auto-sweep cron implemented (or documented as manual for V1; note inline)

### End-to-end bounty test

- [ ] Scan finds a vuln → attestation → operator signs `OperatorPatched` → Safe Module pays bounty to module-author address → leaderboard updates

### 🚦 Day 6 checkpoint (gate)

- [ ] Backend complete, contracts deployed, end-to-end loop with bounty payouts works against test target. Defenses tested.
- If failing: cut all V2 features and dedicate days 7-10 to frontend + demo.

---

## Day 7 — Frontend dashboard, scan submission, persistent-identity banner (2026-05-02)

### Pages

- [ ] `/` landing
  - [ ] Persistent-identity banner: `spieon.base.eth · ERC-8004 #N · Running X days · Y scans · Z findings · W heuristics · Treasury $A · Reputation B`
  - [ ] Buttons: `Wallet`, `Memory`, `All Attestations`
  - [ ] Chain-as-home framing: agent's wallet + onchain state above the dashboard UI; click-throughs to base-sepolia.easscan.org and basescan.org
  - [ ] Recent activity feed
  - [ ] Quick scan input
- [ ] `/scan` submission form
  - [ ] Fields: target URL, budget USDC, bounty USDC, encryption pubkey, consent checkbox (PRD §8.2 text)
  - [ ] Form validation, submit hits `POST /scans`
- [ ] `/scan/[id]` live or historical scan view
  - [ ] WebSocket narration stream (color-coded by phase)
  - [ ] Findings inline at attestation moment
  - [ ] Cost-of-exploit, severity, taxonomy IDs visible per finding
  - [ ] Attestation hash links to base-sepolia.easscan.org
- [ ] `/agent` profile page: total scans, findings, treasury, ERC-8004 reputation, link to `memory.json`

### Components

- [ ] `components/NarrationStream.tsx` — WebSocket subscription, virtualised list, phase color-coding
- [ ] `components/FindingCard.tsx` — severity badge, cost, taxonomy chips, patch-artifact download
- [ ] `components/IdentityBanner.tsx` — banner data fetched from backend stats endpoint
- [ ] Backend: `GET /agent/stats` aggregating banner numbers

---

## Day 8 — Frontend polish + memory page + module registry + benchmarks deployed + NameStone if slack (2026-05-03 morning push)

### Pages

- [ ] `/memory` — viewable procedural memory list with onchain attestation links per heuristic version
- [ ] `/modules` — module registry rendered with OWASP/ATLAS mappings, success rates, ENS-resolved author names
- [ ] `/leaderboard` — module authors ranked by findings landed, bounties earned
- [ ] `/findings` — global feed (metadata only)
- [ ] `/benchmarks` — Spieon's scores on DVMCP, Cybench, DVLA (and AgentDojo if integrated)
- [ ] `/about` — what Spieon is, FAQ, threat model summary, security disclosure

### Polish

- [ ] Mobile responsive across all pages
- [ ] ENS resolution: `spieon.eth` resolves to dashboard
- [ ] All attestation hashes click through to base-sepolia.easscan.org

### Benchmarks (separate VPS)

- [ ] Deploy DVMCP, DVLA, Cybench subset (10-15 tasks), custom vulnerable target
- [ ] Run Spieon against each, capture numbers for `/benchmarks` and demo voiceover
- [~] AgentDojo dropped from V1 per pre-day-1 decision.

### Optional if slack

- [ ] NameStone L2 subname resolver for module authors (`alice.spieon.base.eth`); else simple address mapping
- [ ] ProjectDiscovery recon (nuclei + httpx + katana) wrapped for non-MCP web targets

### Demo dry-run

- [ ] End-to-end demo executed without manual intervention or visible errors
- [ ] Numbers locked into demo script

### 🚦 Day 8 checkpoint (gate)

- [ ] Demo performable end-to-end. Benchmark numbers captured.
- If failing: day 9 fixes, day 10 video only.

---

## Day 9 — Demo dry-run + bug fixes + ProjectDiscovery if slack (2026-05-03 — same day as deadline; assume deadline-day rush)

> **Note:** PRD's day numbering puts day 9–10 across the deadline. With submission Sun 11:59 ET (2026-05-03), days 9 and 10 collapse — bug-fixing and video happen the same day. Treat anything below as "must finish before submit cutoff."

- [ ] Run full demo at least 3 times; record timing
- [ ] Fix anything broken, slow, or confusing
- [ ] ProjectDiscovery recon wrapped if slack (else V2)
- [ ] Write submission text and devpost description draft
- [ ] Lock final benchmark run; freeze numbers for video

---

## Day 10 — Video + submission + buffer (2026-05-03 evening)

- [ ] Record 4-minute demo video covering all 7 beats from PRD §2 (setup, target, probing-with-narration, attestation, bounty, memory, benchmark credibility, closing)
- [ ] Edit + voiceover
- [ ] Submit to ETHGlobal Showcase
- [ ] Post devpost submission
- [ ] Tag a `v1.0.0-hackathon` git tag at submission time

---

## Cross-cutting workstreams (active throughout)

### Observability (Langfuse)

- [ ] Every LangGraph node decorated with Langfuse trace
- [ ] Every tool call traced (recon, plan, probes, narrate, memory ops, chain ops)
- [ ] Every chain interaction (eas.attest, bounty.payout) traced with USDC cost

### Tests

- [ ] Pytest covers: probe normalizer, cost meter, dedupe, prompt-injection defense, safety harness rate limits, severity normalization
- [ ] Integration test: full scan against fixture target, asserts finding + attestation + memory update

### Documentation

- [ ] Root `README.md` quick-start (clone, `.env`, `make up`)
- [ ] `docs/THREAT_MODEL.md` — surfaces from PRD §8 expanded into one page
- [ ] `docs/RECOVERY.md` — wallet rotation, cold Safe sweep, memory backup
- [ ] `docs/MODULE_AUTHORS.md` — how to register a module, taxonomy IDs required
- [ ] `docs/AI_USAGE.md` kept current as features land

### Sponsor checklist

- [~] **ENS:** deferred V1. $5K sponsor prize accepted as a knowing cut.
- [ ] **ZeroG:** encrypted finding bundles uploaded; URI in every attestation. Now the primary sponsor target.
- [ ] **Keeperhub (if attempted):** scheduled re-scan trigger by day 8.

---

## Cuts on the table (PRD §12)

If day 3 fails: drop adaptive attacker (probe-list executor only), drop Cybench, drop patch artifact generation.
If day 6 fails: 3 native probes instead of 5, one benchmark target, frontend single-page, AgentDojo dropped, NameStone dropped, ProjectDiscovery dropped.

V1 explicitly does **not** ship: DSPy, Graphiti, Hats, ZK proofs, Cisco mcp-scanner, agentic_security, promptfoo Hydra, auto-publish disclosure, per-target Safe pools, module submission UX, Validation Registry, scheduled scanning via Keeperhub, multi-chain, TS / Mastra alternative.
