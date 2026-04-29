from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from eth_abi import decode as abi_decode

from app.chain.eas import (
    SCHEMA_SOLIDITY_TYPES,
    FindingAttestationPayload,
    attest_finding,
    encode_finding_data,
)


def _payload() -> FindingAttestationPayload:
    return FindingAttestationPayload(
        scan_id=uuid.UUID("11111111-2222-3333-4444-555555555555"),
        target="https://target.example/mcp",
        severity="high",
        module_hash="0x" + "ab" * 32,
        cost_usdc=Decimal("0.250000"),
        encrypted_bundle_uri="ipfs://bafy...",
        ciphertext_sha256="0x" + "cd" * 32,
        owasp_id="LLM01",
        atlas_technique_id="AML.T0051",
        maestro_id="M-99",
    )


def test_encode_finding_data_roundtrips_through_eth_abi() -> None:
    payload = _payload()
    encoded = encode_finding_data(payload)
    decoded = abi_decode(list(SCHEMA_SOLIDITY_TYPES), encoded)

    assert decoded[0].hex().endswith(payload.scan_id.hex)
    assert decoded[1] == payload.target
    assert decoded[2] == 2  # severity high
    assert decoded[3].hex() == "ab" * 32
    assert decoded[4] == 250_000
    assert decoded[5] == payload.encrypted_bundle_uri
    assert decoded[6].hex() == "cd" * 32
    assert decoded[7] == "LLM01"
    assert decoded[8] == "AML.T0051"
    assert decoded[9] == "M-99"


@pytest.mark.asyncio
async def test_attest_finding_falls_back_to_stub_when_unconfigured() -> None:
    payload = _payload()
    uid = await attest_finding(payload)
    assert uid.startswith("0x")
    assert len(uid) == 66
