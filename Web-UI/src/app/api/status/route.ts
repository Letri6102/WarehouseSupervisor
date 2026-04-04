import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const AI_SERVER = process.env.AI_SERVER_URL || "http://127.0.0.1:8000";

export async function GET() {
  try {
    const upstream = await fetch(`${AI_SERVER}/status`, {
      cache: "no-store",
    });

    const text = await upstream.text();

    return new NextResponse(text, {
      status: upstream.status,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
      },
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        ok: false,
        stream_ready: false,
        stream_error: `Không kết nối được backend AI: ${String(error?.message || error)}`,
      },
      { status: 502 }
    );
  }
}