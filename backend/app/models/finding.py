import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.scan import Scan


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Finding(TimestampMixin, table=True):
    __tablename__ = "findings"
    __table_args__ = (UniqueConstraint("scan_id", "dedup_key", name="uq_finding_scan_dedup"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    scan_id: uuid.UUID = Field(foreign_key="scans.id", index=True)

    severity: Severity = Field(index=True)
    title: str = Field(max_length=512)
    summary: str

    # Module attribution — hex-encoded 32-byte hash of the probe code
    module_hash: str = Field(max_length=128, index=True)

    # Cost-of-exploit (sum of contributing probe costs; PRD §7)
    cost_usdc: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=6)

    # Taxonomy mappings — populated at verify-time (PRD §9.2 EAS schema)
    owasp_id: str | None = Field(default=None, max_length=64)
    atlas_technique_id: str | None = Field(default=None, max_length=64)
    maestro_id: str | None = Field(default=None, max_length=64)

    # Onchain artifacts
    encrypted_bundle_uri: str | None = Field(default=None, max_length=512)
    ciphertext_sha256: str | None = Field(default=None, max_length=64)  # hex
    eas_attestation_uid: str | None = Field(default=None, max_length=128, index=True)
    attested_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

    # Cross-engine dedupe key (attack-signature hash; unique per scan)
    dedup_key: str = Field(max_length=128, index=True)

    scan: "Scan" = Relationship(back_populates="findings")
