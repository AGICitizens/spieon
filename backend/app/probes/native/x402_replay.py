from __future__ import annotations

import base64
import hashlib
import json
from decimal import Decimal

from app.cost.meter import CostMeter
from app.models.finding import Severity
from app.models.probe_run import ProbeEngine
from app.probes.normalize import RawFinding
from app.probes.protocol import ProbeContext, ProbeOutcome
from app.probes.registry import ProbeSpec, register_probe
from app.x402 import X402Client

PROBE_ID = "x402-replay-attack"
MODULE_HASH = "0x" + hashlib.sha256(PROBE_ID.encode()).hexdigest()


class X402ReplayProbe:
    id = PROBE_ID

    async def run(self, ctx: ProbeContext, *, meter: CostMeter) -> ProbeOutcome:
        async with X402Client(attribution_headers=ctx.attribution_headers) as client:
            try:
                first = await client.request("GET", ctx.target_url)
            except Exception as exc:
                return ProbeOutcome(
                    vulnerable=False,
                    error=f"first request failed: {exc}",
                )

            if first.used_payment is None or first.transaction is None:
                return ProbeOutcome(
                    vulnerable=False,
                    response_excerpt=_excerpt(first.response.text),
                    notes={"reason": "target did not require x402 payment"},
                )

            await meter.record(first)

            replay_header = base64.b64encode(
                json.dumps(first.used_payment.to_dict(), separators=(",", ":")).encode()
            ).decode()
            replay_headers = dict(ctx.attribution_headers)
            replay_headers["X-Payment"] = replay_header

            try:
                replay = await client._client.request("GET", ctx.target_url, headers=replay_headers)
            except Exception as exc:
                return ProbeOutcome(
                    vulnerable=False,
                    error=f"replay request failed: {exc}",
                    cost_usdc=meter.cost.total,
                )

        if replay.status_code == 200 and replay.headers.get("x-payment-response"):
            return _vulnerable(meter.cost.total, replay)
        if replay.status_code == 200:
            return _vulnerable(meter.cost.total, replay, settled=False)
        return ProbeOutcome(
            vulnerable=False,
            response_excerpt=_excerpt(replay.text),
            cost_usdc=meter.cost.total,
            notes={
                "replay_status": replay.status_code,
                "first_status": first.status_code,
            },
        )


def _excerpt(body: str | None, *, limit: int = 800) -> str | None:
    if not body:
        return None
    return body[:limit]


def _vulnerable(cost: Decimal, replay, *, settled: bool = True) -> ProbeOutcome:
    finding = RawFinding(
        title="x402 payment replay accepted",
        summary=(
            "Target accepted a replayed X-Payment header. "
            "An attacker who observes one payment can reuse it indefinitely "
            "until validBefore expires, draining the protected resource."
        ),
        severity=Severity.high,
        module_hash=MODULE_HASH,
        owasp_id="API07",
        atlas_technique_id="AML.T0049",
        cost_usdc=cost,
        signature_parts=(MODULE_HASH, "x402-replay", "accepted"),
        extra={
            "replay_status": replay.status_code,
            "second_settlement": settled,
        },
    )
    return ProbeOutcome(
        vulnerable=True,
        findings=[finding],
        response_excerpt=_excerpt(replay.text),
        cost_usdc=cost,
        notes={"replay_status": replay.status_code, "second_settlement": settled},
    )


SPEC = register_probe(
    ProbeSpec(
        id=PROBE_ID,
        engine=ProbeEngine.native,
        probe_class="x402-replay",
        severity_cap=Severity.high,
        cost_estimate_usdc=Decimal("0.10"),
        owasp_id="API07",
        atlas_technique_id="AML.T0049",
        maestro_id=None,
        factory=X402ReplayProbe,
        module_hash=MODULE_HASH,
        description=(
            "Pays the 402 challenge once, replays the same X-Payment header on a "
            "fresh request, and flags the target if the second response succeeds."
        ),
        tags=("x402", "payment", "replay"),
    )
)
