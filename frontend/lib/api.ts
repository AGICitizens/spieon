const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS ?? 15000);

export type Health = {
  status: "ok" | "degraded";
  db: boolean;
  error?: string;
};

export type ScanStatus =
  | "pending"
  | "running"
  | "verifying"
  | "attesting"
  | "done"
  | "failed"
  | "canceled";

export type Scan = {
  id: string;
  target_url: string;
  operator_address: string;
  recipient_pubkey: string;
  budget_usdc: string;
  bounty_usdc: string;
  spent_usdc: string;
  status: ScanStatus;
  consent_at: string;
  started_at: string | null;
  completed_at: string | null;
  adapt_iterations: number;
  error: string | null;
  created_at: string;
  updated_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const abortSignal = init?.signal;
  let timedOut = false;
  const cancelOnAbort = () => controller.abort();
  const timeoutId = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);

  abortSignal?.addEventListener("abort", cancelOnAbort, { once: true });

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "content-type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
    }
    if (res.status === 204) {
      return undefined as T;
    }
    return (await res.json()) as T;
  } catch (error) {
    if (timedOut) {
      throw new Error(`Request timed out after ${REQUEST_TIMEOUT_MS}ms: ${path}`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    abortSignal?.removeEventListener("abort", cancelOnAbort);
  }
}

export type AgentStats = {
  address: string | null;
  ens_name: string | null;
  ens_primary_name: string | null;
  ens_avatar: string | null;
  ens_chain_id: number | null;
  scans: number;
  scans_completed: number;
  findings: number;
  heuristics_attested: number;
  spent_usdc: string;
  balances: { eth: string | null; usdc: string | null };
  as_of: string;
};

export type Finding = {
  id: string;
  scan_id: string;
  target_url: string | null;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  summary: string;
  module_hash: string;
  cost_usdc: string;
  owasp_id: string | null;
  atlas_technique_id: string | null;
  maestro_id: string | null;
  encrypted_bundle_uri: string | null;
  ciphertext_sha256: string | null;
  eas_attestation_uid: string | null;
  attested_at: string | null;
  created_at: string;
  bounty_recipient: string | null;
  bounty_amount_usdc: string | null;
  bounty_tx_hash: string | null;
  bounty_paid_at: string | null;
};

export type PayoutResult = {
  finding_id: string;
  recipient: string;
  amount_usdc: string;
  tx_hash: string;
  paid_at: string;
  onchain: boolean;
  keeperhub_execution_id: string | null;
  keeperhub_status: string | null;
  keeperhub_paid: boolean;
};

export type KeeperHubStatus = {
  configured: boolean;
  api_key_present: boolean;
  workflow_id: string | null;
  base_url: string;
};

export type KeeperHubRunsResponse = {
  executions?: Array<{
    id?: string;
    status?: string;
    createdAt?: string;
    [k: string]: unknown;
  }>;
  [k: string]: unknown;
};

export type Heuristic = {
  id: string;
  heuristic_key: string;
  version: number;
  rule: string;
  target_type: string | null;
  probe_class: string | null;
  success_count: number;
  sample_size: number;
  success_rate: number;
  owasp_id: string | null;
  atlas_technique_id: string | null;
  content_hash: string;
  eas_attestation_uid: string | null;
  attested_at: string | null;
  created_at: string;
};

export type ModuleEntry = {
  module_hash: string;
  probe_id: string | null;
  author_address: string | null;
  metadata_uri: string | null;
  severity_cap: "low" | "medium" | "high" | "critical";
  times_used: number;
  success_count: number;
  findings_landed: number;
  bounties_earned_usdc: string;
  owasp_id: string | null;
  atlas_technique_id: string | null;
  registered_at: string | null;
  last_synced_at: string | null;
};

export const api = {
  health: () => request<Health>("/health"),
  listScans: () => request<Scan[]>("/scans"),
  getScan: (id: string) => request<Scan>(`/scans/${id}`),
  createScan: (input: {
    target_url: string;
    operator_address: string;
    recipient_pubkey: string;
    budget_usdc?: string;
    bounty_usdc?: string;
    consent: boolean;
  }) =>
    request<Scan>("/scans", {
      method: "POST",
      body: JSON.stringify({
        budget_usdc: "0",
        bounty_usdc: "0",
        ...input,
      }),
    }),
  agentStats: () => request<AgentStats>("/agent/stats"),
  listFindings: (params?: { scanId?: string; limit?: number }) => {
    const search = new URLSearchParams();
    if (params?.scanId) search.set("scan_id", params.scanId);
    if (params?.limit) search.set("limit", String(params.limit));
    const suffix = search.toString();
    return request<Finding[]>(`/findings${suffix ? `?${suffix}` : ""}`);
  },
  listModules: (limit?: number) =>
    request<ModuleEntry[]>(`/modules${limit ? `?limit=${limit}` : ""}`),
  payFinding: (
    findingId: string,
    body: { recipient: string; amount_usdc: string },
  ) =>
    request<PayoutResult>(`/findings/${findingId}/payout`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listHeuristics: (limit?: number) =>
    request<Heuristic[]>(`/memory/heuristics${limit ? `?limit=${limit}` : ""}`),
  keeperhubStatus: () => request<KeeperHubStatus>("/keeperhub/status"),
  keeperhubRuns: (limit?: number) =>
    request<KeeperHubRunsResponse>(
      `/keeperhub/runs${limit ? `?limit=${limit}` : ""}`,
    ),
};
