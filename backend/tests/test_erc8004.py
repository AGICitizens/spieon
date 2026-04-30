from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.db import get_sessionmaker
from app.models.scan import Scan, ScanStatus


async def _seed_scan() -> uuid.UUID:
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
        return scan.id


@pytest.mark.asyncio
async def test_agent_descriptor_carries_capabilities(client: AsyncClient) -> None:
    response = await client.get("/.well-known/agent.json")
    assert response.status_code == 200
    body = response.json()
    assert body["schemaVersion"] == "erc8004.identity.v0"
    assert body["name"] == "Spieon"
    assert body["chain"]["id"] == 84532
    capability_ids = {c["id"] for c in body["capabilities"]}
    assert {
        "x402-replay-attack",
        "mcp-schema-poisoning",
        "mcp-tool-description-injection",
    } <= capability_ids
    assert body["endpoints"]["feedback"] == "/agent/feedback"


@pytest.mark.asyncio
async def test_feedback_round_trip(client: AsyncClient) -> None:
    scan_id = await _seed_scan()

    create = await client.post(
        "/agent/feedback",
        json={
            "scan_id": str(scan_id),
            "operator_address": "0xOperator",
            "score": 5,
            "rationale": "Great scan, found a real bug.",
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["score"] == 5
    assert body["operator_address"] == "0xOperator"

    listing = await client.get(f"/agent/feedback?scan_id={scan_id}")
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == 1
    assert items[0]["rationale"].startswith("Great scan")


@pytest.mark.asyncio
async def test_feedback_rejects_unknown_scan(client: AsyncClient) -> None:
    bogus = uuid.uuid4()
    response = await client.post(
        "/agent/feedback",
        json={
            "scan_id": str(bogus),
            "operator_address": "0xOperator",
            "score": 4,
        },
    )
    assert response.status_code == 404
