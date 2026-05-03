# Demo recording playbook

Operational steps for recording the 4-minute submission video. The narrative is
locked in [PRD.md §2](PRD.md) (the 7 beats); this doc is the mechanics.
For the presenter-friendly version with exact voice-over lines and event cues,
use [DEMO_SCRIPT.md](./DEMO_SCRIPT.md).

## 0. Sponsor integrations (judges' cheat sheet)

We claim two sponsor tracks, $7K addressable. **0G was scoped out** (its compute and storage SDKs both require per-call signed headers + a funded 0G wallet — not shippable in submission-day time without a Node.js sidecar).

The frontend now exposes a dedicated judge-facing route at `https://spieon.agicitizens.com/hackathon` that consolidates the AI disclosure, sponsor summary, bounty explanation, and repo verification links below. Use it as the “open the review packet” page before diving into the live demo beats.

| Sponsor | Track | What's wired | Files | Verify |
|---|---|---|---|---|
| **ENS** | Best ENS Integration for AI Agents ($2.5K) | `spieon-agent.eth` on Sepolia owns the agent identity. Text records (`url`, `description`, `org.erc8004.descriptor`, `org.spieon.scan-endpoint`, `com.github`) and reverse name read **live from Sepolia at request time** — no hardcoded values. Surfaced in `/.well-known/agent.json`, `/agent/stats`, and the `/agent` profile page. | `backend/app/chain/ens.py`, `backend/app/api/erc8004.py:31-110`, `backend/app/api/agent.py:65-95`, `backend/scripts/ens_setup.py`, `frontend/app/agent/page.tsx` | `curl /.well-known/agent.json | jq .ens` shows non-null `name` + `textRecords` populated from chain; agent profile UI shows the name above the wallet hex |
| **KeeperHub** | Best Integration with KeeperHub — x402 bridge ($4.5K) | After every confirmed on-chain payout, Spieon triggers a KeeperHub workflow at `app.keeperhub.com/api/workflow/{id}/execute`, paid via the same `X402Client` we use for security probes — making KH the second consumer of our x402 stack. Returns `executionId` + `keeperhub_paid: true` on the payout response, surfaced live in the `/agent` page panel. | `backend/app/keeperhub/client.py`, `backend/app/keeperhub/workflows.py`, `backend/app/api/keeperhub.py`, `backend/app/api/payouts.py:113-148` | `GET /keeperhub/status` shows `configured: true`; click "Pay bounty" in beat 5 → response carries a `keeperhub_execution_id`; `/agent` page lists the run |

### What's already live (verified May 3 13:50 ET)

- ENS name `spieon-agent.eth` resolves on Sepolia and one text record (`avatar`) is set; descriptor + agent stats render the partial ENS block correctly.
- KeeperHub API key is loaded; `GET /keeperhub/status` reports `api_key_present: true`.
- 3 seeded attestations on Base Sepolia ready for the Beat 5 bounty payout (currently `bounty_tx_hash=null` — they trigger the KH workflow when paid).
- The homepage links straight to the OSS repo and the `/hackathon` review page, so judges can move from product to source without hunting through the nav.

### Outstanding actions before recording

1. **Publish the rest of ENS records + reverse name** (one shot, ~7 txs on Sepolia):
   ```bash
   docker compose exec -T backend uv run python scripts/ens_setup.py \
       --base-url https://<your-public-backend>     # localhost is fine for the recording
   ```
   Sets `url`, `description`, `org.erc8004.descriptor`, `org.spieon.scan-endpoint`, `com.github`, `org.spieon.identity`, plus reverse name. Cost: ~0.001 ETH on Sepolia. Verify at https://sepolia.app.ens.domains/spieon-agent.eth.
