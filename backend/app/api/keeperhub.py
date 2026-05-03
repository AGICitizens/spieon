from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.keeperhub import KeeperHubError, get_keeperhub_client
from app.keeperhub.workflows import payout_on_attest_template

log = logging.getLogger(__name__)
router = APIRouter(prefix="/keeperhub", tags=["keeperhub"])


class InstallBody(BaseModel):
    callback_url: str | None = Field(default=None, max_length=512)
    discord_webhook: str | None = Field(default=None, max_length=512)
    name: str = Field(default="spieon.finding.payout", max_length=128)


class InstallResult(BaseModel):
    workflow_id: str
    workflow: dict[str, Any]
    note: str


@router.post("/install", response_model=InstallResult, status_code=201)
async def install_payout_workflow(body: InstallBody) -> InstallResult:
    client = get_keeperhub_client()
    if not client.configured:
        raise HTTPException(status_code=400, detail="KEEPERHUB_API_KEY not set")

    spec = payout_on_attest_template(
        name=body.name,
        callback_url=body.callback_url,
        discord_webhook=body.discord_webhook,
    )
    try:
        created = await client.create_workflow(spec)
    except KeeperHubError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    workflow_id = (
        created.get("id") or created.get("workflowId") or created.get("workflow_id")
    )
    if not workflow_id:
        raise HTTPException(
            status_code=502,
            detail=f"keeperhub did not return a workflow id: {created}",
        )

    return InstallResult(
        workflow_id=str(workflow_id),
        workflow=created,
        note=(
            f"Set KEEPERHUB_PAYOUT_WORKFLOW_ID={workflow_id} in .env so payouts "
            "are routed through this workflow."
        ),
    )


class StatusResponse(BaseModel):
    configured: bool
    api_key_present: bool
    workflow_id: str | None
    base_url: str


@router.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    s = get_settings()
    return StatusResponse(
        configured=bool(s.keeperhub_api_key and s.keeperhub_payout_workflow_id),
        api_key_present=bool(s.keeperhub_api_key),
        workflow_id=s.keeperhub_payout_workflow_id or None,
        base_url=s.keeperhub_base_url,
    )


@router.get("/runs")
async def list_runs(limit: int = 25) -> dict[str, Any]:
    s = get_settings()
    if not s.keeperhub_payout_workflow_id:
        raise HTTPException(
            status_code=400, detail="KEEPERHUB_PAYOUT_WORKFLOW_ID not set"
        )
    client = get_keeperhub_client()
    if not client.configured:
        raise HTTPException(status_code=400, detail="KEEPERHUB_API_KEY not set")
    try:
        return await client.list_executions(
            s.keeperhub_payout_workflow_id, limit=min(limit, 100)
        )
    except KeeperHubError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/runs/{execution_id}")
async def get_run(execution_id: str) -> dict[str, Any]:
    client = get_keeperhub_client()
    if not client.configured:
        raise HTTPException(status_code=400, detail="KEEPERHUB_API_KEY not set")
    try:
        return await client.get_execution(execution_id)
    except KeeperHubError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
