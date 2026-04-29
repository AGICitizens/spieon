from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.heuristic import Heuristic
from app.models.memory import MemoryItem, MemoryTier


@dataclass(slots=True)
class RecallHit:
    kind: str
    id: str
    content: str
    target_type: str | None
    probe_class: str | None
    extra: dict[str, Any]


async def recall_items(
    session: AsyncSession,
    *,
    target_type: str | None = None,
    probe_class: str | None = None,
    tiers: tuple[MemoryTier, ...] = (MemoryTier.working, MemoryTier.longterm),
    limit: int = 10,
) -> list[MemoryItem]:
    stmt = select(MemoryItem).where(MemoryItem.tier.in_([t.value for t in tiers]))
    if target_type is not None:
        stmt = stmt.where(MemoryItem.target_type == target_type)
    if probe_class is not None:
        stmt = stmt.where(MemoryItem.probe_class == probe_class)
    stmt = stmt.order_by(
        MemoryItem.usefulness_score.desc(),
        MemoryItem.last_retrieved.desc().nullslast(),
    ).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def recall_heuristics(
    session: AsyncSession,
    *,
    target_type: str | None = None,
    probe_class: str | None = None,
    limit: int = 10,
) -> list[Heuristic]:
    stmt = select(Heuristic)
    if target_type is not None:
        stmt = stmt.where(Heuristic.target_type == target_type)
    if probe_class is not None:
        stmt = stmt.where(Heuristic.probe_class == probe_class)
    stmt = stmt.order_by(
        Heuristic.success_rate.desc(),
        Heuristic.sample_size.desc(),
    ).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def recall(
    session: AsyncSession,
    *,
    target_type: str | None = None,
    probe_class: str | None = None,
    limit: int = 10,
) -> list[RecallHit]:
    heuristics = await recall_heuristics(
        session, target_type=target_type, probe_class=probe_class, limit=limit
    )
    items = await recall_items(
        session, target_type=target_type, probe_class=probe_class, limit=limit
    )

    hits: list[RecallHit] = []
    for h in heuristics:
        hits.append(
            RecallHit(
                kind="heuristic",
                id=str(h.id),
                content=h.rule,
                target_type=h.target_type,
                probe_class=h.probe_class,
                extra={
                    "version": h.version,
                    "success_rate": h.success_rate,
                    "sample_size": h.sample_size,
                    "owasp_id": h.owasp_id,
                    "atlas_technique_id": h.atlas_technique_id,
                    "eas_attestation_uid": h.eas_attestation_uid,
                },
            )
        )
    for i in items:
        hits.append(
            RecallHit(
                kind="memory_item",
                id=str(i.id),
                content=i.content,
                target_type=i.target_type,
                probe_class=i.probe_class,
                extra={
                    "tier": str(i.tier),
                    "usefulness_score": i.usefulness_score,
                    "cycles_unused": i.cycles_unused,
                    "retrieval_count": i.retrieval_count,
                },
            )
        )
    return hits[:limit]
