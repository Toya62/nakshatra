import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8004";

export async function GET(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  const target = `${BACKEND_URL}/${path.join("/")}${req.nextUrl.search}`;
  try {
    const res = await fetch(target, { cache: "no-store" });
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" },
    });
  } catch (err: unknown) {
    return NextResponse.json(
      { detail: `Proxy GET failed: ${(err as Error).message}` },
      { status: 502 }
    );
  }
}

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  const target = `${BACKEND_URL}/${path.join("/")}${req.nextUrl.search}`;
  try {
    const bodyText = await req.text();
    const res = await fetch(target, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: bodyText,
      cache: "no-store",
    });
    if (res.headers.get("Content-Type")?.includes("text/event-stream") && res.body) {
      return new Response(res.body, {
        status: res.status,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache, no-transform",
          "Connection": "keep-alive",
        },
      });
    }

    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" },
    });
  } catch (err: unknown) {
    return NextResponse.json(
      { detail: `Proxy POST failed: ${(err as Error).message}` },
      { status: 502 }
    );
  }
}