2. **Generate a `kh_…` KeeperHub API key** (the existing `wfb_…` token is read-only, can't create workflows). On https://app.keeperhub.com → Organization / API Keys. Replace `KEEPERHUB_API_KEY` in `.env`, then `docker compose up -d --force-recreate backend` to pick up the new env, then:
   ```bash
   curl -s -X POST https://api-spieon.agicitizens.com/keeperhub/install \
       -H 'content-type: application/json' \
       -d '{"name": "spieon.finding.payout"}'
   ```
   Copy the returned `workflow_id` → `KEEPERHUB_PAYOUT_WORKFLOW_ID` in `.env` → recreate backend again.



The demo is **hybrid**: a live scan demonstrates the agent's reasoning loop in
real time, and a pre-existing seeded scan provides the findings, attestations,
and bounty payouts for the chain proof beats.

## 1. One-time setup (do once before the first dry-run)

### 1.1 Environment

`.env` at repo root must have all of:

```
OPENROUTER_API_KEY=sk-or-v1-…           # see openrouter.ai/keys
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-120b    # or anthropic/claude-3.5-sonnet
JUDGE_MODEL=anthropic/claude-3.5-haiku

AGENT_PRIVATE_KEY=…                     # 64-char hex (no 0x prefix)
AGENT_ADDRESS=0x…                       # checksummed
EAS_SCHEMA_UID=0x…                      # 66-char hex; registered once on Base Sepolia
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
EAS_CONTRACT_ADDRESS=0x4200000000000000000000000000000000000021
EAS_SCHEMA_REGISTRY_ADDRESS=0x4200000000000000000000000000000000000020
```

### 1.2 Generate the agent wallet (skip if already done)

```bash
docker compose exec -T backend uv run python -c "
from eth_account import Account
acct = Account.create()
print(f'AGENT_ADDRESS={acct.address}')
print(f'AGENT_PRIVATE_KEY={acct.key.hex()}')
"
```

Paste both into `.env`. Fund the address with ~0.005 ETH on Base Sepolia from
any no-mainnet faucet (bwarelabs, chainlink, thirdweb, triangle).

### 1.3 Register the EAS schema (skip if already done)

The schema only needs to be registered once. Run from the backend container so
it picks up the agent key:

```bash
docker compose exec -T backend uv run python <<'PY'
import asyncio
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider
from eth_account import Account
from app.config import get_settings

REGISTRY_ABI = [{"inputs":[{"name":"schema","type":"string"},{"name":"resolver","type":"address"},{"name":"revocable","type":"bool"}],"name":"register","outputs":[{"name":"","type":"bytes32"}],"stateMutability":"nonpayable","type":"function"}]
SCHEMA = "bytes32 scanId, string target, uint8 severity, bytes32 moduleHash, uint256 costInUsdcMicros, string encryptedBundleURI, bytes32 ciphertextSha256, string owaspId, string atlasTechniqueId, string maestroId"

async def main():
    s = get_settings()
    w3 = AsyncWeb3(AsyncHTTPProvider(s.base_sepolia_rpc_url))
    acct = Account.from_key(s.agent_private_key)
    contract = w3.eth.contract(address=w3.to_checksum_address(s.eas_schema_registry_address), abi=REGISTRY_ABI)
    nonce = await w3.eth.get_transaction_count(acct.address)
    tx = await contract.functions.register(SCHEMA, "0x0000000000000000000000000000000000000000", True).build_transaction({"from": acct.address, "nonce": nonce, "chainId": s.base_sepolia_chain_id, "value": 0})
    signed = acct.sign_transaction(tx)
    raw = signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction
    tx_hash = await w3.eth.send_raw_transaction(raw)
    receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"status: {receipt.status}")
    for log in receipt.logs:
        if len(log.get("topics") or []) >= 2:
            uid = log["topics"][1]
            uid = uid.hex() if hasattr(uid, "hex") else str(uid)
            if not uid.startswith("0x"): uid = "0x" + uid
            print(f"SCHEMA_UID={uid}")
            return

asyncio.run(main())
PY
```

Paste the printed `SCHEMA_UID` into `.env` as `EAS_SCHEMA_UID=`.

## 2. Stage the demo environment (every run)

```bash
docker compose up -d                                          # postgres + langfuse + backend
docker compose exec -T backend uv run alembic upgrade head    # migrations
docker compose exec -T postgres psql -U spieon -d spieon -c "DELETE FROM findings;"   # wipe stub findings if reseeding
docker compose exec -T backend uv run python scripts/seed_demo.py
make frontend                                                 # :3000 on the host
```

Verify before recording:

```bash
curl -s https://api-spieon.agicitizens.com/agent/stats
# expect non-zero scans/findings/heuristics
```

Open `https://spieon.agicitizens.com/`. HTTPS satisfies the Web Crypto secure
context requirement, so the hosted site is now the default demo surface.

## 3. The 7 beats — concrete clicks

### Beat 1 — Setup (0:00–0:25)

Land on `https://spieon.agicitizens.com/`. Banner reads e.g. _"24 scans · 24 completed ·
4 findings · 7 heuristics attested"_. Mention persistent-identity, agent
address, ERC-8004 entry.

Optional pre-roll: open `/hackathon` first for 5-10 seconds to show the judge packet, then return home and continue the live product walkthrough.

**Quick aside (optional, ~5s):** click into `/agent`. Two new things to call
out without dwelling:

- The **ENS identity** block above the wallet hex — `spieon-agent.eth` plus
  chain id, all resolved live from Sepolia. Voice-over: _"the agent has its own
  ENS name; everything below is read from chain at request time, no hardcoded
  strings."_
- The **KeeperHub · Payout workflow** panel — shows `live · paid per run via
  x402` once the workflow is installed. This previews Beat 5.

### Beat 2 — Target (0:25–0:45)

Click **Scan**. Form fields:

- **Target URL**: a **publicly reachable** MCP or x402 endpoint the production backend can access. If you still want to use the local DVMCP SSE target, keep the live-scan beat on the local stack instead of the hosted one.
- **Operator address**: any 0x address (your wallet)
- **Budget**: `0.50` USDC · **Bounty**: `5.0` USDC
- **Recipient key**: click **Generate**, then **Download**
- **Consent**: check
- **Submit**

### Beat 3 — Probing with narration (0:45–2:30)

Browser auto-redirects to `/scan/<id>`. The narration WebSocket streams:

1. _recon_ — "Inspecting <target> (target_type=...)"
2. _plan_ — real gpt-oss-120b rationale, e.g. _"For an MCP SSE endpoint, schema and tool description injection probes directly test LLM handling…"_
3. _probe_ — "Ran 2 probes, 0 findings…"
4. _reflect_ — real gpt-oss-120b decision, e.g. _"Reflect: continue_planned. We've executed two probes without findings and only have one iteration left…"_
5. _adapt_ — "Adaptive iteration 1: continuing planned probes"
6. Two more reflect/adapt cycles
7. _verify_ / _attest_ / _consolidate_ — workflow closes out

This is the "watch the agent think" beat. Total time ≈ 60–90s. Voice over the
plan and reflect rationales — they're the demo's centerpiece.

> **Why might the live scan show zero findings?** That's acceptable for the
> hosted demo. The live beat is there to show planning, reflection, adaptation,
> and budget-aware execution. The attestation and payout proof beats come from
> seeded scans with stable onchain artifacts.

### Beat 4 — Attestation (2:30–3:00)

**Click into a seeded scan** (top of the scan list — `https://demo.spieon/mcp`
or `https://demo.spieon/x402-protected`). It has:

- 1–3 findings shown with severity, OWASP ID, attestation hash
- Each attestation hash links to `https://base-sepolia.easscan.org/attestation/view/0x…` and **resolves to a real onchain attestation** signed by the agent wallet. Click one through to prove it.

Use the verified UIDs from the seeded data:

| Finding                                | UID           | easscan link                                                                                                                 |
| -------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| MCP tool description injection (LLM01) | `0x5c9d0bd5…` | [view](https://base-sepolia.easscan.org/attestation/view/0x5c9d0bd59a21403b1bbb7ec827837119b8b27968fd693fccefd4d939c992a054) |
| x402 payment replay accepted (API07)   | `0x418c0920…` | [view](https://base-sepolia.easscan.org/attestation/view/0x418c09205731621cc4ca35078452e99dd40fbf814ce81cb6e3c95b236df498fd) |
| MCP tool description injection (LLM01) | `0x0a2e079c…` | [view](https://base-sepolia.easscan.org/attestation/view/0x0a2e079cf786ebf897e523e7e1c07939ce5df65bb90a7112186ad0345e0aef91) |
| x402 payment replay accepted (API07)   | `0x0d5b913b…` | [view](https://base-sepolia.easscan.org/attestation/view/0x0d5b913b725bafaec104d612d22333f60b514271ed3d6534ddede6cb1e5faa8b) |

(These are stable until you re-run `seed_demo.py` with `DELETE FROM findings`.)

### Beat 5 — Bounty (3:00–3:20)

From the same seeded scan view, hit the **Pay bounty** action. The backend
calls `BountyPool.payout(...)` on Base Sepolia. Show the tx hash — links to
basescan.org. Leaderboard at `/leaderboard` updates with the module author's
balance.

**KeeperHub callout (~5s):** the same response carries
`keeperhub_execution_id` and `keeperhub_paid: true` — Spieon also fired a
KeeperHub workflow (paid via x402 USDC) to log the payout off-chain. Bounce
back to `/agent`; the KeeperHub panel now shows the new execution row with its
status. Voice-over: _"every payout is rail-bridged through KeeperHub, paid in
USDC over x402 — same client we use for the security probes themselves."_

### Beat 6 — Memory (3:20–3:45)

Navigate to `/memory`. Show the heuristics list — at least one reads
_"FastMCP servers tend to accept Cyrillic look-alike characters in tool
names…"_. Mention the L1→L2→L3 promotion process, which the seeded scans have
already exercised (banner shows N heuristics attested).

### Beat 7 — Benchmark credibility (3:45–4:00)

Navigate to `/benchmarks`. Show DVMCP / Cybench / DVLA numbers. Lock these
_before_ recording — don't re-run benchmarks between takes.

### Closing (4:00)

Voice the line from PRD §2 — "Spieon is open source. Every scan public…"

## 4. Recording mechanics

- Prefer `https://spieon.agicitizens.com` for the actual demo take. HTTPS
  satisfies the Web Crypto secure-context requirement for recipient key
  generation.
- Use localhost only if your chosen live target is reachable from your laptop
  but not from the production backend.
- Browser at 1440×900 or 1920×1080 zoomed so wallet addresses + attestation
  hashes are legible.
- Hide bookmarks bar, close other tabs, silence notifications, DnD on.
- One continuous take per beat where possible.
- Have a backup recording of a successful scan ready in case OpenRouter or RPC
  flakes mid-take (PRD §10 risk row).

## 5. Pre-flight smoke test (10 min before take 1)

```bash
# 1. backend healthy
curl -s https://api-spieon.agicitizens.com/health
# expect: {"status":"ok","db":true}

# 2. OpenRouter key still works
docker compose exec -T backend sh -c 'curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/auth/key | head -c 200'
# expect: {"data":{"label":"sk-or-…","limit":...

# 3. agent wallet still has ETH
ADDR=$(grep '^AGENT_ADDRESS=' .env | cut -d= -f2)
curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"$ADDR\",\"latest\"],\"id\":1}" \
  https://sepolia.base.org
# expect: result with non-zero balance

# 4. one of the seeded attestations still resolves
curl -s 'https://base-sepolia.easscan.org/graphql' -H 'Content-Type: application/json' \
  -d '{"query":"{attestation(where:{id:\"0x5c9d0bd59a21403b1bbb7ec827837119b8b27968fd693fccefd4d939c992a054\"}){id attester}}"}'
# expect: {"data":{"attestation":{"id":"0x5c9d…","attester":"0xf89BD3…"}}}

# 5. ENS identity flowing live from Sepolia (sponsor: ENS)
curl -s https://api-spieon.agicitizens.com/.well-known/agent.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ens'))"
# expect: dict with 'name' = 'spieon-agent.eth' and 'textRecords' containing 'url', 'description', etc.
#         (if textRecords only has 'avatar', re-run scripts/ens_setup.py before the take)

# 6. KeeperHub workflow installed (sponsor: KeeperHub)
curl -s https://api-spieon.agicitizens.com/keeperhub/status
# expect: {"configured": true, "api_key_present": true, "workflow_id": "wf_…", ...}
# if "configured": false → either the kh_ key is wrong or KEEPERHUB_PAYOUT_WORKFLOW_ID is unset

# 7. one-shot live integration sweep (runs all three sponsor checks at once)
docker compose exec -T backend uv run python scripts/sponsor_smoketest.py
# expect: PASS on ENS and KeeperHub. (0G is intentionally skipped — see §0.)

# 8. submit one throwaway scan and watch /scan/<id> WS narrate
```

If all eight pass, you're cleared to record.

## 6. Submission

- Upload to YouTube (unlisted)
- ETHGlobal Showcase
- Devpost
- `git tag v1.0.0-hackathon && git push --tags`

## Known gaps to NOT highlight

- Live scan against DVMCP yields zero findings (SSE/streamable-HTTP transport
  mismatch). Don't promise findings during the live beat — promise reasoning.
- The seed's `MCP schema poisoning` finding type silently fails to attest
  onchain (unicode in title breaks ABI encoding). Ship without it; the four
  remaining findings are enough for the chain-proof beat.
- **0G** was scoped out — both Compute and Storage need a Node.js sidecar (per-call
  signed headers + funded $0G wallet). Don't claim 0G in voice-over. The
  sponsor cheat sheet in §0 only lists ENS + KeeperHub.
- The `0g-storage-only-stub` ([backend/app/storage/bundles.py:81](../backend/app/storage/bundles.py#L81))
  exists in code but the env vars are unset, so bundles fall through to
  `LocalBundleStorage`. Judges who read the source will see this — fine, just
  don't pitch it.
