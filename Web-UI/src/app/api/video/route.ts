import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const AI_SERVER = process.env.AI_SERVER_URL || "http://127.0.0.1:8000";

export async function GET() {
  try {
    const upstream = await fetch(`${AI_SERVER}/video`, {
      cache: "no-store",
    });

    if (!upstream.ok || !upstream.body) {
      const text = await upstream.text().catch(() => "");
      return new NextResponse(
        text || "Cannot connect to AI video stream",
        { status: upstream.status || 502 }
      );
    }

    return new NextResponse(upstream.body, {
      status: 200,
      headers: {
        "Content-Type":
          upstream.headers.get("content-type") ||
          "multipart/x-mixed-replace; boundary=frame",
        "Cache-Control":
          "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
        Pragma: "no-cache",
        Expires: "0",
      },
    });
  } catch (error: any) {
    return new NextResponse(
      `Video proxy error: ${String(error?.message || error)}`,
      { status: 502 }
    );
  }
}