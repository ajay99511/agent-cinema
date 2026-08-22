# Agentic Cinema — Screenplay Structural Map

An AI agent that gives a **screenwriter-in-revision** an interactive emotional/structural map of their
draft, with **percentile comparisons against a produced-film corpus** ("this scene is in the bottom 8%
for conflict density at this act-position in produced thrillers") — never opaque scores.

Built for the **Agentic Cinema hackathon — ClickHouse track**.

- **AI:** Google Gemini via Vertex AI (Agent Development Kit)
- **Data + retrieval:** ClickHouse, queried **at runtime via the ClickHouse MCP server**
- **Key idea:** a screenplay ships a RAPTOR-style retrieval tree *for free* from its formatting
  (line → scene → sequence → act → film). One `script_nodes` table holds both the corpus and the
  user's draft; comparison is one partition-pruned query.

> **Design invariant:** every number the user sees comes from a live SQL query. Numbers are SQL
> aggregates; the LLM only writes prose and embeddings. No client-side analytics on cached data.

## Repository layout

| Path | What |
|---|---|
| `agent/` | Python ADK agent + thin FastAPI adapter (`server.py`). Deploys to Vertex AI Agent Engine / Cloud Run. |
| `web/` | Next.js frontend. Deploys to Cloud Run (or Vercel). |
| `etl/` | Offline corpus pipeline (parse → tree → NRC score → embed → load). *Slice 2.* |
| `infra/clickhouse/` | `schema.sql` (the `script_nodes` table) + `seed.sql` (Slice-1 skeleton data). |
| `docs/plans/` | The implementation spec. |
| `features/PROGRESS.md` | Living build tracker — **read this first** to see current state. |

## Quick start (Slice 1 skeleton)

Prerequisites: a **ClickHouse Cloud** service, a **Google Cloud** project with Vertex AI enabled, and
`gcloud auth application-default login` completed.

```bash
# 1. Create the table and seed it (paste into ClickHouse Cloud SQL console, or via clickhouse client)
#    infra/clickhouse/schema.sql  then  infra/clickhouse/seed.sql

# 2. Agent (Python)
cd agent
cp .env.example .env         # fill in ClickHouse + GCP values
uv sync
uv run pytest                # runs the offline unit tests
uv run uvicorn server:app --reload --port 8080

# 3. Web (Next.js), in another terminal
cd web
cp .env.example .env.local   # set AGENT_URL=http://localhost:8080
npm install
npm run dev                  # http://localhost:3000
```

Ask *"What is the average conflict of the scenes?"* — the agent turns it into a `SELECT` run through
the ClickHouse MCP server, and the UI shows both the answer and the SQL that produced it.

## Status

See [`features/PROGRESS.md`](features/PROGRESS.md). Currently: **Slice 1 — walking skeleton.**

## License

MIT — see [`LICENSE`](LICENSE).
