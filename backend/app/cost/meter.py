from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.cost.receipts import PaymentReceiptParser, UsdcTransfer, X402ReceiptParser


@dataclass(slots=True)
class ProbeCost:
    probe_id: str
    transfers: list[UsdcTransfer] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return sum((t.amount for t in self.transfers), Decimal("0"))

    def add(self, transfer: UsdcTransfer) -> None:
        self.transfers.append(transfer)


class CostMeter:
    def __init__(
        self,
        probe_id: str,
        *,
        parser: PaymentReceiptParser | None = None,
    ) -> None:
        self._cost = ProbeCost(probe_id=probe_id)
        self._parser: PaymentReceiptParser = parser or X402ReceiptParser()

    @property
    def cost(self) -> ProbeCost:
        return self._cost

    async def __aenter__(self) -> CostMeter:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def record(self, response: object) -> UsdcTransfer | None:
        transfer = await self._parser.parse(response)
        if transfer is not None:
            self._cost.add(transfer)
        return transfer
