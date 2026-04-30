from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from functools import lru_cache
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.chain.client import get_w3, signer
from app.config import get_settings
from app.models.finding import Severity
from app.models.module import Module

MODULE_REGISTRY_ABI: list[dict[str, Any]] = [
    {
        "type": "function",
        "stateMutability": "view",
        "name": "isRegistered",
        "inputs": [{"name": "moduleHash", "type": "bytes32"}],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "type": "function",
        "stateMutability": "view",
        "name": "totalModules",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "stateMutability": "view",
        "name": "moduleHashes",
        "inputs": [
            {"name": "cursor", "type": "uint256"},
            {"name": "limit", "type": "uint256"},
        ],
        "outputs": [
            {"name": "page", "type": "bytes32[]"},
            {"name": "nextCursor", "type": "uint256"},
        ],
    },
    {
        "type": "function",
        "stateMutability": "view",
        "name": "getModule",
        "inputs": [{"name": "moduleHash", "type": "bytes32"}],
        "outputs": [
            {
                "components": [
                    {"name": "author", "type": "address"},
                    {"name": "metadataURI", "type": "string"},
                    {"name": "severityCap", "type": "uint8"},
                    {"name": "owaspId", "type": "bytes32"},
                    {"name": "atlasTechniqueId", "type": "bytes32"},
                    {"name": "maestroId", "type": "bytes32"},
                    {"name": "registeredAt", "type": "uint64"},
                    {"name": "timesUsed", "type": "uint128"},
                    {"name": "successCount", "type": "uint128"},
                    {"name": "exists", "type": "bool"},
                ],
                "name": "",
                "type": "tuple",
            }
        ],
    },
    {
        "type": "function",
        "stateMutability": "nonpayable",
        "name": "register",
        "inputs": [
            {"name": "moduleHash", "type": "bytes32"},
            {"name": "metadataURI", "type": "string"},
            {"name": "severityCap", "type": "uint8"},
            {"name": "owaspId", "type": "bytes32"},
            {"name": "atlasTechniqueId", "type": "bytes32"},
            {"name": "maestroId", "type": "bytes32"},
        ],
        "outputs": [{"name": "", "type": "bytes32"}],
    },
    {
        "type": "function",
        "stateMutability": "nonpayable",
        "name": "recordUsage",
        "inputs": [
            {"name": "moduleHash", "type": "bytes32"},
            {"name": "succeeded", "type": "bool"},
        ],
        "outputs": [],
    },
]


