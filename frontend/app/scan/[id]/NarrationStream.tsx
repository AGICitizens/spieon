"use client";

import { useEffect, useRef, useState } from "react";
import type { NarrationEvent } from "@/lib/api";
import { sseBaseUrl, type WsMessage } from "@/lib/ws";

const PHASE_STYLE: Record<NarrationEvent["phase"], string> = {
  recon:
    "border-[color:color-mix(in_srgb,var(--info)_40%,black_10%)] bg-[color:color-mix(in_srgb,var(--info)_8%,white_92%)] text-[color:color-mix(in_srgb,var(--info)_82%,black_18%)]",
  plan:
    "border-[color:color-mix(in_srgb,var(--accent)_40%,black_10%)] bg-[color:color-mix(in_srgb,var(--accent)_8%,white_92%)] text-[color:color-mix(in_srgb,var(--accent)_82%,black_18%)]",
  probe:
    "border-[color:color-mix(in_srgb,var(--warning)_40%,black_10%)] bg-[color:color-mix(in_srgb,var(--warning)_8%,white_92%)] text-[color:color-mix(in_srgb,var(--warning)_85%,black_15%)]",
  reflect:
    "border-[color:color-mix(in_srgb,var(--info)_40%,black_10%)] bg-[color:color-mix(in_srgb,var(--info)_8%,white_92%)] text-[color:color-mix(in_srgb,var(--info)_82%,black_18%)]",
  adapt:
    "border-[color:color-mix(in_srgb,var(--warning)_40%,black_10%)] bg-[color:color-mix(in_srgb,var(--warning)_8%,white_92%)] text-[color:color-mix(in_srgb,var(--warning)_85%,black_15%)]",
  verify:
    "border-[color:color-mix(in_srgb,var(--success)_40%,black_10%)] bg-[color:color-mix(in_srgb,var(--success)_8%,white_92%)] text-[color:color-mix(in_srgb,var(--success)_82%,black_18%)]",
  attest:
    "border-[color:color-mix(in_srgb,var(--accent)_40%,black_10%)] bg-[color:color-mix(in_srgb,var(--accent)_8%,white_92%)] text-[color:color-mix(in_srgb,var(--accent)_82%,black_18%)]",
  consolidate: "border-[var(--line-strong)] bg-[var(--panel)] text-[var(--ink)]",
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
  initialEvents,
}: {
  scanId: string;
  scanStatus?: string | null;
  initialEvents?: NarrationEvent[];
}) {
  const [events, setEvents] = useState<NarrationEvent[]>(initialEvents ?? []);
  const [state, setState] = useState<ConnectionState>(
    scanStatus && !IN_FLIGHT_STATUSES.has(scanStatus) ? "closed" : "connecting",
  );
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const streamRef = useRef<EventSource | null>(null);
  const inFlight = scanStatus ? IN_FLIGHT_STATUSES.has(scanStatus) : true;

  useEffect(() => {
    setEvents(initialEvents ?? []);
  }, [initialEvents]);

  useEffect(() => {
    if (!inFlight) return;
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, [inFlight]);

  useEffect(() => {
    if (!inFlight) {
      setState("closed");
      return;
    }
    const url = `${sseBaseUrl()}/sse/scans/${scanId}`;
    const stream = new EventSource(url);
    streamRef.current = stream;
    let opened = false;
    const failOpenId = window.setTimeout(() => {
      if (!opened) {
        setState("closed");
        setError("live stream unavailable; showing recorded events");
      }
    }, 5000);

    stream.onopen = () => {
      opened = true;
      window.clearTimeout(failOpenId);
      setState("open");
    };
    stream.onerror = () => {
      if (!opened) {
        setState("closed");
        setError("live stream unavailable; showing recorded events");
      }
    };
    stream.onmessage = (raw) => {
      try {
        const msg = JSON.parse(raw.data) as WsMessage;
        if (msg.type === "narration") {
          setEvents((prev) =>
            prev.some((event) => event.id === msg.event.id) ? prev : [...prev, msg.event],
          );
        } else if (msg.type === "error") {
          setError(msg.error);
        }
      } catch (err) {
        setError(`bad frame: ${(err as Error).message}`);
      }
    };

    return () => {
      window.clearTimeout(failOpenId);
      stream.close();
      streamRef.current = null;
    };
  }, [scanId, inFlight]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--muted)]">
        <span className="border border-[var(--line-strong)] px-2.5 py-1 font-editorial-mono uppercase tracking-[0.18em]">
          {state}
        </span>
        <span className="font-editorial-mono uppercase tracking-[0.18em]">
          {events.length} events
        </span>
        {error ? <span className="text-[var(--danger)]">· {error}</span> : null}
      </div>
      <ol className="space-y-2">
        {events.map((event) => (
          <li
            key={event.id}
            className={`border px-4 py-3 text-sm ${PHASE_STYLE[event.phase]}`}
          >
            <div className="flex items-baseline justify-between gap-3 font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] opacity-75">
              <span>{event.phase}</span>
              <span>
                {new Date(event.created_at).toLocaleTimeString(undefined, {
                  hour12: false,
                })}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6">{event.content}</p>
            {event.decision || event.next_action ? (
              <p className="mt-2 text-xs leading-5 opacity-75">
                {event.decision ? `decision: ${event.decision}` : ""}
                {event.decision && event.next_action ? " · " : ""}
                {event.next_action ? `next: ${event.next_action}` : ""}
              </p>
            ) : null}
          </li>
        ))}
        {events.length === 0 && state === "open" && inFlight ? (
          <li className="editorial-card flex items-center gap-2 p-4 text-sm text-[var(--muted)]">
            <Spinner />
            Connected. Waiting for the agent's first narration event…
          </li>
        ) : null}
        {events.length === 0 && !inFlight ? (
          <li className="editorial-card p-4 text-sm text-[var(--muted)]">
            No narration events were recorded for this scan.
          </li>
        ) : null}
        {inFlight && events.length > 0 ? (
          <li className="editorial-card flex items-center gap-2 border-dashed p-4 text-sm text-[var(--muted)]">
            <Spinner />
            <span>
              {NEXT_PHASE_HINT[events[events.length - 1].phase]}
            </span>
            <span className="ml-auto font-editorial-mono text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
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
      className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-[var(--line-strong)] border-t-[var(--ink)]"
    />
  );
}

function formatElapsed(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}
