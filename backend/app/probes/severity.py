from __future__ import annotations

from app.models.finding import Severity


def from_score(score: float) -> Severity:
    if score >= 9.0:
        return Severity.critical
    if score >= 7.0:
        return Severity.high
    if score >= 4.0:
        return Severity.medium
    return Severity.low


def from_label(label: str) -> Severity:
    text = (label or "").strip().lower()
    if text in {"critical", "crit", "p0", "blocker"}:
        return Severity.critical
    if text in {"high", "p1", "major"}:
        return Severity.high
    if text in {"medium", "med", "moderate", "p2"}:
        return Severity.medium
    if text in {"low", "info", "informational", "p3", "p4", "minor"}:
        return Severity.low
    raise ValueError(f"unrecognised severity label {label!r}")


def cap(severity: Severity, ceiling: Severity) -> Severity:
    order = [Severity.low, Severity.medium, Severity.high, Severity.critical]
    return order[min(order.index(severity), order.index(ceiling))]
