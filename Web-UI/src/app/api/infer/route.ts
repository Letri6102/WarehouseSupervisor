import { NextResponse } from "next/server";

export const runtime = "nodejs";

const AI_SERVER = process.env.AI_SERVER_URL || "http://127.0.0.1:8000";

export async function POST(req: Request) {
  try {
    const formData = await req.formData();

    const upstream = await fetch(`${AI_SERVER}/infer`, {
      method: "POST",
      body: formData,
    });

    const text = await upstream.text();

    // log để bạn nhìn ngay trong terminal Next.js
    if (!upstream.ok) {
      console.error("AI_SERVER error:", upstream.status, text);
      return NextResponse.json(
        { ok: false, where: "ai_server", status: upstream.status, body: text },
        { status: 502 }
      );
    }

    // parse JSON an toàn
    try {
      const data = JSON.parse(text);
      return NextResponse.json({ ok: true, ...data });
    } catch {
      console.error("Non-JSON from AI_SERVER:", text);
      return NextResponse.json(
        { ok: false, where: "proxy_parse", body: text },
        { status: 502 }
      );
    }
  } catch (e: any) {
    console.error("Proxy exception:", e);
    return NextResponse.json(
      { ok: false, where: "proxy_exception", message: String(e?.message || e) },
      { status: 500 }
    );
  }
}
