# Spieon — threat model

This is the operator-facing companion to PRD §8. It catalogs who can hurt
Spieon, who Spieon can hurt, and the in-tree mitigation for each one.

## Actors

| Actor | Goal |
| --- | --- |
| **Adversarial target** | Manipulate Spieon's agent loop via prompt injection in tool descriptions, schemas, or response bodies, or pass off a junk "vulnerability" so Spieon files a false attestation. |
| **Adversarial operator** | Drain the bounty pool by submitting malicious targets, replaying false-positive findings, or chaining payouts. |
| **Adversarial module author** | Register a probe whose `successCount` looks legitimate but produces unverifiable findings to claim bounties. |
| **Compromised infrastructure** | Postgres + LangGraph checkpointer / agent hot wallet / e2b sandbox stolen or read by an attacker who breached the host. |
| **Operator key loss** | Operator loses the X25519 secret key generated at scan submission. |

## Surface 1 — agent prompt injection

Targets feed untrusted text into the agent loop. Mitigations live in
[backend/app/defense/](../backend/app/defense/) and the system prompt
[`agent/prompts.py`](../backend/app/agent/prompts.py):

- **Structured tool calls only.** The agent's planning loop never interpolates
  raw target output into its instruction stream — every action flows through
  a typed tool (`narrate_decision`, `memory.recall`, registered probes).
- **Guard prompt.** Verbatim PRD §8.1 text in `SYSTEM_PROMPT` instructs the
  agent to treat all target content as data, log manipulation attempts as
  findings, and never act on them.
- **Probe-side canary detection.** `mcp-tool-description-injection` and
  `mcp-schema-poisoning` actively scan responses for canary phrases
  (`system prompt`, `etc/passwd`, hidden instructions) and surface an attempt
  as a high-severity finding instead of letting it influence behaviour.

## Surface 2 — destructive probes

Probes run against live targets. Mitigations live in
[`safety/harness.py`](../backend/app/safety/harness.py):

- **Per-host token bucket.** 60 req/min and 1000 req/hr per target host by
  default. The harness blocks above the threshold; the agent sees a
  `HarnessDecision.block` and moves on.
- **Destructive blocklist.** `dos`, `denial-of-service`, `auth-brute`,
  `filesystem-write`, `filesystem-delete`, `data-destruction` probe classes
  are blocked outright.
- **Auto-stop conditions.** Budget exhausted, 5 consecutive 5xx, max
  attempts (200 default), operator wallet under remaining budget → workflow
  short-circuits with an `AutoStopReason`.
- **Attribution headers.** Every outbound request carries
  `User-Agent: Spieon-Pentest/1.0 (+spieon.eth)` and `X-Spieon-Scan-Id`.
  Operators can grep their logs and unilaterally rate-limit Spieon.
- **Consent.** `POST /scans` rejects without `consent: true`; the frontend
  form refuses to submit without the checkbox + key download.

## Surface 3 — adversarial operator

Operator could submit junk targets or replay findings to drain the pool.
Mitigations live in
[`contracts/src/BountyPool.sol`](../contracts/src/BountyPool.sol):

- **Per-severity caps.** Hard-coded in the contract: `$5 / $2 / $0.50 / $0.10`
  for critical / high / medium / low.
- **Per-module daily cap.** `$10/day/module` blocks a single module from
  draining the pool inside one day.
- **Outsized-payout flag.** Any single payout `>= $20` reverts unless invoked
  through `payoutWithCosign(...)` with a configured cosigner; emits
  `OutsizedFlagged` for off-chain alerting.
- **Single-use attestations.** The pool tracks `attestationConsumed`;
  re-attempting payout for the same EAS UID reverts `AlreadyPaid`.
- **Module-must-be-registered.** Payouts to unregistered module hashes revert
  `UnknownModule`.

## Surface 4 — agent infrastructure

If the agent host is compromised:

- **Encrypted finding bundles.** Every bundle is age-encrypted to the
  operator's X25519 recipient at scan-submission time. The agent never has
  the matching identity. Past scan bundles cannot be retroactively decrypted
  even with full DB + RAM access.
- **Hot-wallet cap.** Recommended operating limit `$50` USDC on the hot
  wallet, sweep overflow to the cold Safe at `COLD_SAFE_ADDRESS`. See
  [RECOVERY.md](RECOVERY.md).
- **Checkpoint restart safety.** LangGraph checkpoints are written to
  Postgres per `thread_id = scan_id`; a crashed scan can be resumed by
  re-invoking the graph with the same thread id (V2 will auto-resume on
  startup).

## Surface 5 — operator key loss

The operator's X25519 secret key is the only path to plaintext findings.

- **Single-use download.** The submission form gates submission on the
  operator clicking "Download key file" first.
- **No recovery.** Spieon does not store the secret. Document this clearly in
  the UI (`/scan` page) and refuse to surface a recovery flow.
- **Public hash, private bundle.** The EAS attestation only commits to
  `sha256(ciphertext)`; if the operator loses the key, attestation history
  is still verifiable, only the plaintext is gone.

## Out of scope (V1)

- DoS resilience of the Spieon control-plane itself.
- Side-channel timing attacks against the agent's LLM calls.
- Validation Registry (ERC-8004 third-party validators) — slated for V2.
- Multi-chain payouts.
