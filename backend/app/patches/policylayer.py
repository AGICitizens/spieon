from __future__ import annotations

import json
from typing import Any


def build_policylayer_rule(finding: dict[str, Any]) -> str:
    rule_id = finding.get("id") or finding.get("module_hash", "spieon-finding")
    severity = finding.get("severity", "medium")
    probe_class = finding.get("probe_class") or finding.get("module_hash", "")

    rule = {
        "id": f"spieon.{rule_id}",
        "version": 1,
        "category": "x402-payment",
        "severity": severity,
        "match": {
            "request": {
                "headers": {"X-Payment": {"present": True}},
                "method": ["GET", "POST"],
            }
        },
        "checks": [
            {
                "id": "verify-payment-payload",
                "type": "verifier",
                "rule": (
                    "decode X-Payment as base64 JSON, ensure x402Version, scheme, "
                    "network, payload.signature (66 byte hex) and payload.authorization "
                    "(from/to/value/validAfter/validBefore/nonce) are all present and "
                    "structurally well-formed before forwarding to the facilitator"
                ),
            },
            {
                "id": "reject-replayed-nonce",
                "type": "nonce-guard",
                "rule": (
                    "track payload.authorization.nonce per (asset,from) for the longer "
                    "of validBefore - now() and 24h; reject any second use"
                ),
            },
            {
                "id": "require-settlement-receipt",
                "type": "settlement-guard",
                "rule": (
                    "do not return 200 to the protected resource until the facilitator "
                    "settle call has emitted a USDC Transfer log; if the client cancels "
                    "mid-settlement, abort the resource fetch"
                ),
            },
        ],
        "metadata": {
            "owasp_id": finding.get("owasp_id"),
            "atlas_technique_id": finding.get("atlas_technique_id"),
            "probe_class": probe_class,
        },
    }
    return json.dumps(rule, indent=2, sort_keys=True)
