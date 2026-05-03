from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

PROBE_HARD_TIMEOUT_SEC = 15.0

from sqlalchemy.ext.asyncio import AsyncSession

from app.cost.meter import CostMeter
from app.cost.receipts import PaymentReceiptParser
from app.models.probe_run import ProbeRun, ProbeRunStatus
from app.probes.dedup import dedupe
from app.probes.judge import JudgeFn, judge_finding
from app.probes.normalize import RawFinding
from app.probes.protocol import ProbeContext, ProbeOutcome
from app.probes.registry import resolve_probe
from app.probes.severity import cap as cap_severity
from app.safety.harness import (
    AutoStopReason,
    HarnessDecision,
    HarnessVerdict,
    SafetyHarness,
    attribution_headers_for,
)


@dataclass(slots=True)
class ProbeExecution:
    probe_run: ProbeRun
    outcome: ProbeOutcome
    findings: list[RawFinding] = field(default_factory=list)
    verdict: HarnessVerdict | None = None
    auto_stop: AutoStopReason | None = None


@dataclass(slots=True)
class ProbePlanItem:
    probe_id: str
    params: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class RunReport:
    executions: list[ProbeExecution] = field(default_factory=list)
    consolidated: list[RawFinding] = field(default_factory=list)
    total_cost_usdc: Decimal = Decimal("0")
    auto_stop: AutoStopReason | None = None


async def execute_probe(
    session: AsyncSession,
    *,
    scan_id: uuid.UUID,
    target_url: str,
    plan_item: ProbePlanItem,
    harness: SafetyHarness,
    budget_remaining_usdc: Decimal,
    operator_balance_usdc: Decimal | None = None,
    receipt_parser: PaymentReceiptParser | None = None,
) -> ProbeExecution:
    spec = resolve_probe(plan_item.probe_id)
    verdict = harness.check(
        target_url=target_url,
        probe_class=spec.probe_class,
        budget_remaining_usdc=budget_remaining_usdc,
        operator_balance_usdc=operator_balance_usdc,
    )

    probe_run = ProbeRun(
        scan_id=scan_id,
        probe_id=spec.id,
        engine=spec.engine,
        params=dict(plan_item.params),
        status=ProbeRunStatus.pending,
    )
    session.add(probe_run)
    await session.flush()
    await session.refresh(probe_run)

    if verdict.decision is HarnessDecision.block:
        probe_run.status = ProbeRunStatus.skipped
        probe_run.error = verdict.reason
        probe_run.finished_at = datetime.now(UTC)
        session.add(probe_run)
        await session.flush()
        return ProbeExecution(
            probe_run=probe_run, outcome=ProbeOutcome(vulnerable=False), verdict=verdict
        )

    if verdict.decision is HarnessDecision.stop:
        probe_run.status = ProbeRunStatus.skipped
        probe_run.error = verdict.reason
        probe_run.finished_at = datetime.now(UTC)
        session.add(probe_run)
        await session.flush()
        return ProbeExecution(
            probe_run=probe_run,
            outcome=ProbeOutcome(vulnerable=False),
            verdict=verdict,
            auto_stop=verdict.auto_stop,
        )

    harness.record_attempt(target_url)
    probe_run.status = ProbeRunStatus.running
    probe_run.started_at = datetime.now(UTC)
    session.add(probe_run)
    await session.flush()

    meter = CostMeter(spec.id, parser=receipt_parser) if receipt_parser else CostMeter(spec.id)
    ctx = ProbeContext(
        scan_id=scan_id,
        probe_run_id=probe_run.id,
        target_url=target_url,
        budget_remaining_usdc=budget_remaining_usdc,
        params=dict(plan_item.params),
        attribution_headers=attribution_headers_for(scan_id),
    )

    probe = spec.factory()
    try:
        outcome = await asyncio.wait_for(
            probe.run(ctx, meter=meter), timeout=PROBE_HARD_TIMEOUT_SEC
        )
        if outcome.error:
            probe_run.status = ProbeRunStatus.failed
            probe_run.error = outcome.error
        else:
            probe_run.status = ProbeRunStatus.succeeded
        probe_run.vulnerable = outcome.vulnerable
        probe_run.cost_usdc = outcome.cost_usdc or meter.cost.total
        probe_run.response_excerpt = outcome.response_excerpt
    except asyncio.TimeoutError:
        probe_run.status = ProbeRunStatus.failed
        probe_run.error = f"probe exceeded {PROBE_HARD_TIMEOUT_SEC}s hard timeout"
        outcome = ProbeOutcome(vulnerable=False, error=probe_run.error)
    except Exception as exc:
        probe_run.status = ProbeRunStatus.failed
        probe_run.error = f"{type(exc).__name__}: {exc}"
        outcome = ProbeOutcome(vulnerable=False, error=probe_run.error)

    probe_run.finished_at = datetime.now(UTC)
    session.add(probe_run)
    await session.flush()

    findings: list[RawFinding] = []
    for raw in outcome.findings:
        capped = cap_severity(raw.severity, spec.severity_cap)
        if capped is not raw.severity:
            raw = RawFinding(
                title=raw.title,
                summary=raw.summary,
                severity=capped,
                module_hash=raw.module_hash,
                owasp_id=raw.owasp_id,
                atlas_technique_id=raw.atlas_technique_id,
                maestro_id=raw.maestro_id,
                cost_usdc=raw.cost_usdc,
                encrypted_bundle_uri=raw.encrypted_bundle_uri,
                ciphertext_sha256=raw.ciphertext_sha256,
                eas_attestation_uid=raw.eas_attestation_uid,
                signature_parts=raw.signature_parts,
                extra=raw.extra,
            )
        findings.append(raw)

    return ProbeExecution(
        probe_run=probe_run,
        outcome=outcome,
        findings=findings,
        verdict=verdict,
    )


