"use client";

import { LogEntry, LogLevel } from "./types";

const KEY = "zena_monitor_logs_v1";

function uid() {
  try {
    return crypto.randomUUID();
  } catch {
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }
}

function safeParse(s: string | null): LogEntry[] {
  if (!s) return [];
  try {
    const arr = JSON.parse(s);
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

export function readLogs(): LogEntry[] {
  if (typeof window === "undefined") return [];
  return safeParse(localStorage.getItem(KEY)).sort((a, b) => b.ts - a.ts);
}

export function writeLogs(logs: LogEntry[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(logs.slice(0, 500))); // giới hạn 500 dòng
  // ping để các page khác biết refresh (simple)
  localStorage.setItem(KEY + "_ping", String(Date.now()));
}

export function addLog(
  level: LogLevel,
  source: LogEntry["source"],
  message: string,
  data?: Record<string, any>
) {
  const logs = readLogs();
  logs.unshift({ id: uid(), ts: Date.now(), level, source, message, data });
  writeLogs(logs);
}

export function clearLogs() {
  writeLogs([]);
}

export function exportLogsJson(): string {
  return JSON.stringify(readLogs(), null, 2);
}
