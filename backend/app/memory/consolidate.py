from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.memory import MemoryEvent, MemoryItem, MemoryTier


@dataclass(slots=True)
class ConsolidationReport:
    promoted_to_l2: int = 0
    promoted_to_l3: int = 0
    dropped_l2: int = 0


async def _l1_to_l2(session: AsyncSession, *, older_than: datetime) -> int:
    stmt = (
        select(MemoryEvent)
        .where(MemoryEvent.created_at < older_than)
        .order_by(MemoryEvent.created_at.asc())
    )
    events = list((await session.execute(stmt)).scalars().all())
    if not events:
        return 0

    buckets: dict[tuple[str | None, str | None], list[MemoryEvent]] = defaultdict(list)
    for e in events:
        buckets[(e.target_type, e.probe_class)].append(e)

    promoted = 0
    for (target_type, probe_class), bucket in buckets.items():
        snippet = bucket[-1].content
        summary = (
            f"{len(bucket)} L1 events about target_type={target_type}"
            f" probe_class={probe_class}: ...{snippet[-160:]}"
        )
        item = MemoryItem(
            tier=MemoryTier.working,
            content=summary,
            source_event_ids=[str(e.id) for e in bucket],
            target_type=target_type,
            probe_class=probe_class,
            usefulness_score=0,
            cycles_unused=0,
            retrieval_count=0,
        )
        session.add(item)
        promoted += 1

    event_ids = [e.id for e in events]
    await session.execute(delete(MemoryEvent).where(MemoryEvent.id.in_(event_ids)))
    return promoted


async def _l2_to_l3(session: AsyncSession, *, threshold: int) -> int:
    stmt = (
        select(MemoryItem)
        .where(MemoryItem.tier == MemoryTier.working.value)
        .where(MemoryItem.usefulness_score >= threshold)
    )
    items = list((await session.execute(stmt)).scalars().all())
    for item in items:
        item.tier = MemoryTier.longterm
        item.cycles_unused = 0
        session.add(item)
    return len(items)


async def _drop_stale_l2(session: AsyncSession, *, max_unused: int) -> int:
    stmt = (
        select(MemoryItem.id)
        .where(MemoryItem.tier == MemoryTier.working.value)
        .where(MemoryItem.cycles_unused >= max_unused)
    )
    ids = list((await session.execute(stmt)).scalars().all())
    if not ids:
        return 0
    await session.execute(delete(MemoryItem).where(MemoryItem.id.in_(ids)))
    return len(ids)


async def consolidate(
    session: AsyncSession,
    *,
    l1_age_days: int = 7,
    promote_threshold: int = 3,
    drop_max_unused: int = 5,
) -> ConsolidationReport:
    older_than = datetime.now(UTC) - timedelta(days=l1_age_days)
    report = ConsolidationReport()
    report.promoted_to_l2 = await _l1_to_l2(session, older_than=older_than)
    report.promoted_to_l3 = await _l2_to_l3(session, threshold=promote_threshold)
    report.dropped_l2 = await _drop_stale_l2(session, max_unused=drop_max_unused)
    await session.commit()
    return report
