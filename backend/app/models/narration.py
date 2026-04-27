import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.scan import Scan


class Phase(str, Enum):
    recon = "recon"
    plan = "plan"
    probe = "probe"
    reflect = "reflect"
    adapt = "adapt"
    verify = "verify"
    attest = "attest"
    consolidate = "consolidate"


class NarrationEvent(TimestampMixin, table=True):
    """One row per agent decision. Fans out to the WebSocket stream + Langfuse + memory.

    Shape mirrors the structured `narrate_decision` tool the agent calls
    (PRD §4.3 / IMPLEMENTATION_TODO.md). `content` is the human-readable line
    rendered in the dashboard; the structured fields drive the adapt logic.
    """

    __tablename__ = "narration_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    scan_id: uuid.UUID = Field(foreign_key="scans.id", index=True)
    probe_run_id: uuid.UUID | None = Field(
        default=None, foreign_key="probe_runs.id", index=True
    )

    phase: Phase = Field(index=True)

    # Did the just-completed action succeed? None = narrative-only event.
    success_signal: bool | None = Field(default=None)

    # Agent's structured observations about the target / probe response
    target_observations: dict = Field(default_factory=dict, sa_type=JSONB)

    # Free-form short tags so we can keep schema flexible across phases:
    #   adapt: "continue_planned" | "mutate" | "pivot" | "forward_to_verify"
    #   plan:  "initial_plan" | "replan"
    #   probe: probe_id
    decision: str | None = Field(default=None, max_length=64, index=True)
    next_action: str | None = Field(default=None, max_length=128)

    # The prose narration shown live in the dashboard
    content: str

    # Anything else worth keeping (memory IDs used, cost so far, planner state)
    context: dict = Field(default_factory=dict, sa_type=JSONB)

    scan: "Scan" = Relationship(back_populates="narration_events")
