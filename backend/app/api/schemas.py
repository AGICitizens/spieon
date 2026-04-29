from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.scan import ScanStatus


class ScanCreate(BaseModel):
    target_url: str = Field(min_length=1, max_length=2048)
    operator_address: str = Field(min_length=1, max_length=64)
    recipient_pubkey: str = Field(min_length=1, max_length=128)
    budget_usdc: Decimal = Field(default=Decimal("0"))
    bounty_usdc: Decimal = Field(default=Decimal("0"))
    consent: bool


class ScanRead(BaseModel):
    id: uuid.UUID
    target_url: str
    operator_address: str
    recipient_pubkey: str
    budget_usdc: Decimal
    bounty_usdc: Decimal
    spent_usdc: Decimal
    status: ScanStatus
    consent_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    adapt_iterations: int
    error: str | None
    created_at: datetime
    updated_at: datetime
