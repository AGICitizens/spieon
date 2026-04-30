from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.db import get_sessionmaker
from app.models.finding import Finding, Severity
from app.models.scan import Scan, ScanStatus


async def _seed_finding(*, with_attestation: bool = True, severity: Severity = Severity.high) -> tuple[uuid.UUID, uuid.UUID]:
    sm = get_sessionmaker()
    async with sm() as session:
        scan = Scan(
            target_url="https://target.example/x",
            operator_address="0xtest",
            recipient_pubkey="pk",
            consent_at=datetime.now(UTC),
            status=ScanStatus.pending,
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)

        finding = Finding(
            scan_id=scan.id,
            severity=severity,
            title="payout test finding",
            summary="payout test",
            module_hash="0x" + "ab" * 32,
            cost_usdc=Decimal("0.1"),
            dedup_key="payout-test-" + uuid.uuid4().hex,
            eas_attestation_uid=("0x" + "cd" * 32) if with_attestation else None,
            attested_at=datetime.now(UTC) if with_attestation else None,
        )
        session.add(finding)
        await session.commit()
        await session.refresh(finding)
        return scan.id, finding.id


@pytest.mark.asyncio
async def test_payout_stub_path_when_pool_unconfigured(client: AsyncClient) -> None:
    _, finding_id = await _seed_finding()
    response = await client.post(
        f"/findings/{finding_id}/payout",
        json={"recipient": "0xModuleAuthor", "amount_usdc": "1.5"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["onchain"] is False
    assert body["tx_hash"].startswith("0x")
    assert body["recipient"] == "0xModuleAuthor"
    assert Decimal(body["amount_usdc"]) == Decimal("1.5")


@pytest.mark.asyncio
async def test_payout_rejects_amount_above_severity_cap(client: AsyncClient) -> None:
    _, finding_id = await _seed_finding(severity=Severity.high)
    response = await client.post(
        f"/findings/{finding_id}/payout",
        json={"recipient": "0xModuleAuthor", "amount_usdc": "5"},
    )
    assert response.status_code == 400
    assert "exceeds severity cap" in response.json()["detail"]


@pytest.mark.asyncio
async def test_payout_requires_attestation(client: AsyncClient) -> None:
    _, finding_id = await _seed_finding(with_attestation=False)
    response = await client.post(
        f"/findings/{finding_id}/payout",
        json={"recipient": "0xModuleAuthor", "amount_usdc": "1"},
    )
    assert response.status_code == 400
    assert "attestation" in response.json()["detail"]


@pytest.mark.asyncio
async def test_payout_blocks_double_pay(client: AsyncClient) -> None:
    _, finding_id = await _seed_finding()
    first = await client.post(
        f"/findings/{finding_id}/payout",
        json={"recipient": "0xModuleAuthor", "amount_usdc": "1"},
    )
    assert first.status_code == 200
    second = await client.post(
        f"/findings/{finding_id}/payout",
        json={"recipient": "0xModuleAuthor", "amount_usdc": "1"},
    )
    assert second.status_code == 409
