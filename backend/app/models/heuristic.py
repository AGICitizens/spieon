"""Procedural memory — public, hash-attested onchain per version (PRD §5.1).

Heuristics are derived from Layer 3 patterns and exposed at `spieon.eth/memory.json`.
Each version is a fresh row + a fresh EAS attestation; we never mutate prior versions.
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import TimestampMixin
from app.models.memory import EMBEDDING_DIM


class Heuristic(TimestampMixin, table=True):
    __tablename__ = "heuristics"
    __table_args__ = (
        UniqueConstraint("heuristic_key", "version", name="uq_heuristic_key_version"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Slug identifying the heuristic across versions, e.g. "fastmcp-unicode-schema-poisoning"
    heuristic_key: str = Field(max_length=128, index=True)
    version: int = Field(default=1)

    # The natural-language rule shown in memory.json and inside the agent's recall context
    rule: str

    # Generalization keys — what kind of target / probe class does this rule cover?
    target_type: str | None = Field(default=None, max_length=128, index=True)
    probe_class: str | None = Field(default=None, max_length=128, index=True)

    # Evidence — UUIDs of scans and memory events that contributed
    evidence_scan_ids: list[str] = Field(default_factory=list, sa_type=JSONB)
    evidence_event_ids: list[str] = Field(default_factory=list, sa_type=JSONB)

    # Empirical support
    success_count: int = Field(default=0)
    sample_size: int = Field(default=0)
    success_rate: float = Field(default=0.0)  # success_count / sample_size, snapshot

    # Taxonomy mappings (mirrored into the EAS attestation)
    owasp_id: str | None = Field(default=None, max_length=64)
    atlas_technique_id: str | None = Field(default=None, max_length=64)

    # Content-addressing — hex sha256 of the canonical rule serialization.
    # Allows the public memory.json + EAS attestation to commit to the same bytes.
    content_hash: str = Field(max_length=64, index=True)

    # Onchain artifacts (populated after sync)
    eas_attestation_uid: str | None = Field(default=None, max_length=128, index=True)
    attested_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(EMBEDDING_DIM), nullable=True),
    )
