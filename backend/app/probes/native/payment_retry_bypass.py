from __future__ import annotations

import base64
import hashlib
import json
from decimal import Decimal

import httpx

from app.cost.meter import CostMeter
from app.models.finding import Severity
from app.models.probe_run import ProbeEngine
from app.probes.normalize import RawFinding
from app.probes.protocol import ProbeContext, ProbeOutcome
from app.probes.registry import ProbeSpec, register_probe

PROBE_ID = "x402-payment-retry-bypass"
MODULE_HASH = "0x" + hashlib.sha256(PROBE_ID.encode()).hexdigest()


class PaymentRetryBypassProbe:
    id = PROBE_ID

    async def run(self, ctx: ProbeContext, *, meter: CostMeter) -> ProbeOutcome:
        async with httpx.AsyncClient(timeout=30.0) as client:
            no_header = await client.get(ctx.target_url, headers=dict(ctx.attribution_headers))
            if no_header.status_code != 402:
                return ProbeOutcome(
                    vulnerable=False,
                    response_excerpt=_excerpt(no_header.text),
                    notes={"reason": "endpoint did not return 402 on bare request"},
                )

            attempts: list[tuple[str, int]] = []
            for label, header in _bogus_headers():
                try:
                    response = await client.get(
                        ctx.target_url,
                        headers={**ctx.attribution_headers, "X-Payment": header},
                    )
                except Exception as exc:
                    attempts.append((label, -1))
                    return ProbeOutcome(
                        vulnerable=False,
                        error=f"retry {label!r} failed: {exc}",
                        notes={"attempts": attempts},
                        cost_usdc=meter.cost.total,
                    )
                attempts.append((label, response.status_code))
                if response.status_code == 200:
                    return _vulnerable(label, response, attempts, meter.cost.total)

        return ProbeOutcome(
            vulnerable=False,
            cost_usdc=meter.cost.total,
            notes={"attempts": attempts},
        )


def _bogus_headers() -> list[tuple[str, str]]:
    empty_payload = base64.b64encode(b"{}").decode()
    truncated = base64.b64encode(b'{"x402Version":1,"scheme":"exact"}').decode()
    expired = base64.b64encode(
        json.dumps(
            {
                "x402Version": 1,
                "scheme": "exact",
                "network": "base-sepolia",
                "payload": {
                    "signature": "0x" + "00" * 65,
                    "authorization": {
                        "from": "0x" + "00" * 20,
                        "to": "0x" + "00" * 20,
                        "value": "1",
                        "validAfter": "0",
                        "validBefore": "1",
                        "nonce": "0x" + "00" * 32,
                    },
                },
            }
        ).encode()
    ).decode()
    return [
        ("empty", empty_payload),
        ("truncated", truncated),
        ("expired", expired),
        ("garbage", "not-base64-at-all"),
    ]


def _excerpt(body: str | None, *, limit: int = 800) -> str | None:
    if not body:
        return None
    return body[:limit]


def _vulnerable(label: str, response: httpx.Response, attempts, cost: Decimal) -> ProbeOutcome:
    finding = RawFinding(
        title=f"Bogus X-Payment ({label}) bypassed 402 challenge",
        summary=(
            f"Sending an X-Payment header with the {label!r} payload returned 200. "
            "The facilitator (or upstream verifier) is not validating the payload "
            "before granting access to the protected resource."
        ),
        severity=Severity.critical,
        module_hash=MODULE_HASH,
        owasp_id="API01",
        atlas_technique_id="AML.T0049",
        cost_usdc=cost,
        signature_parts=(MODULE_HASH, "retry-bypass", label),
        extra={"label": label, "status": response.status_code},
    )
    return ProbeOutcome(
        vulnerable=True,
        findings=[finding],
        response_excerpt=_excerpt(response.text),
        cost_usdc=cost,
        notes={"attempts": attempts, "winning_label": label},
    )


SPEC = register_probe(
    ProbeSpec(
        id=PROBE_ID,
        engine=ProbeEngine.native,
        probe_class="x402-retry-bypass",
        severity_cap=Severity.critical,
        cost_estimate_usdc=Decimal("0"),
        owasp_id="API01",
        atlas_technique_id="AML.T0049",
        maestro_id=None,
        factory=PaymentRetryBypassProbe,
        module_hash=MODULE_HASH,
        description=(
            "After receiving 402, retry with empty / truncated / expired / garbage "
            "X-Payment headers. Any retry that returns 200 indicates the verifier "
            "is missing input validation."
        ),
        tags=("x402", "payment", "verification"),
    )
)
