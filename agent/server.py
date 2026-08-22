"""Thin HTTP adapter around the ADK agent.

Purpose: (1) run the agent locally before it's deployed to Agent Engine, and (2) shape the
response into the frontend contract ``{answer, sql_shown, data}`` — including the SQL the
agent actually ran, which is our "every number came from a live query" proof.

Deployable to Cloud Run as-is. POST /ask {message, session_id?} -> AgentReply.
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

from screenplay_agent.agent import root_agent
from screenplay_agent.events import extract_reply

APP_NAME = "screenplay-analyst"

app = FastAPI(title="Screenplay Analyst Agent")

# The Next.js app calls this from the browser during local dev; lock down in production
# via an env-driven allowlist when the web origin is known.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

_session_service = InMemorySessionService()
_runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=_session_service)


class AskRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask")
async def ask(req: AskRequest) -> dict:
    user_id = "web"
    session_id = req.session_id or str(uuid.uuid4())

    # InMemorySessionService is idempotent-friendly: ensure the session exists.
    await _session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text=req.message)])

    events = []
    async for event in _runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        events.append(event)

    reply = extract_reply(events)
    return {"session_id": session_id, **reply.to_dict()}
