from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.cost.meter import CostMeter
from app.db import get_sessionmaker
from app.models.finding import Severity
from app.models.probe_run import ProbeEngine, ProbeRunStatus
from app.models.scan import Scan, ScanStatus
from app.probes.normalize import RawFinding
from app.probes.protocol import ProbeContext, ProbeOutcome
from app.probes.registry import _REGISTRY, ProbeSpec, register_probe
from app.probes.runner import ProbePlanItem, run_plan
from app.safety.harness import SafetyHarness


class _StubReplayProbe:
    id = "stub-replay"

    async def run(self, ctx: ProbeContext, *, meter: CostMeter) -> ProbeOutcome:
        return ProbeOutcome(
            vulnerable=True,
            findings=[
                RawFinding(
                    title="stub replay accepted",
                    summary="stub probe always finds it",
                    severity=Severity.high,
                    module_hash="0x" + "11" * 32,
                    owasp_id="API07",
                    atlas_technique_id="AML.T0049",
                    cost_usdc=Decimal("0.10"),
                    signature_parts=("0x" + "11" * 32, "stub-replay"),
                )
            ],
            cost_usdc=Decimal("0.10"),
            response_excerpt="stub body",
        )


class _StubBlockedProbe:
    id = "stub-dos"

    async def run(self, ctx: ProbeContext, *, meter: CostMeter) -> ProbeOutcome:
        return ProbeOutcome(vulnerable=True, cost_usdc=Decimal("0"))


@pytest.fixture(autouse=True)
def _register_stubs():
    keep = {"stub-replay", "stub-dos"}
    if "stub-replay" not in _REGISTRY:
        register_probe(
            ProbeSpec(
                id="stub-replay",
                engine=ProbeEngine.native,
                probe_class="x402-replay",
                severity_cap=Severity.high,
                cost_estimate_usdc=Decimal("0.10"),
                owasp_id="API07",
                atlas_technique_id="AML.T0049",
                maestro_id=None,
                factory=_StubReplayProbe,
                module_hash="0x" + "11" * 32,
            )
        )
    if "stub-dos" not in _REGISTRY:
        register_probe(
            ProbeSpec(
                id="stub-dos",
                engine=ProbeEngine.native,
                probe_class="dos",
                severity_cap=Severity.high,
                cost_estimate_usdc=Decimal("0"),
                owasp_id=None,
                atlas_technique_id=None,
                maestro_id=None,
                factory=_StubBlockedProbe,
                module_hash="0x" + "22" * 32,
            )
        )
    yield
    for k in list(_REGISTRY.keys()):
        if k in keep:
            del _REGISTRY[k]


async def _make_scan(target: str = "https://target.example/x") -> uuid.UUID:
    async with get_sessionmaker()() as s:
        scan = Scan(
            target_url=target,
            operator_address="0x1",
            recipient_pubkey="pk",
            consent_at=datetime.now(UTC),
            status=ScanStatus.pending,
        )
        s.add(scan)
        await s.commit()
        await s.refresh(scan)
        return scan.id


@pytest.mark.asyncio
async def test_run_plan_persists_probe_runs_and_dedupes_findings() -> None:
    scan_id = await _make_scan()

    async with get_sessionmaker()() as session:
        report = await run_plan(
            session,
            scan_id=scan_id,
            target_url="https://target.example/x",
            plan=[
                ProbePlanItem(probe_id="stub-replay"),
                ProbePlanItem(probe_id="stub-replay"),  # second one should dedupe out
            ],
            harness=SafetyHarness(),
            budget_usdc=Decimal("1.00"),
        )
        await session.commit()

    assert len(report.executions) == 2
    for execution in report.executions:
        assert execution.probe_run.status is ProbeRunStatus.succeeded
        assert execution.probe_run.vulnerable is True
        assert execution.probe_run.cost_usdc == Decimal("0.10")

    assert len(report.consolidated) == 1
    merged = report.consolidated[0]
    assert merged.cost_usdc == Decimal("0.20")  # summed across the two runs
    assert report.total_cost_usdc == Decimal("0.20")
    assert report.auto_stop is None


@pytest.mark.asyncio
async def test_run_plan_skips_destructive_probes() -> None:
    scan_id = await _make_scan()

    async with get_sessionmaker()() as session:
        report = await run_plan(
            session,
            scan_id=scan_id,
            target_url="https://target.example/x",
            plan=[
                ProbePlanItem(probe_id="stub-dos"),
                ProbePlanItem(probe_id="stub-replay"),
            ],
            harness=SafetyHarness(),
            budget_usdc=Decimal("1.00"),
        )
        await session.commit()

    statuses = [e.probe_run.status for e in report.executions]
    assert statuses[0] is ProbeRunStatus.skipped
    assert statuses[1] is ProbeRunStatus.succeeded
    assert len(report.consolidated) == 1
    assert report.consolidated[0].title == "stub replay accepted"


@pytest.mark.asyncio
async def test_run_plan_auto_stops_on_budget_exhaustion() -> None:
    scan_id = await _make_scan()

    async with get_sessionmaker()() as session:
        report = await run_plan(
            session,
            scan_id=scan_id,
            target_url="https://target.example/x",
            plan=[
                ProbePlanItem(probe_id="stub-replay"),
                ProbePlanItem(probe_id="stub-replay"),
            ],
            harness=SafetyHarness(),
            budget_usdc=Decimal("0.05"),  # less than one probe's cost
        )
        await session.commit()

    assert report.auto_stop is not None
    assert report.auto_stop.value == "budget_exhausted"
    statuses = [e.probe_run.status for e in report.executions]
    assert statuses[0] is ProbeRunStatus.succeeded
    assert statuses[1] is ProbeRunStatus.skipped
