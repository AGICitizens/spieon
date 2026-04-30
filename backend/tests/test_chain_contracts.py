from __future__ import annotations

import pytest

from app.chain.contracts import (
    SEVERITY_TO_UINT8,
    UINT8_TO_SEVERITY,
    _bytes32_to_str,
    _hex_to_bytes32,
    _string_to_bytes32,
    encode_taxonomy,
    sync_modules,
)
from app.db import get_sessionmaker
from app.models.finding import Severity


def test_severity_uint8_round_trip() -> None:
    for s in (Severity.low, Severity.medium, Severity.high, Severity.critical):
        assert UINT8_TO_SEVERITY[SEVERITY_TO_UINT8[s]] is s


def test_hex_to_bytes32_pads_short_input() -> None:
    raw = _hex_to_bytes32("0xabcd")
    assert len(raw) == 32
    assert raw[-2:] == b"\xab\xcd"
    assert raw[:30] == b"\x00" * 30


def test_hex_to_bytes32_handles_none_and_bare_hex() -> None:
    assert _hex_to_bytes32(None) == b"\x00" * 32
    assert _hex_to_bytes32("dead") == b"\x00" * 30 + b"\xde\xad"


def test_string_to_bytes32_truncates_long_inputs() -> None:
    encoded = _string_to_bytes32("a" * 60)
    assert encoded == b"a" * 32

    short = _string_to_bytes32("LLM01")
    assert short[:5] == b"LLM01"
    assert short[5:] == b"\x00" * 27


def test_bytes32_to_str_recovers_taxonomy_string() -> None:
    encoded = encode_taxonomy("API07")
    assert _bytes32_to_str(encoded) == "API07"
    assert _bytes32_to_str(b"\x00" * 32) is None


@pytest.mark.asyncio
async def test_sync_modules_is_a_noop_when_addresses_unset() -> None:
    async with get_sessionmaker()() as session:
        written = await sync_modules(session)
    assert written == 0
