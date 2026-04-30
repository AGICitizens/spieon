from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.agent.planner import PlannerHint, PlannerInput, plan_probes
from app.agent.tools.narrate import NarrateDecision, write_narration
from app.chain import attest_finding, encrypt_bundle
from app.chain.eas import FindingAttestationPayload
from app.config import get_settings
from app.db import get_sessionmaker
from app.memory import consolidate as memory_consolidate
from app.memory.recall import recall_heuristics
from app.models.finding import Finding
from app.models.narration import Phase
from app.models.scan import Scan
from app.patches import build_patches
from app.probes import ProbePlanItem, normalize_finding, run_plan
from app.probes.registry import list_probe_ids
from app.safety import SafetyHarness
from app.storage import get_bundle_storage
from app.workflow.state import ScanState


def _classify_target(target_url: str) -> str:
    text = (target_url or "").lower()
    if "/mcp" in text or text.endswith("/jsonrpc"):
        return "mcp-http"
    if "/sse" in text:
        return "mcp-sse"
    if "x402" in text or "/pay" in text or "/protected" in text:
        return "x402-http"
    return "http"

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


async def _load_scan(session: AsyncSession, scan_id: uuid.UUID) -> Scan | None:
    result = await session.execute(select(Scan).where(Scan.id == scan_id))
    return result.scalar_one_or_none()


async def _findings_for_scan(
    session: AsyncSession, scan_id: uuid.UUID
) -> list[Finding]:
    result = await session.execute(
        select(Finding).where(Finding.scan_id == scan_id).order_by(Finding.created_at)
    )
    return list(result.scalars().all())


