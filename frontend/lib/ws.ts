const FALLBACK = "ws://localhost:8000";

export function wsBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_URL;
  if (explicit) return explicit.replace(/\/$/, "");
  const api = process.env.NEXT_PUBLIC_API_URL;
  if (!api) return FALLBACK;
  return api.replace(/^http/, "ws").replace(/\/$/, "");
}

export type NarrationEvent = {
  id: string;
  scan_id: string;
  phase:
    | "recon"
    | "plan"
    | "probe"
    | "reflect"
    | "adapt"
    | "verify"
    | "attest"
    | "consolidate";
  success_signal: boolean | null;
  target_observations: Record<string, unknown>;
  decision: string | null;
  next_action: string | null;
  content: string;
  context: Record<string, unknown>;
  created_at: string;
};

export type WsMessage =
  | { type: "narration"; event: NarrationEvent }
  | { type: "ready" }
  | { type: "ping" }
  | { type: "error"; error: string };
