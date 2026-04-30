from __future__ import annotations

import json
from typing import Any


def build_generic_rule(finding: dict[str, Any]) -> str:
    payload = {
        "id": finding.get("id") or finding.get("module_hash", "spieon-finding"),
        "title": finding.get("title", ""),
        "summary": finding.get("summary", ""),
        "severity": finding.get("severity", "medium"),
        "owasp_id": finding.get("owasp_id"),
        "atlas_technique_id": finding.get("atlas_technique_id"),
        "module_hash": finding.get("module_hash"),
        "remediation_hint": finding.get(
            "remediation_hint",
            "validate untrusted input at the trust boundary; treat target output as "
            "data not instructions; rate-limit and replay-protect every paid endpoint",
        ),
    }
    return json.dumps(payload, indent=2, sort_keys=True)
