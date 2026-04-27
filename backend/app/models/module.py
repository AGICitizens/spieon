"""DB mirror of the onchain `ModuleRegistry` contract (PRD §9.2).

Source of truth lives onchain; this table is the cached read-side. A periodic
sync job pulls registered modules + their `timesUsed` / `successCount` counters
so the dashboard can render the leaderboard without an RPC round-trip per row.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field

from app.models.base import TimestampMixin
from app.models.finding import Severity


class Module(TimestampMixin, table=True):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("module_hash", name="uq_module_hash"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Hex-encoded bytes32 identifier from `ModuleRegistry.modules` mapping.
    # This is what `Finding.module_hash` refers to (loose coupling — no FK so
    # findings can record before the module sync catches up).
    module_hash: str = Field(max_length=128, index=True)

    # Author identity (resolved via ENS / NameStone where available)
    author_address: str = Field(max_length=64, index=True)
    author_ens_name: str | None = Field(default=None, max_length=255)

    # IPFS or ZeroG URI describing the module
    metadata_uri: str = Field(max_length=512)

    # Maximum severity this module is allowed to claim (enforces bounty caps)
    severity_cap: Severity = Field(default=Severity.medium)

    # Cached counters from chain
    times_used: int = Field(default=0)
    success_count: int = Field(default=0)

    # Taxonomy mappings — mirrors the onchain bytes32 fields
    owasp_id: str | None = Field(default=None, max_length=64, index=True)
    atlas_technique_id: str | None = Field(default=None, max_length=64, index=True)

    # Sync bookkeeping
    registered_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_synced_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
