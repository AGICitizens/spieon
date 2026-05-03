"""One-shot: publish the Spieon agent's ENS identity on Sepolia.

Prereqs (do once, manually):
    1. Register an ENS name on Sepolia via https://sepolia.app.ens.domains
       (free for 5+ char names; ~5 min). Use the agent wallet so it owns the name.
    2. Set ENS_NAME in .env to that name (e.g. spieon-agent.eth).
    3. Make sure AGENT_PRIVATE_KEY and ENS_RPC_URL (Sepolia) are set.

This script then:
    - Sets text records on the public resolver pointing at the live backend
      (descriptor URL, scan endpoint, GitHub, etc.)
    - Sets primary (reverse) name so block explorers show ens-name → wallet.

Usage:
    cd backend && uv run python scripts/ens_setup.py \\
        --base-url https://api.spieon.example \\
        [--description "..."] [--github agicitizens/spieon] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

from ens import ENS
from ens.utils import is_valid_name
from eth_account import Account
from web3 import Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder

from app.config import get_settings

REVERSE_REGISTRAR_ABI = [
    {
        "inputs": [{"internalType": "string", "name": "name", "type": "string"}],
        "name": "setName",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

# ENS Sepolia deployments — see https://docs.ens.domains/learn/deployments
SEPOLIA_REVERSE_REGISTRAR = "0xCF75B92126B02C9811d8c632144288a3eb84afC8"


def _build_records(args: argparse.Namespace, name: str) -> dict[str, str]:
    base = args.base_url.rstrip("/")
    return {
        "url": base,
        "description": args.description
        or "Spieon — autonomous AI security scanner. Pen-tests x402 + MCP.",
        "com.github": args.github,
        "org.erc8004.descriptor": f"{base}/.well-known/agent.json",
        "org.spieon.scan-endpoint": f"{base}/scans",
        "org.spieon.identity": name,
    }


def _send(
    w3: Web3,
    account,
    to: str,
    data: bytes,
    *,
    label: str,
    dry_run: bool,
) -> None:
    print(f"  {label}…", end=" ", flush=True)
    if dry_run:
        print("dry-run (skipped)")
        return
    tx = {
        "from": account.address,
        "to": Web3.to_checksum_address(to),
        "data": data,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        "chainId": w3.eth.chain_id,
        "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
    }
    tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
    tx_hash = w3.eth.send_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    status = "ok" if receipt.status == 1 else "FAILED"
    print(f"{status} ({receipt.transactionHash.hex()})")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Public backend base URL")
    parser.add_argument("--description", default=None)
    parser.add_argument("--github", default="agicitizens/spieon")
    parser.add_argument("--skip-reverse", action="store_true",
                        help="Don't set primary (reverse) name")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    settings = get_settings()
    name = settings.ens_name
    if not name:
        print("ENS_NAME is not set in .env", file=sys.stderr)
        return 2
    if not is_valid_name(name):
        print(f"ENS_NAME {name!r} is not a valid ENS name", file=sys.stderr)
        return 2
    if not settings.agent_private_key:
        print("AGENT_PRIVATE_KEY is not set", file=sys.stderr)
        return 2

    w3 = Web3(Web3.HTTPProvider(settings.ens_rpc_url))
    if not w3.is_connected():
        print(f"Cannot reach ENS RPC at {settings.ens_rpc_url}", file=sys.stderr)
        return 2
    if w3.eth.chain_id != settings.ens_chain_id:
        print(
            f"Connected chain id {w3.eth.chain_id} != ENS_CHAIN_ID "
            f"{settings.ens_chain_id}; refusing to send.",
            file=sys.stderr,
        )
        return 2

    account = Account.from_key(settings.agent_private_key)
    w3.middleware_onion.inject(
        SignAndSendRawMiddlewareBuilder.build(account), layer=0,
    )

    ns = ENS.from_web3(w3)
    owner = ns.owner(name)
    if owner.lower() != account.address.lower():
        print(
            f"Agent {account.address} does not own {name} (owner={owner}). "
            f"Register the name first via https://sepolia.app.ens.domains",
            file=sys.stderr,
        )
        return 2

    resolver = ns.resolver(name)
    if resolver is None or resolver.address in (None, "0x" + "0" * 40):
        print(
            f"{name} has no resolver set. Set the public resolver in the ENS UI first.",
            file=sys.stderr,
        )
        return 2

    print(f"Agent: {account.address}")
    print(f"Name:  {name}")
    print(f"Resolver: {resolver.address}")
    print()

    records = _build_records(args, name)
    print("Setting text records:")
    for key, value in records.items():
        data = resolver.encode_abi(
            "setText", args=[Web3.to_bytes(hexstr=ns.namehash(name).hex()), key, value]
        )
        _send(
            w3, account, resolver.address, data,
            label=f"{key} = {value[:60]}",
            dry_run=args.dry_run,
        )

    if not args.skip_reverse:
        print()
        print("Setting reverse (primary) name:")
        reverse = w3.eth.contract(
            address=Web3.to_checksum_address(SEPOLIA_REVERSE_REGISTRAR),
            abi=REVERSE_REGISTRAR_ABI,
        )
        data = reverse.encode_abi("setName", args=[name])
        _send(
            w3, account, SEPOLIA_REVERSE_REGISTRAR, data,
            label=f"primary name → {name}",
            dry_run=args.dry_run,
        )

    print()
    print("Done. Verify:")
    print(f"  https://sepolia.app.ens.domains/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
