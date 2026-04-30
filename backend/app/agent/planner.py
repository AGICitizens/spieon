from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.agent.llm import default_model, get_anthropic
from app.config import get_settings
from app.probes.registry import iter_probes

log = logging.getLogger(__name__)


SELECT_TOOL = {
    "name": "select_probes",
    "description": (
        "Decide which registered probes to run, in priority order, against the target. "
        "Always call this tool exactly once."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["probe_ids", "rationale"],
        "properties": {
            "probe_ids": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string"},
                "description": "Registered probe ids in execution order.",
            },
            "rationale": {
                "type": "string",
                "description": "One-sentence justification of the chosen ordering.",
            },
        },
    },
}


PLANNER_SYSTEM = (
    "You are the planning step of an autonomous security agent. Given a target URL, "
    "any prior heuristics about that target type, and the available probe palette, "
    "pick which probes to run and in which order. Prefer high-information-per-USDC "
    "probes first. Skip probes that are obviously irrelevant for the target shape. "
    "Always call the select_probes tool exactly once."
)


@dataclass(slots=True)
class PlannerHint:
    probe_id: str
    rule: str
    success_rate: float
    sample_size: int


@dataclass(slots=True)
class PlannerInput:
    target_url: str
    target_type: str | None = None
    hints: list[PlannerHint] = field(default_factory=list)


def _registered_probe_payload() -> list[dict]:
    return [
        {
            "id": spec.id,
            "probe_class": spec.probe_class,
            "severity_cap": spec.severity_cap.value,
            "cost_estimate_usdc": str(spec.cost_estimate_usdc),
            "owasp_id": spec.owasp_id,
            "atlas_technique_id": spec.atlas_technique_id,
            "description": spec.description,
        }
        for spec in iter_probes()
    ]


def _deterministic_plan() -> list[str]:
    return sorted(spec.id for spec in iter_probes())


async def plan_probes(
    payload: PlannerInput,
    *,
    model: str | None = None,
) -> tuple[list[str], str]:
    settings = get_settings()
    if not settings.anthropic_api_key:
        return _deterministic_plan(), "deterministic plan: no ANTHROPIC_API_KEY"

    available = _registered_probe_payload()
    user_message = json.dumps(
        {
            "target_url": payload.target_url,
            "target_type": payload.target_type,
            "available_probes": available,
            "prior_hints": [
                {
                    "probe_id": h.probe_id,
                    "rule": h.rule,
                    "success_rate": h.success_rate,
                    "sample_size": h.sample_size,
                }
                for h in payload.hints
            ],
        },
        sort_keys=True,
    )

    try:
        client = get_anthropic()
        response = await client.messages.create(
            model=model or default_model(),
            max_tokens=2048,
            system=PLANNER_SYSTEM,
            tools=[SELECT_TOOL],
            tool_choice={"type": "tool", "name": "select_probes"},
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as exc:
        log.warning("planner LLM failed, falling back to deterministic plan: %s", exc)
        return _deterministic_plan(), f"deterministic plan: planner error ({exc})"

    registered_ids = {spec.id for spec in iter_probes()}
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "select_probes":
            input_data = block.input or {}
            ids = input_data.get("probe_ids") or []
            rationale = str(input_data.get("rationale") or "")
            filtered = [p for p in ids if p in registered_ids]
            if filtered:
                return filtered, rationale or "planner-selected"

    return _deterministic_plan(), "deterministic plan: planner returned no usable selection"
