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
};
