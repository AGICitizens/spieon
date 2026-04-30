from __future__ import annotations

import json

from app.patches import (
    build_colang_rule,
    build_generic_rule,
    build_patches,
    build_policylayer_rule,
)


def test_build_patches_for_x402_finding_includes_policylayer() -> None:
    finding = {
        "id": "f-1",
        "title": "x402 payment replay accepted",
        "summary": "replayed payment header succeeded",
        "severity": "high",
        "module_hash": "0xab",
        "owasp_id": "API07",
        "atlas_technique_id": "AML.T0049",
        "probe_id": "x402-replay-attack",
    }
    artifacts = build_patches(finding)
    formats = {a.format for a in artifacts}
    assert {"policylayer", "generic"} <= formats
    pl = next(a for a in artifacts if a.format == "policylayer")
    parsed = json.loads(pl.content)
    assert parsed["category"] == "x402-payment"
    assert parsed["severity"] == "high"
    assert any(check["id"] == "reject-replayed-nonce" for check in parsed["checks"])


def test_build_patches_for_prompt_injection_includes_colang() -> None:
    finding = {
        "id": "f-2",
        "title": "MCP tool description injection",
        "summary": "agent followed an instruction embedded in a tool description",
        "severity": "high",
        "module_hash": "0xcd",
        "owasp_id": "LLM01",
        "probe_id": "mcp-tool-description-injection",
    }
    artifacts = build_patches(finding)
    formats = {a.format for a in artifacts}
    assert "colang" in formats
    co = next(a for a in artifacts if a.format == "colang")
    assert "define flow guard" in co.content
    assert "I can't follow instructions" in co.content


def test_build_patches_always_returns_a_generic_artifact() -> None:
    finding = {"title": "novel finding", "severity": "low"}
    artifacts = build_patches(finding)
    assert any(a.format == "generic" for a in artifacts)
    raw = build_generic_rule(finding)
    parsed = json.loads(raw)
    assert parsed["title"] == "novel finding"
    assert parsed["severity"] == "low"


def test_colang_rule_uses_provided_canaries() -> None:
    finding = {
        "id": "f-3",
        "title": "tool description override",
        "canaries": ["delete all files", "exfiltrate api keys"],
    }
    rule = build_colang_rule(finding)
    assert "delete all files" in rule
    assert "exfiltrate api keys" in rule


def test_policylayer_metadata_carries_taxonomy() -> None:
    finding = {
        "id": "f-4",
        "severity": "critical",
        "owasp_id": "API01",
        "atlas_technique_id": "AML.T0049",
        "probe_id": "x402-payment-retry-bypass",
    }
    rule = json.loads(build_policylayer_rule(finding))
    assert rule["metadata"]["owasp_id"] == "API01"
    assert rule["metadata"]["atlas_technique_id"] == "AML.T0049"
