export const runtime = "nodejs";

const AI_SERVER = process.env.AI_SERVER_URL || "http://127.0.0.1:8000";

export async function GET() {
  try {
    const r = await fetch(`${AI_SERVER}/status`, { cache: "no-store" });
    const text = await r.text();

    if (!r.ok) {
      return Response.json(
        { ok: false, where: "ai_server", status: r.status, body: text, ai: AI_SERVER },
        { status: 502 }
      );
    }

    // parse JSON safe
    try {
      const data = JSON.parse(text);
      return Response.json({ ok: true, ...data });
    } catch {
      return Response.json(
        { ok: false, where: "parse", body: text, ai: AI_SERVER },
        { status: 502 }
      );
    }
  } catch (e: any) {
    return Response.json(
      { ok: false, where: "connect", message: String(e?.message || e), ai: AI_SERVER },
      { status: 502 }
    );
  }
}
