import { useEffect, useRef, useState } from "react";
import { eventsUrl } from "../api";
import type { SSEEvent } from "../types";

const KNOWN_EVENT_TYPES = [
  "run_parsing",
  "stage_started",
  "stage_generated",
  "stage_validated",
  "stage_repaired",
  "stage_awaiting",
  "stage_complete",
  "stage_failed",
  "run_complete",
  "run_cancelled",
];

/**
 * Native EventSource reconnects with Last-Event-ID automatically, and the
 * backend replays from that seq before resuming live streaming -- a refresh
 * mid-run sees no gap, per the build spec.
 */
export function useRunEvents(runId: string | null, onEvent: (event: SSEEvent) => void) {
  const [connected, setConnected] = useState(false);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!runId) return;

    const source = new EventSource(eventsUrl(runId));
    setConnected(true);

    const handlers = KNOWN_EVENT_TYPES.map((type) => {
      const handler = (evt: MessageEvent) => {
        try {
          const data = JSON.parse(evt.data);
          onEventRef.current({ seq: Number(evt.lastEventId), type, stage_id: data.stage_id ?? null, data });
        } catch {
          // ignore malformed event payloads
        }
      };
      source.addEventListener(type, handler as EventListener);
      return [type, handler] as const;
    });

    source.onerror = () => setConnected(false);
    source.onopen = () => setConnected(true);

    return () => {
      for (const [type, handler] of handlers) source.removeEventListener(type, handler as EventListener);
      source.close();
    };
  }, [runId]);

  return { connected };
}
