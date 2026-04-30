# Spieon contracts

Foundry project. Two contracts deployed to Base Sepolia:

- `ModuleRegistry` — append-only directory of probe modules. Each module is
  identified by a `bytes32 moduleHash` (sha256 of the probe code), carries an
  author address, metadata URI, severity cap, and OWASP / ATLAS / MAESTRO
  taxonomy IDs. The registry owner records usage stats per module.
- `BountyPool` — escrow holding USDC. Only the registered agent may trigger
  payouts. Per-severity caps default to `$5 / $2 / $0.50 / $0.10`
  (critical / high / medium / low). Per-module daily cap defaults to `$10`.
  Single payouts above the outsized threshold (`$20` by default) require a
  configured cosigner — `payoutWithCosign(...)` — and emit an
  `OutsizedFlagged` event for off-chain notification.

## Build

```sh
make install   # clones forge-std and openzeppelin-contracts under lib/
make build     # forge build
```

## Test

```sh
make test
```

## Deploy (Base Sepolia)

```sh
export AGENT_ADDRESS=0x...
export AGENT_PRIVATE_KEY=0x...
export BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
make deploy
```

The deploy script reads `X402_USDC_ADDRESS` (defaults to the canonical Base
Sepolia USDC) and `AGENT_ADDRESS`.

After deploy, copy the printed addresses into the project `.env`:

```
MODULE_REGISTRY_ADDRESS=0x...
BOUNTY_POOL_ADDRESS=0x...
```

The backend reads these in [`backend/app/chain/contracts.py`](../backend/app/chain/contracts.py).