BOUNTY_POOL_ABI: list[dict[str, Any]] = [
    {
        "type": "function",
        "stateMutability": "nonpayable",
        "name": "payout",
        "inputs": [
            {
                "components": [
                    {"name": "scanId", "type": "bytes32"},
                    {"name": "moduleHash", "type": "bytes32"},
                    {"name": "attestationUid", "type": "bytes32"},
                    {"name": "severity", "type": "uint8"},
                    {"name": "amountUsdc6", "type": "uint256"},
                    {"name": "recipient", "type": "address"},
                ],
                "name": "req",
                "type": "tuple",
            }
        ],
        "outputs": [],
    },
    {
        "type": "function",
        "stateMutability": "view",
        "name": "severityCap",
        "inputs": [{"name": "sev", "type": "uint8"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "stateMutability": "view",
        "name": "moduleDailyCap",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "stateMutability": "view",
        "name": "outsizedThreshold",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "stateMutability": "view",
        "name": "attestationConsumed",
        "inputs": [{"name": "uid", "type": "bytes32"}],
        "outputs": [{"name": "", "type": "bool"}],
    },
]


SEVERITY_TO_UINT8 = {
    Severity.low: 0,
    Severity.medium: 1,
    Severity.high: 2,
    Severity.critical: 3,
}
UINT8_TO_SEVERITY = {v: k for k, v in SEVERITY_TO_UINT8.items()}


@dataclass(slots=True)
class OnchainModule:
    module_hash: str
    author: str
    metadata_uri: str
    severity_cap: Severity
    owasp_id: str | None
    atlas_technique_id: str | None
    maestro_id: str | None
    registered_at: datetime
    times_used: int
    success_count: int


def _bytes32_to_str(raw: bytes | str) -> str | None:
    if isinstance(raw, str):
        if raw == "0x" + "00" * 32:
            return None
        return raw
    if not raw or all(b == 0 for b in raw):
        return None
    text = raw.rstrip(b"\x00").decode("utf-8", errors="replace")
    return text or None


def _hex_to_bytes32(hex_str: str | None) -> bytes:
    if not hex_str:
        return b"\x00" * 32
    raw = hex_str[2:] if hex_str.startswith("0x") else hex_str
    raw = raw.rjust(64, "0")[-64:]
    return bytes.fromhex(raw)


def _string_to_bytes32(value: str | None) -> bytes:
    if not value:
        return b"\x00" * 32
    encoded = value.encode("utf-8")[:32]
    return encoded.ljust(32, b"\x00")


def _addresses_configured() -> bool:
    settings = get_settings()
    return bool(settings.module_registry_address) and bool(settings.bounty_pool_address)


@lru_cache
def _registry():
    settings = get_settings()
    if not settings.module_registry_address:
        raise RuntimeError("MODULE_REGISTRY_ADDRESS is not set")
    w3 = get_w3()
    return w3.eth.contract(
        address=w3.to_checksum_address(settings.module_registry_address),
        abi=MODULE_REGISTRY_ABI,
    )


@lru_cache
def _pool():
    settings = get_settings()
    if not settings.bounty_pool_address:
        raise RuntimeError("BOUNTY_POOL_ADDRESS is not set")
    w3 = get_w3()
    return w3.eth.contract(
        address=w3.to_checksum_address(settings.bounty_pool_address),
        abi=BOUNTY_POOL_ABI,
    )


async def fetch_module(module_hash: str) -> OnchainModule | None:
    contract = _registry()
    raw_hash = _hex_to_bytes32(module_hash)
    exists = await contract.functions.isRegistered(raw_hash).call()
    if not exists:
        return None
    m = await contract.functions.getModule(raw_hash).call()
    author, metadata_uri, severity_cap_u8, owasp, atlas, maestro, registered_at, times_used, success_count, _exists = m
    return OnchainModule(
        module_hash=module_hash if module_hash.startswith("0x") else "0x" + module_hash,
        author=author,
        metadata_uri=metadata_uri,
        severity_cap=UINT8_TO_SEVERITY.get(severity_cap_u8, Severity.medium),
        owasp_id=_bytes32_to_str(owasp),
        atlas_technique_id=_bytes32_to_str(atlas),
        maestro_id=_bytes32_to_str(maestro),
        registered_at=datetime.fromtimestamp(int(registered_at), tz=UTC),
        times_used=int(times_used),
        success_count=int(success_count),
    )


async def list_module_hashes(*, page_size: int = 200) -> list[str]:
    contract = _registry()
    total = int(await contract.functions.totalModules().call())
    out: list[str] = []
    cursor = 0
    while cursor < total:
        page, cursor = await contract.functions.moduleHashes(cursor, page_size).call()
        for raw in page:
            out.append(raw.hex() if hasattr(raw, "hex") else str(raw))
    return out


async def sync_modules(session: AsyncSession) -> int:
    if not _addresses_configured():
        return 0
    hashes = await list_module_hashes()
    written = 0
    for raw in hashes:
        module_hex = raw if raw.startswith("0x") else "0x" + raw
        onchain = await fetch_module(module_hex)
        if onchain is None:
            continue

        result = await session.execute(
            select(Module).where(Module.module_hash == module_hex)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = Module(
                module_hash=module_hex,
                author_address=onchain.author,
                metadata_uri=onchain.metadata_uri,
                severity_cap=onchain.severity_cap,
                times_used=onchain.times_used,
                success_count=onchain.success_count,
                owasp_id=onchain.owasp_id,
                atlas_technique_id=onchain.atlas_technique_id,
                registered_at=onchain.registered_at,
                last_synced_at=datetime.now(UTC),
            )
            session.add(row)
            written += 1
        else:
            row.author_address = onchain.author
            row.metadata_uri = onchain.metadata_uri
            row.severity_cap = onchain.severity_cap
            row.times_used = onchain.times_used
            row.success_count = onchain.success_count
            row.owasp_id = onchain.owasp_id
            row.atlas_technique_id = onchain.atlas_technique_id
            row.registered_at = onchain.registered_at
            row.last_synced_at = datetime.now(UTC)
            session.add(row)
            written += 1
    await session.commit()
    return written


@dataclass(slots=True)
class PayoutRequest:
    scan_id: uuid.UUID
    module_hash: str
    attestation_uid: str
    severity: Severity
    amount_usdc: Decimal
    recipient: str


async def submit_payout(req: PayoutRequest) -> str:
    settings = get_settings()
    if not settings.bounty_pool_address or not settings.agent_private_key:
        raise RuntimeError("bounty pool not configured")

    pool = _pool()
    w3 = get_w3()
    account = signer()

    amount_micros = int((req.amount_usdc * Decimal(10**6)).to_integral_value())
    tuple_arg = (
        _hex_to_bytes32("0x" + req.scan_id.hex),
        _hex_to_bytes32(req.module_hash),
        _hex_to_bytes32(req.attestation_uid),
        SEVERITY_TO_UINT8[req.severity],
        amount_micros,
        w3.to_checksum_address(req.recipient),
    )
    nonce = await w3.eth.get_transaction_count(account.address)
    tx = await pool.functions.payout(tuple_arg).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": settings.base_sepolia_chain_id,
            "value": 0,
        }
    )
    signed = account.sign_transaction(tx)
    raw = signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction
    tx_hash = await w3.eth.send_raw_transaction(raw)
    return tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)


