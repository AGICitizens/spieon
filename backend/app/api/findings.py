from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db import get_session
from app.models.finding import Finding
from app.models.scan import Scan

router = APIRouter(prefix="/findings", tags=["findings"])


class FindingRead(BaseModel):
    id: uuid.UUID
    scan_id: uuid.UUID
    target_url: str | None
    severity: str
    title: str
    summary: str
    module_hash: str
    cost_usdc: Decimal
    owasp_id: str | None
    atlas_technique_id: str | None
    maestro_id: str | None
    encrypted_bundle_uri: str | None
    ciphertext_sha256: str | None
    eas_attestation_uid: str | None
    attested_at: datetime | None
    created_at: datetime


def _serialize(row: Finding, scan: Scan | None) -> FindingRead:
    severity = (
        row.severity.value if hasattr(row.severity, "value") else str(row.severity)
    )
    return FindingRead(
        id=row.id,
        scan_id=row.scan_id,
        target_url=scan.target_url if scan else None,
        severity=severity,
        title=row.title,
        summary=row.summary,
        module_hash=row.module_hash,
        cost_usdc=row.cost_usdc,
        owasp_id=row.owasp_id,
        atlas_technique_id=row.atlas_technique_id,
        maestro_id=row.maestro_id,
        encrypted_bundle_uri=row.encrypted_bundle_uri,
        ciphertext_sha256=row.ciphertext_sha256,
        eas_attestation_uid=row.eas_attestation_uid,
        attested_at=row.attested_at,
        created_at=row.created_at,
    )


@router.get("", response_model=list[FindingRead])
async def list_findings(
    limit: int = Query(default=50, le=200),
    scan_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[FindingRead]:
    stmt = (
        select(Finding, Scan)
        .join(Scan, Scan.id == Finding.scan_id, isouter=True)
        .order_by(Finding.created_at.desc())
        .limit(limit)
    )
    if scan_id is not None:
        stmt = stmt.where(Finding.scan_id == scan_id)
    result = await session.execute(stmt)
    return [_serialize(row, scan) for row, scan in result.all()]
