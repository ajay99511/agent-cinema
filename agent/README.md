# Agent

Python ADK agent (Gemini via Vertex AI) that queries ClickHouse **through the ClickHouse MCP
server**, plus a thin FastAPI adapter for local runs and Cloud Run deploys.

## Layout
- `screenplay_agent/config.py` — env-driven settings (import-safe, no cloud calls).
- `screenplay_agent/events.py` — pure helper: fold ADK events into `{answer, sql_shown, data}`.
- `screenplay_agent/agent.py` — the ADK agent + ClickHouse MCP toolset (`root_agent`).
- `server.py` — FastAPI: `POST /ask`, `GET /health`.
- `tests/test_events.py` — offline unit tests (no credentials needed).

## Develop
```bash
uv sync                 # create venv + install
uv run pytest           # offline unit tests
cp .env.example .env     # fill in ClickHouse + GCP values
gcloud auth application-default login
uv run uvicorn server:app --reload --port 8080
```

Smoke-test once creds are in place:
```bash
curl -s localhost:8080/health
curl -s localhost:8080/ask -H 'content-type: application/json' \
  -d '{"message":"What is the average conflict of the scenes?"}' | python -m json.tool
```
The response's `sql_shown` should contain the `SELECT` the agent ran.

## Notes
- All AI stays on Google (Vertex/Gemini). Do not add another AI provider — it is disqualifying.
- ClickHouse access is read-only by virtue of the MCP server's query tool.
