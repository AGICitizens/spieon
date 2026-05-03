# AI Tool Usage

Per ETHGlobal Open Agents rules, AI tools (Claude Code, ChatGPT, Copilot, Cursor, etc.) are permitted as development assistants. They must not create the entire project, and their use must be documented. This file is the living record of where AI was used while building Spieon.

Update this file as you go. At submission time it should give a judge a complete, honest picture.

## Tools used

| Tool        | Purpose                                                                 |
| ----------- | ----------------------------------------------------------------------- |
| Claude Code | PRD drafting, backend/frontend scaffolding, refactors, debugging, docs |
| ChatGPT     | Writing support for product phrasing, review copy, and documentation    |

## Where AI assisted

Note the file or component, what the AI did, and what was hand-authored on top of it.

### Planning and specification

- `docs/PRD.md` — drafted with AI assistance through iterative dialogue. Architecture, scope, day-by-day plan, sponsor strategy, and risk list were directed by the human; AI helped with structure, phrasing, and consistency.

### Backend (FastAPI, scan workflow, agent runtime)

- `backend/app/api/agent.py` — assisted with diagnosing and fixing the slow `/agent/stats` path by restructuring independent RPC / ENS lookups to run concurrently.

### Smart contracts

- _(fill in per contract as built)_

### Probe library

- _(fill in per probe as built)_

### Frontend

- `frontend/app/page.tsx` — assisted with homepage iteration, including replacing the old explainer panel with OSS + hackathon review links.
- `frontend/app/hackathon/page.tsx` — assisted with structuring the judge-facing brief that summarizes AI disclosure, sponsor integrations, bounty flow, and verification links.
- `frontend/components/SiteNav.tsx` — assisted with navigation updates so the hackathon brief is directly reachable from the primary UI.
- `frontend/app/layout.tsx` — assisted with suppressing an extension-triggered hydration warning on the root `<body>` node.

### Tests

- TypeScript validation and endpoint checks were run after UI and backend changes; AI assisted with the verification loop and issue isolation.

### Infrastructure (Docker, deploy scripts, CI)

- `docs/DEMO.md`, `README.md`, and deployment-adjacent repo docs were revised with AI assistance to keep sponsor, OSS, and review guidance aligned with the live product surface.

## Where AI was NOT used

State the parts of the project that are entirely human work. Examples to fill in honestly:

- Architecture and component boundaries
- Probe design (which vulnerabilities to test, attack patterns)
- Memory consolidation policy (thresholds, promotion rules)
- Onchain schema design (EAS schema, contract interfaces)
- Demo narrative and timing
- Sponsor selection and scoping decisions

## Prompts and spec files

Per the spec-driven workflow guidance, list any prompt or spec artifacts included in this repo:

- `docs/PRD.md` — master product specification
- `docs/DEMO.md` — demo runbook and judge verification flow

## Disclosure summary

A short paragraph for the submission write-up. Update at the end.

> Spieon was built solo over the ETHGlobal Open Agents hackathon window (April 26 – May 3, 2026). AI tools (primarily Claude Code, with limited ChatGPT writing support) were used as development assistants for drafting the PRD, shaping UI copy, scaffolding boilerplate, fixing bugs, and keeping docs in sync. All architectural decisions, probe designs, sponsor-scoping choices, and the demo narrative are human-authored. Every commit was reviewed and edited by hand before landing.
