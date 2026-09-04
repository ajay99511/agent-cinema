# Devpost submission draft

Copy/paste into the submission form, editing to taste. Ground truth for every claim below is
`features/PROGRESS.md`; don't add anything here that isn't verified there.

---

## Project name

**Agentic Cinema — Screenplay Structural Map**

## Tagline (one line)

An agent that shows a screenwriter the shape of their draft — scored, mapped, and compared
against real produced films, one live ClickHouse query at a time.

## Inspiration

A screenwriter mid-rewrite can tell you a scene *feels* flat. They can't tell you why, or
whether it's actually a problem — there's nothing to compare it to. Coverage notes are
subjective; a 1-10 score on a page is opaque. We wanted a comparison that's specific and
defensible: "this scene is in the bottom 5% for conflict among Act II scenes in produced
dramas" — not a number pulled from nowhere.

The key insight: a screenplay already ships its own retrieval tree, for free, from its own
formatting — line → scene (slugline-delimited) → sequence → act → film. No clustering, no
embeddings-based hierarchy induction. A writer already knows what "Act II" means; that
structure is the whole basis for the comparison.

## What it does

- **An interactive structural/emotional map** (`/map`): pick a film, see its 3-act emotional
  arc, drill down act → sequence → scene, with every point backed by a live SQL query and a
  "show SQL" panel proving it.
- **A natural-language agent** (`/`): ask about the corpus in plain English. The agent can
  answer ad-hoc questions via SQL it writes itself, or — for the comparative claims that
  matter most — call purpose-built tools that compute real percentiles ("this scene's
  conflict is in the 4th percentile among 363 comparable drama scenes") and find similar
  scenes by embedding distance.
- **A real corpus**: 25 produced films (~4,200 scenes) scored, embedded, and summarized, all
  stored in one ClickHouse table alongside the tree structure itself — no separate metadata
  store.

Every number the user sees — chart point, tooltip, chat answer, percentile — comes from a
live query at request time. If the backend is down, the UI shows nothing rather than a
cached or fabricated number.

## How we built it

- **Google ADK + Gemini via Vertex AI** for the agent — both the open-ended `run_query` tool
  (via the ClickHouse MCP server) and native tools for percentile/similarity queries where
  correctness matters more than flexibility.
- **ClickHouse Cloud**, one `script_nodes` table holding the corpus and the tree structure
  together; `cosineDistance` for exact (not approximate) similarity search, filter-first.
- **An offline ETL pipeline**: screenplay text → scene segmentation → NRC VAD lexicon
  emotional scoring (deterministic, not LLM-guessed) → Vertex embeddings → Gemini prose
  summaries → loaded with every parent node's numbers computed as a real `AVG`/`SUM` over its
  children, never invented.
- **Next.js** frontend, **FastAPI** agent adapter, both deployed to **Cloud Run**.

## Challenges we ran into

- **Screenplay formatting is not standardized.** Some sources use clean `INT./EXT.`
  sluglines; others are loose transcripts with none. Rather than build a parser general
  enough for both, we empirically screened every candidate title before including it.
- **A hung network call can silently stall a multi-hour batch job with no error at all** — the
  Vertex AI client had no request timeout configured, so retry logic that only triggers on an
  exception never got the chance to engage. Fixed with an explicit timeout.
- **Deployed code can drift from local code** — we caught a real gap where hours of local
  work (new tools, a whole new UI page) had never actually reached the live URLs, discovered
  only by checking the production endpoints directly rather than trusting local test success.

## Accomplishments we're proud of

- Every one of the "no fabricated numbers" guardrails held under a **real** failure, not a
  staged one — a genuine ClickHouse cold-start timeout produced an honest "couldn't retrieve
  the data" instead of an invented answer.
- The percentile/similarity tools were verified through the **full agent orchestration path**,
  not just direct calls — asking a natural, ambiguous question live gets the agent to
  correctly chain a lookup query into a percentile computation on its own.

## What's next

- User draft upload (`is_corpus=0`), comparing a real in-progress screenplay against the
  corpus, not just exploring produced films.
- A larger, more genre-balanced corpus.
- Brush-to-select on the chart (currently click-to-drill only).

## Built with

Google Agent Development Kit (ADK) · Gemini (Vertex AI) · Vertex AI Embeddings ·
ClickHouse Cloud · ClickHouse MCP Server · Next.js · FastAPI · Google Cloud Run ·
Google Secret Manager · NRC VAD Lexicon (emotional scoring)

---

## Notes for filling out the form

- **Video:** link the ≤3-min recording (see `docs/demo-video-script.md` for the shot list;
  raw screen-capture footage of the live product may already exist in the session scratch
  files — check before re-recording from scratch).
- **Try it out link:** https://agent-cinema-web-742393615246.us-central1.run.app
- **GitHub repo:** confirm it's set to Public before submitting (unresolved as of this draft).
- **Track:** ClickHouse.
