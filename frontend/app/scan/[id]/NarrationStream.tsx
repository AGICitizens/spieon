"use client";

import { useEffect, useRef, useState } from "react";
import { type NarrationEvent, type WsMessage, wsBaseUrl } from "@/lib/ws";

const PHASE_STYLE: Record<NarrationEvent["phase"], string> = {
  recon: "border-sky-700 bg-sky-950/40 text-sky-200",
  plan: "border-indigo-700 bg-indigo-950/40 text-indigo-200",
  probe: "border-orange-700 bg-orange-950/40 text-orange-200",
  reflect: "border-cyan-700 bg-cyan-950/40 text-cyan-200",
  adapt: "border-amber-700 bg-amber-950/40 text-amber-200",
  verify: "border-emerald-700 bg-emerald-950/40 text-emerald-200",
  attest: "border-purple-700 bg-purple-950/40 text-purple-200",
  consolidate: "border-zinc-700 bg-zinc-950/40 text-zinc-200",
};

const NEXT_PHASE_HINT: Record<NarrationEvent["phase"], string> = {
  recon: "Planning probes…",
  plan: "Running probes…",
  probe: "Reflecting on results…",
  reflect: "Adapting plan…",
  adapt: "Running probes…",
  verify: "Posting attestations on-chain…",
  attest: "Consolidating memory…",
  consolidate: "Wrapping up…",
};

const IN_FLIGHT_STATUSES = new Set([
  "pending",
  "running",
  "verifying",
  "attesting",
]);

type ConnectionState = "connecting" | "open" | "closed";

export default function NarrationStream({
  scanId,
  scanStatus,
}: {
  scanId: string;
  scanStatus?: string | null;
}) {
  const [events, setEvents] = useState<NarrationEvent[]>([]);
  const [state, setState] = useState<ConnectionState>("connecting");
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const wsRef = useRef<WebSocket | null>(null);
  const inFlight = scanStatus ? IN_FLIGHT_STATUSES.has(scanStatus) : true;

  useEffect(() => {
    if (!inFlight) return;
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, [inFlight]);

  useEffect(() => {
    const url = `${wsBaseUrl()}/ws/scans/${scanId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setState("open");
    ws.onclose = () => setState("closed");
    ws.onerror = () => setError("websocket error");
    ws.onmessage = (raw) => {
      try {
        const msg = JSON.parse(raw.data) as WsMessage;
        if (msg.type === "narration") {
          setEvents((prev) => [...prev, msg.event]);
        } else if (msg.type === "error") {
          setError(msg.error);
        }
      } catch (err) {
        setError(`bad frame: ${(err as Error).message}`);
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [scanId]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 text-xs text-zinc-500">
        <span className="rounded border border-zinc-800 px-2 py-0.5">
          {state}
        </span>
        <span>{events.length} events</span>
        {error ? <span className="text-red-400">· {error}</span> : null}
      </div>
      <ol className="space-y-2">
        {events.map((event) => (
          <li
            key={event.id}
            className={`rounded-md border px-3 py-2 text-sm ${PHASE_STYLE[event.phase]}`}
          >
            <div className="flex items-baseline justify-between gap-3 text-xs uppercase tracking-wide opacity-70">
              <span>{event.phase}</span>
              <span>
                {new Date(event.created_at).toLocaleTimeString(undefined, {
                  hour12: false,
                })}
              </span>
            </div>
            <p className="mt-1 text-sm">{event.content}</p>
            {event.decision || event.next_action ? (
              <p className="mt-1 text-xs opacity-70">
                {event.decision ? `decision: ${event.decision}` : ""}
                {event.decision && event.next_action ? " · " : ""}
                {event.next_action ? `next: ${event.next_action}` : ""}
              </p>
            ) : null}
          </li>
        ))}
        {events.length === 0 && state === "open" && inFlight ? (
          <li className="flex items-center gap-2 text-sm text-zinc-500">
            <Spinner />
            Connected. Waiting for the agent's first narration event…
          </li>
        ) : null}
        {inFlight && events.length > 0 ? (
          <li className="flex items-center gap-2 rounded-md border border-dashed border-zinc-700 bg-zinc-950/40 px-3 py-2 text-sm text-zinc-400">
            <Spinner />
            <span>
              {NEXT_PHASE_HINT[events[events.length - 1].phase]}
            </span>
            <span className="ml-auto text-xs text-zinc-500">
              {formatElapsed(now - new Date(events[events.length - 1].created_at).getTime())} since last event
            </span>
          </li>
        ) : null}
      </ol>
    </div>
  );
}

function Spinner() {
  return (
    <span
      aria-hidden
      className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-zinc-600 border-t-zinc-200"
    />
  );
}

function formatElapsed(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}
