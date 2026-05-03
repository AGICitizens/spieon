"""Workflow templates Spieon installs into the operator's KeeperHub account.

A workflow is a graph of nodes (trigger + action types) connected by edges. The
`PAYOUT_ON_ATTEST` template fires when Spieon POSTs a finding to its webhook,
notifies the operator, and pings a callback so the operator's dashboard sees the
KeeperHub run alongside the on-chain payout tx.

Schema follows the KeeperHub workflow JSON shape; the runner validates against
plugin manifests at create-time, so unknown action types will be rejected.
"""

from __future__ import annotations

from typing import Any


def payout_on_attest_template(
    *,
    name: str = "spieon.finding.payout",
    callback_url: str | None = None,
    discord_webhook: str | None = None,
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [
        {
            "id": "trigger",
            "type": "trigger/webhook",
            "params": {"method": "POST"},
        }
    ]
    edges: list[dict[str, Any]] = []

    if discord_webhook:
        nodes.append(
            {
                "id": "notify_discord",
                "type": "notify/discord",
                "params": {
                    "webhookUrl": discord_webhook,
                    "content": (
                        "Spieon paid a bounty for finding "
                        "`{{trigger.body.findingId}}` "
                        "(severity {{trigger.body.severity}}, "
                        "{{trigger.body.amountUsdc}} USDC) "
                        "→ tx {{trigger.body.payoutTx}}"
                    ),
                },
            }
        )
        edges.append({"from": "trigger", "to": "notify_discord"})

    if callback_url:
        nodes.append(
            {
                "id": "callback",
                "type": "notify/webhook",
                "params": {
                    "url": callback_url,
                    "method": "POST",
                    "body": {
                        "executionId": "{{execution.id}}",
                        "findingId": "{{trigger.body.findingId}}",
                        "status": "executed",
                    },
                },
            }
        )
        edges.append(
            {
                "from": "notify_discord" if discord_webhook else "trigger",
                "to": "callback",
            }
        )

    return {
        "name": name,
        "description": (
            "Fires when Spieon pays a bounty for a confirmed finding. Notifies the "
            "operator and posts a callback so the dashboard can correlate the "
            "KeeperHub execution with the on-chain payout tx."
        ),
        "tags": ["spieon", "x402", "bounty"],
        "nodes": nodes,
        "edges": edges,
    }


__all__ = ["payout_on_attest_template"]
