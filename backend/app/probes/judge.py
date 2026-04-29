from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from app.agent.llm import get_anthropic, judge_model
from app.probes.normalize import RawFinding

JUDGE_TOOL = {
    "name": "judge_finding",
    "description": (
        "Decide whether a probe finding looks like a real security issue or a false "
        "positive. Always call this tool exactly once."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["confirmed", "confidence", "rationale"],
        "properties": {
            "confirmed": {"type": "boolean"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"},
            "suggested_severity": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
            },
        },
    },
}


JUDGE_SYSTEM = (
    "You are a security finding triage judge. You will receive a structured probe "
    "finding and the supporting evidence. Decide whether the finding is a real "
    "vulnerability or a false positive. Be decisive but conservative — if "
    "evidence is missing, mark it not-confirmed with low confidence and explain "
    "what would convince you. Always call the judge_finding tool exactly once."
)


@dataclass(slots=True)
class Judgment:
    confirmed: bool
    confidence: float
    rationale: str
    suggested_severity: str | None


JudgeFn = Callable[[RawFinding, str | None], Awaitable[Judgment]]


def _serialize_finding(raw: RawFinding) -> str:
    return json.dumps(
        {
            "title": raw.title,
            "summary": raw.summary,
            "severity": raw.severity.value,
            "owasp_id": raw.owasp_id,
            "atlas_technique_id": raw.atlas_technique_id,
            "module_hash": raw.module_hash,
            "extra": raw.extra,
        },
        sort_keys=True,
    )


async def judge_finding(
    raw: RawFinding,
    evidence: str | None = None,
    *,
    client: AsyncAnthropic | None = None,
    model: str | None = None,
) -> Judgment:
    llm = client or get_anthropic()
    model_id = model or judge_model()

    user = (
        "Finding payload:\n"
        f"{_serialize_finding(raw)}\n\n"
        "Supporting evidence (probe response excerpt or notes):\n"
        f"{(evidence or '')[:4000]}"
    )

    response = await llm.messages.create(
        model=model_id,
        max_tokens=1024,
        system=JUDGE_SYSTEM,
        tools=[JUDGE_TOOL],
        tool_choice={"type": "tool", "name": "judge_finding"},
        messages=[{"role": "user", "content": user}],
    )

    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "judge_finding":
            payload = block.input
            return Judgment(
                confirmed=bool(payload.get("confirmed", False)),
                confidence=float(payload.get("confidence", 0.0)),
                rationale=str(payload.get("rationale", "")),
                suggested_severity=payload.get("suggested_severity"),
            )

    return Judgment(
        confirmed=False,
        confidence=0.0,
        rationale="judge tool returned no structured output",
        suggested_severity=None,
    )
