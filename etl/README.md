# ETL — corpus pipeline (Slice 2, not yet built)

Offline pipeline that turns a parsed screenplay dataset into `script_nodes` rows with `is_corpus=1`.

Planned stages (see `docs/plans/agentic-cinema-screenplay-map.md` §6, Slice 2):

1. `acquire`      — pull a parsed dataset (pending Q1: ScriptBase / ScreenPy / pre-parsed IMSDb).
2. `parse_script` — segment into scenes + the four screenplay elements.
3. `build_tree`   — scene → sequence → act → film.
4. `score_valence`— NRC VAD lexicon (deterministic; no LLM).
5. `embed`        — Vertex AI text-embedding (pin model + dim: Q4).
6. `aggregate_parents` — parent numbers = SQL AVG/SUM (never LLM).
7. `summarize`    — Gemini, prose only.
8. `load`         — idempotent insert, `is_corpus=1`.

Invariant to assert after loading: `parent.valence ≈ AVG(child.valence)`.
