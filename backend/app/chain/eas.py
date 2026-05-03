from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from decimal import Decimal

from eth_abi import encode as abi_encode

from app.chain.client import agent_address, get_w3, signer
from app.config import get_settings
from app.models.finding import Severity

ZERO_BYTES32 = b"\x00" * 32

EAS_ATTEST_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "schema", "type": "bytes32"},
                    {
                        "components": [
                            {"name": "recipient", "type": "address"},
                            {"name": "expirationTime", "type": "uint64"},
                            {"name": "revocable", "type": "bool"},
                            {"name": "refUID", "type": "bytes32"},
                            {"name": "data", "type": "bytes"},
                            {"name": "value", "type": "uint256"},
                        ],
                        "name": "data",
                        "type": "tuple",
                    },
                ],
                "name": "request",
                "type": "tuple",
            }
        ],
        "name": "attest",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "payable",
        "type": "function",
    }
]


SCHEMA_SOLIDITY_TYPES = (
    "bytes32",  # scanId (uuid as bytes32)
    "string",   # target
    "uint8",    # severity (low=0, medium=1, high=2, critical=3)
    "bytes32",  # moduleHash
    "uint256",  # costInUsdcMicros (USDC * 10^6)
    "string",   # encryptedBundleURI
    "bytes32",  # ciphertextSha256
    "string",   # owaspId
    "string",   # atlasTechniqueId
    "string",   # maestroId
)


SEVERITY_TO_UINT8 = {
    Severity.low: 0,
    Severity.medium: 1,
    Severity.high: 2,
    Severity.critical: 3,
}


@dataclass(slots=True)
class FindingAttestationPayload:
    scan_id: uuid.UUID
    target: str
    severity: str
    module_hash: str
    cost_usdc: Decimal
    encrypted_bundle_uri: str | None
    ciphertext_sha256: str | None
    owasp_id: str | None
    atlas_technique_id: str | None
    maestro_id: str | None


def _hex_to_bytes32(hex_str: str | None) -> bytes:
    if not hex_str:
        return ZERO_BYTES32
    raw = hex_str[2:] if hex_str.startswith("0x") else hex_str
    raw = raw.rjust(64, "0")[-64:]
    return bytes.fromhex(raw)


def _scan_id_to_bytes32(scan_id: uuid.UUID) -> bytes:
    return scan_id.bytes.rjust(32, b"\x00")


def _severity_value(severity: str) -> int:
    if isinstance(severity, Severity):
        return SEVERITY_TO_UINT8[severity]
    return SEVERITY_TO_UINT8[Severity(severity)]


def _stub_uid(payload: FindingAttestationPayload) -> str:
    canonical = json.dumps(
        {
            "scan_id": str(payload.scan_id),
            "target": payload.target,
            "severity": payload.severity,
            "module_hash": payload.module_hash,
            "cost_usdc": str(payload.cost_usdc),
            "encrypted_bundle_uri": payload.encrypted_bundle_uri,
            "ciphertext_sha256": payload.ciphertext_sha256,
            "owasp_id": payload.owasp_id,
            "atlas_technique_id": payload.atlas_technique_id,
            "maestro_id": payload.maestro_id,
        },
        sort_keys=True,
    ).encode()
    return "0x" + hashlib.sha256(canonical).hexdigest()


def encode_finding_data(payload: FindingAttestationPayload) -> bytes:
    cost_micros = int((payload.cost_usdc * Decimal(10**6)).to_integral_value())
    return abi_encode(
        SCHEMA_SOLIDITY_TYPES,
        (
            _scan_id_to_bytes32(payload.scan_id),
            payload.target,
            _severity_value(payload.severity),
            _hex_to_bytes32(payload.module_hash),
            cost_micros,
            payload.encrypted_bundle_uri or "",
            _hex_to_bytes32(payload.ciphertext_sha256),
            payload.owasp_id or "",
            payload.atlas_technique_id or "",
            payload.maestro_id or "",
        ),
    )


def _can_attest_onchain() -> bool:
    settings = get_settings()
    return bool(
        settings.eas_schema_uid
        and settings.eas_contract_address
        and settings.agent_private_key
    )


async def _attest_onchain(payload: FindingAttestationPayload) -> str:
    settings = get_settings()
    w3 = get_w3()
    account = signer()
    contract = w3.eth.contract(
        address=w3.to_checksum_address(settings.eas_contract_address),
        abi=EAS_ATTEST_ABI,
    )

    request = (
        _hex_to_bytes32(settings.eas_schema_uid),
        (
            w3.to_checksum_address(agent_address()),
            0,
            True,
            ZERO_BYTES32,
            encode_finding_data(payload),
            0,
        ),
    )

    nonce = await w3.eth.get_transaction_count(account.address)
    chain_id = settings.base_sepolia_chain_id
    tx = await contract.functions.attest(request).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": chain_id,
            "value": 0,
        }
    )
    signed = account.sign_transaction(tx)
    raw = signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction
    tx_hash = await w3.eth.send_raw_transaction(raw)
    receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)

    eas_address = w3.to_checksum_address(settings.eas_contract_address).lower()
    attested_topic0 = w3.keccak(text="Attested(address,address,bytes32,bytes32)").hex()
    if not attested_topic0.startswith("0x"):
        attested_topic0 = "0x" + attested_topic0

    for log in receipt.get("logs", []):
        log_addr = log.get("address")
        if log_addr is None or log_addr.lower() != eas_address:
            continue
        topics = log.get("topics") or []
        if not topics:
            continue
        t0 = topics[0]
        t0_hex = t0.hex() if hasattr(t0, "hex") else str(t0)
        if not t0_hex.startswith("0x"):
            t0_hex = "0x" + t0_hex
        if t0_hex.lower() != attested_topic0.lower():
            continue
        data = log.get("data")
        data_hex = data.hex() if hasattr(data, "hex") else str(data)
        if data_hex.startswith("0x"):
            data_hex = data_hex[2:]
        if len(data_hex) >= 64:
            return "0x" + data_hex[:64]

    raw_hash = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
    return raw_hash if raw_hash.startswith("0x") else "0x" + raw_hash


async def attest_finding(payload: FindingAttestationPayload) -> str:
    if _can_attest_onchain():
        try:
            return await _attest_onchain(payload)
        except Exception:
            return _stub_uid(payload)
    return _stub_uid(payload)
