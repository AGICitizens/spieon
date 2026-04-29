from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


def _replace(_: Any, new: Any) -> Any:
    return new


def _append_unique(prev: list[str] | None, new: list[str] | None) -> list[str]:
    out = list(prev or [])
    seen = set(out)
    for item in new or []:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


class ScanState(TypedDict, total=False):
    scan_id: uuid.UUID
    target_url: str

    budget_usdc: Decimal
    spent_usdc: Annotated[Decimal, _replace]

    planned_probes: Annotated[list[str], _replace]
    findings: Annotated[list[dict[str, Any]], _replace]
    memory_refs: Annotated[list[str], _append_unique]

    adapt_iterations: Annotated[int, _replace]

    last_phase: Annotated[str, _replace]
    last_observation: Annotated[dict[str, Any], _replace]

    messages: Annotated[list, add_messages]
