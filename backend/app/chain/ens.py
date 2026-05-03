"""ENS resolution + reverse-resolution for the Spieon agent identity.

The agent owns an ENS name (e.g. `spieon-agent.eth` on Sepolia) whose text records
expose the ERC-8004 descriptor URL, scan endpoint, and other discovery metadata.
This module reads those records live at request time so the descriptor and stats
endpoints don't ship hardcoded strings.

If `ens_name` is unset, every helper degrades to None — callers should treat ENS
as optional metadata, not a hard dependency.
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache

from ens import AsyncENS
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

from app.config import get_settings

log = logging.getLogger(__name__)

_TTL_SECONDS = 60.0
_text_cache: dict[tuple[str, str], tuple[float, str | None]] = {}
_name_cache: dict[str, tuple[float, str | None]] = {}


@lru_cache
def _w3() -> AsyncWeb3:
    return AsyncWeb3(AsyncHTTPProvider(get_settings().ens_rpc_url))


@lru_cache
def _ens() -> AsyncENS:
    return AsyncENS.from_web3(_w3())


def configured_name() -> str | None:
    return get_settings().ens_name or None


def text_keys() -> list[str]:
    raw = get_settings().ens_text_keys
    return [k.strip() for k in raw.split(",") if k.strip()]


async def resolve_text(name: str, key: str) -> str | None:
    """Return the value of a text record, or None if unset / lookup fails."""
    cache_key = (name.lower(), key)
    now = time.monotonic()
    cached = _text_cache.get(cache_key)
    if cached and now - cached[0] < _TTL_SECONDS:
        return cached[1]
    try:
        value = await _ens().get_text(name, key)
    except Exception as exc:
        log.debug("ens text lookup failed for %s/%s: %s", name, key, exc)
        value = None
    _text_cache[cache_key] = (now, value or None)
    return value or None


async def lookup_name(address: str) -> str | None:
    """Reverse-resolve an address to its primary ENS name, or None."""
    addr = address.lower()
    now = time.monotonic()
    cached = _name_cache.get(addr)
    if cached and now - cached[0] < _TTL_SECONDS:
        return cached[1]
    try:
        name = await _ens().name(address)
    except Exception as exc:
        log.debug("ens reverse lookup failed for %s: %s", address, exc)
        name = None
    _name_cache[addr] = (now, name or None)
    return name or None


async def resolve_address(name: str) -> str | None:
    """Forward-resolve an ENS name to an address, or None."""
    try:
        return await _ens().address(name)
    except Exception as exc:
        log.debug("ens forward lookup failed for %s: %s", name, exc)
        return None


async def fetch_text_records(name: str | None = None) -> dict[str, str]:
    """Read the configured text record set for a name. Returns only set keys."""
    target = name or configured_name()
    if not target:
        return {}
    out: dict[str, str] = {}
    for key in text_keys():
        value = await resolve_text(target, key)
        if value:
            out[key] = value
    return out
