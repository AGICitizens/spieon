from __future__ import annotations

import uuid
from decimal import Decimal

import httpx
import pytest
import respx

from app.cost.meter import CostMeter
from app.probes.native.payment_retry_bypass import PaymentRetryBypassProbe
from app.probes.protocol import ProbeContext


def _ctx() -> ProbeContext:
    return ProbeContext(
        scan_id=uuid.uuid4(),
        probe_run_id=uuid.uuid4(),
        target_url="https://target.example/x402",
        budget_remaining_usdc=Decimal("1.0"),
        attribution_headers={"User-Agent": "Spieon-Pentest/1.0 (+spieon.eth)"},
    )


@pytest.mark.asyncio
@respx.mock
async def test_payment_retry_bypass_flags_when_empty_payload_returns_200() -> None:
    challenge = httpx.Response(402, json={"x402Version": 1, "accepts": []})
    respx.get("https://target.example/x402").mock(
        side_effect=[
            challenge,
            httpx.Response(200, json={"resource": "leaked"}),
        ]
    )

    probe = PaymentRetryBypassProbe()
    outcome = await probe.run(_ctx(), meter=CostMeter(probe.id))

    assert outcome.vulnerable is True
    assert outcome.findings[0].severity.value == "critical"
    assert outcome.notes["winning_label"] == "empty"


@pytest.mark.asyncio
@respx.mock
async def test_payment_retry_bypass_clean_when_all_retries_rejected() -> None:
    respx.get("https://target.example/x402").mock(
        side_effect=[
            httpx.Response(402, json={"x402Version": 1, "accepts": []}),
            httpx.Response(402, json={"error": "missing payment"}),
            httpx.Response(402, json={"error": "missing payment"}),
            httpx.Response(402, json={"error": "missing payment"}),
            httpx.Response(400, json={"error": "bad header"}),
        ]
    )

    probe = PaymentRetryBypassProbe()
    outcome = await probe.run(_ctx(), meter=CostMeter(probe.id))

    assert outcome.vulnerable is False
    statuses = [s for _, s in outcome.notes["attempts"]]
    assert statuses == [402, 402, 402, 400]


@pytest.mark.asyncio
@respx.mock
async def test_payment_retry_bypass_skips_when_no_402() -> None:
    respx.get("https://target.example/x402").mock(
        return_value=httpx.Response(200, json={"resource": "free"})
    )
    probe = PaymentRetryBypassProbe()
    outcome = await probe.run(_ctx(), meter=CostMeter(probe.id))
    assert outcome.vulnerable is False
    assert "did not return 402" in outcome.notes["reason"]
