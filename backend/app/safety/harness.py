from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from urllib.parse import urlparse

DESTRUCTIVE_PROBE_CLASSES = frozenset(
    {
        "dos",
        "denial-of-service",
        "auth-brute",
        "filesystem-write",
        "filesystem-delete",
        "data-destruction",
    }
)


class HarnessDecision(str, Enum):
    allow = "allow"
    block = "block"
    stop = "stop"


class AutoStopReason(str, Enum):
    budget_exhausted = "budget_exhausted"
    target_5xx_streak = "target_5xx_streak"
    max_attempts = "max_attempts"
    operator_balance_insufficient = "operator_balance_insufficient"


@dataclass(slots=True)
class HarnessVerdict:
    decision: HarnessDecision
    reason: str
    auto_stop: AutoStopReason | None = None


@dataclass(slots=True)
class _RateBucket:
    minute_window: deque[float] = field(default_factory=deque)
    hour_window: deque[float] = field(default_factory=deque)


def attribution_headers_for(scan_id: uuid.UUID) -> dict[str, str]:
    return {
        "User-Agent": "Spieon-Pentest/1.0 (+spieon.eth)",
        "X-Spieon-Scan-Id": str(scan_id),
    }


class SafetyHarness:
    def __init__(
        self,
        *,
        per_minute: int = 60,
        per_hour: int = 1000,
        max_5xx_streak: int = 5,
        max_attempts: int = 200,
        destructive_classes: frozenset[str] = DESTRUCTIVE_PROBE_CLASSES,
    ) -> None:
        self.per_minute = per_minute
        self.per_hour = per_hour
        self.max_5xx_streak = max_5xx_streak
        self.max_attempts = max_attempts
        self.destructive_classes = destructive_classes

        self._buckets: dict[str, _RateBucket] = {}
        self._5xx_streak: dict[str, int] = {}
        self._attempts = 0

    @staticmethod
    def _host(target_url: str) -> str:
        parsed = urlparse(target_url)
        host = (parsed.hostname or target_url).lower()
        return host

    def _trim_window(self, window: deque[float], horizon: float) -> None:
        now = time.monotonic()
        while window and (now - window[0]) > horizon:
            window.popleft()

    def check(
        self,
        *,
        target_url: str,
        probe_class: str,
        budget_remaining_usdc: Decimal,
        operator_balance_usdc: Decimal | None = None,
    ) -> HarnessVerdict:
        if probe_class in self.destructive_classes:
            return HarnessVerdict(
                decision=HarnessDecision.block,
                reason=f"probe_class {probe_class!r} is on the destructive blocklist",
            )
        if budget_remaining_usdc <= Decimal("0"):
            return HarnessVerdict(
                decision=HarnessDecision.stop,
                reason="scan budget exhausted",
                auto_stop=AutoStopReason.budget_exhausted,
            )
        if operator_balance_usdc is not None and operator_balance_usdc < budget_remaining_usdc:
            return HarnessVerdict(
                decision=HarnessDecision.stop,
                reason="operator wallet balance below remaining budget",
                auto_stop=AutoStopReason.operator_balance_insufficient,
            )
        if self._attempts >= self.max_attempts:
            return HarnessVerdict(
                decision=HarnessDecision.stop,
                reason=f"max_attempts ({self.max_attempts}) reached",
                auto_stop=AutoStopReason.max_attempts,
            )

        host = self._host(target_url)
        bucket = self._buckets.setdefault(host, _RateBucket())
        self._trim_window(bucket.minute_window, 60.0)
        self._trim_window(bucket.hour_window, 3600.0)
        if len(bucket.minute_window) >= self.per_minute:
            return HarnessVerdict(
                decision=HarnessDecision.block,
                reason=f"rate limit: {self.per_minute} req/min on {host}",
            )
        if len(bucket.hour_window) >= self.per_hour:
            return HarnessVerdict(
                decision=HarnessDecision.block,
                reason=f"rate limit: {self.per_hour} req/hr on {host}",
            )
        if self._5xx_streak.get(host, 0) >= self.max_5xx_streak:
            return HarnessVerdict(
                decision=HarnessDecision.stop,
                reason=f"target {host} returned 5xx {self.max_5xx_streak} times in a row",
                auto_stop=AutoStopReason.target_5xx_streak,
            )

        return HarnessVerdict(decision=HarnessDecision.allow, reason="ok")

    def record_attempt(self, target_url: str) -> None:
        host = self._host(target_url)
        bucket = self._buckets.setdefault(host, _RateBucket())
        now = time.monotonic()
        bucket.minute_window.append(now)
        bucket.hour_window.append(now)
        self._attempts += 1

    def record_status(self, target_url: str, status_code: int) -> None:
        host = self._host(target_url)
        if 500 <= status_code < 600:
            self._5xx_streak[host] = self._5xx_streak.get(host, 0) + 1
        else:
            self._5xx_streak[host] = 0

    @property
    def attempts(self) -> int:
        return self._attempts
