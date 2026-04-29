from __future__ import annotations

from decimal import Decimal

import pytest

from app.cost import CostMeter, ProbeCost, UsdcTransfer


class _StubParser:
    def __init__(self, transfer: UsdcTransfer | None) -> None:
        self.transfer = transfer
        self.calls = 0

    async def parse(self, response: object) -> UsdcTransfer | None:
        self.calls += 1
        return self.transfer


@pytest.mark.asyncio
async def test_cost_meter_aggregates_transfers() -> None:
    transfers = [
        UsdcTransfer(
            tx_hash=f"0x{i:064x}",
            from_address="0xfrom",
            to_address="0xto",
            amount=amount,
            block_number=10 + i,
        )
        for i, amount in enumerate([Decimal("0.10"), Decimal("0.40"), Decimal("0.05")])
    ]

    parser = _StubParser(transfer=None)
    meter = CostMeter("x402-replay", parser=parser)

    async with meter as m:
        for t in transfers:
            parser.transfer = t
            recorded = await m.record(object())
            assert recorded is t

    assert parser.calls == 3
    assert isinstance(meter.cost, ProbeCost)
    assert meter.cost.total == Decimal("0.55")
    assert [t.tx_hash for t in meter.cost.transfers] == [t.tx_hash for t in transfers]


@pytest.mark.asyncio
async def test_cost_meter_skips_when_parser_returns_none() -> None:
    parser = _StubParser(transfer=None)
    meter = CostMeter("free-probe", parser=parser)
    async with meter:
        result = await meter.record(object())
    assert result is None
    assert meter.cost.total == Decimal("0")
