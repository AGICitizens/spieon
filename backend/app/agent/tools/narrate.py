from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm import schema_to_tool
from app.models.narration import NarrationEvent, Phase
from app.observability import get_langfuse
from app.realtime import narration_broker


class NarrateDecision(BaseModel):
    phase: Phase
    success_signal: bool | None = Field(
        default=None,
        description="Did the action that just completed succeed? Null for narrative-only events.",
    )
    target_observations: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured observations about the target. Keys are short snake_case names.",
    )
    decision: str | None = Field(
        default=None,
        max_length=64,
        description=(
            "Short tag describing the decision taken in this phase, e.g. 'continue_planned', "
            "'mutate', 'pivot', 'forward_to_verify', 'initial_plan', or a probe id."
        ),
    )
    next_action: str | None = Field(
        default=None,
        max_length=128,
        description="Short label describing the immediately following action.",
    )
    content: str = Field(
        min_length=1,
        description="Human-readable narration shown live in the dashboard.",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form bag — memory IDs used, cost so far, planner state.",
    )


NARRATE_DECISION_TOOL = schema_to_tool(
    "narrate_decision",
    "Emit one structured narration event. Call this exactly once per phase transition.",
    NarrateDecision,
)


def render_fallback_template(phase: Phase, success: bool | None) -> str:
    base = {
        Phase.recon: "Inspecting target",
        Phase.plan: "Drafting probe plan",
        Phase.probe: "Running probe",
        Phase.reflect: "Reflecting on probe outcome",
        Phase.adapt: "Choosing next move",
        Phase.verify: "Verifying finding",
        Phase.attest: "Attesting on chain",
        Phase.consolidate: "Consolidating memory",
    }[phase]
    if success is True:
        return f"{base} — succeeded."
    if success is False:
        return f"{base} — failed; surfacing for adaptation."
    return f"{base}."


async def write_narration(
    session: AsyncSession,
    *,
    scan_id: uuid.UUID,
    payload: NarrateDecision,
    probe_run_id: uuid.UUID | None = None,
) -> NarrationEvent:
    event = NarrationEvent(
        scan_id=scan_id,
        probe_run_id=probe_run_id,
        phase=payload.phase,
        success_signal=payload.success_signal,
        target_observations=payload.target_observations,
        decision=payload.decision,
        next_action=payload.next_action,
        content=payload.content,
        context=payload.context,
    )
    session.add(event)
    await session.flush()
    await session.refresh(event)

    await narration_broker.publish(
        scan_id,
        {
            "id": str(event.id),
            "scan_id": str(scan_id),
            "phase": payload.phase.value,
            "success_signal": payload.success_signal,
            "target_observations": payload.target_observations,
            "decision": payload.decision,
            "next_action": payload.next_action,
            "content": payload.content,
            "context": payload.context,
            "created_at": event.created_at.isoformat(),
        },
    )

    client = get_langfuse()
    if client is not None:
        try:
            with client.start_as_current_span(
                name=f"narrate.{payload.phase.value}",
                input=payload.model_dump(mode="json"),
            ):
                pass
        except Exception:
            pass

    return event


async def narrate_from_tool_input(
    session: AsyncSession,
    *,
    scan_id: uuid.UUID,
    raw: dict[str, Any] | str,
    probe_run_id: uuid.UUID | None = None,
) -> NarrationEvent:
    if isinstance(raw, str):
        try:
            import json

            raw = json.loads(raw)
        except Exception:
            raw = {}

    try:
        payload = NarrateDecision.model_validate(raw)
    except Exception:
        phase = (
            Phase(raw.get("phase"))
            if isinstance(raw, dict) and raw.get("phase") in {p.value for p in Phase}
            else Phase.reflect
        )
        success = raw.get("success_signal") if isinstance(raw, dict) else None
        payload = NarrateDecision(
            phase=phase,
            success_signal=success if isinstance(success, bool) else None,
            content=render_fallback_template(phase, success if isinstance(success, bool) else None),
        )

    return await write_narration(
        session, scan_id=scan_id, payload=payload, probe_run_id=probe_run_id
    )
