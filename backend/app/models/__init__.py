"""SQLModel table definitions.

Importing this package registers every `table=True` model with SQLModel.metadata,
which is what Alembic autogenerate reads when producing migrations.
"""

from app.models.base import TimestampMixin, utcnow
from app.models.feedback import OperatorFeedback
from app.models.finding import Finding, Severity
from app.models.heuristic import Heuristic
from app.models.memory import (
    EMBEDDING_DIM,
    MemoryEvent,
    MemoryEventType,
    MemoryItem,
    MemoryTier,
)
from app.models.module import Module
from app.models.narration import NarrationEvent, Phase
from app.models.probe_run import ProbeEngine, ProbeRun, ProbeRunStatus
from app.models.scan import Scan, ScanStatus

__all__ = [
    "EMBEDDING_DIM",
    "Finding",
    "Heuristic",
    "MemoryEvent",
    "MemoryEventType",
    "MemoryItem",
    "MemoryTier",
    "Module",
    "NarrationEvent",
    "OperatorFeedback",
    "Phase",
    "ProbeEngine",
    "ProbeRun",
    "ProbeRunStatus",
    "Scan",
    "ScanStatus",
    "Severity",
    "TimestampMixin",
    "utcnow",
]
