from __future__ import annotations

import asyncio
import contextlib
import hashlib
from decimal import Decimal

import httpx

from app.cost.meter import CostMeter
from app.models.finding import Severity
from app.models.probe_run import ProbeEngine
from app.probes.normalize import RawFinding
from app.probes.protocol import ProbeContext, ProbeOutcome
from app.probes.registry import ProbeSpec, register_probe
from app.x402 import X402Client, encode_payment_header

PROBE_ID = "x402-settlement-skip"
MODULE_HASH = "0x" + hashlib.sha256(PROBE_ID.encode()).hexdigest()


class SettlementSkipProbe:
    id = PROBE_ID

    async def run(self, ctx: ProbeContext, *, meter: CostMeter) -> ProbeOutcome:
        async with X402Client(attribution_headers=ctx.attribution_headers) as client:
            try:
                first = await client.request("GET", ctx.target_url)
            except Exception as exc:
                return ProbeOutcome(vulnerable=False, error=f"first request failed: {exc}")
            if first.used_payment is None:
                return ProbeOutcome(
                    vulnerable=False,
                    notes={"reason": "endpoint did not require x402 payment"},
                )

            await meter.record(first)

            payment_header = encode_payment_header(first.used_payment)

            try:
                async with httpx.AsyncClient(timeout=2.0) as throwaway:
                    request = throwaway.build_request(
                        "GET",
                        ctx.target_url,
                        headers={
                            **ctx.attribution_headers,
                            "X-Payment": payment_header,
                        },
                    )
                    send_task = asyncio.create_task(throwaway.send(request))
                    await asyncio.sleep(0.05)
                    send_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError, Exception):
                        await send_task
            except Exception:
                pass

            await asyncio.sleep(0.5)

            verify = await client._client.request(
                "GET",
                ctx.target_url,
                headers={
                    **ctx.attribution_headers,
                    "X-Payment": payment_header,
                },
            )

        if verify.status_code == 200 and not verify.headers.get("x-payment-response"):
            finding = RawFinding(
                title="x402 access granted without settlement",
                summary=(
                    "After cancelling mid-settlement and reusing the same X-Payment "
                    "header, the target served the protected resource without an "
                    "X-Payment-Response settlement record. Funds may not have moved."
                ),
                severity=Severity.high,
                module_hash=MODULE_HASH,
                owasp_id="API01",
                atlas_technique_id="AML.T0049",
                cost_usdc=meter.cost.total,
                signature_parts=(MODULE_HASH, "settlement-skip", "no-receipt"),
                extra={"verify_status": verify.status_code},
            )
            return ProbeOutcome(
                vulnerable=True,
                findings=[finding],
                cost_usdc=meter.cost.total,
                response_excerpt=verify.text[:800] if verify.text else None,
                notes={"verify_status": verify.status_code},
            )

        return ProbeOutcome(
            vulnerable=False,
            cost_usdc=meter.cost.total,
            notes={"verify_status": verify.status_code},
        )


SPEC = register_probe(
    ProbeSpec(
        id=PROBE_ID,
        engine=ProbeEngine.native,
        probe_class="x402-settlement-skip",
        severity_cap=Severity.high,
        cost_estimate_usdc=Decimal("0.10"),
        owasp_id="API01",
        atlas_technique_id="AML.T0049",
        maestro_id=None,
        factory=SettlementSkipProbe,
        module_hash=MODULE_HASH,
        description=(
            "Sends a valid payment, cancels the connection during settlement, then "
            "retries; flags the target if the resource is served without an "
            "X-Payment-Response settlement record."
        ),
        tags=("x402", "payment", "settlement"),
    )
)
