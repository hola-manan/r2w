// Realtime WebSocket hook (P08) honoring the P07 event union.
import { useEffect, useRef, useState } from "react";
import { API_BASE } from "./client";
import type { Artifact, ImpactItem, Scorecard } from "./types";

export type RealtimeEvent =
  | { t: "reply"; stage: number | null; text: string }
  | { t: "artifact_upserted"; node: Artifact }
  | { t: "scorecard"; scorecard: Scorecard }
  | { t: "impact_diff"; items: ImpactItem[] }
  | { t: "escalation"; payload: Record<string, unknown> }
  | { t: "needs_review"; stages: number[] }
  | { t: "done" }
  | { t: "error"; detail: string };

function wsUrl(projectId: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/projects/${projectId}/ws`;
}

export function useRealtime(projectId: string, onEvent: (e: RealtimeEvent) => void) {
  const [connected, setConnected] = useState(false);
  const ref = useRef<WebSocket | null>(null);
  const cb = useRef(onEvent);
  cb.current = onEvent;

  useEffect(() => {
    const ws = new WebSocket(wsUrl(projectId));
    ref.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      try {
        cb.current(JSON.parse(ev.data) as RealtimeEvent);
      } catch {
        /* ignore malformed frames */
      }
    };
    return () => ws.close();
  }, [projectId]);

  const send = (message: string, persona: string) => {
    ref.current?.send(JSON.stringify({ message, persona }));
  };

  return { connected, send };
}
