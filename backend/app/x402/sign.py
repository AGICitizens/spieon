from __future__ import annotations

import secrets
import time

from eth_account.messages import encode_typed_data
from eth_account.signers.local import LocalAccount

from app.x402.types import PaymentPayload, PaymentRequirements

_NETWORK_CHAIN_IDS = {
    "base-sepolia": 84532,
    "base": 8453,
}


def _resolve_chain_id(network: str, requirements: PaymentRequirements) -> int:
    if extra_id := requirements.extra.get("chainId"):
        return int(extra_id)
    if network in _NETWORK_CHAIN_IDS:
        return _NETWORK_CHAIN_IDS[network]
    raise ValueError(f"unknown x402 network: {network!r}")


def _resolve_token_meta(requirements: PaymentRequirements) -> tuple[str, str]:
    name = requirements.extra.get("name") or "USD Coin"
    version = requirements.extra.get("version") or "2"
    return str(name), str(version)


def build_authorization(
    *,
    payer: str,
    requirements: PaymentRequirements,
    valid_for_seconds: int = 60,
) -> dict[str, str]:
    now = int(time.time())
    nonce_hex = "0x" + secrets.token_hex(32)
    return {
        "from": payer,
        "to": requirements.pay_to,
        "value": str(requirements.max_amount_required),
        "validAfter": str(now - 5),
        "validBefore": str(now + valid_for_seconds),
        "nonce": nonce_hex,
    }


def sign_payment(
    account: LocalAccount,
    requirements: PaymentRequirements,
    *,
    x402_version: int = 1,
    valid_for_seconds: int = 60,
) -> PaymentPayload:
    chain_id = _resolve_chain_id(requirements.network, requirements)
    token_name, token_version = _resolve_token_meta(requirements)
    authorization = build_authorization(
        payer=account.address,
        requirements=requirements,
        valid_for_seconds=valid_for_seconds,
    )

    typed = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ],
        },
        "primaryType": "TransferWithAuthorization",
        "domain": {
            "name": token_name,
            "version": token_version,
            "chainId": chain_id,
            "verifyingContract": requirements.asset,
        },
        "message": {
            "from": account.address,
            "to": requirements.pay_to,
            "value": int(authorization["value"]),
            "validAfter": int(authorization["validAfter"]),
            "validBefore": int(authorization["validBefore"]),
            "nonce": authorization["nonce"],
        },
    }

    encoded = encode_typed_data(full_message=typed)
    signed = account.sign_message(encoded)

    raw_sig = signed.signature
    if hasattr(raw_sig, "to_0x_hex"):
        signature_hex = raw_sig.to_0x_hex()
    elif isinstance(raw_sig, (bytes, bytearray)):
        signature_hex = "0x" + bytes(raw_sig).hex()
    else:
        text = str(raw_sig)
        signature_hex = text if text.startswith("0x") else "0x" + text

    return PaymentPayload(
        x402_version=x402_version,
        scheme=requirements.scheme,
        network=requirements.network,
        payload={
            "signature": signature_hex,
            "authorization": authorization,
        },
    )
