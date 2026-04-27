import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.scan import Scan


class ProbeEngine(str, Enum):
    garak = "garak"
    pyrit = "pyrit"
    snyk = "snyk"
    native = "native"


class ProbeRunStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"  # probe executed cleanly (regardless of vuln finding)
    failed = "failed"        # probe errored / target unreachable / etc.
    skipped = "skipped"      # safety harness blocked it


class ProbeRun(TimestampMixin, table=True):
    __tablename__ = "probe_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    scan_id: uuid.UUID = Field(foreign_key="scans.id", index=True)

    # Identity in the probe registry (e.g. "x402-replay-attack", "garak.promptinject")
    probe_id: str = Field(max_length=128, index=True)
    engine: ProbeEngine = Field(index=True)

    # Inputs / outputs (JSONB for query flexibility on Postgres)
    params: dict = Field(default_factory=dict, sa_type=JSONB)
    response_excerpt: str | None = Field(default=None)  # truncated capture for forensics

    # Lifecycle
    status: ProbeRunStatus = Field(default=ProbeRunStatus.pending, index=True)
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    finished_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    error: str | None = Field(default=None)

    # Did this probe surface a vulnerability? Only meaningful when status=succeeded.
    vulnerable: bool = Field(default=False, index=True)

    # Cost-of-exploit (USDC; aggregated into Finding.cost_usdc per PRD §7)
    cost_usdc: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=6)

    scan: "Scan" = Relationship(back_populates="probe_runs")
