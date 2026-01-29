"use client";

import { useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import { addLog } from "@/lib/logStore";

const VIDEO_DETECT_URL = "http://127.0.0.1:8000/video_detect";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>("");

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : ""), [file]);

  const onUpload = async () => {
    if (!file) return;
    setBusy(true);
    setError("");
    setResult(null);

    addLog("INFO", "upload", "Upload started", { name: file.name, size: file.size });

    try {
      const fd = new FormData();
      fd.append("file", file);

      const r = await fetch(VIDEO_DETECT_URL, { method: "POST", body: fd });
      const text = await r.text();

      if (!r.ok) {
        setError(`Backend error ${r.status}: ${text}`);
        addLog("ERROR", "upload", "Backend returned error", { status: r.status, body: text });
        return;
      }

      let data: any = null;
      try {
        data = JSON.parse(text);
      } catch {
        setError("Backend returned non-JSON response.");
        addLog("ERROR", "upload", "Non-JSON response", { body: text });
        return;
      }

      setResult(data);
      addLog("INFO", "upload", "Upload finished", { summary: data?.summary ?? null });
    } catch (e: any) {
      setError(String(e?.message || e));
      addLog("ERROR", "upload", "Upload failed", { error: String(e) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell
      title="Upload Video Detect"
      subtitle="Tải video lên backend để chạy detect theo batch (cần endpoint /video_detect)."
      right={
        <a
          href={VIDEO_DETECT_URL}
          target="_blank"
          rel="noreferrer"
          className="rounded-xl border px-3 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
        >
          Backend endpoint
        </a>
      }
    >
      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-12 lg:col-span-7">
          <div className="rounded-3xl border bg-white p-5 shadow-sm space-y-4">
            <div>
              <div className="text-base font-semibold">Chọn video</div>
              <div className="text-sm text-neutral-600">
                Gợi ý: video ngắn để test. Backend sẽ trả bbox/count theo từng đoạn hoặc summary.
              </div>
            </div>

            <input
              type="file"
              accept="video/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm"
            />

            <div className="flex gap-2">
              <button
                disabled={!file || busy}
                onClick={onUpload}
                className="rounded-2xl bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                {busy ? "Detecting..." : "Upload & Detect"}
              </button>
              <button
                disabled={busy}
                onClick={() => {
                  setFile(null);
                  setResult(null);
                  setError("");
                  addLog("INFO", "upload", "Cleared upload form");
                }}
                className="rounded-2xl border px-4 py-2 text-sm hover:bg-neutral-50 disabled:opacity-50"
              >
                Clear
              </button>
            </div>

            {error ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
                <div className="mt-2 text-xs text-red-600">
                  Nếu backend chưa có endpoint <b>/video_detect</b> thì lỗi là bình thường. Bạn muốn mình code endpoint đó luôn không?
                </div>
              </div>
            ) : null}
          </div>
        </section>

        <aside className="col-span-12 lg:col-span-5 space-y-6">
          <div className="rounded-3xl border bg-white p-5 shadow-sm">
            <div className="text-base font-semibold">Preview</div>
            <div className="mt-3 rounded-2xl bg-black overflow-hidden aspect-video">
              {file ? (
                <video src={previewUrl} controls className="w-full h-full object-contain" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-white/70 text-sm">
                  Chưa chọn video
                </div>
              )}
            </div>
            {file ? (
              <div className="mt-2 text-xs text-neutral-500">
                {file.name} • {(file.size / (1024 * 1024)).toFixed(2)} MB
              </div>
            ) : null}
          </div>

          <div className="rounded-3xl border bg-white p-5 shadow-sm">
            <div className="text-base font-semibold">Result</div>
            <div className="mt-2 text-sm text-neutral-700">
              {result ? (
                <pre className="max-h-[40vh] overflow-auto rounded-2xl bg-neutral-50 p-3 text-xs">
                  {JSON.stringify(result, null, 2)}
                </pre>
              ) : (
                <div className="text-neutral-500">Chưa có kết quả.</div>
              )}
            </div>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
