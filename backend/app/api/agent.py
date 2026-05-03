from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.chain import ens as ens_lookup
from app.chain.client import (
    agent_address as resolve_agent_address,
)
from app.chain.client import (
    get_balance_eth,
    get_usdc_balance,
)
from app.config import get_settings
from app.db import get_session
from app.models.finding import Finding
from app.models.heuristic import Heuristic
from app.models.scan import Scan, ScanStatus

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/stats")
async def stats(session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    settings = get_settings()
    scan_count = (
        await session.execute(select(func.count()).select_from(Scan))
    ).scalar_one()
    finding_count = (
        await session.execute(select(func.count()).select_from(Finding))
    ).scalar_one()
    heuristic_count = (
        await session.execute(
            select(func.count()).select_from(Heuristic).where(
                Heuristic.eas_attestation_uid.isnot(None)
            )
        )
    ).scalar_one()
    spent_total = (
        await session.execute(select(func.coalesce(func.sum(Scan.spent_usdc), 0)))
    ).scalar_one()
    completed_count = (
        await session.execute(
            select(func.count()).select_from(Scan).where(Scan.status == ScanStatus.done.value)
        )
    ).scalar_one()

    address: str | None = None
    eth_balance: str | None = None
    usdc_balance: str | None = None
    if settings.agent_private_key or settings.agent_address:
        try:
            address = resolve_agent_address()
        except Exception:
            address = settings.agent_address or None
    if address:
        try:
            eth_balance = format(await get_balance_eth(address), "f")
        except Exception:
            eth_balance = None
        try:
            usdc_balance = format(await get_usdc_balance(address), "f")
        except Exception:
            usdc_balance = None

    ens_name = ens_lookup.configured_name()
    primary_ens: str | None = None
    ens_avatar: str | None = None
    if address:
        primary_ens = await ens_lookup.lookup_name(address)
    if ens_name:
        ens_avatar = await ens_lookup.resolve_text(ens_name, "avatar")

    return {
        "address": address,
        "ens_name": ens_name,
        "ens_primary_name": primary_ens,
        "ens_avatar": ens_avatar,
        "ens_chain_id": settings.ens_chain_id if ens_name else None,
        "scans": int(scan_count),
        "scans_completed": int(completed_count),
        "findings": int(finding_count),
        "heuristics_attested": int(heuristic_count),
        "spent_usdc": str(Decimal(spent_total)),
        "balances": {"eth": eth_balance, "usdc": usdc_balance},
        "as_of": datetime.now(UTC).isoformat(),
    }
