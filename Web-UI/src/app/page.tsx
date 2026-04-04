import NavCard from "@/components/NavCard";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-neutral-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="rounded-3xl border bg-white p-6 shadow-sm">
          <div className="text-2xl font-bold">Monitoring Dashboard</div>
          <div className="mt-2 text-sm text-neutral-600">
            Điều hướng nhanh các chức năng: Webcam stream, Upload video detect, Logs.
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <NavCard
            href="/webcam"
            title="Webcam Monitor"
            desc="Xem live stream do AI backend đọc camera + overlay YOLO."
            meta="LIVE"
          />
          <NavCard
            href="/upload"
            title="Upload Video Detect"
            desc="Tải video lên để chạy detect (phụ thuộc endpoint backend)."
            meta="BATCH"
          />
          <NavCard
            href="/logs"
            title="Logs"
            desc="Xem log hoạt động: kết nối backend, count thay đổi, lỗi upload."
            meta="AUDIT"
          />
        </div>

        <div className="rounded-3xl border bg-white p-6 shadow-sm text-sm text-neutral-700">
          <div className="font-semibold mb-2">Ghi chú</div>
          <ul className="list-disc pl-5 space-y-1">
            <li>Trang <b>/webcam</b> sẽ hiển thị MJPEG stream từ backend (vd: 127.0.0.1:8000/video).</li>
            <li>Logs hiện lưu ở <b>localStorage</b> (MVP). Sau này có thể chuyển sang DB + API.</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
