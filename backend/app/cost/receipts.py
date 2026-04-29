from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

from app.chain.client import get_w3
from app.config import get_settings
from app.x402.client import X402Response

USDC_DECIMALS = 6
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class ReceiptError(RuntimeError):
    pass


@dataclass(slots=True)
class UsdcTransfer:
    tx_hash: str
    from_address: str
    to_address: str
    amount: Decimal
    block_number: int


@runtime_checkable
class PaymentReceiptParser(Protocol):
    async def parse(self, response: object) -> UsdcTransfer | None: ...


def _decode_topic_address(topic: str) -> str:
    raw = topic[2:] if topic.startswith("0x") else topic
    return "0x" + raw[-40:]


def _parse_amount(data: str) -> Decimal:
    raw = int(data, 16)
    return Decimal(raw) / Decimal(10**USDC_DECIMALS)


class X402ReceiptParser:
    def __init__(self, *, usdc_address: str | None = None) -> None:
        configured = usdc_address or get_settings().x402_usdc_address
        self._usdc_address = configured.lower()

    async def parse(self, response: object) -> UsdcTransfer | None:
        if not isinstance(response, X402Response):
            return None
        if response.payment_response is None or not response.transaction:
            return None

        tx_hash = response.transaction
        receipt = await get_w3().eth.get_transaction_receipt(tx_hash)
        if receipt is None:
            raise ReceiptError(f"no receipt for tx {tx_hash}")

        for log in receipt.get("logs", []):
            if log["address"].lower() != self._usdc_address:
                continue
            topics = log.get("topics") or []
            if not topics:
                continue
            topic0 = topics[0].hex() if hasattr(topics[0], "hex") else topics[0]
            if topic0.lower() != TRANSFER_TOPIC:
                continue
            data = log["data"].hex() if hasattr(log["data"], "hex") else log["data"]
            from_addr = _decode_topic_address(
                topics[1].hex() if hasattr(topics[1], "hex") else topics[1]
            )
            to_addr = _decode_topic_address(
                topics[2].hex() if hasattr(topics[2], "hex") else topics[2]
            )
            amount = _parse_amount(data)
            return UsdcTransfer(
                tx_hash=tx_hash,
                from_address=from_addr,
                to_address=to_addr,
                amount=amount,
                block_number=int(receipt.get("blockNumber") or 0),
            )

        raise ReceiptError(f"tx {tx_hash} settled but no USDC Transfer log on {self._usdc_address}")
