from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from app.agent.llm import default_model, get_anthropic
from app.config import get_settings
from app.probes.registry import iter_probes

log = logging.getLogger(__name__)

Decision = Literal["continue_planned", "mutate", "pivot", "forward_to_verify"]

REFLECT_TOOL = {
    "name": "reflect_on_scan",
    "description": (
        "Decide what the agent should do after the latest probe pass. Always call "
        "this tool exactly once."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["decision", "rationale"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": [
                    "continue_planned",
                    "mutate",
                    "pivot",
                    "forward_to_verify",
                ],
            },
            "next_probes": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "When decision is mutate or pivot, the ordered probe ids to run "
                    "next; ignored otherwise."
                ),
            },
            "rationale": {"type": "string"},
        },
    },
}

REFLECTOR_SYSTEM = (
    "You are the reflection step of an autonomous security agent. Given the most "
    "recent probe outcomes and remaining budget, choose one of four decisions: "
    "continue_planned (the rest of the planned probes still look promising), "
    "mutate (rerun a similar attack class with different parameters), pivot (try a "
    "different attack class against the same target), or forward_to_verify (we have "
    "enough findings to attest, or no probe is likely to surface more). Be cheap "
    "with the budget — do not pivot if the budget is tight. Always call the "
    "reflect_on_scan tool exactly once."
)


@dataclass(slots=True)
class ReflectResult:
    decision: Decision
    next_probes: list[str]
    rationale: str


def _registered_ids() -> list[str]:
    return [spec.id for spec in iter_probes()]


def _registered_payload() -> list[dict[str, Any]]:
    return [
        {
            "id": spec.id,
            "probe_class": spec.probe_class,
            "owasp_id": spec.owasp_id,
        }
        for spec in iter_probes()
    ]


async def reflect_decision(
    *,
    target_url: str,
    findings_so_far: list[dict[str, Any]],
    last_executions: list[dict[str, Any]],
    budget_remaining_usdc: str,
    adapt_iterations: int,
    max_iterations: int,
) -> ReflectResult:
    settings = get_settings()
    if not settings.anthropic_api_key:
        return _default_decision(findings_so_far, adapt_iterations, max_iterations)

    user = json.dumps(
        {
            "target_url": target_url,
            "findings_so_far": findings_so_far,
            "last_executions": last_executions,
            "budget_remaining_usdc": budget_remaining_usdc,
            "adapt_iterations": adapt_iterations,
            "max_iterations": max_iterations,
            "available_probes": _registered_payload(),
        },
        sort_keys=True,
    )
    try:
        client = get_anthropic()
        response = await client.messages.create(
            model=default_model(),
            max_tokens=1024,
            system=REFLECTOR_SYSTEM,
            tools=[REFLECT_TOOL],
            tool_choice={"type": "tool", "name": "reflect_on_scan"},
            messages=[{"role": "user", "content": user}],
        )
    except Exception as exc:
        log.warning("reflector LLM failed, defaulting to forward_to_verify: %s", exc)
        return _default_decision(findings_so_far, adapt_iterations, max_iterations)

    registered = set(_registered_ids())
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "reflect_on_scan":
            payload = block.input or {}
            decision = str(payload.get("decision", "forward_to_verify"))
            if decision not in {"continue_planned", "mutate", "pivot", "forward_to_verify"}:
                decision = "forward_to_verify"
            next_probes = [
                p for p in (payload.get("next_probes") or []) if p in registered
            ]
            rationale = str(payload.get("rationale") or "")
            if decision in {"mutate", "pivot"} and not next_probes:
                decision = "forward_to_verify"
                rationale = (
                    rationale + " (downgraded: no valid next_probes)"
                ).strip()
            return ReflectResult(
                decision=decision,  # type: ignore[arg-type]
                next_probes=next_probes,
                rationale=rationale,
            )

    return _default_decision(findings_so_far, adapt_iterations, max_iterations)


def _default_decision(
    findings_so_far: list[dict[str, Any]],
    adapt_iterations: int,
    max_iterations: int,
) -> ReflectResult:
    if findings_so_far or adapt_iterations >= max_iterations:
        return ReflectResult(
            decision="forward_to_verify",
            next_probes=[],
            rationale="default: have findings or hit iteration cap",
        )
    return ReflectResult(
        decision="forward_to_verify",
        next_probes=[],
        rationale="default: no API key, no need to loop",
    )
