from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.models.finding import Finding, Severity


@dataclass(slots=True)
class RawFinding:
    title: str
    summary: str
    severity: Severity
    module_hash: str
    owasp_id: str | None = None
    atlas_technique_id: str | None = None
    maestro_id: str | None = None
    cost_usdc: Decimal = Decimal("0")
    encrypted_bundle_uri: str | None = None
    ciphertext_sha256: str | None = None
    eas_attestation_uid: str | None = None
    signature_parts: tuple[str, ...] = field(default_factory=tuple)
    extra: dict[str, Any] = field(default_factory=dict)


def _dedup_key(raw: RawFinding) -> str:
    parts = list(raw.signature_parts) or [
        raw.module_hash,
        raw.title,
        raw.owasp_id or "",
        raw.atlas_technique_id or "",
    ]
    canonical = "|".join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_finding(raw: RawFinding, *, scan_id) -> Finding:
    return Finding(
        scan_id=scan_id,
        severity=raw.severity,
        title=raw.title[:512],
        summary=raw.summary,
        module_hash=raw.module_hash,
        cost_usdc=raw.cost_usdc,
        owasp_id=raw.owasp_id,
        atlas_technique_id=raw.atlas_technique_id,
        maestro_id=raw.maestro_id,
        encrypted_bundle_uri=raw.encrypted_bundle_uri,
        ciphertext_sha256=raw.ciphertext_sha256,
        eas_attestation_uid=raw.eas_attestation_uid,
        dedup_key=_dedup_key(raw),
    )
