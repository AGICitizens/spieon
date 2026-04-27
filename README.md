# spieon

Open-source AI Red Team for the Agent Economy. See [docs/PRD.md](docs/PRD.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/IMPLEMENTATION_TODO.md](docs/IMPLEMENTATION_TODO.md).

## Layout

```
backend/    FastAPI service (Python 3.12+, uv) — agent runtime, scan workflow, chain ops
frontend/   Next.js 15 dashboard (TypeScript, App Router)
docs/       PRD, architecture diagrams, implementation TODO
```

The frontend consumes types generated from the backend's OpenAPI schema (`pnpm --dir frontend gen:api`) — that's the only contract between the two.

## Quick start

Prereqs: Docker, [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/), Node 20+.

```bash
cp .env.example .env          # then fill in keys
make up                        # postgres + langfuse + backend
make migrate                   # apply alembic schema
make frontend                  # next dev on :3000
```

Backend runs on `:8000`, Langfuse on `:3001`, Postgres on `:5432`. See `make help` for everything else.

## Stack

| Layer | Choice |
|-------|--------|
| Agent runtime | LangGraph + LangMem on pgvector |
| Backend | FastAPI + SQLModel (async, asyncpg) |
| Frontend | Next.js 15 + Tailwind + viem/wagmi |
| Sandboxing | e2b |
| Observability | Langfuse (self-hosted) |
| Chain | Base Sepolia · EAS · Safe · ERC-8004 |
| Payments | x402 via Coinbase facilitator |
| Encryption | age + X25519 — agent has no decryption capability |
