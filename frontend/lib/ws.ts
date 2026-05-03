import type { NarrationEvent } from "@/lib/api";

const HTTP_FALLBACK = "http://localhost:8000";

export function sseBaseUrl(): string {
  const api = process.env.NEXT_PUBLIC_API_URL;
  if (!api) return HTTP_FALLBACK;
  return api.replace(/\/$/, "");
}

export type WsMessage =
  | { type: "narration"; event: NarrationEvent }
  | { type: "ready" }
  | { type: "ping" }
  | { type: "error"; error: string };
