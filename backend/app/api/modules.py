from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db import get_session
from app.models.finding import Finding
from app.models.module import Module
from app.probes.registry import iter_probes

router = APIRouter(prefix="/modules", tags=["modules"])


class ModuleEntry(BaseModel):
    module_hash: str
    probe_id: str | None
    author_address: str | None
    metadata_uri: str | None
    severity_cap: str
    times_used: int
    success_count: int
    findings_landed: int
    bounties_earned_usdc: Decimal
    owasp_id: str | None
    atlas_technique_id: str | None
    registered_at: datetime | None
    last_synced_at: datetime | None


@router.get("", response_model=list[ModuleEntry])
async def list_modules(
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[ModuleEntry]:
    onchain_result = await session.execute(select(Module))
    onchain_rows = list(onchain_result.scalars().all())

    counts_result = await session.execute(
        select(
            Finding.module_hash,
            func.count().label("findings_landed"),
            func.coalesce(func.sum(Finding.cost_usdc), 0).label("bounties"),
        ).group_by(Finding.module_hash)
    )
    counts: dict[str, tuple[int, Decimal]] = {}
    for module_hash, landed, bounties in counts_result.all():
        counts[module_hash] = (int(landed), Decimal(bounties))

    spec_by_hash = {spec.module_hash: spec for spec in iter_probes()}

    seen: set[str] = set()
    entries: list[ModuleEntry] = []
    for row in onchain_rows:
        landed, bounties = counts.get(row.module_hash, (0, Decimal("0")))
        spec = spec_by_hash.get(row.module_hash)
        entries.append(
            ModuleEntry(
                module_hash=row.module_hash,
                probe_id=spec.id if spec else None,
                author_address=row.author_address,
                metadata_uri=row.metadata_uri,
                severity_cap=row.severity_cap.value
                if hasattr(row.severity_cap, "value")
                else str(row.severity_cap),
                times_used=row.times_used,
                success_count=row.success_count,
                findings_landed=landed,
                bounties_earned_usdc=bounties,
                owasp_id=row.owasp_id,
                atlas_technique_id=row.atlas_technique_id,
                registered_at=row.registered_at,
                last_synced_at=row.last_synced_at,
            )
        )
        seen.add(row.module_hash)

    for spec in spec_by_hash.values():
        if spec.module_hash in seen:
            continue
        landed, bounties = counts.get(spec.module_hash, (0, Decimal("0")))
        entries.append(
            ModuleEntry(
                module_hash=spec.module_hash,
                probe_id=spec.id,
                author_address=None,
                metadata_uri=None,
                severity_cap=spec.severity_cap.value,
                times_used=0,
                success_count=0,
                findings_landed=landed,
                bounties_earned_usdc=bounties,
                owasp_id=spec.owasp_id,
                atlas_technique_id=spec.atlas_technique_id,
                registered_at=None,
                last_synced_at=None,
            )
        )

    entries.sort(key=lambda e: (-e.findings_landed, -e.success_count, e.probe_id or ""))
    return entries[:limit]


class ModuleSummary(BaseModel):
    module_hash: str
    probe_id: str
    severity_cap: str
    cost_estimate_usdc: Decimal
    owasp_id: str | None
    atlas_technique_id: str | None
    description: str
    tags: list[str]


@router.get("/registered", response_model=list[ModuleSummary])
async def list_registered_probes() -> list[ModuleSummary]:
    return [
        ModuleSummary(
            module_hash=spec.module_hash,
            probe_id=spec.id,
            severity_cap=spec.severity_cap.value,
            cost_estimate_usdc=spec.cost_estimate_usdc,
            owasp_id=spec.owasp_id,
            atlas_technique_id=spec.atlas_technique_id,
            description=spec.description,
            tags=list(spec.tags),
        )
        for spec in iter_probes()
    ]


