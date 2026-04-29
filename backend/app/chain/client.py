from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

from app.config import get_settings


@lru_cache
def get_w3() -> AsyncWeb3:
    settings = get_settings()
    return AsyncWeb3(AsyncHTTPProvider(settings.base_sepolia_rpc_url))


@lru_cache
def signer() -> LocalAccount:
    settings = get_settings()
    if not settings.agent_private_key:
        raise RuntimeError("AGENT_PRIVATE_KEY is not set")
    return Account.from_key(settings.agent_private_key)


def agent_address() -> str:
    settings = get_settings()
    if settings.agent_address:
        return settings.agent_address
    return signer().address


async def current_block() -> int:
    return await get_w3().eth.block_number


async def get_balance_eth(address: str | None = None) -> Decimal:
    addr = address or agent_address()
    wei = await get_w3().eth.get_balance(addr)
    return Decimal(wei) / Decimal(10**18)


_USDC_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    }
]


async def get_usdc_balance(address: str | None = None) -> Decimal:
    settings = get_settings()
    w3 = get_w3()
    addr = w3.to_checksum_address(address or agent_address())
    contract = w3.eth.contract(
        address=w3.to_checksum_address(settings.x402_usdc_address),
        abi=_USDC_ABI,
    )
    raw = await contract.functions.balanceOf(addr).call()
    return Decimal(raw) / Decimal(10**6)
