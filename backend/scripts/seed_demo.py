"""Seed the local DB with demo data so a fresh clone has something to render.

Usage:
    cd backend
    uv run python scripts/seed_demo.py

Idempotent: each run inserts a fresh batch of scans + findings + heuristics
keyed off a UTC timestamp suffix.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pyrage

from app.chain.eas import FindingAttestationPayload, attest_finding
from app.chain.encrypt import encrypt_bundle
from app.db import get_sessionmaker
from app.memory.procedural import attach_attestation, record_heuristic
from app.models.finding import Finding, Severity
from app.models.narration import NarrationEvent, Phase
from app.models.scan import Scan, ScanStatus


async def _seed_scan(
    *,
    target_url: str,
    findings_spec: list[dict[str, object]],
    when: datetime,
) -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        identity = pyrage.x25519.Identity.generate()
        recipient = str(identity.to_public())

        scan = Scan(
            target_url=target_url,
            operator_address="0xDemoOperator0000000000000000000000DemoOp",
            recipient_pubkey=recipient,
            budget_usdc=Decimal("1.0"),
            bounty_usdc=Decimal("5.0"),
            spent_usdc=Decimal("0.30"),
            status=ScanStatus.done,
            consent_at=when,
            started_at=when,
            completed_at=when + timedelta(minutes=2),
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)

        narration_lines = [
            (Phase.recon, "Inspecting target."),
            (Phase.plan, "Plan: x402-replay-attack, mcp-tool-description-injection."),
            (Phase.probe, "Running planned probes."),
            (Phase.reflect, "Two findings, forwarding to verify."),
            (Phase.adapt, "Adaptive iteration 1: forwarding to verify."),
            (Phase.verify, "Verified findings against DB."),
            (Phase.attest, "Attesting findings on chain."),
            (Phase.consolidate, "Consolidation complete."),
        ]
        for phase, content in narration_lines:
            session.add(
                NarrationEvent(
                    scan_id=scan.id,
                    phase=phase,
                    success_signal=True,
                    target_observations={},
                    decision=phase.value,
                    next_action=None,
                    content=content,
                    context={},
                )
            )

        for spec in findings_spec:
            severity = spec["severity"]
            if not isinstance(severity, Severity):
                severity = Severity(str(severity))
            module_hash = "0x" + hashlib.sha256(str(spec["title"]).encode()).hexdigest()
            payload = {
                "scan_id": str(scan.id),
                "title": spec["title"],
                "summary": spec["summary"],
                "severity": severity.value,
                "module_hash": module_hash,
            }
            bundle = encrypt_bundle(payload, recipient_pubkey=recipient)
            uid = await attest_finding(
                FindingAttestationPayload(
                    scan_id=scan.id,
                    target=target_url,
                    severity=severity.value,
                    module_hash=module_hash,
                    cost_usdc=Decimal(str(spec.get("cost_usdc", "0.10"))),
                    encrypted_bundle_uri=None,
                    ciphertext_sha256=bundle.sha256,
                    owasp_id=spec.get("owasp_id"),
                    atlas_technique_id=spec.get("atlas_technique_id"),
                    maestro_id=None,
                )
            )
            session.add(
                Finding(
                    scan_id=scan.id,
                    severity=severity,
                    title=str(spec["title"]),
                    summary=str(spec["summary"]),
                    module_hash=module_hash,
                    cost_usdc=Decimal(str(spec.get("cost_usdc", "0.10"))),
                    owasp_id=spec.get("owasp_id"),
                    atlas_technique_id=spec.get("atlas_technique_id"),
                    encrypted_bundle_uri=f"file:///tmp/spieon-bundles/{scan.id}/seed.age",
                    ciphertext_sha256=bundle.sha256,
                    eas_attestation_uid=uid,
                    attested_at=when + timedelta(minutes=1, seconds=30),
                    dedup_key=hashlib.sha256(
                        (module_hash + str(spec["title"])).encode()
                    ).hexdigest(),
                )
            )
        await session.commit()


async def _seed_heuristic() -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        heuristic = await record_heuristic(
            session,
            heuristic_key="fastmcp-unicode-schema-poisoning",
            rule=(
                "FastMCP servers tend to accept Cyrillic look-alike characters in tool "
                "names; pair this with a tools/register payload to shadow ASCII tools."
            ),
            target_type="mcp-http",
            probe_class="mcp-schema-poisoning",
            evidence_scan_ids=[],
            success_count=4,
            sample_size=5,
            owasp_id="LLM05",
            atlas_technique_id="AML.T0051",
        )
        uid = await attest_finding(
            FindingAttestationPayload(
                scan_id=heuristic.id,
                target="memory.spieon",
                severity="high",
                module_hash="0x" + heuristic.content_hash,
                cost_usdc=Decimal("0"),
                encrypted_bundle_uri=None,
                ciphertext_sha256=heuristic.content_hash,
                owasp_id="LLM05",
                atlas_technique_id="AML.T0051",
                maestro_id=None,
            )
        )
        await attach_attestation(session, heuristic, uid)
        await session.commit()


async def main() -> None:
    now = datetime.now(UTC)
    await _seed_scan(
        target_url="https://demo.spieon/x402-protected",
        when=now - timedelta(hours=2),
        findings_spec=[
            {
                "title": "x402 payment replay accepted",
                "summary": (
                    "Target accepted a replayed X-Payment header. Drains the "
                    "protected resource until validBefore expires."
                ),
                "severity": Severity.high,
                "owasp_id": "API07",
                "atlas_technique_id": "AML.T0049",
                "cost_usdc": "0.10",
            },
        ],
    )
    await _seed_scan(
        target_url="https://demo.spieon/mcp",
        when=now - timedelta(hours=1),
        findings_spec=[
            {
                "title": "MCP schema accepted poisoned tool (unicode_confusable)",
                "summary": (
                    "Server registered a tool with a Cyrillic look-alike that "
                    "shadows the ASCII version of get_user."
                ),
                "severity": Severity.high,
                "owasp_id": "LLM05",
                "atlas_technique_id": "AML.T0051",
                "cost_usdc": "0",
            },
            {
                "title": "MCP tool description injection",
                "summary": (
                    "Tool description survived into the response, suggesting the "
                    "agent followed the embedded instruction."
                ),
                "severity": Severity.high,
                "owasp_id": "LLM01",
                "atlas_technique_id": "AML.T0051",
                "cost_usdc": "0",
            },
        ],
    )
    await _seed_heuristic()
    print("seed complete")


if __name__ == "__main__":
    asyncio.run(main())
