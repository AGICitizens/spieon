from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.db import get_sessionmaker
from app.main import app
from app.models.narration import NarrationEvent, Phase
from app.models.scan import Scan, ScanStatus
from app.realtime import narration_broker


def test_ws_returns_404_for_unknown_scan() -> None:
    client = TestClient(app)
    bogus = uuid.uuid4()
    with client.websocket_connect(f"/ws/scans/{bogus}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"


@pytest.mark.asyncio
async def test_scan_narration_history_endpoint_returns_recorded_events(client) -> None:
    sessionmaker = get_sessionmaker()
    scan_id = uuid.uuid4()
    async with sessionmaker() as session:
        scan = Scan(
            id=scan_id,
            target_url="https://example.test",
            operator_address="0xabc",
            recipient_pubkey="age1test",
            budget_usdc="0",
            bounty_usdc="0",
            status=ScanStatus.done,
            consent_at=datetime.now(UTC),
        )
        session.add(scan)
        session.add(
            NarrationEvent(
                scan_id=scan_id,
                phase=Phase.recon,
                success_signal=True,
                content="Inspecting target.",
            )
        )
        await session.commit()

    response = await client.get(f"/scans/{scan_id}/narration")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["phase"] == "recon"
    assert body[0]["content"] == "Inspecting target."


@pytest.mark.asyncio
async def test_broker_delivers_to_subscribers() -> None:
    scan_id = uuid.uuid4()
    queue = await narration_broker.subscribe(scan_id)
    try:
        delivered = await narration_broker.publish(
            scan_id, {"phase": "recon", "content": "looking"}
        )
        assert delivered == 1
        msg = await queue.get()
        assert msg["phase"] == "recon"

        other = uuid.uuid4()
        delivered_other = await narration_broker.publish(other, {"phase": "plan"})
        assert delivered_other == 0
    finally:
        await narration_broker.unsubscribe(scan_id, queue)


@pytest.mark.asyncio
async def test_broker_drops_when_queue_full() -> None:
    scan_id = uuid.uuid4()
    queue = await narration_broker.subscribe(scan_id)
    try:
        for i in range(queue.maxsize):
            await narration_broker.publish(scan_id, {"i": i})
        delivered = await narration_broker.publish(scan_id, {"i": 9999})
        assert delivered == 0
    finally:
        await narration_broker.unsubscribe(scan_id, queue)
