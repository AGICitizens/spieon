from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.db import get_sessionmaker
from app.models.scan import Scan, ScanStatus
from app.workflow.graph import build_graph, checkpointer
from app.workflow.state import ScanState

log = logging.getLogger(__name__)

_running: dict[uuid.UUID, asyncio.Task] = {}


async def _set_status(scan_id: uuid.UUID, status: ScanStatus, *, error: str | None = None) -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        scan = await session.get(Scan, scan_id)
        if scan is None:
            return
        scan.status = status
        if status == ScanStatus.running and scan.started_at is None:
            scan.started_at = datetime.now(UTC)
        if status in {ScanStatus.done, ScanStatus.failed}:
            scan.completed_at = datetime.now(UTC)
        if error is not None:
            scan.error = error[:1000]
        session.add(scan)
        await session.commit()


async def _execute(scan_id: uuid.UUID, target_url: str, budget_usdc: Decimal) -> None:
    try:
        await _set_status(scan_id, ScanStatus.running)
        sessionmaker = get_sessionmaker()
        async with checkpointer() as saver:
            compiled = build_graph(sessionmaker).compile(checkpointer=saver)
            config = {"configurable": {"thread_id": str(scan_id)}}
            state: ScanState = {
                "scan_id": scan_id,
                "target_url": target_url,
                "budget_usdc": budget_usdc,
                "spent_usdc": Decimal("0"),
                "planned_probes": [],
                "findings": [],
                "memory_refs": [],
                "adapt_iterations": 0,
            }
            await compiled.ainvoke(state, config=config)
        await _set_status(scan_id, ScanStatus.done)
    except Exception as exc:
        log.exception("workflow failed for scan %s", scan_id)
        await _set_status(scan_id, ScanStatus.failed, error=str(exc))
    finally:
        _running.pop(scan_id, None)


def start_scan_workflow(
    scan_id: uuid.UUID, target_url: str, budget_usdc: Decimal
) -> asyncio.Task:
    if scan_id in _running and not _running[scan_id].done():
        return _running[scan_id]
    task = asyncio.create_task(_execute(scan_id, target_url, budget_usdc))
    _running[scan_id] = task
    return task


def is_running(scan_id: uuid.UUID) -> bool:
    task = _running.get(scan_id)
    return task is not None and not task.done()


async def wait_for(scan_id: uuid.UUID) -> None:
    task = _running.get(scan_id)
    if task is not None:
        await task
