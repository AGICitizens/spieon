from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.agent.tools.narrate import NarrateDecision, write_narration
from app.config import get_settings
from app.db import get_sessionmaker
from app.models.narration import Phase
from app.probes import ProbePlanItem, run_plan
from app.probes.registry import list_probe_ids
from app.safety import SafetyHarness
from app.workflow.state import ScanState

NodeFn = Callable[[ScanState], Awaitable[dict[str, Any]]]


async def _emit(
    sessionmaker: async_sessionmaker | None,
    state: ScanState,
    *,
    phase: Phase,
    content: str,
    success: bool | None = None,
    decision: str | None = None,
    next_action: str | None = None,
    target_observations: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> None:
    if sessionmaker is None:
        return
    scan_id = state.get("scan_id")
    if scan_id is None:
        return
    payload = NarrateDecision(
        phase=phase,
        content=content,
        success_signal=success,
        decision=decision,
        next_action=next_action,
        target_observations=target_observations or {},
        context=context or {},
    )
    async with sessionmaker() as session:
        await write_narration(session, scan_id=scan_id, payload=payload)
        await session.commit()


def _make_nodes(sessionmaker: async_sessionmaker | None) -> dict[str, NodeFn]:
    async def recon(state: ScanState) -> dict[str, Any]:
        observations = {"target_url": state.get("target_url"), "tools_seen": 0}
        await _emit(
            sessionmaker,
            state,
            phase=Phase.recon,
            content=f"Inspecting {state.get('target_url')}.",
            success=True,
            decision="recon",
            next_action="plan",
            target_observations=observations,
        )
        return {"last_phase": "recon", "last_observation": observations}

    async def plan(state: ScanState) -> dict[str, Any]:
        registered = set(list_probe_ids())
        planned = state.get("planned_probes") or list_probe_ids()
        valid = [p for p in planned if p in registered]
        await _emit(
            sessionmaker,
            state,
            phase=Phase.plan,
            content=f"Drafting probe order: {', '.join(valid) if valid else '(no probes)'}.",
            success=True,
            decision="initial_plan",
            next_action="probe",
            context={"planned_probes": valid},
        )
        return {"last_phase": "plan", "planned_probes": valid}

    async def probe(state: ScanState) -> dict[str, Any]:
        planned = state.get("planned_probes") or []
        target_url = state.get("target_url") or ""
        scan_id = state.get("scan_id")
        budget_remaining = (state.get("budget_usdc") or Decimal("0")) - (
            state.get("spent_usdc") or Decimal("0")
        )

        if sessionmaker is None or not planned or scan_id is None or not target_url:
            await _emit(
                sessionmaker,
                state,
                phase=Phase.probe,
                content="No probe plan to execute.",
                success=None,
                next_action="reflect",
            )
            return {
                "last_phase": "probe",
                "spent_usdc": state.get("spent_usdc") or Decimal("0"),
                "findings": state.get("findings") or [],
            }

        plan_items = [ProbePlanItem(probe_id=p) for p in planned]
        async with sessionmaker() as session:
            report = await run_plan(
                session,
                scan_id=scan_id,
                target_url=target_url,
                plan=plan_items,
                harness=SafetyHarness(),
                budget_usdc=budget_remaining,
            )
            await session.commit()

        spent = (state.get("spent_usdc") or Decimal("0")) + report.total_cost_usdc
        findings_payload = [
            {
                "title": f.title,
                "severity": f.severity.value,
                "module_hash": f.module_hash,
                "owasp_id": f.owasp_id,
                "cost_usdc": str(f.cost_usdc),
            }
            for f in report.consolidated
        ]

        skipped = sum(
            1 for e in report.executions if e.verdict and e.verdict.decision.value != "allow"
        )
        await _emit(
            sessionmaker,
            state,
            phase=Phase.probe,
            content=(
                f"Ran {len(report.executions)} probes, {len(findings_payload)} findings"
                f" survived dedupe, {skipped} skipped by harness."
            ),
            success=bool(findings_payload) or len(report.executions) > 0,
            next_action="reflect",
            context={
                "spent_usdc": str(spent),
                "auto_stop": report.auto_stop.value if report.auto_stop else None,
            },
        )

        return {
            "last_phase": "probe",
            "spent_usdc": spent,
            "findings": (state.get("findings") or []) + findings_payload,
        }

    async def reflect(state: ScanState) -> dict[str, Any]:
        await _emit(
            sessionmaker,
            state,
            phase=Phase.reflect,
            content="Reflecting on probe outcome.",
            decision="forward_to_verify",
            next_action="adapt",
        )
        return {"last_phase": "reflect"}

    async def adapt(state: ScanState) -> dict[str, Any]:
        n = (state.get("adapt_iterations") or 0) + 1
        await _emit(
            sessionmaker,
            state,
            phase=Phase.adapt,
            content=f"Adaptive iteration {n}: continuing planned probe.",
            decision="continue_planned",
            next_action="verify",
            context={"adapt_iterations": n},
        )
        return {"last_phase": "adapt", "adapt_iterations": n}

    async def verify(state: ScanState) -> dict[str, Any]:
        await _emit(
            sessionmaker,
            state,
            phase=Phase.verify,
            content="Verifying findings before attestation.",
            success=True,
            next_action="attest",
        )
        return {"last_phase": "verify", "findings": state.get("findings") or []}

    async def attest(state: ScanState) -> dict[str, Any]:
        await _emit(
            sessionmaker,
            state,
            phase=Phase.attest,
            content="Attesting findings on chain.",
            success=True,
            next_action="consolidate",
        )
        return {"last_phase": "attest"}

    async def consolidate(state: ScanState) -> dict[str, Any]:
        await _emit(
            sessionmaker,
            state,
            phase=Phase.consolidate,
            content="Consolidating memory and procedural heuristics.",
            success=True,
            next_action=None,
        )
        return {"last_phase": "consolidate"}

    return {
        "recon": recon,
        "plan": plan,
        "probe": probe,
        "reflect": reflect,
        "adapt": adapt,
        "verify": verify,
        "attest": attest,
        "consolidate": consolidate,
    }


def build_graph(sessionmaker: async_sessionmaker | None = None) -> StateGraph:
    nodes = _make_nodes(sessionmaker)
    g = StateGraph(ScanState)

    for name, fn in nodes.items():
        g.add_node(name, fn)

    g.add_edge(START, "recon")
    g.add_edge("recon", "plan")
    g.add_edge("plan", "probe")
    g.add_edge("probe", "reflect")
    g.add_edge("reflect", "adapt")
    g.add_edge("adapt", "verify")
    g.add_edge("verify", "attest")
    g.add_edge("attest", "consolidate")
    g.add_edge("consolidate", END)

    return g


def _psycopg_dsn() -> str:
    sync_url = get_settings().database_url_sync
    return sync_url.replace("postgresql+psycopg://", "postgresql://", 1)


@asynccontextmanager
async def checkpointer() -> AsyncIterator[AsyncPostgresSaver]:
    async with AsyncPostgresSaver.from_conn_string(_psycopg_dsn()) as saver:
        await saver.setup()
        yield saver


async def run_hello_world(
    target_url: str = "https://example.invalid",
    *,
    scan_id: uuid.UUID | None = None,
    emit_narration: bool = False,
) -> ScanState:
    sessionmaker = get_sessionmaker() if emit_narration else None
    async with checkpointer() as saver:
        compiled = build_graph(sessionmaker).compile(checkpointer=saver)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        state: ScanState = {
            "scan_id": scan_id or uuid.uuid4(),
            "target_url": target_url,
            "budget_usdc": Decimal("1.00"),
            "spent_usdc": Decimal("0"),
            "planned_probes": [],
            "findings": [],
            "memory_refs": [],
            "adapt_iterations": 0,
        }
        return await compiled.ainvoke(state, config=config)
