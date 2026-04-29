from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

import httpx
from eth_account.signers.local import LocalAccount

from app.chain.client import signer
from app.x402.sign import sign_payment
from app.x402.types import PaymentPayload, PaymentRequirements, PaymentResponse


class X402PaymentError(RuntimeError):
    pass


@dataclass(slots=True)
class X402Response:
    response: httpx.Response
    used_payment: PaymentPayload | None
    payment_response: PaymentResponse | None

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @property
    def transaction(self) -> str | None:
        return self.payment_response.transaction if self.payment_response else None


def _encode_payment_header(payload: PaymentPayload) -> str:
    raw = json.dumps(payload.to_dict(), separators=(",", ":")).encode()
    return base64.b64encode(raw).decode()


def _decode_payment_response(header_value: str) -> PaymentResponse | None:
    if not header_value:
        return None
    try:
        decoded = base64.b64decode(header_value).decode()
        return PaymentResponse.from_dict(json.loads(decoded))
    except Exception:
        return None


def _select_requirements(body: dict[str, Any]) -> PaymentRequirements:
    accepts = body.get("accepts") or body.get("acceptedPaymentRequirements") or []
    if not accepts:
        raise X402PaymentError("402 response had no accepts[] payment requirements")
    return PaymentRequirements.from_dict(accepts[0])


class X402Client:
    def __init__(
        self,
        *,
        account: LocalAccount | None = None,
        client: httpx.AsyncClient | None = None,
        attribution_headers: dict[str, str] | None = None,
    ) -> None:
        self._account = account
        self._client = client
        self._owns_client = client is None
        self._attribution = attribution_headers or {}

    async def __aenter__(self) -> X402Client:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
            self._owns_client = True
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    def _resolve_account(self) -> LocalAccount:
        if self._account is not None:
            return self._account
        return signer()

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: Any | None = None,
    ) -> X402Response:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
            self._owns_client = True

        merged_headers = dict(self._attribution)
        if headers:
            merged_headers.update(headers)

        first = await self._client.request(method, url, headers=merged_headers, json=json_body)
        if first.status_code != 402:
            return X402Response(response=first, used_payment=None, payment_response=None)

        try:
            body = first.json()
        except ValueError as exc:
            raise X402PaymentError(f"402 response was not JSON: {first.text!r}") from exc

        requirements = _select_requirements(body)
        payment = sign_payment(self._resolve_account(), requirements)

        retry_headers = dict(merged_headers)
        retry_headers["X-Payment"] = _encode_payment_header(payment)
        second = await self._client.request(method, url, headers=retry_headers, json=json_body)
        payment_response = _decode_payment_response(second.headers.get("x-payment-response", ""))
        return X402Response(
            response=second, used_payment=payment, payment_response=payment_response
        )
