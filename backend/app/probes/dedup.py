from __future__ import annotations

import hashlib
from collections.abc import Iterable

from app.probes.normalize import RawFinding


def signature(raw: RawFinding) -> str:
    parts = list(raw.signature_parts) or [
        raw.module_hash,
        raw.title,
        raw.owasp_id or "",
        raw.atlas_technique_id or "",
    ]
    canonical = "|".join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def merge(a: RawFinding, b: RawFinding) -> RawFinding:
    """Merge two findings that share a signature.

    Picks the higher severity, longer summary, and union of taxonomy hits.
    `cost_usdc` is summed because each finding represents real spend.
    """
    severity_order = ["low", "medium", "high", "critical"]
    severity = (
        a.severity
        if severity_order.index(a.severity.value) >= severity_order.index(b.severity.value)
        else b.severity
    )
    summary = a.summary if len(a.summary) >= len(b.summary) else b.summary
    return RawFinding(
        title=a.title if len(a.title) >= len(b.title) else b.title,
        summary=summary,
        severity=severity,
        module_hash=a.module_hash,
        owasp_id=a.owasp_id or b.owasp_id,
        atlas_technique_id=a.atlas_technique_id or b.atlas_technique_id,
        maestro_id=a.maestro_id or b.maestro_id,
        cost_usdc=a.cost_usdc + b.cost_usdc,
        encrypted_bundle_uri=a.encrypted_bundle_uri or b.encrypted_bundle_uri,
        ciphertext_sha256=a.ciphertext_sha256 or b.ciphertext_sha256,
        eas_attestation_uid=a.eas_attestation_uid or b.eas_attestation_uid,
        signature_parts=a.signature_parts or b.signature_parts,
        extra={**b.extra, **a.extra},
    )


def dedupe(findings: Iterable[RawFinding]) -> list[RawFinding]:
    by_sig: dict[str, RawFinding] = {}
    for f in findings:
        sig = signature(f)
        if sig in by_sig:
            by_sig[sig] = merge(by_sig[sig], f)
        else:
            by_sig[sig] = f
    return list(by_sig.values())
