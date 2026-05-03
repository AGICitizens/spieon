"""KeeperHub integration — workflow execution paid via x402.

Spieon delegates payout coordination to KeeperHub workflows. Management calls
(create / list / inspect) use the API key; per-execution calls use x402, so the
agent literally pays USDC per finding payout it triggers — proving the bridge
between x402 (a payment rail) and KeeperHub (an execution layer).
"""

from app.keeperhub.client import KeeperHubClient, KeeperHubError, get_keeperhub_client

__all__ = ["KeeperHubClient", "KeeperHubError", "get_keeperhub_client"]
