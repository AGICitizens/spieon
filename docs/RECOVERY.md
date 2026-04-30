# Spieon — recovery posture

This is the runbook for the four ways Spieon can fall over and the steps to
rebuild without losing money or attestations.

## Hot wallet → cold Safe sweep

The agent's hot wallet (`AGENT_ADDRESS`) holds USDC for x402 probe payments
and ETH for gas. Recommended operating limit: **`$50` USDC, 0.1 ETH**.

- Set `COLD_SAFE_ADDRESS` in `.env` to a Gnosis Safe controlled by
  multisig signers (none of which are the agent key).
- Sweep overflow manually any time the hot wallet exceeds the limit:
  ```sh
  cast send --private-key $AGENT_PRIVATE_KEY \
      --rpc-url $BASE_SEPOLIA_RPC_URL \
      $X402_USDC_ADDRESS "transfer(address,uint256)" \
      $COLD_SAFE_ADDRESS <amount_usdc6>
  ```
- A V1 sweep cron is **not** shipped; operators run the sweep manually when
  the agent stats banner shows a USDC balance above their threshold.

## Hot-key rotation

If `AGENT_PRIVATE_KEY` is suspected compromised:

1. Pause: stop accepting new scans by setting `APP_ENV=maintenance`
   (the API rejects new scans in maintenance mode — V2 will land a
   middleware; for V1 stop the backend container).
2. Sweep remaining USDC + ETH to cold Safe (above).
3. Generate a fresh key:
   ```sh
   cast wallet new
   ```
4. Update `.env` with the new `AGENT_PRIVATE_KEY` / `AGENT_ADDRESS`.
5. Re-register identity: hit `BountyPool.setAgent(newAddress)` from the
   pool owner; previous payouts remain consumed via
   `attestationConsumed[uid]` so no double-pay risk during rotation.
6. Re-fund the new hot wallet from the cold Safe.

## Memory & checkpoint snapshots

The LangGraph checkpointer writes state to the Postgres `checkpoints`
schema. A daily `pg_dump` to encrypted offsite covers checkpoint + Spieon
tables in one shot:

```sh
pg_dump --no-owner --format=custom \
    "$DATABASE_URL_SYNC" \
    | age -r $BACKUP_AGE_RECIPIENT > spieon-$(date -u +%Y%m%dT%H%M%SZ).age
```

Restore is the reverse — `age -d -i ~/.age-backup-key < snapshot.age | pg_restore`.

V1 ships a documented manual procedure; V2 will land an automated cron.

## Encrypted finding bundles

Every bundle is age-encrypted to the operator's X25519 recipient at scan
submission. The agent only sees the ciphertext sha256.

- If the operator **loses the secret key**: there is no recovery. The EAS
  attestation still proves the agent committed to a specific ciphertext at a
  specific time; the bundle plaintext is unreachable.
- If the operator **leaks the secret key**: rotate forward by submitting
  fresh scans with a new keypair. Past bundles for the leaked key are
  exposed but can no longer be reused — every scan generates a new
  recipient.

## EAS schema continuity

`EAS_SCHEMA_UID` pins the on-chain schema. If the schema needs to change,
**register a new schema** rather than mutating in place — the registry is
append-only.

- Old findings keep their attestations against the old schema.
- Update `EAS_SCHEMA_UID` in `.env`; new attestations land against the new
  schema.
- Document the schema migration in `docs/CHANGELOG.md` so the public
  memory log can be cross-checked.

## Bounty-pool drain alarm

`BountyPool.OutsizedFlagged(uid, amount)` fires for any single payout
`>= outsizedThreshold` (default `$20`). Wire an off-chain listener to email
or Slack on this event. V1 ships the contract event + a documented filter;
the operator wires the alert at deploy time.

## Recovery checklist

Run this whenever the hot wallet is rotated or the host is rebuilt:

- [ ] `make up` brings postgres + langfuse + backend healthy
- [ ] Alembic at head: `make migrate` reports no pending revisions
- [ ] `/health` returns `{"status":"ok","db":true}`
- [ ] `/agent/stats` shows the expected wallet address and USDC balance
- [ ] `/.well-known/agent.json` returns the ERC-8004 descriptor with the
      new address
- [ ] One trial scan against a benign target completes end-to-end
      (`probe → verify → attest → consolidate`)
