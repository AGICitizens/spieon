from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.patches.colang import build_colang_rule
from app.patches.generic import build_generic_rule
from app.patches.policylayer import build_policylayer_rule


@dataclass(slots=True)
class PatchArtifact:
    format: str
    filename: str
    content: str


PROMPT_INJECTION_OWASP = {"LLM01", "LLM05"}
X402_PROBE_HINTS = ("x402-", "API01", "API07")


def _looks_x402(finding: dict[str, Any]) -> bool:
    pid = (finding.get("probe_id") or finding.get("module_hash") or "").lower()
    owasp = (finding.get("owasp_id") or "").upper()
    if any(hint in pid for hint in ("x402", "payment", "settlement")):
        return True
    return owasp in {"API01", "API07"}


def _looks_prompt_injection(finding: dict[str, Any]) -> bool:
    owasp = (finding.get("owasp_id") or "").upper()
    pid = (finding.get("probe_id") or "").lower()
    if owasp in PROMPT_INJECTION_OWASP:
        return True
    return "injection" in pid or "schema" in pid or "tool" in pid


def build_patches(finding: dict[str, Any]) -> list[PatchArtifact]:
    artifacts: list[PatchArtifact] = []
    fid = finding.get("id") or finding.get("module_hash", "finding")[:16]

    if _looks_prompt_injection(finding):
        artifacts.append(
            PatchArtifact(
                format="colang",
                filename=f"{fid}.co",
                content=build_colang_rule(finding),
            )
        )
    if _looks_x402(finding):
        artifacts.append(
            PatchArtifact(
                format="policylayer",
                filename=f"{fid}.policylayer.json",
                content=build_policylayer_rule(finding),
            )
        )

    artifacts.append(
        PatchArtifact(
            format="generic",
            filename=f"{fid}.generic.json",
            content=build_generic_rule(finding),
        )
    )
    return artifacts
