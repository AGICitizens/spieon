"""Live smoke test for the three sponsor integrations.

Verifies (without leaking secrets):
    - 0G Compute: a real chat.completions call lands.
    - ENS: the configured name resolves and text records are readable.
    - KeeperHub: API key auth works against /workflows.

Doesn't trigger paid KeeperHub workflow execution and doesn't write any chain tx.
Run from the repo root so pydantic-settings finds .env.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from app.config import get_settings


def _ok(label: str, detail: str = "") -> None:
    print(f"  \x1b[32m✓\x1b[0m {label}{(' — ' + detail) if detail else ''}")


def _fail(label: str, detail: str) -> None:
    print(f"  \x1b[31m✗\x1b[0m {label} — {detail}")


def _skip(label: str, reason: str) -> None:
    print(f"  \x1b[33m·\x1b[0m {label} (skipped: {reason})")


async def test_zerog_compute() -> str:
    print("\n[1/3] 0G Compute")
    s = get_settings()
    if not s.zerog_compute_api_key:
        _skip("api key", "ZEROG_COMPUTE_API_KEY unset (sponsor intentionally cut)")
        return "skip"
    if not s.zerog_compute_model:
        _skip("model", "ZEROG_COMPUTE_MODEL unset")
        return "skip"

    from app.agent.llm import chat_client, default_model, judge_model, llm_provider

    provider = llm_provider()
    if provider != "0g-compute":
        _fail("provider selection", f"expected 0g-compute, got {provider}")
        return False
    _ok("provider routes to 0g-compute", f"model={default_model()} judge={judge_model()}")

    try:
        client = chat_client()
        res = await client.chat.completions.create(
            model=default_model(),
            max_tokens=24,
            messages=[
                {"role": "system", "content": "Reply with the single word: pong."},
                {"role": "user", "content": "ping"},
            ],
        )
        content = (res.choices[0].message.content or "").strip()
        if not content:
            _fail("chat.completions", "empty response body")
            return "fail"
        _ok("chat.completions", f"response={content!r}")
        return "pass"
    except Exception as exc:
        _fail("chat.completions", f"{type(exc).__name__}: {exc}")
        return "fail"


async def test_ens() -> str:
    print("\n[2/3] ENS")
    s = get_settings()
    if not s.ens_name:
        _skip("name", "ENS_NAME unset")
        return "skip"

    from app.chain.client import agent_address
    from app.chain.ens import (
        configured_name,
        fetch_text_records,
        lookup_name,
        resolve_address,
    )

    name = configured_name() or ""
    _ok("name configured", name)

    try:
        addr = await resolve_address(name)
    except Exception as exc:
        _fail("forward resolve", f"{type(exc).__name__}: {exc}")
        return "fail"
    if not addr:
        _fail("forward resolve", f"{name} does not resolve to an address")
        return "fail"
    _ok("forward resolve", f"{name} → {addr[:8]}…{addr[-6:]}")

    expected_keys = {"url", "description", "com.github", "org.erc8004.descriptor"}
    try:
        records = await fetch_text_records(name)
    except Exception as exc:
        _fail("text records", f"{type(exc).__name__}: {exc}")
        return "fail"
    missing = expected_keys - set(records.keys())
    if not records:
        _fail(
            "text records",
            "no records set — run scripts/ens_setup.py",
        )
        records_ok = False
    elif missing:
        _fail(
            "text records",
            f"have {sorted(records)}; missing {sorted(missing)} — run scripts/ens_setup.py",
        )
        records_ok = False
    else:
        _ok("text records", f"{len(records)} keys: {sorted(records)}")
        records_ok = True

    try:
        agent_addr = agent_address()
    except Exception as exc:
        _fail("agent wallet", f"{type(exc).__name__}: {exc}")
        return "fail"
    try:
        primary = await lookup_name(agent_addr)
    except Exception as exc:
        _fail("reverse resolve", f"{type(exc).__name__}: {exc}")
        return "fail"
    if primary:
        _ok("reverse resolve", f"{agent_addr[:8]}… → {primary}")
        reverse_ok = True
    else:
        _fail(
            "reverse resolve",
            "agent address has no primary name (run scripts/ens_setup.py)",
        )
        reverse_ok = False

    return "pass" if (records_ok and reverse_ok) else "fail"


async def test_keeperhub() -> str:
    print("\n[3/3] KeeperHub")
    s = get_settings()
    if not s.keeperhub_api_key:
        _skip("api key", "KEEPERHUB_API_KEY unset")
        return "skip"

    from app.keeperhub import KeeperHubError, get_keeperhub_client

    client = get_keeperhub_client()
    if not client.configured:
        _fail("client", "client.configured is False")
        return "fail"
    _ok("api key present", f"{s.keeperhub_api_key[:5]}…")

    try:
        body = await client.list_workflows()
    except KeeperHubError as exc:
        _fail("auth (list workflows)", str(exc))
        return "fail"
    except Exception as exc:
        _fail("auth (list workflows)", f"{type(exc).__name__}: {exc}")
        return "fail"

    workflows: list[Any] = []
    if isinstance(body, dict):
        workflows = (
            body.get("workflows")
            or body.get("data")
            or body.get("items")
            or []
        )
        if not workflows and "id" in body:
            workflows = [body]
    elif isinstance(body, list):
        workflows = body

    _ok(
        "auth works",
        f"{len(workflows)} workflow(s) on account",
    )

    if not s.keeperhub_payout_workflow_id:
        _fail(
            "payout workflow",
            "KEEPERHUB_PAYOUT_WORKFLOW_ID unset (POST /keeperhub/install to create)",
        )
        return "fail"

    try:
        execs = await client.list_executions(
            s.keeperhub_payout_workflow_id, limit=5
        )
        count = 0
        if isinstance(execs, dict):
            items = (
                execs.get("executions")
                or execs.get("data")
                or execs.get("items")
                or []
            )
            count = len(items)
        elif isinstance(execs, list):
            count = len(execs)
        _ok(
            "payout workflow",
            f"{s.keeperhub_payout_workflow_id[:12]}… ({count} runs)",
        )
        return "pass"
    except Exception as exc:
        _fail("payout workflow", f"{type(exc).__name__}: {exc}")
        return "fail"


_MARKERS = {
    "pass": "\x1b[32mPASS\x1b[0m",
    "fail": "\x1b[31mFAIL\x1b[0m",
    "skip": "\x1b[33mSKIP\x1b[0m",
}


async def main() -> int:
    print("Spieon sponsor smoke test\n" + "=" * 30)
    results = [
        ("0G Compute", await test_zerog_compute()),
        ("ENS",        await test_ens()),
        ("KeeperHub",  await test_keeperhub()),
    ]
    print("\n" + "=" * 30)
    for label, status in results:
        print(f"  {_MARKERS[status]}  {label}")
    return 0 if not any(s == "fail" for _, s in results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
