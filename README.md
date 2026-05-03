# spieon

Open-source AI Red Team for the Agent Economy. Spieon scans MCP servers and
x402-protected endpoints, attests findings on Base Sepolia, encrypts the bundle
to the operator, and pays bounties to the module authors whose probes landed.

See [docs/PRD.md](docs/PRD.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md), [docs/RECOVERY.md](docs/RECOVERY.md),
[docs/AI_USAGE.md](docs/AI_USAGE.md), and [docs/DEMO.md](docs/DEMO.md).

## Layout

```
backend/    FastAPI service (Python 3.12+, uv) — agent runtime, scan workflow, chain ops
frontend/   Next.js 15 dashboard (TypeScript, App Router)
contracts/  Foundry — ModuleRegistry + BountyPool
docs/       PRD, architecture, threat model, recovery, AI usage, domain landscape
```

The frontend consumes types generated from the backend's OpenAPI schema
(`pnpm --dir frontend gen:api`) — that's the only contract between the two.

## Quick start

Prereqs: Docker, [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/),
Node 20+, Foundry (only if you plan to build / deploy contracts).

```bash
cp .env.example .env                 # then fill in OPENROUTER_API_KEY etc.
make up                              # postgres + langfuse
cd backend && uv sync --group dev    # backend deps + dev tools
make migrate                         # alembic upgrade head
make backend                         # uvicorn on :8000
```

Frontend (separate terminal):

```bash
cd frontend && pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev   # next dev on :3000
```

Open `http://localhost:3000`. Submit a scan from `/scan` and watch the
narration stream live on `/scan/<id>`. The recipient key is generated in your
browser at submission and only its public form (`age1…`) is sent to the
backend; the secret stays on your machine. The homepage also links to the open
source GitHub repo and a dedicated `/hackathon` brief for judges, hosts, and
sponsor reviewers.

## What you get end-to-end

1. **Submit a scan** — operator picks a target URL, generates an X25519
   recipient in the browser, downloads the secret key, accepts the consent
   text, hits submit.
2. **The agent plans** — recon classifies the target, plan recalls prior
   heuristics from procedural memory and picks probes via an Anthropic
   `select_probes` tool call (or a deterministic fallback).
3. **Probes run** through a safety harness (per-host token bucket,
   destructive blocklist, auto-stop on budget / 5xx streak / max attempts)
   and a CostMeter that pulls real USDC `Transfer` amounts from the x402
   payment receipts.
4. **Findings** are deduped by signature, optionally LLM-judged, persisted
   as `findings` rows.
5. **Verify → attest** encrypts each bundle with patches (Colang +
   PolicyLayer + JSON), uploads to ZeroG / IPFS / local fallback, and posts
   the EAS attestation to Base Sepolia with `sha256(ciphertext)` + the
   bundle URI.
6. **Bounty** — operator confirms a payout from `/scan/<id>`; the backend
   calls `BountyPool.payout(...)` enforcing the per-severity cap and the
   per-module daily cap.
7. **Consolidate** — three-tier memory advances; promoted L3 items become
   procedural heuristics, attested per version.

Backend on `:8000`, Langfuse on `:3001`, Postgres on `:5432`.
`make help` lists every shortcut. `cd backend && uv run pytest -q` runs the
test suite (64 tests).

## Contracts

```bash
cd contracts
make install          # forge-std + openzeppelin-contracts under lib/
make test             # forge test
make deploy           # AGENT_ADDRESS / AGENT_PRIVATE_KEY / BASE_SEPOLIA_RPC_URL must be set
```

After deploy, paste the printed addresses into `.env` (`MODULE_REGISTRY_ADDRESS`,
`BOUNTY_POOL_ADDRESS`); the backend lifespan handler will register every
native probe on chain on next startup.

## Stack

| Layer | Choice |
|-------|--------|
| Agent runtime | LangGraph + LangMem on pgvector |
| Backend | FastAPI + SQLModel (async, asyncpg) |
| Frontend | Next.js 15 + Tailwind + viem/wagmi |
| Sandboxing | e2b |
| Observability | Langfuse (self-hosted) |
| Chain | Base Sepolia · EAS · ERC-8004 |
| Payments | x402 via Coinbase facilitator |
| Encryption | age + X25519 — agent has no decryption capability |
