from __future__ import annotations

import time
from decimal import Decimal

from app.safety import (
    AutoStopReason,
    HarnessDecision,
    SafetyHarness,
    attribution_headers_for,
)


def test_attribution_headers_carry_scan_id() -> None:
    import uuid

    sid = uuid.uuid4()
    headers = attribution_headers_for(sid)
    assert headers["User-Agent"].startswith("Spieon-Pentest")
    assert headers["X-Spieon-Scan-Id"] == str(sid)


def test_destructive_blocklist_blocks_dos_class() -> None:
    h = SafetyHarness()
    verdict = h.check(
        target_url="https://target.example/x",
        probe_class="dos",
        budget_remaining_usdc=Decimal("1"),
    )
    assert verdict.decision is HarnessDecision.block
    assert "destructive" in verdict.reason


def test_budget_exhaustion_stops_scan() -> None:
    h = SafetyHarness()
    verdict = h.check(
        target_url="https://target.example/x",
        probe_class="x402-replay",
        budget_remaining_usdc=Decimal("0"),
    )
    assert verdict.decision is HarnessDecision.stop
    assert verdict.auto_stop is AutoStopReason.budget_exhausted


def test_per_minute_rate_limit_kicks_in() -> None:
    h = SafetyHarness(per_minute=3, per_hour=10000)
    url = "https://target.example/x"
    for _ in range(3):
        v = h.check(
            target_url=url,
            probe_class="x402-replay",
            budget_remaining_usdc=Decimal("1"),
        )
        assert v.decision is HarnessDecision.allow
        h.record_attempt(url)
    final = h.check(
        target_url=url,
        probe_class="x402-replay",
        budget_remaining_usdc=Decimal("1"),
    )
    assert final.decision is HarnessDecision.block
    assert "rate limit" in final.reason


def test_5xx_streak_triggers_auto_stop() -> None:
    h = SafetyHarness(max_5xx_streak=2)
    url = "https://target.example/x"
    h.record_attempt(url)
    h.record_status(url, 500)
    h.record_attempt(url)
    h.record_status(url, 502)

    v = h.check(
        target_url=url,
        probe_class="x402-replay",
        budget_remaining_usdc=Decimal("1"),
    )
    assert v.decision is HarnessDecision.stop
    assert v.auto_stop is AutoStopReason.target_5xx_streak


def test_2xx_resets_5xx_streak() -> None:
    h = SafetyHarness(max_5xx_streak=2)
    url = "https://target.example/x"
    h.record_attempt(url)
    h.record_status(url, 500)
    h.record_attempt(url)
    h.record_status(url, 200)

    v = h.check(
        target_url=url,
        probe_class="x402-replay",
        budget_remaining_usdc=Decimal("1"),
    )
    assert v.decision is HarnessDecision.allow


def test_max_attempts_stops_scan() -> None:
    h = SafetyHarness(max_attempts=2)
    url = "https://target.example/x"
    h.record_attempt(url)
    h.record_attempt(url)
    v = h.check(
        target_url=url,
        probe_class="x402-replay",
        budget_remaining_usdc=Decimal("1"),
    )
    assert v.decision is HarnessDecision.stop
    assert v.auto_stop is AutoStopReason.max_attempts


def test_operator_balance_below_remaining_budget_stops() -> None:
    h = SafetyHarness()
    v = h.check(
        target_url="https://target.example/x",
        probe_class="x402-replay",
        budget_remaining_usdc=Decimal("1"),
        operator_balance_usdc=Decimal("0.5"),
    )
    assert v.decision is HarnessDecision.stop
    assert v.auto_stop is AutoStopReason.operator_balance_insufficient


def test_minute_window_drops_old_entries() -> None:
    h = SafetyHarness(per_minute=2)
    url = "https://target.example/x"

    h.record_attempt(url)
    h.record_attempt(url)
    bucket = h._buckets[h._host(url)]
    bucket.minute_window[0] -= 120
    bucket.minute_window[1] -= 120

    v = h.check(
        target_url=url,
        probe_class="x402-replay",
        budget_remaining_usdc=Decimal("1"),
    )
    assert v.decision is HarnessDecision.allow
    _ = time
