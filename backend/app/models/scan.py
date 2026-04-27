import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.narration import NarrationEvent
    from app.models.probe_run import ProbeRun


class ScanStatus(str, Enum):
    pending = "pending"
    running = "running"
    verifying = "verifying"
    attesting = "attesting"
    done = "done"
    failed = "failed"
    canceled = "canceled"


class Scan(TimestampMixin, table=True):
    __tablename__ = "scans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Target + operator
    target_url: str = Field(index=True, max_length=2048)
    operator_address: str = Field(index=True, max_length=64)

    # Encryption recipient — X25519 pubkey for `age`. Generated client-side.
    # Spieon never sees the matching private key. See PRD §9.5 / docs/IMPLEMENTATION_TODO.md.
    recipient_pubkey: str = Field(max_length=128)

    # Budgets and accounting (USDC; 6 decimals on Base Sepolia)
    budget_usdc: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=6)
    bounty_usdc: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=6)
    spent_usdc: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=6)

    # Lifecycle
    status: ScanStatus = Field(default=ScanStatus.pending, index=True)
    consent_at: datetime = Field(sa_type=DateTime(timezone=True))
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

    # Adaptive-attacker bookkeeping (cap on plan/probe/reflect cycles per scan)
    adapt_iterations: int = Field(default=0)

    error: str | None = Field(default=None)

    findings: list["Finding"] = Relationship(back_populates="scan")
    probe_runs: list["ProbeRun"] = Relationship(back_populates="scan")
    narration_events: list["NarrationEvent"] = Relationship(back_populates="scan")
