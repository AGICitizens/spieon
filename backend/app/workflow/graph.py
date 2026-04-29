from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph

from app.config import get_settings
from app.workflow.state import ScanState


async def recon_node(state: ScanState) -> dict[str, Any]:
    return {
        "last_phase": "recon",
        "last_observation": {"target_url": state.get("target_url"), "tools_seen": 0},
    }


async def plan_node(state: ScanState) -> dict[str, Any]:
    planned = state.get("planned_probes") or ["x402-replay", "schema-poisoning"]
    return {"last_phase": "plan", "planned_probes": planned}


async def probe_node(state: ScanState) -> dict[str, Any]:
    return {"last_phase": "probe", "spent_usdc": state.get("spent_usdc") or Decimal("0")}


async def reflect_node(state: ScanState) -> dict[str, Any]:
    return {"last_phase": "reflect"}


async def adapt_node(state: ScanState) -> dict[str, Any]:
    return {
        "last_phase": "adapt",
        "adapt_iterations": (state.get("adapt_iterations") or 0) + 1,
    }


async def verify_node(state: ScanState) -> dict[str, Any]:
    return {"last_phase": "verify", "findings": state.get("findings") or []}


async def attest_node(state: ScanState) -> dict[str, Any]:
    return {"last_phase": "attest"}


async def consolidate_node(state: ScanState) -> dict[str, Any]:
    return {"last_phase": "consolidate"}


def build_graph() -> StateGraph:
    g = StateGraph(ScanState)

    g.add_node("recon", recon_node)
    g.add_node("plan", plan_node)
    g.add_node("probe", probe_node)
    g.add_node("reflect", reflect_node)
    g.add_node("adapt", adapt_node)
    g.add_node("verify", verify_node)
    g.add_node("attest", attest_node)
    g.add_node("consolidate", consolidate_node)

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


async def run_hello_world(target_url: str = "https://example.invalid") -> ScanState:
    async with checkpointer() as saver:
        compiled = build_graph().compile(checkpointer=saver)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        state: ScanState = {
            "scan_id": uuid.uuid4(),
            "target_url": target_url,
            "budget_usdc": Decimal("1.00"),
            "spent_usdc": Decimal("0"),
            "planned_probes": [],
            "findings": [],
            "memory_refs": [],
            "adapt_iterations": 0,
        }
        return await compiled.ainvoke(state, config=config)