async def severity_cap_usdc(severity: Severity) -> Decimal:
    pool = _pool()
    raw = await pool.functions.severityCap(SEVERITY_TO_UINT8[severity]).call()
    return Decimal(raw) / Decimal(10**6)


async def attestation_already_paid(attestation_uid: str) -> bool:
    pool = _pool()
    return bool(
        await pool.functions.attestationConsumed(_hex_to_bytes32(attestation_uid)).call()
    )


def encode_taxonomy(value: str | None) -> bytes:
    return _string_to_bytes32(value)


async def register_module_onchain(
    *,
    module_hash: str,
    metadata_uri: str,
    severity_cap: Severity,
    owasp_id: str | None,
    atlas_technique_id: str | None,
    maestro_id: str | None,
) -> str | None:
    settings = get_settings()
    if not settings.module_registry_address or not settings.agent_private_key:
        return None

    contract = _registry()
    raw_hash = _hex_to_bytes32(module_hash)
    if await contract.functions.isRegistered(raw_hash).call():
        return None

    w3 = get_w3()
    account = signer()
    nonce = await w3.eth.get_transaction_count(account.address)
    tx = await contract.functions.register(
        raw_hash,
        metadata_uri,
        SEVERITY_TO_UINT8[severity_cap],
        _string_to_bytes32(owasp_id),
        _string_to_bytes32(atlas_technique_id),
        _string_to_bytes32(maestro_id),
    ).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": settings.base_sepolia_chain_id,
            "value": 0,
        }
    )
    signed = account.sign_transaction(tx)
    raw = (
        signed.raw_transaction
        if hasattr(signed, "raw_transaction")
        else signed.rawTransaction
    )
    tx_hash = await w3.eth.send_raw_transaction(raw)
    return tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)


async def register_native_probes() -> dict[str, str | None]:
    from app.probes.registry import iter_probes

    settings = get_settings()
    if not settings.module_registry_address or not settings.agent_private_key:
        return {}

    results: dict[str, str | None] = {}
    for spec in iter_probes():
        try:
            tx = await register_module_onchain(
                module_hash=spec.module_hash,
                metadata_uri=f"spieon-native://{spec.id}",
                severity_cap=spec.severity_cap,
                owasp_id=spec.owasp_id,
                atlas_technique_id=spec.atlas_technique_id,
                maestro_id=spec.maestro_id,
            )
            results[spec.id] = tx
        except Exception as exc:
            results[spec.id] = f"error: {exc}"
    return results
