from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.realtime import narration_broker


def test_ws_returns_404_for_unknown_scan() -> None:
    client = TestClient(app)
    bogus = uuid.uuid4()
    with client.websocket_connect(f"/ws/scans/{bogus}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"


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
