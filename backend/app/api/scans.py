from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.schemas import NarrationEventRead, ScanCreate, ScanRead
from app.db import get_session
from app.models.narration import NarrationEvent
from app.models.scan import Scan, ScanStatus
from app.workflow.runner import start_scan_workflow

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("", response_model=ScanRead, status_code=status.HTTP_201_CREATED)
async def create_scan(
    payload: ScanCreate,
    session: AsyncSession = Depends(get_session),
) -> Scan:
    if not payload.consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="consent must be granted before a scan can run",
        )

    scan = Scan(
        target_url=payload.target_url,
        operator_address=payload.operator_address,
        recipient_pubkey=payload.recipient_pubkey,
        budget_usdc=payload.budget_usdc,
        bounty_usdc=payload.bounty_usdc,
        consent_at=datetime.now(UTC),
        status=ScanStatus.pending,
    )
    session.add(scan)
    await session.commit()
    await session.refresh(scan)

    start_scan_workflow(scan.id, scan.target_url, scan.budget_usdc)
    return scan


@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan(
    scan_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Scan:
    result = await session.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scan not found")
    return scan


@router.get("", response_model=list[ScanRead])
async def list_scans(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> list[Scan]:
    result = await session.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(min(limit, 200))
    )
    return list(result.scalars().all())


@router.get("/{scan_id}/narration", response_model=list[NarrationEventRead])
async def list_scan_narration(
    scan_id: uuid.UUID,
    limit: int = 200,
    session: AsyncSession = Depends(get_session),
) -> list[NarrationEvent]:
    scan_result = await session.execute(select(Scan.id).where(Scan.id == scan_id))
    if scan_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scan not found")

    result = await session.execute(
        select(NarrationEvent)
        .where(NarrationEvent.scan_id == scan_id)
        .order_by(NarrationEvent.created_at.asc())
        .limit(min(limit, 500))
    )
    return list(result.scalars().all())
