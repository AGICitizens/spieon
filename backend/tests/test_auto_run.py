from __future__ import annotations

import asyncio
import uuid

import pyrage
import pytest
from httpx import AsyncClient

from app.db import get_sessionmaker
from app.models.scan import Scan, ScanStatus
from app.workflow.runner import is_running, wait_for


@pytest.mark.asyncio
async def test_post_scan_auto_runs_workflow_to_done(client: AsyncClient) -> None:
    identity = pyrage.x25519.Identity.generate()
    recipient = str(identity.to_public())

    response = await client.post(
        "/scans",
        json={
            "target_url": "http://target.invalid/auto",
            "operator_address": "0xtest",
            "recipient_pubkey": recipient,
            "budget_usdc": "0.5",
            "bounty_usdc": "1",
            "consent": True,
        },
    )
    assert response.status_code == 201
    scan_id = uuid.UUID(response.json()["id"])

    for _ in range(60):
        if not is_running(scan_id):
            break
        await asyncio.sleep(0.25)
    await wait_for(scan_id)

    sm = get_sessionmaker()
    async with sm() as session:
        scan = await session.get(Scan, scan_id)
    assert scan is not None
    assert scan.status in {ScanStatus.done, ScanStatus.failed}
    assert scan.started_at is not None
    assert scan.completed_at is not None
