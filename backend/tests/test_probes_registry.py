from __future__ import annotations

from app.probes import iter_probes, list_probe_ids, resolve_probe


def test_native_probes_are_registered_with_taxonomy() -> None:
    ids = list_probe_ids()
    expected = {
        "x402-replay-attack",
        "x402-payment-retry-bypass",
        "x402-settlement-skip",
        "mcp-tool-description-injection",
        "mcp-schema-poisoning",
    }
    assert expected.issubset(set(ids))

    for spec in iter_probes():
        assert spec.module_hash.startswith("0x") and len(spec.module_hash) == 66
        assert spec.severity_cap is not None
        if spec.id.startswith("x402-"):
            assert spec.atlas_technique_id == "AML.T0049"
        if spec.id.startswith("mcp-"):
            assert spec.atlas_technique_id == "AML.T0051"


def test_resolve_probe_round_trip() -> None:
    spec = resolve_probe("x402-replay-attack")
    assert spec.probe_class == "x402-replay"
    assert spec.factory.__name__ == "X402ReplayProbe"
