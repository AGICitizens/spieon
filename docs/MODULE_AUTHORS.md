# Spieon — module authors guide

This is the contract between a probe author and Spieon. If you write a probe,
register it onchain, and Spieon's planner picks it on a paid scan that lands a
finding, the operator can pay you a bounty up to the per-severity cap.

## What a probe looks like

A probe is a Python class implementing the `Probe` protocol in
[`backend/app/probes/protocol.py`](../backend/app/probes/protocol.py):

```python
class Probe(Protocol):
    id: str

    async def run(self, ctx: ProbeContext, *, meter: CostMeter) -> ProbeOutcome: ...
```

`ProbeContext` carries the scan id, target URL, remaining budget, and the
attribution headers Spieon adds to every outbound request
(`User-Agent: Spieon-Pentest/1.0 (+spieon.eth)` + `X-Spieon-Scan-Id`).
`CostMeter` is the async context that records USDC payments via the
`PaymentReceiptParser` so cost-of-exploit lands on the resulting finding.

`ProbeOutcome` returns one or more `RawFinding`s. Each finding is mandatory
about its taxonomy:

- `severity: Severity` — `low | medium | high | critical`. The bounty pool
  caps payout per severity.
- `module_hash: str` — `0x` + sha256 of your probe's stable identifier.
  Findings that share a `module_hash` are attributed to you.
- `owasp_id`, `atlas_technique_id`, `maestro_id` — at least one taxonomy must
  be set so the EAS attestation has something to filter on.
- `signature_parts: tuple[str, ...]` — drives cross-engine dedupe. Two probes
  emitting the same signature_parts collapse into a single finding before
  attestation.

See [`backend/app/probes/native/x402_replay.py`](../backend/app/probes/native/x402_replay.py)
for a minimal reference probe.

## Registering a probe

Probes live in two places: a registered `ProbeSpec` in process and a
registered module hash on chain.

### In-process spec

```python
from app.probes.registry import ProbeSpec, register_probe

register_probe(
    ProbeSpec(
        id="x402-replay-attack",
        engine=ProbeEngine.native,
        probe_class="x402-replay",
        severity_cap=Severity.high,
        cost_estimate_usdc=Decimal("0.10"),
        owasp_id="API07",
        atlas_technique_id="AML.T0049",
        maestro_id=None,
        factory=X402ReplayProbe,
        module_hash=MODULE_HASH,
        description="...",
        tags=("x402", "payment", "replay"),
    )
)
```

### On chain

The backend lifespan handler calls
[`register_native_probes()`](../backend/app/chain/contracts.py) on startup; if
`MODULE_REGISTRY_ADDRESS` and `AGENT_PRIVATE_KEY` are set in `.env`, every
spec missing from the on-chain registry is registered idempotently.

Manual register:

```sh
cd backend
uv run python -c "
import asyncio
from app.chain.contracts import register_module_onchain
from app.models.finding import Severity
asyncio.run(register_module_onchain(
    module_hash='0x...',
    metadata_uri='ipfs://...',
    severity_cap=Severity.high,
    owasp_id='API07',
    atlas_technique_id='AML.T0049',
    maestro_id=None,
))
"
```

## Severity caps and bounties

`BountyPool` enforces the PRD §6 caps:

| Severity | Cap (USDC) |
|----------|-----------|
| critical | $5.00 |
| high | $2.00 |
| medium | $0.50 |
| low | $0.10 |

Per-module daily cap is $10. Single payouts above $20 revert unless the
operator invokes `payoutWithCosign(...)` with a configured cosigner; Spieon
emits an `OutsizedFlagged` event for off-chain alerting.

Your `severity_cap` on the `ProbeSpec` is the *highest* severity your probe is
allowed to claim — Spieon's runner caps every finding to it, so a probe
declared `Severity.high` can never produce a critical-severity finding.

## Required taxonomy fields

OWASP IDs we expect to see (use the exact string):

- `LLM01` — prompt injection
- `LLM05` — supply chain / model risk (we apply this to schema poisoning)
- `API01` — broken object-level authorization
- `API07` — server-side request / replay-protection failures

ATLAS technique IDs we expect:

- `AML.T0049` — manipulate AI model
- `AML.T0051` — LLM prompt injection

If your probe targets something outside these, pick the closest taxonomy ID
and document it in your probe's `description`.

## Cost-of-exploit

If your probe pays for x402 challenges:

1. Wrap the call in `X402Client(attribution_headers=ctx.attribution_headers)`.
2. Pass the `X402Response` through `meter.record(...)` so the
   `X402ReceiptParser` pulls the actual USDC `Transfer` from the receipt.

The runner sums every `meter.record` call into `Finding.cost_usdc` for you.

## Dedupe

Findings with identical `signature_parts` collapse into a single finding
before attestation. Use stable parts (module hash, attack class, target
fingerprint), never timestamps or random ids.

## Patch artifacts

Findings that match prompt-injection or x402 shape automatically get
[Colang](../backend/app/patches/colang.py) /
[PolicyLayer](../backend/app/patches/policylayer.py) artifacts attached to the
encrypted bundle. If you want to ship a custom artifact for your probe class,
extend `app/patches/registry.py` with your generator.
