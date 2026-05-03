from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.chain import (
    PayoutRequest,
    attestation_already_paid,
    severity_cap_usdc,
    submit_payout,
)
from app.config import get_settings
from app.db import get_session
from app.keeperhub import KeeperHubError, get_keeperhub_client
from app.keeperhub.client import encode_payout_payload
from app.models.finding import Finding, Severity

log = __import__("logging").getLogger(__name__)

router = APIRouter(prefix="/findings", tags=["payouts"])


DEFAULT_SEVERITY_CAPS_USDC: dict[Severity, Decimal] = {
    Severity.critical: Decimal("5"),
    Severity.high: Decimal("2"),
    Severity.medium: Decimal("0.5"),
    Severity.low: Decimal("0.1"),
}


class PayoutBody(BaseModel):
    recipient: str = Field(min_length=1, max_length=64)
    amount_usdc: Decimal = Field(gt=Decimal("0"))


class PayoutResult(BaseModel):
    finding_id: uuid.UUID
    recipient: str
    amount_usdc: Decimal
    tx_hash: str
    paid_at: datetime
    onchain: bool
    keeperhub_execution_id: str | None = None
    keeperhub_status: str | None = None
    keeperhub_paid: bool = False


def _stub_tx_hash(finding_id: uuid.UUID, recipient: str, amount: Decimal) -> str:
    seed = f"{finding_id}|{recipient}|{amount}|{datetime.now(UTC).isoformat()}"
    return "0x" + hashlib.sha256(seed.encode()).hexdigest()


def _bounty_pool_configured() -> bool:
    settings = get_settings()
    return bool(settings.bounty_pool_address) and bool(settings.agent_private_key)


async def _resolve_cap(severity: Severity) -> Decimal:
    if _bounty_pool_configured():
        try:
            return await severity_cap_usdc(severity)
        except Exception:
            pass
    return DEFAULT_SEVERITY_CAPS_USDC[severity]


@router.post(
    "/{finding_id}/payout",
    response_model=PayoutResult,
    status_code=status.HTTP_200_OK,
)
async def pay_finding(
    finding_id: uuid.UUID,
    body: PayoutBody,
    session: AsyncSession = Depends(get_session),
) -> PayoutResult:
    result = await session.execute(select(Finding).where(Finding.id == finding_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="finding not found")
    if row.bounty_tx_hash:
        raise HTTPException(status_code=409, detail="finding already paid")
    if row.eas_attestation_uid is None:
        raise HTTPException(
            status_code=400, detail="finding has no attestation; attest before paying"
        )

    severity = (
        row.severity
        if isinstance(row.severity, Severity)
        else Severity(str(row.severity))
    )
    cap = await _resolve_cap(severity)
    if body.amount_usdc > cap:
        raise HTTPException(
            status_code=400,
            detail=f"amount {body.amount_usdc} exceeds severity cap {cap} for {severity.value}",
        )

    if _bounty_pool_configured():
        try:
            already = await attestation_already_paid(row.eas_attestation_uid)
            if already:
                raise HTTPException(
                    status_code=409,
                    detail="attestation already consumed by the bounty pool",
                )
        except HTTPException:
            raise
        except Exception:
            pass

        try:
            tx_hash = await submit_payout(
                PayoutRequest(
                    scan_id=row.scan_id,
                    module_hash=row.module_hash,
                    attestation_uid=row.eas_attestation_uid,
                    severity=severity,
                    amount_usdc=body.amount_usdc,
                    recipient=body.recipient,
                )
            )
            onchain = True
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail=f"payout failed on chain: {exc}"
            ) from exc
    else:
        tx_hash = _stub_tx_hash(finding_id, body.recipient, body.amount_usdc)
        onchain = False

    paid_at = datetime.now(UTC)
    row.bounty_recipient = body.recipient
    row.bounty_amount_usdc = body.amount_usdc
    row.bounty_tx_hash = tx_hash
    row.bounty_paid_at = paid_at
    session.add(row)
    await session.commit()

    kh_execution_id: str | None = None
    kh_status: str | None = None
    kh_paid = False
    settings = get_settings()
    workflow_id = settings.keeperhub_payout_workflow_id
    if workflow_id:
        try:
            client = get_keeperhub_client()
            payload = encode_payout_payload(
                finding_id=str(finding_id),
                recipient=body.recipient,
                amount_usdc=str(body.amount_usdc),
                severity=severity.value,
                attestation_uid=row.eas_attestation_uid,
                tx_hash=tx_hash,
            )
            result = await client.execute_workflow(workflow_id, payload)
            kh_execution_id = result.execution_id
            kh_status = result.status
            kh_paid = result.paid
        except KeeperHubError as exc:
            log.warning("keeperhub workflow execution failed: %s", exc)

    return PayoutResult(
        finding_id=finding_id,
        recipient=body.recipient,
        amount_usdc=body.amount_usdc,
        tx_hash=tx_hash,
        paid_at=paid_at,
        onchain=onchain,
        keeperhub_execution_id=kh_execution_id,
        keeperhub_status=kh_status,
        keeperhub_paid=kh_paid,
    )