def _make_nodes(sessionmaker: async_sessionmaker | None) -> dict[str, NodeFn]:
    async def recon(state: ScanState) -> dict[str, Any]:
        target_url = state.get("target_url") or ""
        target_type = _classify_target(target_url)
        observations = {
            "target_url": target_url,
            "target_type": target_type,
            "tools_seen": 0,
        }
        await _emit(
            sessionmaker,
            state,
            phase=Phase.recon,
            content=f"Inspecting {target_url} (target_type={target_type}).",
            success=True,
            decision="recon",
            next_action="plan",
            target_observations=observations,
        )
        return {"last_phase": "recon", "last_observation": observations}

    async def plan(state: ScanState) -> dict[str, Any]:
        registered = set(list_probe_ids())
        existing = state.get("planned_probes") or []
        valid_existing = [p for p in existing if p in registered]
        if valid_existing:
            await _emit(
                sessionmaker,
                state,
                phase=Phase.plan,
                content=f"Continuing planned probe order: {', '.join(valid_existing)}.",
                success=True,
                decision="initial_plan",
                next_action="probe",
                context={"planned_probes": valid_existing},
            )
            return {"last_phase": "plan", "planned_probes": valid_existing}

        last_observation = state.get("last_observation") or {}
        target_type = last_observation.get("target_type")
        target_url = state.get("target_url") or ""

        hints: list[PlannerHint] = []
        if sessionmaker is not None and target_type:
            try:
                async with sessionmaker() as session:
                    rows = await recall_heuristics(
                        session, target_type=target_type, limit=5
                    )
                hints = [
                    PlannerHint(
                        probe_id=r.probe_class or "",
                        rule=r.rule,
                        success_rate=r.success_rate,
                        sample_size=r.sample_size,
                    )
                    for r in rows
                ]
            except Exception:
                hints = []

        plan_input = PlannerInput(
            target_url=target_url,
            target_type=target_type,
            hints=hints,
        )
        chosen, rationale = await plan_probes(plan_input)
        valid = [p for p in chosen if p in registered]
        if not valid:
            valid = sorted(registered)
            rationale = "fallback: planner returned no valid ids"

        await _emit(
            sessionmaker,
            state,
            phase=Phase.plan,
            content=f"Plan: {', '.join(valid)}. {rationale}",
            success=True,
            decision="initial_plan",
            next_action="probe",
            context={
                "planned_probes": valid,
                "rationale": rationale,
                "hint_count": len(hints),
            },
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

            findings_payload: list[dict[str, Any]] = []
            for raw in report.consolidated:
                row = normalize_finding(raw, scan_id=scan_id)
                session.add(row)
                await session.flush()
                findings_payload.append(
                    {
                        "id": str(row.id),
                        "title": row.title,
                        "severity": row.severity.value if hasattr(row.severity, "value") else str(row.severity),
                        "module_hash": row.module_hash,
                        "owasp_id": row.owasp_id,
                        "cost_usdc": str(row.cost_usdc),
                    }
                )
            await session.commit()

        spent = (state.get("spent_usdc") or Decimal("0")) + report.total_cost_usdc

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
        findings = state.get("findings") or []
        await _emit(
            sessionmaker,
            state,
            phase=Phase.reflect,
            content=(
                f"Found {len(findings)} candidate findings. Forwarding to verify."
                if findings
                else "No findings surfaced this pass. Adapting before retry."
            ),
            success=bool(findings),
            decision="forward_to_verify" if findings else "no_findings",
            next_action="adapt",
        )
        return {"last_phase": "reflect"}

    async def adapt(state: ScanState) -> dict[str, Any]:
        n = (state.get("adapt_iterations") or 0) + 1
        await _emit(
            sessionmaker,
            state,
            phase=Phase.adapt,
            content=f"Adaptive iteration {n}: forwarding to verify.",
            decision="forward_to_verify",
            next_action="verify",
            context={"adapt_iterations": n},
        )
        return {"last_phase": "adapt", "adapt_iterations": n}

    async def verify(state: ScanState) -> dict[str, Any]:
        scan_id = state.get("scan_id")
        if sessionmaker is None or scan_id is None:
            await _emit(
                sessionmaker,
                state,
                phase=Phase.verify,
                content="Verify skipped — no DB session bound.",
                success=None,
                next_action="attest",
            )
            return {"last_phase": "verify", "findings": state.get("findings") or []}

        async with sessionmaker() as session:
            rows = await _findings_for_scan(session, scan_id)
            verified_payload = [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "severity": row.severity.value if hasattr(row.severity, "value") else str(row.severity),
                    "module_hash": row.module_hash,
                    "owasp_id": row.owasp_id,
                    "cost_usdc": str(row.cost_usdc),
                }
                for row in rows
            ]

        await _emit(
            sessionmaker,
            state,
            phase=Phase.verify,
            content=f"Verified {len(verified_payload)} findings against DB.",
            success=bool(verified_payload),
            next_action="attest",
            context={"verified_count": len(verified_payload)},
        )
        return {"last_phase": "verify", "findings": verified_payload}

    async def attest(state: ScanState) -> dict[str, Any]:
        scan_id = state.get("scan_id")
        if sessionmaker is None or scan_id is None:
            await _emit(
                sessionmaker,
                state,
                phase=Phase.attest,
                content="Attestation skipped — no DB session bound.",
                success=None,
                next_action="consolidate",
            )
            return {"last_phase": "attest"}

        attested_count = 0
        async with sessionmaker() as session:
            scan = await _load_scan(session, scan_id)
            rows = await _findings_for_scan(session, scan_id)

            for row in rows:
                if row.eas_attestation_uid:
                    continue
                severity_value = (
                    row.severity.value
                    if hasattr(row.severity, "value")
                    else str(row.severity)
                )
                bundle_payload = {
                    "scan_id": str(scan_id),
                    "finding_id": str(row.id),
                    "title": row.title,
                    "summary": row.summary,
                    "severity": severity_value,
                    "module_hash": row.module_hash,
                    "owasp_id": row.owasp_id,
                    "atlas_technique_id": row.atlas_technique_id,
                    "cost_usdc": str(row.cost_usdc),
                    "patches": [
                        {
                            "format": patch.format,
                            "filename": patch.filename,
                            "content": patch.content,
                        }
                        for patch in build_patches(
                            {
                                "id": str(row.id),
                                "title": row.title,
                                "summary": row.summary,
                                "severity": severity_value,
                                "module_hash": row.module_hash,
                                "owasp_id": row.owasp_id,
                                "atlas_technique_id": row.atlas_technique_id,
                                "probe_id": row.module_hash,
                            }
                        )
                    ],
                }
                if scan and scan.recipient_pubkey:
                    bundle = encrypt_bundle(
                        bundle_payload, recipient_pubkey=scan.recipient_pubkey
                    )
                    row.ciphertext_sha256 = bundle.sha256
                    storage = get_bundle_storage()
                    try:
                        row.encrypted_bundle_uri = await storage.put(
                            scan_id=str(scan_id),
                            finding_id=str(row.id),
                            ciphertext=bundle.ciphertext,
                        )
                    except Exception:
                        row.encrypted_bundle_uri = None

                payload = FindingAttestationPayload(
                    scan_id=scan_id,
                    target=scan.target_url if scan else "",
                    severity=row.severity.value if hasattr(row.severity, "value") else str(row.severity),
                    module_hash=row.module_hash,
                    cost_usdc=row.cost_usdc,
                    encrypted_bundle_uri=row.encrypted_bundle_uri,
                    ciphertext_sha256=row.ciphertext_sha256,
                    owasp_id=row.owasp_id,
                    atlas_technique_id=row.atlas_technique_id,
                    maestro_id=row.maestro_id,
                )
                uid = await attest_finding(payload)
                row.eas_attestation_uid = uid
                row.attested_at = datetime.now(UTC)
                session.add(row)
                attested_count += 1
            await session.commit()

        await _emit(
            sessionmaker,
            state,
            phase=Phase.attest,
            content=f"Attested {attested_count} findings on chain.",
            success=attested_count > 0 or len(state.get("findings") or []) == 0,
            next_action="consolidate",
            context={"attested_count": attested_count},
        )
        return {"last_phase": "attest"}

    async def consolidate(state: ScanState) -> dict[str, Any]:
        if sessionmaker is None:
            await _emit(
                sessionmaker,
                state,
                phase=Phase.consolidate,
                content="Consolidate skipped — no DB session bound.",
                success=None,
                next_action=None,
            )
            return {"last_phase": "consolidate"}

        async with sessionmaker() as session:
            report = await memory_consolidate(session)

        await _emit(
            sessionmaker,
            state,
            phase=Phase.consolidate,
            content=(
                f"Consolidation: {report.promoted_to_l2} L1→L2,"
                f" {report.promoted_to_l3} L2→L3, {report.dropped_l2} stale dropped."
            ),
            success=True,
            next_action=None,
            context={
                "promoted_to_l2": report.promoted_to_l2,
                "promoted_to_l3": report.promoted_to_l3,
                "dropped_l2": report.dropped_l2,
            },
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
