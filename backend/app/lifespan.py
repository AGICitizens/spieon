from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import select

from app.chain.contracts import register_native_probes
from app.db import get_sessionmaker
from app.models.scan import Scan, ScanStatus
from app.workflow.runner import start_scan_workflow

log = logging.getLogger(__name__)


async def _register_probes_safely() -> None:
    try:
        results = await register_native_probes()
    except Exception:
        log.exception("native probe registration raised; continuing")
        return
    registered = [k for k, v in results.items() if v and not str(v).startswith("error")]
    if registered:
        log.info("registered %d native probes on chain: %s", len(registered), registered)


async def _resume_running_scans() -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        result = await session.execute(
            select(Scan).where(Scan.status == ScanStatus.running.value)
        )
        rows = list(result.scalars().all())
    for scan in rows:
        log.info("resuming scan %s after restart", scan.id)
        start_scan_workflow(scan.id, scan.target_url, scan.budget_usdc)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await _register_probes_safely()
    try:
        await _resume_running_scans()
    except Exception:
        log.exception("failed to resume running scans on startup")
    yield
