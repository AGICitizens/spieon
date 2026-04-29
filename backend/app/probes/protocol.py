from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from app.cost.meter import CostMeter
from app.probes.normalize import RawFinding


@dataclass(slots=True)
class ProbeContext:
    scan_id: uuid.UUID
    probe_run_id: uuid.UUID
    target_url: str
    budget_remaining_usdc: Decimal
    params: dict[str, Any] = field(default_factory=dict)
    attribution_headers: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ProbeOutcome:
    vulnerable: bool
    findings: list[RawFinding] = field(default_factory=list)
    response_excerpt: str | None = None
    error: str | None = None
    cost_usdc: Decimal = Decimal("0")
    notes: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Probe(Protocol):
    id: str

    async def run(self, ctx: ProbeContext, *, meter: CostMeter) -> ProbeOutcome: ...
