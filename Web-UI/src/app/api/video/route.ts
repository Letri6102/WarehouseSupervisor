export const runtime = "nodejs";

const AI_SERVER = process.env.AI_SERVER_URL || "http://127.0.0.1:8000";

export async function GET() {
  const upstream = await fetch(`${AI_SERVER}/video`, { cache: "no-store" });

  // Forward stream body
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "multipart/x-mixed-replace; boundary=frame",
      "Cache-Control": "no-cache",
      "Pragma": "no-cache",
    },
  });
}
