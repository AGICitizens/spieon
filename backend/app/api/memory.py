from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db import get_session
from app.models.heuristic import Heuristic

router = APIRouter(prefix="/memory", tags=["memory"])


class HeuristicRead(BaseModel):
    id: uuid.UUID
    heuristic_key: str
    version: int
    rule: str
    target_type: str | None
    probe_class: str | None
    success_count: int
    sample_size: int
    success_rate: float
    owasp_id: str | None
    atlas_technique_id: str | None
    content_hash: str
    eas_attestation_uid: str | None
    attested_at: datetime | None
    created_at: datetime


@router.get("/heuristics", response_model=list[HeuristicRead])
async def list_heuristics(
    target_type: str | None = None,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[HeuristicRead]:
    stmt = select(Heuristic).order_by(
        Heuristic.success_rate.desc(),
        Heuristic.sample_size.desc(),
        Heuristic.created_at.desc(),
    )
    if target_type is not None:
        stmt = stmt.where(Heuristic.target_type == target_type)
    stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        HeuristicRead(
            id=row.id,
            heuristic_key=row.heuristic_key,
            version=row.version,
            rule=row.rule,
            target_type=row.target_type,
            probe_class=row.probe_class,
            success_count=row.success_count,
            sample_size=row.sample_size,
            success_rate=row.success_rate,
            owasp_id=row.owasp_id,
            atlas_technique_id=row.atlas_technique_id,
            content_hash=row.content_hash,
            eas_attestation_uid=row.eas_attestation_uid,
            attested_at=row.attested_at,
            created_at=row.created_at,
        )
        for row in rows
    ]
