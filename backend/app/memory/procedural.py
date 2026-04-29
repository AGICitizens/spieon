from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.heuristic import Heuristic


def _content_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


async def _next_version(session: AsyncSession, heuristic_key: str) -> int:
    stmt = (
        select(Heuristic.version)
        .where(Heuristic.heuristic_key == heuristic_key)
        .order_by(Heuristic.version.desc())
        .limit(1)
    )
    latest = (await session.execute(stmt)).scalar_one_or_none()
    return (latest or 0) + 1


async def record_heuristic(
    session: AsyncSession,
    *,
    heuristic_key: str,
    rule: str,
    target_type: str | None,
    probe_class: str | None,
    evidence_scan_ids: list[uuid.UUID | str],
    evidence_event_ids: list[uuid.UUID | str] | None = None,
    success_count: int,
    sample_size: int,
    owasp_id: str | None = None,
    atlas_technique_id: str | None = None,
) -> Heuristic:
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if success_count < 0 or success_count > sample_size:
        raise ValueError("success_count must be in [0, sample_size]")

    version = await _next_version(session, heuristic_key)
    success_rate = success_count / sample_size

    digest_payload = {
        "heuristic_key": heuristic_key,
        "version": version,
        "rule": rule,
        "target_type": target_type,
        "probe_class": probe_class,
        "owasp_id": owasp_id,
        "atlas_technique_id": atlas_technique_id,
        "success_count": success_count,
        "sample_size": sample_size,
    }
    content_hash = _content_hash(digest_payload)

    heuristic = Heuristic(
        heuristic_key=heuristic_key,
        version=version,
        rule=rule,
        target_type=target_type,
        probe_class=probe_class,
        evidence_scan_ids=[str(i) for i in evidence_scan_ids],
        evidence_event_ids=[str(i) for i in (evidence_event_ids or [])],
        success_count=success_count,
        sample_size=sample_size,
        success_rate=success_rate,
        owasp_id=owasp_id,
        atlas_technique_id=atlas_technique_id,
        content_hash=content_hash,
    )
    session.add(heuristic)
    await session.flush()
    await session.refresh(heuristic)
    return heuristic


async def attach_attestation(
    session: AsyncSession,
    heuristic: Heuristic,
    attestation_uid: str,
) -> Heuristic:
    heuristic.eas_attestation_uid = attestation_uid
    heuristic.attested_at = datetime.now(UTC)
    session.add(heuristic)
    await session.flush()
    await session.refresh(heuristic)
    return heuristic
