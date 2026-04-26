# AI Tool Usage

Per ETHGlobal Open Agents rules, AI tools (Claude Code, ChatGPT, Copilot, Cursor, etc.) are permitted as development assistants. They must not create the entire project, and their use must be documented. This file is the living record of where AI was used while building Spieon.

Update this file as you go. At submission time it should give a judge a complete, honest picture.

## Tools used

| Tool        | Purpose                                            |
| ----------- | -------------------------------------------------- |
| Claude Code | (e.g., drafting, refactoring, debugging — fill in) |
|             |                                                    |

## Where AI assisted

Note the file or component, what the AI did, and what was hand-authored on top of it.

### Planning and specification

- `docs/PRD.md` — drafted with AI assistance through iterative dialogue. Architecture, scope, day-by-day plan, sponsor strategy, and risk list were directed by the human; AI helped with structure, phrasing, and consistency.

### Backend (FastAPI, scan workflow, agent runtime)

- _(fill in per file as built)_

### Smart contracts

- _(fill in per contract as built)_

### Probe library

- _(fill in per probe as built)_

### Frontend

- _(fill in per page/component as built)_

### Tests

- _(fill in)_

### Infrastructure (Docker, deploy scripts, CI)

- _(fill in)_

## Where AI was NOT used

State the parts of the project that are entirely human work. Examples to fill in honestly:

- Architecture and component boundaries
- Probe design (which vulnerabilities to test, attack patterns)
- Memory consolidation policy (thresholds, promotion rules)
- Onchain schema design (EAS schema, contract interfaces)
- Demo narrative and timing

## Prompts and spec files

Per the spec-driven workflow guidance, list any prompt or spec artifacts included in this repo:

- `docs/PRD.md` — master product specification

## Disclosure summary

A short paragraph for the submission write-up. Update at the end.

> Spieon was built solo over the ETHGlobal Open Agents hackathon window (April 26 – May 3, 2026). AI tools (primarily Claude Code) were used as a development assistant for drafting the PRD, scaffolding boilerplate, and debugging. All architectural decisions, probe designs, and the demo narrative are human-authored. Every commit was reviewed and edited by hand before landing.