async def run_plan(
    session: AsyncSession,
    *,
    scan_id: uuid.UUID,
    target_url: str,
    plan: list[ProbePlanItem],
    harness: SafetyHarness | None = None,
    budget_usdc: Decimal,
    operator_balance_usdc: Decimal | None = None,
    receipt_parser: PaymentReceiptParser | None = None,
    judge: JudgeFn | None = None,
    judge_threshold: float = 0.5,
) -> RunReport:
    harness = harness or SafetyHarness()
    report = RunReport()
    spent = Decimal("0")
    raw_findings: list[RawFinding] = []

    for item in plan:
        remaining = budget_usdc - spent
        execution = await execute_probe(
            session,
            scan_id=scan_id,
            target_url=target_url,
            plan_item=item,
            harness=harness,
            budget_remaining_usdc=remaining,
            operator_balance_usdc=operator_balance_usdc,
            receipt_parser=receipt_parser,
        )
        report.executions.append(execution)
        if execution.auto_stop is not None:
            report.auto_stop = execution.auto_stop
            break

        spent += execution.outcome.cost_usdc or Decimal("0")
        raw_findings.extend(execution.findings)

    deduped = dedupe(raw_findings)

    if judge is not None and deduped:
        confirmed: list[RawFinding] = []
        for raw in deduped:
            evidence = next(
                (
                    e.outcome.response_excerpt
                    for e in report.executions
                    if any(f is raw or f.title == raw.title for f in e.findings)
                ),
                None,
            )
            judgment = await judge(raw, evidence)
            if judgment.confirmed and judgment.confidence >= judge_threshold:
                if judgment.suggested_severity:
                    try:
                        from app.probes.severity import from_label

                        suggested = from_label(judgment.suggested_severity)
                        raw = RawFinding(
                            title=raw.title,
                            summary=raw.summary,
                            severity=cap_severity(
                                suggested,
                                resolve_probe_spec_severity(raw),
                            ),
                            module_hash=raw.module_hash,
                            owasp_id=raw.owasp_id,
                            atlas_technique_id=raw.atlas_technique_id,
                            maestro_id=raw.maestro_id,
                            cost_usdc=raw.cost_usdc,
                            encrypted_bundle_uri=raw.encrypted_bundle_uri,
                            ciphertext_sha256=raw.ciphertext_sha256,
                            eas_attestation_uid=raw.eas_attestation_uid,
                            signature_parts=raw.signature_parts,
                            extra={**raw.extra, "judge_rationale": judgment.rationale},
                        )
                    except ValueError:
                        pass
                confirmed.append(raw)
        report.consolidated = confirmed
    else:
        report.consolidated = deduped

    report.total_cost_usdc = spent
    return report


def resolve_probe_spec_severity(raw: RawFinding):
    from app.probes.registry import iter_probes

    for spec in iter_probes():
        if spec.module_hash == raw.module_hash:
            return spec.severity_cap
    return raw.severity


_default_judge: JudgeFn = judge_finding
