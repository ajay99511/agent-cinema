import { NextRequest, NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_URL ?? "http://localhost:8080";

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;
  const scriptId = params.get("script_id");
  const level = params.get("level");
  if (!scriptId || !level) {
    return NextResponse.json({ error: "script_id and level are required" }, { status: 400 });
  }

  const upstream = new URLSearchParams({ script_id: scriptId, level });
  const parentId = params.get("parent_id");
  if (parentId) upstream.set("parent_id", parentId);

  try {
    const res = await fetch(`${AGENT_URL}/arc?${upstream.toString()}`, { cache: "no-store" });
    if (!res.ok) {
      const detail = await res.text();
      return NextResponse.json({ error: `agent error (${res.status})`, detail }, { status: 502 });
    }
    return NextResponse.json(await res.json());
  } catch (err) {
    return NextResponse.json(
      { error: "could not reach the agent", detail: String(err) },
      { status: 502 }
    );
  }
}
