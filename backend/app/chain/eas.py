from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class FindingAttestationPayload:
    scan_id: uuid.UUID
    target: str
    severity: str
    module_hash: str
    cost_usdc: Decimal
    encrypted_bundle_uri: str | None
    ciphertext_sha256: str | None
    owasp_id: str | None
    atlas_technique_id: str | None
    maestro_id: str | None


def _stub_uid(payload: FindingAttestationPayload) -> str:
    canonical = json.dumps(
        {
            "scan_id": str(payload.scan_id),
            "target": payload.target,
            "severity": payload.severity,
            "module_hash": payload.module_hash,
            "cost_usdc": str(payload.cost_usdc),
            "encrypted_bundle_uri": payload.encrypted_bundle_uri,
            "ciphertext_sha256": payload.ciphertext_sha256,
            "owasp_id": payload.owasp_id,
            "atlas_technique_id": payload.atlas_technique_id,
            "maestro_id": payload.maestro_id,
        },
        sort_keys=True,
    ).encode()
    return "0x" + hashlib.sha256(canonical).hexdigest()


async def attest_finding(payload: FindingAttestationPayload) -> str:
    return _stub_uid(payload)
