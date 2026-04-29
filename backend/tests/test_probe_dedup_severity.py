from __future__ import annotations

from decimal import Decimal

import pytest

from app.models.finding import Severity
from app.probes.dedup import dedupe, signature
from app.probes.normalize import RawFinding
from app.probes.severity import cap, from_label, from_score


def _finding(
    title: str = "x402 replay",
    severity: Severity = Severity.high,
    module_hash: str = "0xab",
    cost: Decimal = Decimal("0.10"),
    sig: tuple[str, ...] | None = None,
    summary: str = "summary",
) -> RawFinding:
    return RawFinding(
        title=title,
        summary=summary,
        severity=severity,
        module_hash=module_hash,
        cost_usdc=cost,
        signature_parts=sig or (module_hash, title),
    )


def test_dedupe_collapses_matching_signatures_and_sums_cost() -> None:
    a = _finding(cost=Decimal("0.10"), summary="short")
    b = _finding(cost=Decimal("0.40"), summary="this is a much longer summary")
    out = dedupe([a, b])
    assert len(out) == 1
    merged = out[0]
    assert merged.cost_usdc == Decimal("0.50")
    assert merged.summary == "this is a much longer summary"


def test_dedupe_keeps_higher_severity_when_merging() -> None:
    a = _finding(severity=Severity.high)
    b = _finding(severity=Severity.critical)
    merged = dedupe([a, b])[0]
    assert merged.severity is Severity.critical


def test_dedupe_treats_different_signatures_as_distinct() -> None:
    a = _finding(title="x402 replay", sig=("0xab", "replay"))
    b = _finding(title="schema poisoning", sig=("0xcd", "schema"))
    out = dedupe([a, b])
    assert len(out) == 2
    assert {f.title for f in out} == {"x402 replay", "schema poisoning"}


def test_signature_is_deterministic() -> None:
    a = _finding(sig=("alpha", "beta"))
    b = _finding(sig=("alpha", "beta"))
    assert signature(a) == signature(b)


def test_severity_from_score_maps_thresholds() -> None:
    assert from_score(9.5) is Severity.critical
    assert from_score(7.5) is Severity.high
    assert from_score(5.0) is Severity.medium
    assert from_score(1.0) is Severity.low


def test_severity_from_label_accepts_aliases() -> None:
    assert from_label("Critical") is Severity.critical
    assert from_label("major") is Severity.high
    assert from_label("info") is Severity.low

    with pytest.raises(ValueError):
        from_label("nope")


def test_severity_cap_lowers_above_ceiling() -> None:
    assert cap(Severity.critical, Severity.high) is Severity.high
    assert cap(Severity.medium, Severity.high) is Severity.medium
