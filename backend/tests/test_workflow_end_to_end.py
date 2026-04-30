from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pyrage
import pytest
from sqlmodel import select

from app.cost.meter import CostMeter
from app.db import get_sessionmaker
from app.models.finding import Finding, Severity
from app.models.probe_run import ProbeEngine
from app.models.scan import Scan, ScanStatus
from app.probes.normalize import RawFinding
from app.probes.protocol import ProbeContext, ProbeOutcome
from app.probes.registry import _REGISTRY, ProbeSpec, register_probe
from app.workflow.graph import build_graph


class _StubFindingProbe:
    id = "wf-stub-finding"

    async def run(self, ctx: ProbeContext, *, meter: CostMeter) -> ProbeOutcome:
        return ProbeOutcome(
            vulnerable=True,
            findings=[
                RawFinding(
                    title="workflow stub finding",
                    summary="finding emitted by the end-to-end workflow stub probe",
                    severity=Severity.high,
                    module_hash="0x" + "ee" * 32,
                    owasp_id="API07",
                    atlas_technique_id="AML.T0049",
                    cost_usdc=Decimal("0.10"),
                    signature_parts=("0x" + "ee" * 32, "wf-stub"),
                )
            ],
            cost_usdc=Decimal("0.10"),
            response_excerpt="stub probe payload",
        )


@pytest.fixture(autouse=True)
def _register_stub():
    if "wf-stub-finding" not in _REGISTRY:
        register_probe(
            ProbeSpec(
                id="wf-stub-finding",
                engine=ProbeEngine.native,
                probe_class="x402-replay",
                severity_cap=Severity.high,
                cost_estimate_usdc=Decimal("0.10"),
                owasp_id="API07",
                atlas_technique_id="AML.T0049",
                maestro_id=None,
                factory=_StubFindingProbe,
                module_hash="0x" + "ee" * 32,
            )
        )
    yield
    _REGISTRY.pop("wf-stub-finding", None)


@pytest.mark.asyncio
async def test_workflow_persists_attests_and_consolidates() -> None:
    identity = pyrage.x25519.Identity.generate()
    recipient = str(identity.to_public())

    sessionmaker = get_sessionmaker()
    scan_id = uuid.uuid4()
    async with sessionmaker() as s:
        s.add(
            Scan(
                id=scan_id,
                target_url="https://target.example/wf",
                operator_address="0xtest",
                recipient_pubkey=recipient,
                consent_at=datetime.now(UTC),
                status=ScanStatus.pending,
            )
        )
        await s.commit()

    graph = build_graph(sessionmaker).compile()
    state = await graph.ainvoke(
        {
            "scan_id": scan_id,
            "target_url": "https://target.example/wf",
            "budget_usdc": Decimal("1.00"),
            "spent_usdc": Decimal("0"),
            "planned_probes": ["wf-stub-finding"],
            "findings": [],
            "memory_refs": [],
            "adapt_iterations": 0,
        }
    )

    assert state["last_phase"] == "consolidate"
    assert len(state["findings"]) == 1
    assert state["findings"][0]["title"] == "workflow stub finding"

    async with sessionmaker() as s:
        result = await s.execute(
            select(Finding).where(Finding.scan_id == scan_id)
        )
        rows = list(result.scalars().all())
    assert len(rows) == 1
    row = rows[0]
    assert row.eas_attestation_uid is not None
    assert row.eas_attestation_uid.startswith("0x")
    assert len(row.eas_attestation_uid) == 66
    assert row.ciphertext_sha256 is not None
    assert len(row.ciphertext_sha256) == 64
    assert row.attested_at is not None
