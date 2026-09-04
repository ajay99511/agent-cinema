import { NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_URL ?? "http://localhost:8080";

export async function GET() {
  try {
    const res = await fetch(`${AGENT_URL}/films`, { cache: "no-store" });
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
