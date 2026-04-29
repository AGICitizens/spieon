from __future__ import annotations

import base64
import json

import httpx
import pytest
import respx
from eth_account import Account

from app.x402 import X402Client

SAMPLE_REQUIREMENTS = {
    "scheme": "exact",
    "network": "base-sepolia",
    "maxAmountRequired": "1000",
    "resource": "https://target.example/resource",
    "description": "Test resource",
    "mimeType": "application/json",
    "payTo": "0x000000000000000000000000000000000000dEaD",
    "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "maxTimeoutSeconds": 60,
    "extra": {"name": "USD Coin", "version": "2"},
}


@pytest.mark.asyncio
@respx.mock
async def test_x402_client_handshakes_then_returns_resource() -> None:
    account = Account.create()

    challenge_route = respx.get("https://target.example/resource").mock(
        side_effect=[
            httpx.Response(
                402,
                json={"x402Version": 1, "accepts": [SAMPLE_REQUIREMENTS]},
            ),
            httpx.Response(
                200,
                headers={
                    "x-payment-response": base64.b64encode(
                        json.dumps(
                            {
                                "success": True,
                                "transaction": "0x" + "ab" * 32,
                                "network": "base-sepolia",
                                "payer": account.address,
                            }
                        ).encode()
                    ).decode()
                },
                json={"ok": True},
            ),
        ]
    )

    async with X402Client(
        account=account,
        attribution_headers={"User-Agent": "Spieon-Pentest/1.0 (+spieon.eth)"},
    ) as client:
        result = await client.request("GET", "https://target.example/resource")

    assert result.status_code == 200
    assert result.transaction == "0x" + "ab" * 32
    assert result.payment_response is not None
    assert result.payment_response.success is True

    second_call = challenge_route.calls[1].request
    header_value = second_call.headers.get("x-payment")
    assert header_value, "second request should carry an X-Payment header"
    decoded = json.loads(base64.b64decode(header_value).decode())
    assert decoded["scheme"] == "exact"
    assert decoded["network"] == "base-sepolia"
    assert decoded["payload"]["authorization"]["from"] == account.address
    assert decoded["payload"]["authorization"]["to"] == SAMPLE_REQUIREMENTS["payTo"]
    assert decoded["payload"]["authorization"]["value"] == "1000"
    assert decoded["payload"]["signature"].startswith("0x")
    assert second_call.headers["user-agent"].startswith("Spieon-Pentest")


@pytest.mark.asyncio
@respx.mock
async def test_x402_client_passes_through_non_402() -> None:
    account = Account.create()
    respx.get("https://target.example/free").mock(
        return_value=httpx.Response(200, json={"hello": "world"})
    )

    async with X402Client(account=account) as client:
        result = await client.request("GET", "https://target.example/free")

    assert result.status_code == 200
    assert result.payment_response is None
    assert result.used_payment is None
