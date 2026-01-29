"use client";

import { useEffect, useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import { addLog, clearLogs, exportLogsJson, readLogs } from "@/lib/logStore";
import { LogEntry } from "@/lib/types";

function fmt(ts: number) {
  const d = new Date(ts);
  return d.toLocaleString();
}

function levelBadge(level: string) {
  if (level === "ERROR") return "bg-red-100 text-red-700 border-red-200";
  if (level === "WARN") return "bg-amber-100 text-amber-700 border-amber-200";
  return "bg-blue-100 text-blue-700 border-blue-200";
}

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [q, setQ] = useState("");

  const refresh = () => setLogs(readLogs());

  useEffect(() => {
    addLog("INFO", "system", "Opened Logs page");
    refresh();

    const onStorage = (e: StorageEvent) => {
      if (e.key && e.key.startsWith("zena_monitor_logs_v1")) refresh();
    };
    window.addEventListener("storage", onStorage);

    const timer = setInterval(refresh, 1000);
    return () => {
      window.removeEventListener("storage", onStorage);
      clearInterval(timer);
    };
  }, []);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return logs;
    return logs.filter((l) => {
      const s = `${l.level} ${l.source} ${l.message} ${JSON.stringify(l.data || {})}`.toLowerCase();
      return s.includes(query);
    });
  }, [logs, q]);

  return (
    <AppShell
      title="Logs"
      subtitle="Local logs (localStorage) — MVP. Sau này có thể chuyển sang backend DB."
      right={
        <>
          <button
            onClick={() => {
              const text = exportLogsJson();
              navigator.clipboard.writeText(text);
              addLog("INFO", "system", "Copied logs to clipboard");
            }}
            className="rounded-xl border px-3 py-2 text-sm hover:bg-neutral-50"
          >
            Copy JSON
          </button>
          <button
            onClick={() => {
              clearLogs();
              addLog("INFO", "system", "Logs cleared");
              refresh();
            }}
            className="rounded-xl bg-black px-3 py-2 text-sm text-white hover:opacity-90"
          >
            Clear
          </button>
        </>
      }
    >
      <div className="rounded-3xl border bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-neutral-600">
            Total: <b>{logs.length}</b> • Showing: <b>{filtered.length}</b>
          </div>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search logs..."
            className="w-full max-w-md rounded-2xl border px-3 py-2 text-sm"
          />
        </div>

        <div className="mt-4 space-y-2 max-h-[70vh] overflow-auto pr-1">
          {filtered.length === 0 ? (
            <div className="text-sm text-neutral-500">No logs.</div>
          ) : (
            filtered.map((l) => (
              <div key={l.id} className="rounded-2xl border p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${levelBadge(l.level)}`}>
                      {l.level}
                    </span>
                    <span className="text-xs text-neutral-500">{l.source}</span>
                  </div>
                  <div className="text-xs text-neutral-500">{fmt(l.ts)}</div>
                </div>

                <div className="mt-1 text-sm">{l.message}</div>

                {l.data ? (
                  <pre className="mt-2 max-h-48 overflow-auto rounded-2xl bg-neutral-50 p-2 text-xs">
                    {JSON.stringify(l.data, null, 2)}
                  </pre>
                ) : null}
              </div>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
}
