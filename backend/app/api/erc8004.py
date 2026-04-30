from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.chain.client import agent_address as resolve_agent_address
from app.config import get_settings
from app.db import get_session
from app.models.feedback import OperatorFeedback
from app.models.scan import Scan

router = APIRouter(tags=["erc8004"])


def _agent_address_safe() -> str | None:
    settings = get_settings()
    if settings.agent_private_key or settings.agent_address:
        try:
            return resolve_agent_address()
        except Exception:
            return settings.agent_address or None
    return None


@router.get("/.well-known/agent.json")
async def agent_descriptor() -> dict[str, Any]:
    settings = get_settings()
    address = _agent_address_safe()
    return {
        "schemaVersion": "erc8004.identity.v0",
        "name": "Spieon",
        "description": (
            "Autonomous security agent for the agent economy. Pen-tests x402 endpoints "
            "and MCP servers, attests findings on Base Sepolia, and pays bounties to "
            "module authors."
        ),
        "website": "https://spieon.eth",
        "basename": "spieon.base.eth",
        "agentAddress": address,
        "chain": {
            "id": settings.base_sepolia_chain_id,
            "name": "base-sepolia",
            "rpcUrl": settings.base_sepolia_rpc_url,
        },
        "capabilities": [
            {
                "id": "x402-replay-attack",
                "label": "x402 payment replay detection",
                "owasp": "API07",
                "atlas": "AML.T0049",
            },
            {
                "id": "x402-payment-retry-bypass",
                "label": "x402 verifier validation",
                "owasp": "API01",
                "atlas": "AML.T0049",
            },
            {
                "id": "x402-settlement-skip",
                "label": "x402 settlement integrity",
                "owasp": "API01",
                "atlas": "AML.T0049",
            },
            {
                "id": "mcp-tool-description-injection",
                "label": "MCP tool-description injection",
                "owasp": "LLM01",
                "atlas": "AML.T0051",
            },
            {
                "id": "mcp-schema-poisoning",
                "label": "MCP schema poisoning",
                "owasp": "LLM05",
                "atlas": "AML.T0051",
            },
        ],
        "endpoints": {
            "identity": "/.well-known/agent.json",
            "stats": "/agent/stats",
            "feedback": "/agent/feedback",
            "scans": "/scans",
            "findings": "/findings",
            "modules": "/modules",
        },
        "registries": {
            "moduleRegistry": settings.module_registry_address or None,
            "bountyPool": settings.bounty_pool_address or None,
            "easSchemaUid": settings.eas_schema_uid or None,
        },
    }


class FeedbackBody(BaseModel):
    scan_id: uuid.UUID
    operator_address: str = Field(min_length=1, max_length=64)
    score: int = Field(ge=1, le=5)
    rationale: str | None = Field(default=None, max_length=2048)


class FeedbackRead(BaseModel):
    id: uuid.UUID
    scan_id: uuid.UUID
    operator_address: str
    score: int
    rationale: str | None
    onchain_tx_hash: str | None
    created_at: datetime


@router.post("/agent/feedback", response_model=FeedbackRead, status_code=201)
async def submit_feedback(
    body: FeedbackBody,
    session: AsyncSession = Depends(get_session),
) -> FeedbackRead:
    scan = (
        await session.execute(select(Scan).where(Scan.id == body.scan_id))
    ).scalar_one_or_none()
    if scan is None:
        raise HTTPException(status_code=404, detail="scan not found")

    row = OperatorFeedback(
        scan_id=body.scan_id,
        operator_address=body.operator_address,
        score=body.score,
        rationale=body.rationale,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return FeedbackRead(
        id=row.id,
        scan_id=row.scan_id,
        operator_address=row.operator_address,
        score=row.score,
        rationale=row.rationale,
        onchain_tx_hash=row.onchain_tx_hash,
        created_at=row.created_at,
    )


@router.get("/agent/feedback", response_model=list[FeedbackRead])
async def list_feedback(
    scan_id: uuid.UUID | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> list[FeedbackRead]:
    stmt = select(OperatorFeedback).order_by(OperatorFeedback.created_at.desc())
    if scan_id is not None:
        stmt = stmt.where(OperatorFeedback.scan_id == scan_id)
    stmt = stmt.limit(min(limit, 200))
    rows = (await session.execute(stmt)).scalars().all()
    return [
        FeedbackRead(
            id=row.id,
            scan_id=row.scan_id,
            operator_address=row.operator_address,
            score=row.score,
            rationale=row.rationale,
            onchain_tx_hash=row.onchain_tx_hash,
            created_at=row.created_at,
        )
        for row in rows
    ]
