"use client";

import { useEffect, useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import { addLog } from "@/lib/logStore";

const VIDEO_URL = "http://127.0.0.1:8000/video";
const STATUS_URL = "http://127.0.0.1:8000/status";

function fmtTime(tsMs: number) {
  return new Date(tsMs).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function WebcamPage() {
  const [count, setCount] = useState(0);
  const [lastTsMs, setLastTsMs] = useState<number | null>(null);
  const [status, setStatus] = useState<"connected" | "disconnected">("disconnected");
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const statusPill = useMemo(() => {
    return status === "connected"
      ? "bg-green-100 text-green-700 border-green-200"
      : "bg-red-100 text-red-700 border-red-200";
  }, [status]);

  useEffect(() => {
    addLog("INFO", "system", "Opened Webcam page");
  }, []);

  // Poll backend status
  useEffect(() => {
    let prevStatus: "connected" | "disconnected" = "disconnected";
    let prevCount = -1;

    const timer = setInterval(async () => {
      const t0 = performance.now();
      try {
        const r = await fetch(STATUS_URL, { cache: "no-store" });
        const t1 = performance.now();
        setLatencyMs(Math.round(t1 - t0));

        if (!r.ok) {
          setStatus("disconnected");
          if (prevStatus !== "disconnected") addLog("WARN", "webcam", "Backend disconnected");
          prevStatus = "disconnected";
          return;
        }

        const data = await r.json();
        const c = data.count ?? 0;
        const ts = data.ts ? data.ts * 1000 : null;

        setCount(c);
        setLastTsMs(ts);
        setStatus("connected");

        if (prevStatus !== "connected") addLog("INFO", "webcam", "Backend connected");
        if (prevCount !== -1 && c !== prevCount) {
          addLog("INFO", "webcam", `Count changed: ${prevCount} → ${c}`, { prevCount, count: c });
        }

        prevStatus = "connected";
        prevCount = c;
      } catch (e) {
        setStatus("disconnected");
        if (prevStatus !== "disconnected") addLog("ERROR", "webcam", "Backend poll failed", { error: String(e) });
        prevStatus = "disconnected";
      }
    }, 500);

    return () => clearInterval(timer);
  }, []);

  return (
    <AppShell
      title="Webcam Monitor"
      subtitle="AI backend reads camera & runs YOLO. Web chỉ xem stream + status."
      right={
        <>
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusPill}`}>
            {status === "connected" ? "CONNECTED" : "DISCONNECTED"}
          </span>
          <a
            href={VIDEO_URL}
            target="_blank"
            rel="noreferrer"
            className="rounded-xl border px-3 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
          >
            Open /video
          </a>
          <a
            href={STATUS_URL}
            target="_blank"
            rel="noreferrer"
            className="rounded-xl border px-3 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
          >
            Open /status
          </a>
        </>
      }
    >
      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-12 lg:col-span-8">
          <div className="rounded-3xl border bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-base font-semibold">Live Stream</div>
                <div className="text-xs text-neutral-500">Source: {VIDEO_URL}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-neutral-100 px-3 py-1 text-xs text-neutral-700">
                  Persons: <b className="tabular-nums">{count}</b>
                </span>
                <span className="rounded-full bg-neutral-100 px-3 py-1 text-xs text-neutral-700">
                  Latency: <b className="tabular-nums">{latencyMs ?? "-"}ms</b>
                </span>
              </div>
            </div>

            <div className="relative overflow-hidden rounded-2xl bg-black">
              <div className="aspect-video w-full">
                <img src={VIDEO_URL} className="h-full w-full object-cover" alt="AI stream" />
              </div>

              <div className="absolute left-4 top-4 rounded-xl bg-black/60 px-3 py-1 text-xs text-white">
                {status === "connected" ? "LIVE" : "OFFLINE"}
              </div>

              <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between gap-3">
                <div className="rounded-xl bg-black/60 px-3 py-1 text-xs text-white">
                  Updated:{" "}
                  {lastTsMs ? <b className="tabular-nums">{fmtTime(lastTsMs)}</b> : <span className="opacity-80">—</span>}
                </div>
                <div className="rounded-xl bg-black/60 px-3 py-1 text-xs text-white">
                  Tip: chỉnh conf/iou/imgsz ở backend để tối ưu detection
                </div>
              </div>
            </div>
          </div>
        </section>

        <aside className="col-span-12 lg:col-span-4 space-y-6">
          <div className="rounded-3xl border bg-white p-4 shadow-sm">
            <div className="text-base font-semibold">Summary</div>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border bg-neutral-50 p-3">
                <div className="text-xs text-neutral-500">Detected</div>
                <div className="mt-1 text-2xl font-bold tabular-nums">{count}</div>
                <div className="text-xs text-neutral-500">persons</div>
              </div>
              <div className="rounded-2xl border bg-neutral-50 p-3">
                <div className="text-xs text-neutral-500">Backend</div>
                <div className="mt-1 text-sm font-semibold">
                  {status === "connected" ? "Healthy" : "Down"}
                </div>
                <div className="text-xs text-neutral-500">
                  {latencyMs != null ? `~${latencyMs}ms` : "—"}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border bg-white p-4 shadow-sm">
            <div className="text-base font-semibold">Rule (demo)</div>
            <div className="mt-2 text-sm text-neutral-700">
              Nếu <b>persons &gt; 0</b> → xem như khu vực “occupied”.
            </div>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
