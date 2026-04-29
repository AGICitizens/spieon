"""Three-tier memory tables (PRD §5).

Layer 1 — `MemoryEvent`: raw scan events, no filtering, last 50 scans / 7 days.
Layer 2 / Layer 3 — `MemoryItem`: consolidated items with `tier` distinguishing
working memory (awaiting judgment) from long-term store (promoted, summarized).
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.scan import Scan


# Embedding dimension matches OpenAI `text-embedding-3-small` (1536). If we
# switch model families we'll need a migration to alter the column width.
EMBEDDING_DIM = 1536


class MemoryEventType(str, Enum):
    probe_result = "probe_result"
    target_observation = "target_observation"
    reflection = "reflection"
    plan_revision = "plan_revision"
    error = "error"


class MemoryTier(str, Enum):
    working = "working"    # Layer 2 — awaiting judgment
    longterm = "longterm"  # Layer 3 — promoted, summarized


class MemoryEvent(TimestampMixin, table=True):
    """Layer 1 hot buffer: raw, unfiltered scan events."""

    __tablename__ = "memory_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    scan_id: uuid.UUID = Field(foreign_key="scans.id", index=True)
    probe_run_id: uuid.UUID | None = Field(
        default=None, foreign_key="probe_runs.id", index=True
    )

    event_type: MemoryEventType = Field(index=True, sa_type=String(32))
    content: str

    # Optional generalization keys — let heuristic consolidation cluster events
    # like "FastMCP targets accepting unicode tool descriptions".
    target_type: str | None = Field(default=None, max_length=128, index=True)
    probe_class: str | None = Field(default=None, max_length=128, index=True)

    # Vector index (HNSW) is added in the alembic migration, not here.
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(EMBEDDING_DIM), nullable=True),
    )

    scan: "Scan" = Relationship(back_populates="memory_events")


class MemoryItem(TimestampMixin, table=True):
    """Layer 2 (working) and Layer 3 (long-term) memory.

    Tier distinguishes the two; items move via the consolidation pass
    (PRD §5.2 — usefulness_score / cycles_unused thresholds).
    """

    __tablename__ = "memory_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    tier: MemoryTier = Field(default=MemoryTier.working, index=True, sa_type=String(32))
    content: str

    # Source events that this item summarizes (UUIDs of MemoryEvent rows)
    source_event_ids: list[str] = Field(default_factory=list, sa_type=JSONB)

    # Consolidation counters (PRD §5.2)
    usefulness_score: int = Field(default=0, index=True)
    cycles_unused: int = Field(default=0)
    retrieval_count: int = Field(default=0)
    last_retrieved: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)
    )

    # Generalization keys
    target_type: str | None = Field(default=None, max_length=128, index=True)
    probe_class: str | None = Field(default=None, max_length=128, index=True)

    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(EMBEDDING_DIM), nullable=True),
    )
