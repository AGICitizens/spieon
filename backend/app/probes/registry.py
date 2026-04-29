from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal

from app.models.finding import Severity
from app.models.probe_run import ProbeEngine
from app.probes.protocol import Probe


@dataclass(slots=True)
class ProbeSpec:
    id: str
    engine: ProbeEngine
    probe_class: str
    severity_cap: Severity
    cost_estimate_usdc: Decimal
    owasp_id: str | None
    atlas_technique_id: str | None
    maestro_id: str | None
    factory: type[Probe]
    module_hash: str
    description: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


_REGISTRY: dict[str, ProbeSpec] = {}


def register_probe(spec: ProbeSpec) -> ProbeSpec:
    if spec.id in _REGISTRY:
        raise ValueError(f"probe {spec.id!r} is already registered")
    _REGISTRY[spec.id] = spec
    return spec


def resolve_probe(probe_id: str) -> ProbeSpec:
    if probe_id not in _REGISTRY:
        raise KeyError(f"unknown probe id {probe_id!r}")
    return _REGISTRY[probe_id]


def list_probe_ids() -> list[str]:
    return sorted(_REGISTRY.keys())


def iter_probes() -> Iterator[ProbeSpec]:
    return iter(_REGISTRY.values())
