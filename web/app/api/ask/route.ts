// Server-side proxy to the agent's FastAPI adapter. Keeps AGENT_URL off the client
// and gives us one place to add auth/rate-limiting later.
import { NextRequest, NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_URL ?? "http://localhost:8080";

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON body" }, { status: 400 });
  }

  const { message, session_id } = (body ?? {}) as {
    message?: string;
    session_id?: string;
  };
  if (!message || typeof message !== "string") {
    return NextResponse.json({ error: "message is required" }, { status: 400 });
  }

  try {
    const res = await fetch(`${AGENT_URL}/ask`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ message, session_id }),
    });
    if (!res.ok) {
      const detail = await res.text();
      return NextResponse.json(
        { error: `agent error (${res.status})`, detail },
        { status: 502 }
      );
    }
    return NextResponse.json(await res.json());
  } catch (err) {
    // The agent being unreachable must surface as an honest error, never a fake answer.
    return NextResponse.json(
      { error: "could not reach the agent", detail: String(err) },
      { status: 502 }
    );
  }
}
