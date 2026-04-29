from __future__ import annotations

import base64
import json
import uuid
from decimal import Decimal

import httpx
import pytest
import respx

from app.cost.meter import CostMeter
from app.cost.receipts import UsdcTransfer
from app.probes.native.x402_replay import X402ReplayProbe
from app.probes.protocol import ProbeContext

SAMPLE_REQUIREMENTS = {
    "scheme": "exact",
    "network": "base-sepolia",
    "maxAmountRequired": "1000",
    "resource": "https://target.example/replay",
    "description": "Test resource",
    "mimeType": "application/json",
    "payTo": "0x000000000000000000000000000000000000dEaD",
    "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "maxTimeoutSeconds": 60,
    "extra": {"name": "USD Coin", "version": "2"},
}


def _payment_response_header(tx: str = "0x" + "ab" * 32) -> str:
    return base64.b64encode(
        json.dumps({"success": True, "transaction": tx, "network": "base-sepolia"}).encode()
    ).decode()


def _ctx() -> ProbeContext:
    return ProbeContext(
        scan_id=uuid.uuid4(),
        probe_run_id=uuid.uuid4(),
        target_url="https://target.example/replay",
        budget_remaining_usdc=Decimal("1.0"),
        attribution_headers={"User-Agent": "Spieon-Pentest/1.0 (+spieon.eth)"},
    )


class _StubParser:
    async def parse(self, response: object) -> UsdcTransfer | None:
        return UsdcTransfer(
            tx_hash="0x" + "ab" * 32,
            from_address="0xfrom",
            to_address="0xto",
            amount=Decimal("0.001"),
            block_number=1,
        )


@pytest.mark.asyncio
@respx.mock
async def test_x402_replay_flags_when_replay_is_accepted(monkeypatch) -> None:
    from eth_account import Account

    account = Account.create()
    monkeypatch.setattr("app.x402.client.signer", lambda: account, raising=True)

    respx.get("https://target.example/replay").mock(
        side_effect=[
            httpx.Response(402, json={"x402Version": 1, "accepts": [SAMPLE_REQUIREMENTS]}),
            httpx.Response(
                200,
                headers={"x-payment-response": _payment_response_header()},
                json={"ok": True},
            ),
            httpx.Response(
                200,
                headers={"x-payment-response": _payment_response_header("0x" + "cd" * 32)},
                json={"ok": True},
            ),
        ]
    )

    probe = X402ReplayProbe()
    meter = CostMeter(probe.id, parser=_StubParser())
    outcome = await probe.run(_ctx(), meter=meter)

    assert outcome.vulnerable is True
    assert len(outcome.findings) == 1
    finding = outcome.findings[0]
    assert finding.title == "x402 payment replay accepted"
    assert finding.atlas_technique_id == "AML.T0049"
    assert finding.cost_usdc == Decimal("0.001")
    assert outcome.cost_usdc == Decimal("0.001")


@pytest.mark.asyncio
@respx.mock
async def test_x402_replay_clean_when_replay_rejected(monkeypatch) -> None:
    from eth_account import Account

    account = Account.create()
    monkeypatch.setattr("app.x402.client.signer", lambda: account, raising=True)

    respx.get("https://target.example/replay").mock(
        side_effect=[
            httpx.Response(402, json={"x402Version": 1, "accepts": [SAMPLE_REQUIREMENTS]}),
            httpx.Response(
                200,
                headers={"x-payment-response": _payment_response_header()},
                json={"ok": True},
            ),
            httpx.Response(401, json={"error": "nonce already spent"}),
        ]
    )

    probe = X402ReplayProbe()
    meter = CostMeter(probe.id, parser=_StubParser())
    outcome = await probe.run(_ctx(), meter=meter)

    assert outcome.vulnerable is False
    assert outcome.findings == []
    assert outcome.notes["replay_status"] == 401
