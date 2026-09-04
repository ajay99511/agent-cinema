# Demo video script (≤3 min)

Devpost/judging requirement: problem → user → live demo *showing SQL* → architecture flash.
Record against the deployed URLs, not localhost, once the full corpus has loaded (see
`features/PROGRESS.md` for current status) — swap in a fresh screen recording if any exact
numbers below drift after the full 25-film load finishes.

Live URLs: https://agent-cinema-web-742393615246.us-central1.run.app (app),
https://screenplay-agent-742393615246.us-central1.run.app (agent API, not shown on camera).

---

## 0:00–0:20 — Problem

**Voiceover:** "A screenwriter mid-rewrite can tell you a scene *feels* flat. They can't tell
you *why*, or whether it's actually a problem — because there's nothing to compare it to."

**Visual:** a blank page / a script PDF scrolling, no data, just prose.

## 0:20–0:35 — User & idea

**Voiceover:** "Agentic Cinema gives them that comparison: an interactive structural and
emotional map of their draft, scored against a real corpus of produced films — not a
0-to-10 score, a real percentile: 'this scene is in the bottom 5% for conflict among Act II
scenes in produced dramas.'"

**Visual:** cut to the live `/map` page.

## 0:35–2:10 — Live demo (the core segment)

1. **Film picker → 3-act chart.** Select a film (e.g. *American Beauty*). Two small charts
   appear: valence and conflict across the 3 acts. Narrate: "Every point here is a live
   ClickHouse row — nothing is precomputed."
2. **Drill down.** Click an act → sequences appear. Click a sequence → individual scenes
   appear, each with its own valence/conflict. Hover a point → tooltip shows the scene
   heading and a one-line summary (Gemini-written, from the real scene text).
3. **Show the SQL.** Expand the "Show SQL" panel. Point at the literal query text: "This is
   exactly what ran against ClickHouse — not reconstructed for the video."
4. **Switch to the Q&A page (`/`).** Ask a question live, on camera, not pre-typed:
   *"Which scene in [film] has the lowest valence?"* — show the answer, then expand its SQL
   panel too.
5. **The differentiator: ask a percentile question.** *"How does that scene's conflict
   compare to other scenes at the same point in similar films?"* — the agent chains a lookup
   query, then the `scene_percentiles` tool, and answers with a real percentile + cohort size
   (e.g. "4th percentile, compared to 363 drama scenes"). Expand SQL — **all** of the queries
   show, including the percentile tool's, not just the lookup.

**Narration thread through this segment:** "Every number you just saw — the chart, the
tooltip, the answer, the percentile — came from a live SQL query against ClickHouse. If the
backend goes down, this page shows nothing. It's not allowed to fake it."

## 2:10–2:50 — Architecture flash

**Visual:** `docs/architecture.svg` (also embedded in the README) — full-screen it for this segment.

- **Next.js** (Cloud Run) — the UI you just saw.
- **ADK agent** (Cloud Run) — Gemini via **Vertex AI**, with two kinds of tools: the
  ClickHouse **MCP server** for open-ended questions, and hand-written percentile/similarity
  tools for the comparative queries where correctness matters most.
- **ClickHouse Cloud** — one `script_nodes` table holds the whole corpus *and* the tree
  structure (scene → sequence → act → film) — no separate metadata store.
- **The corpus** — built by an offline pipeline: screenplay text → NRC VAD emotional scoring
  (deterministic, not LLM-guessed) → Vertex embeddings → Gemini prose summaries → loaded with
  every parent number as a real `AVG()`/`SUM()` over its children.

**Line to land:** "Every AI call is Google — Gemini and Vertex embeddings. Every number the
user sees is ClickHouse, live, at request time."

## 2:50–3:00 — Close

**Voiceover:** "Agentic Cinema — a screenwriter's draft, mapped against real produced films,
one live query at a time." — show the Devpost/repo link card.

---

## Recording notes

- Ask the *live* questions genuinely live (don't just show a pre-canned screenshot) — a judge
  re-running the same question should get the same shape of answer, which is the whole point.
- Keep the SQL panel visible long enough to actually read a couple of lines, not a half-second
  flash.
- If a percentile query happens to land on `insufficient_corpus` for whatever scene gets
  picked live, that's fine to show too — it's the honesty guardrail working, not a bug. Say so
  on camera rather than re-recording to dodge it.
