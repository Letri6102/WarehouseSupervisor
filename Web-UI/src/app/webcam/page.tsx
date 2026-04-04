"use client";

import { useEffect, useMemo, useState } from "react";

type StatusResponse = {
  ok?: boolean;
  alarm?: boolean;
  count?: number;
  carry_events?: number;
  latency_ms?: number;
  stream_ready?: boolean;
  stream_error?: string;
  stream_source?: string;
  stream_frames?: number;
};

export default function WebcamPage() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [imgVersion, setImgVersion] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const videoSrc = useMemo(() => `/api/video?v=${imgVersion}`, [imgVersion]);

  useEffect(() => {
    let alive = true;

    const fetchStatus = async () => {
      try {
        const res = await fetch("/api/status", { cache: "no-store" });
        const data = await res.json();

        if (!alive) return;
        setStatus(data);
      } catch (error: any) {
        if (!alive) return;
        setStatus({
          ok: false,
          stream_ready: false,
          stream_error: `Không kết nối được backend AI: ${String(error?.message || error)}`,
        });
      }
    };

    fetchStatus();
    const timer = setInterval(fetchStatus, 2000);

    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  const handleReloadStream = () => {
    setLoading(true);
    setImgVersion((v) => v + 1);
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-white px-4 py-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">RTSP Monitor</h1>
            <p className="text-sm text-neutral-400">
              Luồng camera được xử lý từ backend AI.
            </p>
          </div>

          <button
            type="button"
            onClick={handleReloadStream}
            className="rounded-xl bg-white px-4 py-2 text-sm font-medium text-black hover:bg-neutral-200"
          >
            Reload Stream
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
            <div className="text-sm text-neutral-400">Nguồn</div>
            <div className="mt-1 text-lg font-semibold">
              {status?.stream_source || "rtsp"}
            </div>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
            <div className="text-sm text-neutral-400">Trạng thái</div>
            <div className="mt-1 text-lg font-semibold">
              {status?.stream_ready ? "Đang chạy" : "Chưa sẵn sàng"}
            </div>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
            <div className="text-sm text-neutral-400">Số người</div>
            <div className="mt-1 text-lg font-semibold">{status?.count ?? 0}</div>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
            <div className="text-sm text-neutral-400">Độ trễ</div>
            <div className="mt-1 text-lg font-semibold">
              {status?.latency_ms ?? 0} ms
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-black">
          <div className="flex items-center justify-between border-b border-neutral-800 px-4 py-3">
            <div className="text-sm font-medium">Camera Feed</div>
            <div
              className={`text-xs font-medium ${
                status?.alarm ? "text-red-400" : "text-emerald-400"
              }`}
            >
              {status?.alarm ? "ALARM ON" : "ALARM OFF"}
            </div>
          </div>

          <div className="relative min-h-[320px] bg-black">
            {loading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/60 text-sm text-neutral-300">
                Đang tải luồng RTSP...
              </div>
            )}

            <img
              src={videoSrc}
              alt="RTSP stream"
              className="block h-auto w-full"
              onLoad={() => setLoading(false)}
              onError={() => {
                setLoading(false);
                setStatus((prev) => ({
                  ...(prev || {}),
                  ok: false,
                  stream_ready: false,
                  stream_error: "Không kết nối được backend AI",
                }));
              }}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
            <div className="text-sm text-neutral-400">Carry events</div>
            <div className="mt-1 text-lg font-semibold">
              {status?.carry_events ?? 0}
            </div>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
            <div className="text-sm text-neutral-400">Frames nhận được</div>
            <div className="mt-1 text-lg font-semibold">
              {status?.stream_frames ?? 0}
            </div>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
            <div className="text-sm text-neutral-400">Lỗi stream</div>
            <div className="mt-1 break-words text-sm text-red-400">
              {status?.stream_error || "Không có"}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}