"""Thin HTTP adapter around the ADK agent.

Purpose: (1) run the agent locally before it's deployed to Agent Engine, and (2) shape the
response into the frontend contract ``{answer, sql_shown, data}`` — including the SQL the
agent actually ran, which is our "every number came from a live query" proof.

Deployable to Cloud Run as-is. POST /ask {message, session_id?} -> AgentReply.
"""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

# MUST run before `screenplay_agent.agent` is imported: that module builds `root_agent`
# at import time, and the google-genai SDK reads GOOGLE_GENAI_USE_VERTEXAI /
# GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION straight from the process environment —
# values from `.env` don't exist there until dotenv puts them there.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

from screenplay_agent.agent import root_agent
from screenplay_agent.events import extract_reply
from screenplay_agent.data_api import arc_data, list_films

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


@app.get("/films")
async def films() -> dict:
    return list_films()


@app.get("/arc")
async def arc(script_id: int, level: int, parent_id: int | None = None) -> dict:
    """Direct-SQL data for the interactive map chart — see data_api.py module docstring
    for why this bypasses the LLM agent entirely."""
    return arc_data(script_id, level, parent_id)


@app.post("/ask")
async def ask(req: AskRequest) -> dict:
    user_id = "web"
    session_id = req.session_id or str(uuid.uuid4())

    # create_session() is NOT idempotent — it raises AlreadyExistsError on a repeat
    # session_id rather than being a no-op (confirmed the hard way: this crashed every
    # second-question-onward request in a real multi-turn conversation with a 500, since
    # the frontend correctly reuses the session_id it got back from the first /ask call).
    # get_session() returns None instead of raising, so check first and only create if new.
    if await _session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    ) is None:
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
