from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PaymentRequirements:
    scheme: str
    network: str
    max_amount_required: int
    resource: str
    description: str
    mime_type: str
    pay_to: str
    asset: str
    max_timeout_seconds: int
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> PaymentRequirements:
        return cls(
            scheme=str(raw.get("scheme", "exact")),
            network=str(raw.get("network", "")),
            max_amount_required=int(raw.get("maxAmountRequired", 0)),
            resource=str(raw.get("resource", "")),
            description=str(raw.get("description", "")),
            mime_type=str(raw.get("mimeType", "application/json")),
            pay_to=str(raw.get("payTo", "")),
            asset=str(raw.get("asset", "")),
            max_timeout_seconds=int(raw.get("maxTimeoutSeconds", 60)),
            extra=dict(raw.get("extra") or {}),
        )


@dataclass(slots=True)
class PaymentPayload:
    x402_version: int
    scheme: str
    network: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "x402Version": self.x402_version,
            "scheme": self.scheme,
            "network": self.network,
            "payload": self.payload,
        }


@dataclass(slots=True)
class PaymentResponse:
    success: bool
    transaction: str | None
    network: str | None
    payer: str | None
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> PaymentResponse:
        return cls(
            success=bool(raw.get("success", False)),
            transaction=raw.get("transaction") or raw.get("txHash") or None,
            network=raw.get("network"),
            payer=raw.get("payer"),
            raw=raw,
        )
