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

type ConnectionState = "connecting" | "open" | "closed";

export default function NarrationStream({ scanId }: { scanId: string }) {
  const [events, setEvents] = useState<NarrationEvent[]>([]);
  const [state, setState] = useState<ConnectionState>("connecting");
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

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
        {events.length === 0 && state === "open" ? (
          <li className="text-sm text-zinc-500">
            Connected. Waiting for the agent to emit its first narration event…
          </li>
        ) : null}
      </ol>
    </div>
  );
}
