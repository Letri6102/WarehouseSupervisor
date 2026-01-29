"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { MonitorEvent } from "@/lib/types";
import { BACKEND_WS } from "@/lib/config";

type Options = {
  maxEvents?: number;
};

export function useEventStream(opts: Options = {}) {
  const maxEvents = opts.maxEvents ?? 200;
  const [events, setEvents] = useState<MonitorEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const pushEvent = (ev: MonitorEvent) => {
    setEvents(prev => {
      const next = [ev, ...prev];
      return next.slice(0, maxEvents);
    });
  };

  useEffect(() => {
    let isMounted = true;

    // Connect WS
    try {
      const ws = new WebSocket(BACKEND_WS);
      wsRef.current = ws;

      ws.onopen = () => isMounted && setConnected(true);
      ws.onclose = () => isMounted && setConnected(false);
      ws.onerror = () => isMounted && setConnected(false);

      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          // Backend có thể gửi 1 event hoặc mảng events
          if (Array.isArray(data)) {
            data.forEach(pushEvent);
          } else {
            pushEvent(data);
          }
        } catch {
          // ignore parse error
        }
      };

      return () => {
        isMounted = false;
        ws.close();
      };
    } catch {
      // ignore
    }
  }, [maxEvents]);

  // Một chút tiện ích: stats theo camera
  const countByCamera = useMemo(() => {
    const map: Record<string, number> = {};
    for (const e of events) {
      if (e.type === "COUNT") map[e.camera_id] = (map[e.camera_id] ?? 0) + (e.delta ?? 0);
    }
    return map;
  }, [events]);

  return { events, connected, countByCamera };
}
