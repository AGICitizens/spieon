const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

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
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export type AgentStats = {
  address: string | null;
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
};
