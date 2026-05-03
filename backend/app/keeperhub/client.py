from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx

from app.config import get_settings
from app.x402.client import X402Client, X402PaymentError

log = logging.getLogger(__name__)


class KeeperHubError(RuntimeError):
    pass


@dataclass(slots=True)
class ExecutionResult:
    execution_id: str | None
    status: str
    paid: bool
    payment_tx: str | None
    raw: dict[str, Any]


class KeeperHubClient:
    """Thin async wrapper around KeeperHub's HTTP API.

    Management calls (`create_workflow`, `list_executions`, `get_execution`) use the
    `kh_…` API key bearer auth. The `execute` call goes through `X402Client` so the
    agent pays USDC per execution — this is the integration story we're claiming.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        x402_client: X402Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        s = get_settings()
        self._api_key = api_key if api_key is not None else s.keeperhub_api_key
        self._base = (base_url or s.keeperhub_base_url).rstrip("/")
        self._x402 = x402_client
        self._timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _auth_headers(self) -> dict[str, str]:
        if not self._api_key:
            raise KeeperHubError("KEEPERHUB_API_KEY is not set")
        return {"Authorization": f"Bearer {self._api_key}"}

    async def _management(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            res = await client.request(
                method, url, headers=self._auth_headers(), json=json_body
            )
        if res.status_code >= 400:
            raise KeeperHubError(
                f"keeperhub {method} {path} failed: {res.status_code} {res.text[:300]}"
            )
        try:
            return res.json()
        except ValueError:
            return {"raw": res.text}

    async def create_workflow(self, spec: dict[str, Any]) -> dict[str, Any]:
        return await self._management("POST", "/workflows/create", json_body=spec)

    async def list_workflows(self) -> dict[str, Any]:
        return await self._management("GET", "/workflows")

    async def list_executions(self, workflow_id: str, limit: int = 25) -> dict[str, Any]:
        return await self._management(
            "GET", f"/workflow/{workflow_id}/executions?limit={limit}"
        )

    async def get_execution(self, execution_id: str) -> dict[str, Any]:
        return await self._management("GET", f"/execution/{execution_id}")

    async def execute_workflow(
        self,
        workflow_id: str,
        payload: dict[str, Any],
    ) -> ExecutionResult:
        """Trigger a workflow run, paying via x402 if KeeperHub returns 402.

        Falls back to API-key auth if no 402 challenge is presented (some workflows
        are billed against the user's prepaid balance instead of per-call x402).
        """
        url = f"{self._base}/workflow/{workflow_id}/execute"
        headers = self._auth_headers() if self._api_key else {}

        own_x402 = False
        x402 = self._x402
        if x402 is None:
            x402 = X402Client(
                attribution_headers={"User-Agent": "Spieon-KeeperHub/1.0"}
            )
            own_x402 = True
        try:
            if own_x402:
                await x402.__aenter__()
            try:
                res = await x402.request("POST", url, headers=headers, json_body=payload)
            except X402PaymentError as exc:
                raise KeeperHubError(f"x402 payment to keeperhub failed: {exc}") from exc

            response = res.response
            if response.status_code >= 400:
                raise KeeperHubError(
                    f"keeperhub execute failed: {response.status_code} "
                    f"{response.text[:300]}"
                )
            try:
                body = response.json()
            except ValueError:
                body = {"raw": response.text}

            execution_id = (
                body.get("executionId")
                or body.get("execution_id")
                or body.get("runId")
                or body.get("id")
            )
            status = str(body.get("status") or "queued")
            return ExecutionResult(
                execution_id=execution_id,
                status=status,
                paid=res.used_payment is not None,
                payment_tx=res.transaction,
                raw=body,
            )
        finally:
            if own_x402:
                await x402.__aexit__(None, None, None)


@lru_cache
def get_keeperhub_client() -> KeeperHubClient:
    return KeeperHubClient()


__all__ = [
    "ExecutionResult",
    "KeeperHubClient",
    "KeeperHubError",
    "get_keeperhub_client",
]


def encode_payout_payload(
    *,
    finding_id: str,
    recipient: str,
    amount_usdc: str,
    severity: str,
    attestation_uid: str | None,
    tx_hash: str,
) -> dict[str, Any]:
    """Build the JSON the payout workflow expects on its webhook trigger."""
    return {
        "source": "spieon",
        "kind": "finding.payout",
        "findingId": finding_id,
        "recipient": recipient,
        "amountUsdc": amount_usdc,
        "severity": severity,
        "attestationUid": attestation_uid,
        "payoutTx": tx_hash,
    }


def serialize_workflow_template(template: dict[str, Any]) -> str:
    return json.dumps(template, separators=(",", ":"), sort_keys=True)
