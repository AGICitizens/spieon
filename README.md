# spieon

Open-source AI Red Team for the Agent Economy. See [docs/PRD.md](docs/PRD.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Layout

```
backend/    FastAPI service (Python 3.12+, uv)
frontend/   Next.js 15 dashboard (TypeScript, App Router)
docs/       PRD, architecture diagrams
```

The frontend consumes types generated from the backend's OpenAPI schema (`frontend/npm run gen:api`) — that's the only contract between the two.
