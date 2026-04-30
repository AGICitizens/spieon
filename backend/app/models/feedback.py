import uuid

from sqlmodel import Field

from app.models.base import TimestampMixin


class OperatorFeedback(TimestampMixin, table=True):
    __tablename__ = "operator_feedback"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    scan_id: uuid.UUID = Field(foreign_key="scans.id", index=True)
    operator_address: str = Field(max_length=64, index=True)

    score: int = Field(ge=1, le=5)
    rationale: str | None = Field(default=None, max_length=2048)

    onchain_tx_hash: str | None = Field(default=None, max_length=128, index=True)
